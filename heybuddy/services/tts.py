from heybuddy.config import Config
from heybuddy.services.net_health import is_online
from heybuddy.services.simple_openai import SimpleOpenAIClient

class TTSService:
    def __init__(self):
        self.client = SimpleOpenAIClient() if Config.OPENAI_API_KEY else None
        
    def synthesize(self, text):
        if not is_online() or not self.client:
            print("Using mock synthesis - offline or no API key")
            return self._mock_synthesize()
            
        print(f"Synthesizing speech for: {text[:50]}...")
        result = self.client.text_to_speech(text)
        
        if result:
            print(f"TTS successful, saved to: {result}")
            return result
        else:
            print("TTS failed, using mock")
            return self._mock_synthesize()
            
    def _mock_synthesize(self):
        from heybuddy.services.offline_content import OfflineContent
        offline = OfflineContent()
        return offline.get_random_story()