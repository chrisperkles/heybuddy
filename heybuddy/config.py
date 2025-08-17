import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    SAFETY_MODE = os.getenv('SAFETY_MODE', 'strict')
    LANG = os.getenv('LANG', 'en')
    PERSONA = os.getenv('PERSONA', 'childish')
    
    RECORDING_RATE = 16000
    RECORDING_CHANNELS = 1
    RECORDING_DTYPE = 'int16'
    
    TMP_DIR = 'tmp'
    INPUT_AUDIO_PATH = os.path.join(TMP_DIR, 'in.wav')
    OUTPUT_AUDIO_PATH = os.path.join(TMP_DIR, 'out.wav')
    
    OFFLINE_STORIES_DIR = os.path.join('heybuddy', 'content', 'offline_stories')
    
    WHISPER_MODEL = 'whisper-1'
    GPT_MODEL = 'gpt-4o-mini'
    TTS_MODEL = 'tts-1'
    TTS_VOICE = 'alloy'