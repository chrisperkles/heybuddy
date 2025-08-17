from enum import Enum
import threading
import time

class AppState(Enum):
    IDLE = "idle"
    RECORDING = "recording"
    THINKING = "thinking"
    SPEAKING = "speaking"
    OFFLINE = "offline"

class StateMachine:
    def __init__(self, ui_callback=None):
        self.state = AppState.IDLE
        self.ui_callback = ui_callback
        self.lock = threading.Lock()
        
    def get_state(self):
        with self.lock:
            return self.state
            
    def set_state(self, new_state):
        with self.lock:
            if self.state != new_state:
                self.state = new_state
                if self.ui_callback:
                    self.ui_callback(new_state)
                    
    def is_idle(self):
        return self.get_state() == AppState.IDLE
        
    def is_recording(self):
        return self.get_state() == AppState.RECORDING
        
    def is_thinking(self):
        return self.get_state() == AppState.THINKING
        
    def is_speaking(self):
        return self.get_state() == AppState.SPEAKING
        
    def is_offline(self):
        return self.get_state() == AppState.OFFLINE
        
    def can_start_recording(self):
        return self.get_state() in [AppState.IDLE, AppState.OFFLINE]
        
    def start_recording(self):
        if self.can_start_recording():
            self.set_state(AppState.RECORDING)
            return True
        return False
        
    def stop_recording(self):
        if self.is_recording():
            self.set_state(AppState.THINKING)
            return True
        return False
        
    def start_speaking(self):
        if self.is_thinking():
            self.set_state(AppState.SPEAKING)
            return True
        return False
        
    def finish_speaking(self):
        if self.is_speaking():
            self.set_state(AppState.IDLE)
            return True
        return False
        
    def go_offline(self):
        self.set_state(AppState.OFFLINE)
        
    def go_online(self):
        if self.is_offline():
            self.set_state(AppState.IDLE)