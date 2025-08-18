"""
Remote Debugging System for heyBuddy Raspberry Pi Devices
Provides secure remote access for development and troubleshooting
"""
import asyncio
import logging
import json
import psutil
import os
import socket
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path
import subprocess
import aiofiles
from fastapi import WebSocket
from core.config import settings

logger = logging.getLogger(__name__)


class SystemMonitor:
    """Monitor system health and performance metrics"""
    
    @staticmethod
    async def get_system_info() -> Dict[str, Any]:
        """Get comprehensive system information"""
        try:
            result = {
                "timestamp": datetime.now().isoformat(),
                "cpu": {},
                "memory": {},
                "disk": {},
                "network": {},
                "top_processes": [],
                "uptime_hours": None
            }
            
            # CPU Information
            try:
                cpu_percent = psutil.cpu_percent(interval=0.1)  # Shorter interval
                cpu_count = psutil.cpu_count()
                cpu_freq = psutil.cpu_freq()
                
                result["cpu"] = {
                    "usage_percent": round(cpu_percent, 1),
                    "count": cpu_count,
                    "frequency_mhz": round(cpu_freq.current, 1) if cpu_freq and cpu_freq.current else None,
                    "temperature_celsius": await SystemMonitor._get_pi_temperature()
                }
            except Exception as e:
                logger.warning(f"Error getting CPU info: {e}")
                result["cpu"] = {"error": str(e)}
            
            # Memory Information
            try:
                memory = psutil.virtual_memory()
                swap = psutil.swap_memory()
                
                result["memory"] = {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "used_percent": round(memory.percent, 1),
                    "swap_used_percent": round(swap.percent, 1)
                }
            except Exception as e:
                logger.warning(f"Error getting memory info: {e}")
                result["memory"] = {"error": str(e)}
            
            # Disk Information
            try:
                disk = psutil.disk_usage('/')
                
                result["disk"] = {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "used_percent": round((disk.used / disk.total) * 100, 1)
                }
            except Exception as e:
                logger.warning(f"Error getting disk info: {e}")
                result["disk"] = {"error": str(e)}
            
            # Network Information
            try:
                network_stats = psutil.net_io_counters()
                
                result["network"] = {
                    "bytes_sent": network_stats.bytes_sent,
                    "bytes_recv": network_stats.bytes_recv,
                    "packets_sent": network_stats.packets_sent,
                    "packets_recv": network_stats.packets_recv
                }
            except Exception as e:
                logger.warning(f"Error getting network info: {e}")
                result["network"] = {"error": str(e)}
            
            # Uptime
            try:
                boot_time = psutil.boot_time()
                if boot_time:
                    uptime_seconds = (datetime.now() - datetime.fromtimestamp(boot_time)).total_seconds()
                    result["uptime_hours"] = round(uptime_seconds / 3600, 1)
            except Exception as e:
                logger.warning(f"Error getting uptime: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}
    
    @staticmethod
    async def _get_pi_temperature() -> Optional[float]:
        """Get Raspberry Pi CPU temperature"""
        try:
            if Path("/sys/class/thermal/thermal_zone0/temp").exists():
                async with aiofiles.open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                    temp_str = await f.read()
                    return round(float(temp_str.strip()) / 1000, 1)
        except Exception:
            pass
        return None


class LogStreamer:
    """Stream application logs in real-time"""
    
    def __init__(self):
        self.log_file = "/opt/heybuddy/logs/app.log"
        self.active_streams: Dict[str, WebSocket] = {}
    
    async def add_stream(self, stream_id: str, websocket: WebSocket):
        """Add a new log stream"""
        self.active_streams[stream_id] = websocket
        logger.info(f"Added log stream: {stream_id}")
    
    async def remove_stream(self, stream_id: str):
        """Remove a log stream"""
        if stream_id in self.active_streams:
            del self.active_streams[stream_id]
            logger.info(f"Removed log stream: {stream_id}")
    
    async def stream_logs(self, websocket: WebSocket, lines: int = 100):
        """Stream recent logs and follow new ones"""
        try:
            # Send recent logs first
            if Path(self.log_file).exists():
                result = subprocess.run(
                    ["tail", "-n", str(lines), self.log_file],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        if line.strip():
                            await websocket.send_json({
                                "type": "log_line",
                                "data": {
                                    "line": line,
                                    "timestamp": datetime.now().isoformat(),
                                    "source": "historical"
                                }
                            })
            
            # Follow new logs
            process = None
            try:
                process = await asyncio.create_subprocess_exec(
                    "tail", "-f", self.log_file,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                while True:
                    line = await process.stdout.readline()
                    if not line:
                        break
                    
                    log_line = line.decode().strip()
                    if log_line:
                        await websocket.send_json({
                            "type": "log_line",
                            "data": {
                                "line": log_line,
                                "timestamp": datetime.now().isoformat(),
                                "source": "live"
                            }
                        })
                        
            except asyncio.CancelledError:
                if process:
                    process.terminate()
                    await process.wait()
                raise
                
        except Exception as e:
            logger.error(f"Error streaming logs: {e}")
            await websocket.send_json({
                "type": "error",
                "data": {"message": f"Log streaming error: {str(e)}"}
            })


class ServiceController:
    """Control heyBuddy services remotely"""
    
    @staticmethod
    async def get_service_status() -> Dict[str, Any]:
        """Get status of heyBuddy services"""
        try:
            services = {
                "heybuddy": await ServiceController._get_systemd_status("heybuddy"),
                "heybuddy-updater": await ServiceController._get_systemd_status("heybuddy-updater"),
            }
            
            # Check if main application is responding
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get("http://localhost:8080/health", timeout=5) as response:
                        if response.status == 200:
                            health_data = await response.json()
                            services["application_health"] = health_data
                        else:
                            services["application_health"] = {"status": "unhealthy", "http_status": response.status}
            except Exception as e:
                services["application_health"] = {"status": "unreachable", "error": str(e)}
            
            return services
            
        except Exception as e:
            logger.error(f"Error getting service status: {e}")
            return {"error": str(e)}
    
    @staticmethod
    async def _get_systemd_status(service_name: str) -> Dict[str, Any]:
        """Get systemd service status"""
        try:
            result = subprocess.run(
                ["systemctl", "is-active", service_name],
                capture_output=True,
                text=True
            )
            
            status = result.stdout.strip()
            
            # Get more detailed info
            result_detail = subprocess.run(
                ["systemctl", "status", service_name, "--no-pager", "-l"],
                capture_output=True,
                text=True
            )
            
            return {
                "name": service_name,
                "status": status,
                "active": status == "active",
                "details": result_detail.stdout if result_detail.returncode == 0 else None
            }
            
        except Exception as e:
            return {
                "name": service_name,
                "status": "error",
                "active": False,
                "error": str(e)
            }
    
    @staticmethod
    async def restart_service(service_name: str) -> Dict[str, Any]:
        """Restart a heyBuddy service"""
        try:
            if service_name not in ["heybuddy", "heybuddy-updater"]:
                return {"success": False, "error": "Invalid service name"}
            
            result = subprocess.run(
                ["sudo", "systemctl", "restart", service_name],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully restarted service: {service_name}")
                return {"success": True, "message": f"Service {service_name} restarted"}
            else:
                logger.error(f"Failed to restart service {service_name}: {result.stderr}")
                return {"success": False, "error": result.stderr}
                
        except Exception as e:
            logger.error(f"Error restarting service {service_name}: {e}")
            return {"success": False, "error": str(e)}


class NetworkDiagnostics:
    """Network connectivity and diagnostics"""
    
    @staticmethod
    async def get_network_info() -> Dict[str, Any]:
        """Get network connectivity information"""
        try:
            # Get network interfaces
            interfaces = {}
            for interface, addrs in psutil.net_if_addrs().items():
                interface_info = {
                    "addresses": [],
                    "stats": psutil.net_if_stats().get(interface, {})._asdict() if interface in psutil.net_if_stats() else {}
                }
                
                for addr in addrs:
                    interface_info["addresses"].append({
                        "family": str(addr.family),
                        "address": addr.address,
                        "netmask": addr.netmask,
                        "broadcast": addr.broadcast
                    })
                
                interfaces[interface] = interface_info
            
            # Test connectivity
            connectivity = {
                "internet": await NetworkDiagnostics._test_connectivity("8.8.8.8", 53),
                "openai_api": await NetworkDiagnostics._test_connectivity("api.openai.com", 443),
                "github": await NetworkDiagnostics._test_connectivity("api.github.com", 443)
            }
            
            return {
                "interfaces": interfaces,
                "connectivity": connectivity,
                "hostname": socket.gethostname(),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting network info: {e}")
            return {"error": str(e)}
    
    @staticmethod
    async def _test_connectivity(host: str, port: int, timeout: int = 5) -> Dict[str, Any]:
        """Test connectivity to a specific host and port"""
        try:
            start_time = datetime.now()
            
            # Create connection
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=timeout
            )
            
            # Close connection
            writer.close()
            await writer.wait_closed()
            
            end_time = datetime.now()
            latency = (end_time - start_time).total_seconds() * 1000
            
            return {
                "host": host,
                "port": port,
                "reachable": True,
                "latency_ms": round(latency, 2)
            }
            
        except Exception as e:
            return {
                "host": host,
                "port": port,
                "reachable": False,
                "error": str(e)
            }


class RemoteDebugger:
    """Main remote debugging coordinator"""
    
    def __init__(self):
        self.system_monitor = SystemMonitor()
        self.log_streamer = LogStreamer()
        self.service_controller = ServiceController()
        self.network_diagnostics = NetworkDiagnostics()
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
    
    async def start_debug_session(self, session_id: str, websocket: WebSocket) -> Dict[str, Any]:
        """Start a new remote debugging session"""
        try:
            session_info = {
                "id": session_id,
                "started": datetime.now().isoformat(),
                "websocket": websocket,
                "authenticated": True,  # In production, implement proper auth
                "capabilities": [
                    "system_monitoring",
                    "log_streaming", 
                    "service_control",
                    "network_diagnostics"
                ]
            }
            
            self.active_sessions[session_id] = session_info
            
            # Send initial system snapshot
            system_info = await self.system_monitor.get_system_info()
            service_status = await self.service_controller.get_service_status()
            network_info = await self.network_diagnostics.get_network_info()
            
            await websocket.send_json({
                "type": "session_started",
                "data": {
                    "session_id": session_id,
                    "system_info": system_info,
                    "service_status": service_status,
                    "network_info": network_info
                }
            })
            
            logger.info(f"Remote debugging session started: {session_id}")
            return {"success": True, "session_id": session_id}
            
        except Exception as e:
            logger.error(f"Error starting debug session: {e}")
            return {"success": False, "error": str(e)}
    
    async def end_debug_session(self, session_id: str):
        """End a remote debugging session"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            await self.log_streamer.remove_stream(session_id)
            logger.info(f"Remote debugging session ended: {session_id}")
    
    async def handle_debug_command(self, session_id: str, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle debug commands from remote session"""
        try:
            if session_id not in self.active_sessions:
                return {"success": False, "error": "Invalid session"}
            
            if command == "get_system_info":
                data = await self.system_monitor.get_system_info()
                return {"success": True, "data": data}
                
            elif command == "get_service_status":
                data = await self.service_controller.get_service_status()
                return {"success": True, "data": data}
                
            elif command == "restart_service":
                service_name = params.get("service_name")
                if not service_name:
                    return {"success": False, "error": "service_name required"}
                data = await self.service_controller.restart_service(service_name)
                return data
                
            elif command == "get_network_info":
                data = await self.network_diagnostics.get_network_info()
                return {"success": True, "data": data}
                
            elif command == "stream_logs":
                websocket = self.active_sessions[session_id]["websocket"]
                await self.log_streamer.add_stream(session_id, websocket)
                await self.log_streamer.stream_logs(websocket, params.get("lines", 100))
                return {"success": True, "message": "Log streaming started"}
                
            else:
                return {"success": False, "error": f"Unknown command: {command}"}
                
        except Exception as e:
            logger.error(f"Error handling debug command {command}: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_debug_snapshot(self) -> Dict[str, Any]:
        """Get a complete system debug snapshot"""
        try:
            snapshot = {
                "timestamp": datetime.now().isoformat(),
                "system": await self.system_monitor.get_system_info(),
                "services": await self.service_controller.get_service_status(),
                "network": await self.network_diagnostics.get_network_info(),
                "application": {
                    "version": settings.version,
                    "environment": settings.environment,
                    "language": settings.language,
                    "debug_mode": settings.debug
                },
                "active_sessions": len(self.active_sessions)
            }
            
            return snapshot
            
        except Exception as e:
            logger.error(f"Error creating debug snapshot: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}


# Global instance
remote_debugger = RemoteDebugger()