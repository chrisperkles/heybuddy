from heybuddy.config import Config
from heybuddy.services.persona import get_system_prompt
from heybuddy.services.moderation import ModerationService
from heybuddy.services.net_health import is_online
from heybuddy.services.simple_openai import SimpleOpenAIClient

class LLMService:
    def __init__(self):
        self.client = SimpleOpenAIClient() if Config.OPENAI_API_KEY else None
        self.moderation = ModerationService()
        
    def generate_response(self, user_input, persona=None, lang=None):
        if not is_online() or not self.client:
            print("Using mock response - offline or no API key")
            return self._mock_response()
            
        persona = persona or Config.PERSONA
        lang = lang or Config.LANG
        
        if self.moderation.is_flagged(user_input):
            return "I can't talk about that. Let's pick a fun story instead!"
            
        print(f"Generating response for: {user_input}")
        system_prompt = get_system_prompt(persona, lang)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
        
        response_text = self.client.chat_completion(messages, max_tokens=150)
        
        if response_text:
            if self.moderation.is_flagged(response_text):
                return "I can't talk about that. Let's pick a fun story instead!"
            print(f"Generated response: {response_text}")
            return response_text
        else:
            print("Response generation failed, using mock")
            return self._mock_response()
            
    def _mock_response(self):
        return "Once upon a time, there was a brave little bunny who loved to explore the garden!"