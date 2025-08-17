#!/usr/bin/env python3
"""
heyBuddy AI Companion - Main Application Entry Point
"""
import asyncio
import logging
import signal
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent))

from core.config import settings
from core.audio import AudioManager
from api.app import create_app
from database.local_db import LocalDatabase


class HeyBuddyApp:
    """Main application class"""
    
    def __init__(self):
        self.audio_manager: AudioManager = None
        self.database: LocalDatabase = None
        self.api_server = None
        self.running = False
        self.setup_logging()
        
    def setup_logging(self):
        """Configure logging"""
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        
        if settings.log_file:
            logging.basicConfig(
                level=getattr(logging, settings.log_level),
                format=log_format,
                filename=settings.log_file,
                filemode='a'
            )
        else:
            logging.basicConfig(
                level=getattr(logging, settings.log_level),
                format=log_format
            )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"heyBuddy v{settings.version} starting up")
        self.logger.info(f"Environment: {settings.environment}")
    
    async def initialize(self) -> bool:
        """Initialize all components"""
        try:
            # Initialize database
            self.logger.info("Initializing database...")
            self.database = LocalDatabase()
            if not await self.database.initialize():
                self.logger.error("Failed to initialize database")
                return False
            
            # Initialize audio manager
            self.logger.info("Initializing audio system...")
            self.audio_manager = AudioManager(
                device_type=settings.audio_device,
                sample_rate=settings.sample_rate
            )
            
            if not await self.audio_manager.initialize():
                self.logger.error("Failed to initialize audio system")
                return False
            
            # Initialize API server
            self.logger.info("Initializing API server...")
            self.api_server = create_app(self.audio_manager, self.database)
            
            # Notify systemd if enabled
            if settings.enable_systemd_notify:
                try:
                    import systemd.daemon
                    systemd.daemon.notify('READY=1')
                    systemd.daemon.notify('STATUS=heyBuddy is ready')
                    self.logger.info("Notified systemd of successful startup")
                except ImportError:
                    self.logger.warning("systemd-python not available")
            
            self.logger.info("heyBuddy initialization completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize heyBuddy: {e}")
            return False
    
    async def start_health_monitor(self):
        """Start health monitoring task"""
        while self.running:
            try:
                # Check audio device health
                audio_ok = await self.audio_manager.is_device_available()
                
                # Update systemd status if enabled
                if settings.enable_systemd_notify:
                    try:
                        import systemd.daemon
                        if audio_ok:
                            systemd.daemon.notify('WATCHDOG=1')
                            systemd.daemon.notify('STATUS=All systems operational')
                        else:
                            systemd.daemon.notify('STATUS=Audio device unavailable')
                            self.logger.warning("Audio device health check failed")
                    except ImportError:
                        pass
                
                await asyncio.sleep(settings.health_check_interval)
                
            except Exception as e:
                self.logger.error(f"Health check error: {e}")
                await asyncio.sleep(settings.health_check_interval)
    
    async def run(self):
        """Main application run loop"""
        self.running = True
        
        # Setup signal handlers
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, self.signal_handler)
        
        try:
            # Start health monitoring
            health_task = asyncio.create_task(self.start_health_monitor())
            
            # Start API server
            import uvicorn
            config = uvicorn.Config(
                self.api_server,
                host=settings.api_host,
                port=settings.api_port,
                log_level=settings.log_level.lower(),
                access_log=True
            )
            server = uvicorn.Server(config)
            
            self.logger.info(f"Starting API server on {settings.api_host}:{settings.api_port}")
            
            # Run server and health monitor concurrently
            await asyncio.gather(
                server.serve(),
                health_task,
                return_exceptions=True
            )
            
        except Exception as e:
            self.logger.error(f"Application error: {e}")
            raise
        finally:
            await self.cleanup()
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
        
        # Notify systemd of shutdown
        if settings.enable_systemd_notify:
            try:
                import systemd.daemon
                systemd.daemon.notify('STOPPING=1')
                systemd.daemon.notify('STATUS=Shutting down')
            except ImportError:
                pass
    
    async def cleanup(self):
        """Cleanup resources"""
        self.logger.info("Cleaning up resources...")
        
        if self.audio_manager:
            await self.audio_manager.cleanup()
        
        if self.database:
            await self.database.cleanup()
        
        self.logger.info("heyBuddy shutdown completed")


async def main():
    """Main entry point"""
    app = HeyBuddyApp()
    
    # Initialize application
    if not await app.initialize():
        sys.exit(1)
    
    # Run application
    try:
        await app.run()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logging.error(f"Unhandled error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())