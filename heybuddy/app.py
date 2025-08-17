import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time

from heybuddy.config import Config
from heybuddy.state_machine import StateMachine, AppState
from heybuddy.ui.widgets import LEDIndicator, TranscriptPanel, ResponsePanel, TalkButton, StatusBar
from heybuddy.services.audio_io import AudioIO
from heybuddy.services.asr import ASRService
from heybuddy.services.llm import LLMService
from heybuddy.services.tts import TTSService
from heybuddy.services.net_health import is_online, can_access_openai
from heybuddy.services.offline_content import OfflineContent

class HeyBuddyApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("heyBuddy (Mac Demo)")
        self.root.geometry("500x600")
        self.root.resizable(False, False)
        
        self.state_machine = StateMachine(self.on_state_changed)
        self.audio_io = AudioIO()
        self.asr_service = ASRService()
        self.llm_service = LLMService()
        self.tts_service = TTSService()
        self.offline_content = OfflineContent()
        
        self.persona = Config.PERSONA
        self.language = Config.LANG
        self.safety_mode = Config.SAFETY_MODE
        
        self.setup_ui()
        self.check_network_status()
        
    def setup_ui(self):
        self.create_menu()
        self.create_main_frame()
        self.create_status_bar()
        
    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Preferences", command=self.show_preferences)
        
    def create_main_frame(self):
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        led_frame = tk.Frame(main_frame)
        led_frame.pack(pady=10)
        
        tk.Label(led_frame, text="Status:", font=("Arial", 12)).pack(side=tk.LEFT, padx=(0, 10))
        self.led_indicator = LEDIndicator(led_frame, size=30)
        self.led_indicator.pack(side=tk.LEFT)
        
        self.talk_button = TalkButton(main_frame, width=20, height=3)
        self.talk_button.pack(pady=20)
        self.talk_button.bind("<Button-1>", self.on_button_press)
        self.talk_button.bind("<ButtonRelease-1>", self.on_button_release)
        
        tk.Label(main_frame, text="Transcript:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(20, 5))
        self.transcript_panel = TranscriptPanel(main_frame)
        self.transcript_panel.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(main_frame, text="Response:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(10, 5))
        self.response_panel = ResponsePanel(main_frame)
        self.response_panel.pack(fill=tk.BOTH, expand=True)
        
    def create_status_bar(self):
        self.status_bar = StatusBar(self.root)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def show_preferences(self):
        prefs_window = tk.Toplevel(self.root)
        prefs_window.title("Preferences")
        prefs_window.geometry("300x400")
        prefs_window.resizable(False, False)
        
        frame = tk.Frame(prefs_window, padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(frame, text="Persona:", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=(0, 5))
        self.persona_var = tk.StringVar(value=self.persona)
        tk.Radiobutton(frame, text="Childish", variable=self.persona_var, value="childish").pack(anchor=tk.W)
        tk.Radiobutton(frame, text="Mature", variable=self.persona_var, value="mature").pack(anchor=tk.W)
        
        tk.Label(frame, text="Language:", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=(20, 5))
        self.language_var = tk.StringVar(value=self.language)
        tk.Radiobutton(frame, text="English", variable=self.language_var, value="en").pack(anchor=tk.W)
        tk.Radiobutton(frame, text="German", variable=self.language_var, value="de").pack(anchor=tk.W)
        
        tk.Label(frame, text="Safety:", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=(20, 5))
        self.safety_var = tk.StringVar(value=self.safety_mode)
        tk.Radiobutton(frame, text="Strict", variable=self.safety_var, value="strict").pack(anchor=tk.W)
        tk.Radiobutton(frame, text="Lenient", variable=self.safety_var, value="lenient").pack(anchor=tk.W)
        
        button_frame = tk.Frame(frame)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(30, 0))
        
        tk.Button(button_frame, text="Cancel", command=prefs_window.destroy).pack(side=tk.RIGHT, padx=(10, 0))
        tk.Button(button_frame, text="Save", command=lambda: self.save_preferences(prefs_window)).pack(side=tk.RIGHT)
        
    def save_preferences(self, window):
        self.persona = self.persona_var.get()
        self.language = self.language_var.get()
        self.safety_mode = self.safety_var.get()
        Config.PERSONA = self.persona
        Config.LANG = self.language
        Config.SAFETY_MODE = self.safety_mode
        window.destroy()
        
    def on_button_press(self, event):
        if self.state_machine.start_recording():
            self.talk_button.set_pressed(True)
            self.transcript_panel.clear()
            self.response_panel.clear()
            self.status_bar.set_status("Recording...")
            self.audio_io.start_recording()
            
    def on_button_release(self, event):
        if self.state_machine.stop_recording():
            self.talk_button.set_pressed(False)
            self.status_bar.set_status("Processing...")
            audio_file = self.audio_io.stop_recording()
            
            if audio_file:
                threading.Thread(target=self.process_audio, args=(audio_file,), daemon=True).start()
            else:
                self.state_machine.set_state(AppState.IDLE)
                self.status_bar.set_status("Ready")
                
    def process_audio(self, audio_file):
        try:
            transcript = self.asr_service.transcribe(audio_file)
            
            self.root.after(0, lambda: self.transcript_panel.set_text(transcript))
            
            response = self.llm_service.generate_response(transcript, self.persona, self.language)
            
            self.root.after(0, lambda: self.response_panel.set_text(response))
            
            audio_file = self.tts_service.synthesize(response)
            
            if audio_file and self.state_machine.start_speaking():
                self.root.after(0, lambda: self.status_bar.set_status("Speaking..."))
                
                if self.audio_io.play_audio(audio_file):
                    time.sleep(0.5)
                    
                self.state_machine.finish_speaking()
                self.root.after(0, lambda: self.status_bar.set_status("Ready"))
            else:
                self.state_machine.set_state(AppState.IDLE)
                self.root.after(0, lambda: self.status_bar.set_status("Ready"))
                
        except Exception as e:
            print(f"Error processing audio: {e}")
            self.state_machine.set_state(AppState.IDLE)
            self.root.after(0, lambda: self.status_bar.set_status("Error occurred"))
            
    def on_state_changed(self, state):
        self.root.after(0, lambda: self.led_indicator.update_for_state(state))
        
    def check_network_status(self):
        def check():
            online = is_online()
            has_api = can_access_openai()
            
            if online and has_api:
                if self.state_machine.is_offline():
                    self.state_machine.go_online()
                self.root.after(0, lambda: self.status_bar.set_online_status(True))
            else:
                self.state_machine.go_offline()
                self.root.after(0, lambda: self.status_bar.set_online_status(False))
                
        threading.Thread(target=check, daemon=True).start()
        self.root.after(10000, self.check_network_status)
        
    def run(self):
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.root.quit()

def main():
    app = HeyBuddyApp()
    app.run()

if __name__ == "__main__":
    main()