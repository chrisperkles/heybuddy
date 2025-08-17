import requests
import json
import os
from heybuddy.config import Config

class SimpleOpenAIClient:
    def __init__(self):
        self.api_key = Config.OPENAI_API_KEY
        self.base_url = "https://api.openai.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
    def transcribe_audio(self, audio_file_path):
        """Use Whisper API for speech to text"""
        try:
            with open(audio_file_path, 'rb') as f:
                files = {
                    'file': (os.path.basename(audio_file_path), f, 'audio/wav'),
                    'model': (None, Config.WHISPER_MODEL)
                }
                headers = {"Authorization": f"Bearer {self.api_key}"}
                
                response = requests.post(
                    f"{self.base_url}/audio/transcriptions",
                    headers=headers,
                    files=files,
                    timeout=30
                )
                
                if response.status_code == 200:
                    return response.json().get('text', '').strip()
                else:
                    print(f"Transcription error: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            print(f"Transcription exception: {e}")
            return None
            
    def chat_completion(self, messages, max_tokens=150):
        """Use GPT for chat completion"""
        try:
            data = {
                "model": Config.GPT_MODEL,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": 0.7
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content'].strip()
            else:
                print(f"Chat error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Chat exception: {e}")
            return None
            
    def text_to_speech(self, text):
        """Use TTS API to convert text to speech"""
        try:
            data = {
                "model": Config.TTS_MODEL,
                "voice": Config.TTS_VOICE,
                "input": text
            }
            
            response = requests.post(
                f"{self.base_url}/audio/speech",
                headers=self.headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                # Save audio to file
                os.makedirs(Config.TMP_DIR, exist_ok=True)
                with open(Config.OUTPUT_AUDIO_PATH, 'wb') as f:
                    f.write(response.content)
                return Config.OUTPUT_AUDIO_PATH
            else:
                print(f"TTS error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"TTS exception: {e}")
            return None