import sounddevice as sd
import soundfile as sf
import numpy as np
import os
from heybuddy.config import Config

class AudioIO:
    def __init__(self):
        self.recording = False
        self.recorded_data = []
        
    def start_recording(self):
        self.recording = True
        self.recorded_data = []
        
        def callback(indata, frames, time, status):
            if status:
                print(f"Recording status: {status}")
            if self.recording:
                self.recorded_data.append(indata.copy())
        
        self.stream = sd.InputStream(
            samplerate=Config.RECORDING_RATE,
            channels=Config.RECORDING_CHANNELS,
            dtype=Config.RECORDING_DTYPE,
            callback=callback
        )
        self.stream.start()
        
    def stop_recording(self):
        if hasattr(self, 'stream') and self.stream.active:
            self.recording = False
            self.stream.stop()
            self.stream.close()
            
            if self.recorded_data:
                audio_data = np.concatenate(self.recorded_data, axis=0)
                os.makedirs(Config.TMP_DIR, exist_ok=True)
                sf.write(Config.INPUT_AUDIO_PATH, audio_data, Config.RECORDING_RATE)
                return Config.INPUT_AUDIO_PATH
        return None
        
    def play_audio(self, file_path):
        if os.path.exists(file_path):
            try:
                data, samplerate = sf.read(file_path)
                sd.play(data, samplerate)
                sd.wait()
                return True
            except Exception as e:
                print(f"Error playing audio: {e}")
                return False
        return False
        
    def is_playing(self):
        return sd.get_stream().active if sd.get_stream() else False