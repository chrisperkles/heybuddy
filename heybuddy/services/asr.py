from heybuddy.config import Config
from heybuddy.services.net_health import is_online
from heybuddy.services.simple_openai import SimpleOpenAIClient

class ASRService:
    def __init__(self):
        self.client = SimpleOpenAIClient() if Config.OPENAI_API_KEY else None
        
    def transcribe(self, audio_file_path):
        if not is_online() or not self.client:
            print("Using mock transcription - offline or no API key")
            return self._mock_transcribe()
            
        print(f"Transcribing audio file: {audio_file_path}")
        result = self.client.transcribe_audio(audio_file_path)
        
        if result:
            print(f"Transcription result: {result}")
            return result
        else:
            print("Transcription failed, using mock")
            return self._mock_transcribe()
            
    def _mock_transcribe(self):
        return "Hello heyBuddy, tell me a story!"