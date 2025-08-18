"""
Over-The-Air (OTA) Update System for heyBuddy Raspberry Pi devices
Secure, reliable updates with rollback capability
"""
import os
import sys
import json
import hashlib
import logging
import asyncio
import aiofiles
import aiohttp
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
import subprocess
import shutil
import tempfile
from core.config import settings

logger = logging.getLogger(__name__)


class OTAUpdater:
    """Secure OTA update system for Raspberry Pi deployment"""
    
    def __init__(self):
        self.github_repo = "chrisperkles/heybuddy"
        self.current_version = settings.version
        self.update_api_url = f"https://api.github.com/repos/{self.github_repo}/releases"
        self.install_path = Path("/opt/heybuddy")
        self.backup_path = Path("/opt/heybuddy.backups")
        self.temp_path = Path("/tmp/heybuddy-update")
        self.lock_file = Path("/var/lock/heybuddy-update.lock")
        
    async def check_for_updates(self) -> Optional[Dict[str, Any]]:
        """Check GitHub for new releases"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.update_api_url}/latest") as response:
                    if response.status == 200:
                        release_data = await response.json()
                        latest_version = release_data["tag_name"].lstrip("v")
                        
                        if self._is_newer_version(latest_version, self.current_version):
                            logger.info(f"New version available: {latest_version} (current: {self.current_version})")
                            return {
                                "version": latest_version,
                                "download_url": self._get_download_url(release_data),
                                "release_notes": release_data.get("body", ""),
                                "published_at": release_data["published_at"],
                                "prerelease": release_data.get("prerelease", False)
                            }
                        else:
                            logger.info(f"Already up to date: {self.current_version}")
                            return None
                    else:
                        logger.error(f"Failed to check for updates: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            return None
    
    def _is_newer_version(self, latest: str, current: str) -> bool:
        """Compare version strings (semantic versioning)"""
        def version_tuple(v):
            return tuple(map(int, v.split('.')))
        
        try:
            return version_tuple(latest) > version_tuple(current)
        except ValueError:
            logger.warning(f"Invalid version format: latest={latest}, current={current}")
            return False
    
    def _get_download_url(self, release_data: Dict) -> Optional[str]:
        """Extract download URL from GitHub release"""
        assets = release_data.get("assets", [])
        
        # Look for source code tarball
        for asset in assets:
            if asset["name"].endswith(".tar.gz") and "source" in asset["name"].lower():
                return asset["browser_download_url"]
        
        # Fallback to tarball_url
        return release_data.get("tarball_url")
    
    async def download_update(self, download_url: str, expected_version: str) -> Optional[Path]:
        """Download and verify update package"""
        if self.lock_file.exists():
            logger.error("Update already in progress")
            return None
        
        try:
            # Create lock file
            self.lock_file.touch()
            
            # Create temp directory
            self.temp_path.mkdir(exist_ok=True)
            update_file = self.temp_path / f"heybuddy-{expected_version}.tar.gz"
            
            logger.info(f"Downloading update from {download_url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(download_url) as response:
                    if response.status == 200:
                        async with aiofiles.open(update_file, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                await f.write(chunk)
                        
                        logger.info(f"Downloaded update: {update_file}")
                        
                        # Verify download
                        if await self._verify_update(update_file):
                            return update_file
                        else:
                            logger.error("Update verification failed")
                            return None
                    else:
                        logger.error(f"Download failed: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error downloading update: {e}")
            return None
        finally:
            # Remove lock file
            if self.lock_file.exists():
                self.lock_file.unlink()
    
    async def _verify_update(self, update_file: Path) -> bool:
        """Verify integrity of downloaded update"""
        try:
            # Basic verification - check if it's a valid tar.gz
            result = subprocess.run(
                ["tar", "-tzf", str(update_file)],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info("Update package verification passed")
                return True
            else:
                logger.error(f"Update verification failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error verifying update: {e}")
            return False
    
    async def create_backup(self) -> Optional[Path]:
        """Create backup of current installation"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = self.backup_path / f"backup_{timestamp}"
            backup_dir.parent.mkdir(exist_ok=True)
            
            logger.info(f"Creating backup: {backup_dir}")
            
            # Copy current installation
            shutil.copytree(self.install_path, backup_dir, symlinks=True)
            
            # Create backup metadata
            metadata = {
                "version": self.current_version,
                "created_at": datetime.now().isoformat(),
                "path": str(backup_dir)
            }
            
            metadata_file = backup_dir / "backup_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Backup created successfully: {backup_dir}")
            return backup_dir
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return None
    
    async def apply_update(self, update_file: Path, backup_dir: Path) -> bool:
        """Apply update with rollback capability"""
        try:
            logger.info("Stopping heyBuddy service...")
            subprocess.run(["systemctl", "stop", "heybuddy"], check=True)
            
            # Extract update to temporary location
            extract_dir = self.temp_path / "extracted"
            extract_dir.mkdir(exist_ok=True)
            
            logger.info(f"Extracting update: {update_file}")
            result = subprocess.run([
                "tar", "-xzf", str(update_file), "-C", str(extract_dir), "--strip-components=1"
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Failed to extract update: {result.stderr}")
                return False
            
            # Apply update
            logger.info("Applying update...")
            
            # Remove old installation (except data directory)
            for item in self.install_path.iterdir():
                if item.name not in ["data", "logs", "config"]:
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
            
            # Copy new files
            for item in extract_dir.iterdir():
                if item.name not in ["data", "logs"]:  # Preserve user data
                    dest = self.install_path / item.name
                    if item.is_dir():
                        shutil.copytree(item, dest, dirs_exist_ok=True)
                    else:
                        shutil.copy2(item, dest)
            
            # Update permissions
            shutil.chown(self.install_path, user="heybuddy", group="heybuddy")
            subprocess.run(["chmod", "+x", str(self.install_path / "scripts" / "*.sh")], shell=True)
            
            logger.info("Update applied successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error applying update: {e}")
            return False
    
    async def test_update(self) -> bool:
        """Test if update was successful"""
        try:
            logger.info("Starting heyBuddy service...")
            subprocess.run(["systemctl", "start", "heybuddy"], check=True)
            
            # Wait for service to start
            await asyncio.sleep(10)
            
            # Test health endpoint
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get("http://localhost:8080/health", timeout=30) as response:
                        if response.status == 200:
                            health_data = await response.json()
                            if health_data.get("status") == "healthy":
                                logger.info("Update test passed - service is healthy")
                                return True
                            else:
                                logger.error(f"Health check failed: {health_data}")
                                return False
                        else:
                            logger.error(f"Health endpoint returned {response.status}")
                            return False
                except asyncio.TimeoutError:
                    logger.error("Health check timed out")
                    return False
                    
        except Exception as e:
            logger.error(f"Error testing update: {e}")
            return False
    
    async def rollback_update(self, backup_dir: Path) -> bool:
        """Rollback to previous version"""
        try:
            logger.info(f"Rolling back to backup: {backup_dir}")
            
            # Stop service
            subprocess.run(["systemctl", "stop", "heybuddy"], check=True)
            
            # Remove current installation
            shutil.rmtree(self.install_path)
            
            # Restore from backup
            shutil.copytree(backup_dir, self.install_path, symlinks=True)
            
            # Restore permissions
            shutil.chown(self.install_path, user="heybuddy", group="heybuddy")
            
            # Restart service
            subprocess.run(["systemctl", "start", "heybuddy"], check=True)
            
            logger.info("Rollback completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error during rollback: {e}")
            return False
    
    async def cleanup_old_backups(self, keep_count: int = 3):
        """Cleanup old backups, keeping only the most recent ones"""
        try:
            if not self.backup_path.exists():
                return
            
            backups = sorted(
                [d for d in self.backup_path.iterdir() if d.is_dir()],
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            # Remove old backups
            for backup in backups[keep_count:]:
                logger.info(f"Removing old backup: {backup}")
                shutil.rmtree(backup)
                
        except Exception as e:
            logger.error(f"Error cleaning up backups: {e}")
    
    async def perform_update(self) -> Dict[str, Any]:
        """Perform complete update process"""
        result = {
            "success": False,
            "version_before": self.current_version,
            "version_after": None,
            "error": None,
            "rollback_performed": False
        }
        
        try:
            # Check for updates
            update_info = await self.check_for_updates()
            if not update_info:
                result["error"] = "No updates available"
                return result
            
            new_version = update_info["version"]
            logger.info(f"Starting update to version {new_version}")
            
            # Download update
            update_file = await self.download_update(update_info["download_url"], new_version)
            if not update_file:
                result["error"] = "Failed to download update"
                return result
            
            # Create backup
            backup_dir = await self.create_backup()
            if not backup_dir:
                result["error"] = "Failed to create backup"
                return result
            
            # Apply update
            if not await self.apply_update(update_file, backup_dir):
                result["error"] = "Failed to apply update"
                return result
            
            # Test update
            if await self.test_update():
                result["success"] = True
                result["version_after"] = new_version
                logger.info(f"Update to {new_version} completed successfully")
                
                # Cleanup
                await self.cleanup_old_backups()
                if self.temp_path.exists():
                    shutil.rmtree(self.temp_path)
            else:
                # Rollback on test failure
                logger.error("Update test failed, rolling back...")
                if await self.rollback_update(backup_dir):
                    result["rollback_performed"] = True
                    result["error"] = "Update failed validation, rolled back successfully"
                else:
                    result["error"] = "Update failed and rollback failed - manual intervention required"
            
        except Exception as e:
            logger.error(f"Unexpected error during update: {e}")
            result["error"] = f"Unexpected error: {str(e)}"
        
        return result


async def main():
    """CLI interface for OTA updater"""
    import argparse
    
    parser = argparse.ArgumentParser(description="heyBuddy OTA Updater")
    parser.add_argument("--check", action="store_true", help="Check for updates")
    parser.add_argument("--update", action="store_true", help="Perform update")
    parser.add_argument("--simulate", action="store_true", help="Simulate update (testing)")
    
    args = parser.parse_args()
    
    updater = OTAUpdater()
    
    if args.check:
        update_info = await updater.check_for_updates()
        if update_info:
            print(f"Update available: {update_info['version']}")
            print(f"Release notes: {update_info['release_notes'][:200]}...")
        else:
            print("No updates available")
    
    elif args.update:
        result = await updater.perform_update()
        print(json.dumps(result, indent=2))
    
    elif args.simulate:
        print("Simulating update process...")
        # Simulate update without actually applying it
        update_info = await updater.check_for_updates()
        if update_info:
            print(f"Would update to: {update_info['version']}")
        backup_dir = await updater.create_backup()
        if backup_dir:
            print(f"Backup created: {backup_dir}")


if __name__ == "__main__":
    asyncio.run(main())