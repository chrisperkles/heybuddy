import socket
import requests
from heybuddy.config import Config

def is_online():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        pass
    
    try:
        response = requests.get("https://api.openai.com", timeout=3)
        return response.status_code == 200
    except:
        pass
        
    return False

def can_access_openai():
    if not Config.OPENAI_API_KEY:
        return False
        
    try:
        response = requests.get(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {Config.OPENAI_API_KEY}"},
            timeout=5
        )
        return response.status_code == 200
    except:
        return False