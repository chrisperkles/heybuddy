"""
Integration tests for heyBuddy Raspberry Pi deployment
Tests system integration, hardware interfaces, and production readiness
"""
import pytest
import asyncio
import aiohttp
import json
import time
from pathlib import Path
import sys
import os

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from core.config import settings
from core.ai_client import AIClient
from core.audio import AudioManager
from database.local_db import LocalDatabase
from services.remote_debug import remote_debugger


class TestPiDeployment:
    """Integration tests for Pi deployment"""
    
    @pytest.fixture
    async def ai_client(self):
        """Initialize AI client for testing"""
        client = AIClient(language="de")
        await client.initialize()
        yield client
        await client.cleanup()
    
    @pytest.fixture
    async def audio_manager(self):
        """Initialize audio manager for testing"""
        manager = AudioManager(device_type="mock")
        await manager.initialize()
        yield manager
        await manager.cleanup()
    
    @pytest.fixture
    async def database(self):
        """Initialize database for testing"""
        db = LocalDatabase()
        await db.initialize()
        yield db
        await db.cleanup()
    
    @pytest.fixture
    async def http_session(self):
        """HTTP session for API testing"""
        async with aiohttp.ClientSession() as session:
            yield session
    
    async def test_health_endpoint(self, http_session):
        """Test basic health endpoint"""
        try:
            async with http_session.get("http://localhost:8080/health") as response:
                assert response.status == 200
                data = await response.json()
                assert "status" in data
                assert data["status"] in ["healthy", "degraded"]
                assert "version" in data
                assert "audio_device" in data
        except aiohttp.ClientError:
            pytest.skip("Application not running - start with 'python src/main.py'")
    
    async def test_german_conversation_api(self, http_session):
        """Test German conversation through API"""
        try:
            payload = {
                "message": "Hallo heyBuddy, ich bin heute traurig",
                "user_id": "test_pi_child",
                "age": 8
            }
            
            async with http_session.post(
                "http://localhost:8080/conversation/text",
                json=payload
            ) as response:
                assert response.status == 200
                data = await response.json()
                
                assert data["success"] is True
                assert "response" in data
                assert len(data["response"]) > 0
                
                # Check for German response
                german_words = ["ich", "du", "ist", "das", "und", "der", "die"]
                response_text = data["response"].lower()
                assert any(word in response_text for word in german_words), "Response should be in German"
                
        except aiohttp.ClientError:
            pytest.skip("Application not running")
    
    async def test_german_story_generation(self, http_session):
        """Test German story generation"""
        try:
            payload = {
                "theme": "Ein mutiger kleiner Hase",
                "age": 6,
                "user_id": "test_pi_story"
            }
            
            async with http_session.post(
                "http://localhost:8080/conversation/story",
                json=payload
            ) as response:
                assert response.status == 200
                data = await response.json()
                
                assert data["success"] is True
                assert "response" in data
                assert len(data["response"]) > 50  # Should be a substantial story
                
                # Check for German story elements
                story_text = data["response"].lower()
                german_story_words = ["war", "einmal", "hase", "mutig", "kleine"]
                assert any(word in story_text for word in german_story_words), "Story should be in German"
                
        except aiohttp.ClientError:
            pytest.skip("Application not running")
    
    async def test_audio_pipeline(self, audio_manager):
        """Test complete audio pipeline"""
        # Test audio recording
        audio_data = await audio_manager.record_audio(duration=1.0)
        assert audio_data is not None
        assert len(audio_data) > 0
        
        # Test audio playback
        await audio_manager.play_audio(audio_data)
        
        # Test device availability
        device_available = await audio_manager.is_device_available()
        assert device_available is True
    
    async def test_ai_conversation_flow(self, ai_client):
        """Test AI conversation with safety filters"""
        # Test safe German conversation
        result = await ai_client.process_conversation(
            user_input="Hallo, wie geht es dir?",
            user_id="test_pi_user",
            age=8
        )
        
        assert result["success"] is True
        assert "response" in result
        assert result["language"] == "de"
        
        # Test inappropriate content blocking
        result = await ai_client.process_conversation(
            user_input="Was ist Gewalt?",
            user_id="test_pi_user",
            age=8
        )
        
        assert result["success"] is False
        assert "german_inappropriate" in result.get("error", "")
    
    async def test_emotional_support_detection(self, ai_client):
        """Test emotional support detection and response"""
        result = await ai_client.process_conversation(
            user_input="Ich bin heute sehr traurig und einsam",
            user_id="test_pi_emotional",
            age=8
        )
        
        assert result["success"] is True
        assert "emotional_support" in result
        assert result["emotional_support"]["emotional_support_needed"] is True
        assert "traurig" in result["emotional_support"]["emotional_keywords"]
    
    async def test_database_operations(self, database):
        """Test database operations"""
        # Test storing conversation
        await database.store_conversation(
            user_id="test_pi_db",
            messages=[{"role": "user", "content": "Test"}],
            metadata={"test": True}
        )
        
        # Test retrieving conversation
        conversations = await database.get_user_conversations("test_pi_db")
        assert len(conversations) > 0
        
        # Test conversation summary
        summary = await database.get_conversation_summary("test_pi_db")
        assert "message_count" in summary
    
    async def test_websocket_connection(self, http_session):
        """Test WebSocket real-time updates"""
        try:
            # Test WebSocket endpoint accessibility
            # Note: Full WebSocket testing requires more complex setup
            async with http_session.get("http://localhost:8080/ws/test") as response:
                # WebSocket upgrade should return 426 or connection should be possible
                assert response.status in [426, 101]  # Upgrade Required or Switching Protocols
        except aiohttp.ClientError:
            pytest.skip("WebSocket testing requires running application")
    
    async def test_debug_system(self, http_session):
        """Test debug and monitoring system"""
        try:
            # Test system info endpoint
            async with http_session.get("http://localhost:8080/debug/system") as response:
                assert response.status == 200
                data = await response.json()
                
                assert "cpu" in data
                assert "memory" in data
                assert "disk" in data
                assert "timestamp" in data
                
                # Check CPU metrics
                if "error" not in data["cpu"]:
                    assert "usage_percent" in data["cpu"]
                    assert data["cpu"]["usage_percent"] >= 0
                
                # Check memory metrics
                if "error" not in data["memory"]:
                    assert "total_gb" in data["memory"]
                    assert data["memory"]["total_gb"] > 0
            
            # Test service status
            async with http_session.get("http://localhost:8080/debug/services") as response:
                assert response.status == 200
                data = await response.json()
                
                assert "application_health" in data
                
        except aiohttp.ClientError:
            pytest.skip("Debug endpoints not available")
    
    async def test_system_performance(self):
        """Test system performance metrics"""
        system_info = await remote_debugger.system_monitor.get_system_info()
        
        if "error" not in system_info:
            # Check CPU usage is reasonable
            if "error" not in system_info.get("cpu", {}):
                cpu_usage = system_info["cpu"].get("usage_percent", 0)
                assert cpu_usage < 95, f"CPU usage too high: {cpu_usage}%"
            
            # Check memory usage is reasonable
            if "error" not in system_info.get("memory", {}):
                memory_usage = system_info["memory"].get("used_percent", 0)
                assert memory_usage < 95, f"Memory usage too high: {memory_usage}%"
            
            # Check disk usage is reasonable
            if "error" not in system_info.get("disk", {}):
                disk_usage = system_info["disk"].get("used_percent", 0)
                assert disk_usage < 95, f"Disk usage too high: {disk_usage}%"
    
    async def test_ota_update_check(self):
        """Test OTA update system"""
        from services.ota_updater import OTAUpdater
        
        updater = OTAUpdater()
        
        # Test update checking (without actually updating)
        update_info = await updater.check_for_updates()
        # Should return None (no update) or dict with update info
        assert update_info is None or isinstance(update_info, dict)
        
        if update_info:
            assert "version" in update_info
            assert "download_url" in update_info
    
    async def test_configuration_validation(self):
        """Test configuration validation"""
        # Test that all required settings are present
        assert settings.openai_api_key is not None, "OpenAI API key must be set"
        assert settings.language == "de", "Language should be set to German"
        assert settings.app_name == "heyBuddy", "App name should be heyBuddy"
        
        # Test audio settings
        assert settings.audio_device in ["auto", "mock", "powerconf"], "Invalid audio device"
        assert settings.sample_rate > 0, "Sample rate must be positive"
        
        # Test safety settings
        assert settings.enable_moderation is True, "Content moderation should be enabled"
        assert settings.max_conversation_length > 0, "Max conversation length must be positive"


class TestPiPerformance:
    """Performance testing for Pi hardware constraints"""
    
    async def test_conversation_latency(self, http_session):
        """Test AI conversation response times"""
        try:
            payload = {
                "message": "Hallo heyBuddy!",
                "user_id": "test_performance",
                "age": 8
            }
            
            start_time = time.time()
            
            async with http_session.post(
                "http://localhost:8080/conversation/text",
                json=payload
            ) as response:
                assert response.status == 200
                data = await response.json()
                
                end_time = time.time()
                latency = end_time - start_time
                
                # Should respond within reasonable time for Pi
                assert latency < 10.0, f"Response too slow: {latency:.2f}s"
                assert data["success"] is True
                
        except aiohttp.ClientError:
            pytest.skip("Application not running")
    
    async def test_memory_usage_stability(self):
        """Test memory usage doesn't grow excessively"""
        initial_info = await remote_debugger.system_monitor.get_system_info()
        initial_memory = initial_info.get("memory", {}).get("used_percent", 0)
        
        # Simulate multiple conversations to test memory stability
        ai_client = AIClient(language="de")
        await ai_client.initialize()
        
        try:
            for i in range(10):
                await ai_client.process_conversation(
                    user_input=f"Test Nachricht {i}",
                    user_id="memory_test",
                    age=8
                )
            
            # Check memory after load
            final_info = await remote_debugger.system_monitor.get_system_info()
            final_memory = final_info.get("memory", {}).get("used_percent", 0)
            
            memory_increase = final_memory - initial_memory
            assert memory_increase < 10, f"Memory usage increased too much: {memory_increase}%"
            
        finally:
            await ai_client.cleanup()
    
    async def test_concurrent_conversations(self, http_session):
        """Test handling multiple simultaneous conversations"""
        try:
            tasks = []
            
            for i in range(3):  # 3 concurrent conversations
                payload = {
                    "message": f"Hallo, ich bin Kind {i}",
                    "user_id": f"concurrent_test_{i}",
                    "age": 8
                }
                
                task = http_session.post(
                    "http://localhost:8080/conversation/text",
                    json=payload
                )
                tasks.append(task)
            
            # Execute all requests concurrently
            start_time = time.time()
            responses = await asyncio.gather(*[task.__aenter__() for task in tasks])
            end_time = time.time()
            
            # Check all responses succeeded
            for response in responses:
                assert response.status == 200
                data = await response.json()
                assert data["success"] is True
                await response.__aexit__(None, None, None)
            
            # Should handle concurrent requests efficiently
            total_time = end_time - start_time
            assert total_time < 15.0, f"Concurrent requests too slow: {total_time:.2f}s"
            
        except aiohttp.ClientError:
            pytest.skip("Application not running")


# Test fixtures and utilities
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


if __name__ == "__main__":
    """Run tests directly for development"""
    import subprocess
    
    print("🧪 Running heyBuddy Pi Deployment Tests...")
    
    # Check if application is running
    try:
        import requests
        response = requests.get("http://localhost:8080/health", timeout=5)
        if response.status_code == 200:
            print("✅ Application is running")
        else:
            print("❌ Application health check failed")
            exit(1)
    except requests.exceptions.RequestException:
        print("❌ Application not running. Start with: python src/main.py")
        exit(1)
    
    # Run pytest
    result = subprocess.run([
        "python", "-m", "pytest", 
        __file__, 
        "-v", 
        "--tb=short",
        "--asyncio-mode=auto"
    ])
    
    exit(result.returncode)