"""
Debug API routes for remote development and troubleshooting
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from typing import Dict, Any
import logging
import json
import uuid
from pathlib import Path

from services.remote_debug import remote_debugger
from core.config import settings

logger = logging.getLogger(__name__)


def create_debug_router() -> APIRouter:
    """Create debug router for development tools"""
    router = APIRouter(prefix="/debug", tags=["debug"])
    
    # Only enable debug routes in development or when explicitly enabled
    if not settings.debug and settings.environment != "development":
        logger.warning("Debug routes disabled in production")
        return router
    
    @router.get("/")
    async def debug_dashboard():
        """Serve the debug dashboard"""
        debug_html_path = Path(__file__).parent.parent.parent / "web_dashboard" / "debug.html"
        if debug_html_path.exists():
            with open(debug_html_path, 'r', encoding='utf-8') as f:
                return HTMLResponse(content=f.read())
        else:
            raise HTTPException(status_code=404, detail="Debug dashboard not found")
    
    @router.websocket("/ws/{session_id}")
    async def debug_websocket(websocket: WebSocket, session_id: str):
        """WebSocket endpoint for real-time debugging"""
        await websocket.accept()
        
        try:
            # Start debug session
            await remote_debugger.start_debug_session(session_id, websocket)
            
            # Handle incoming messages
            while True:
                try:
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    if message.get("type") == "debug_command":
                        command = message.get("command")
                        params = message.get("params", {})
                        
                        result = await remote_debugger.handle_debug_command(
                            session_id, command, params
                        )
                        
                        await websocket.send_json({
                            "type": "command_result",
                            "command": command,
                            "result": result
                        })
                        
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.error(f"Error handling debug WebSocket message: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "data": {"message": str(e)}
                    })
                    
        except WebSocketDisconnect:
            pass
        except Exception as e:
            logger.error(f"Debug WebSocket error: {e}")
        finally:
            await remote_debugger.end_debug_session(session_id)
    
    @router.get("/snapshot")
    async def get_debug_snapshot():
        """Get a complete system debug snapshot"""
        try:
            snapshot = await remote_debugger.get_debug_snapshot()
            return snapshot
        except Exception as e:
            logger.error(f"Error creating debug snapshot: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/system")
    async def get_system_info():
        """Get current system information"""
        try:
            system_info = await remote_debugger.system_monitor.get_system_info()
            return system_info
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/services")
    async def get_service_status():
        """Get status of all heyBuddy services"""
        try:
            service_status = await remote_debugger.service_controller.get_service_status()
            return service_status
        except Exception as e:
            logger.error(f"Error getting service status: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/services/{service_name}/restart")
    async def restart_service(service_name: str):
        """Restart a specific service"""
        try:
            result = await remote_debugger.service_controller.restart_service(service_name)
            return result
        except Exception as e:
            logger.error(f"Error restarting service {service_name}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/network")
    async def get_network_info():
        """Get network connectivity information"""
        try:
            network_info = await remote_debugger.network_diagnostics.get_network_info()
            return network_info
        except Exception as e:
            logger.error(f"Error getting network info: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/logs")
    async def get_logs_page():
        """Serve a simple logs viewing page"""
        html_content = """
        <!DOCTYPE html>
        <html lang="de">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>heyBuddy System Logs</title>
            <script src="https://cdn.tailwindcss.com"></script>
            <style>
                .log-line { font-family: 'Courier New', monospace; font-size: 12px; }
            </style>
        </head>
        <body class="bg-gray-900 text-white">
            <div class="container mx-auto px-4 py-6">
                <h1 class="text-2xl font-bold mb-6">heyBuddy System Logs</h1>
                <div class="bg-gray-800 rounded-lg p-6">
                    <div class="flex justify-between items-center mb-4">
                        <h2 class="text-xl">Live Application Logs</h2>
                        <button onclick="refreshLogs()" class="px-4 py-2 bg-blue-600 rounded hover:bg-blue-700">
                            Aktualisieren
                        </button>
                    </div>
                    <div id="logs" class="bg-gray-900 rounded p-4 h-96 overflow-y-auto">
                        <div class="text-gray-500">Logs werden geladen...</div>
                    </div>
                </div>
            </div>
            
            <script>
                function refreshLogs() {
                    fetch('/debug/logs/raw')
                        .then(response => response.text())
                        .then(data => {
                            const logContainer = document.getElementById('logs');
                            const lines = data.split('\\n').map(line => 
                                `<div class="log-line text-gray-300">${line}</div>`
                            ).join('');
                            logContainer.innerHTML = lines || '<div class="text-gray-500">Keine Logs verfügbar</div>';
                            logContainer.scrollTop = logContainer.scrollHeight;
                        })
                        .catch(error => {
                            document.getElementById('logs').innerHTML = 
                                '<div class="text-red-500">Fehler beim Laden der Logs: ' + error + '</div>';
                        });
                }
                
                // Auto-refresh every 10 seconds
                setInterval(refreshLogs, 10000);
                
                // Initial load
                refreshLogs();
            </script>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)
    
    @router.get("/logs/raw")
    async def get_raw_logs():
        """Get raw log content"""
        try:
            log_file = Path("/opt/heybuddy/logs/app.log")
            if not log_file.exists():
                # Development fallback
                log_file = Path("logs/heybuddy.log")
            
            if log_file.exists():
                with open(log_file, 'r') as f:
                    # Return last 200 lines
                    lines = f.readlines()
                    return "".join(lines[-200:])
            else:
                return "Log file not found"
                
        except Exception as e:
            return f"Error reading logs: {str(e)}"
    
    @router.get("/health")
    async def debug_health_check():
        """Extended health check for debugging"""
        try:
            snapshot = await remote_debugger.get_debug_snapshot()
            
            # Determine overall health
            health_status = "healthy"
            issues = []
            
            # Check CPU usage
            if snapshot.get("system", {}).get("cpu", {}).get("usage_percent", 0) > 90:
                health_status = "degraded"
                issues.append("High CPU usage")
            
            # Check memory usage
            if snapshot.get("system", {}).get("memory", {}).get("used_percent", 0) > 90:
                health_status = "degraded"
                issues.append("High memory usage")
            
            # Check disk usage
            if snapshot.get("system", {}).get("disk", {}).get("used_percent", 0) > 90:
                health_status = "degraded"
                issues.append("High disk usage")
            
            # Check service status
            services = snapshot.get("services", {})
            for service_name, service_info in services.items():
                if isinstance(service_info, dict) and not service_info.get("active", False):
                    if service_name != "application_health":  # Skip this meta-service
                        health_status = "unhealthy"
                        issues.append(f"Service {service_name} not active")
            
            return {
                "status": health_status,
                "timestamp": snapshot.get("timestamp"),
                "issues": issues,
                "debug_snapshot": snapshot
            }
            
        except Exception as e:
            logger.error(f"Error in debug health check: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": None
            }
    
    logger.info("Debug routes enabled for development")
    return router