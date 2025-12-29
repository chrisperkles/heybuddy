"""
Audio processing and device management for heyBuddy
"""
import asyncio
import logging
import os
import io
import wave
from abc import ABC, abstractmethod
from typing import Optional, Callable
from pathlib import Path

# Fix pygame on headless systems (Raspberry Pi without display)
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'alsa')

import pygame

logger = logging.getLogger(__name__)


class AudioInterface(ABC):
    """Abstract interface for audio devices"""
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the audio device"""
        pass
    
    @abstractmethod
    async def record(self, duration: float = 5.0) -> bytes:
        """Record audio for specified duration"""
        pass
    
    @abstractmethod
    async def play(self, audio_data: bytes) -> None:
        """Play audio data"""
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """Check if device is available and working"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup resources"""
        pass


class MockAudioDevice(AudioInterface):
    """Mock audio device for development and testing"""
    
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.is_initialized = False
        
    async def initialize(self) -> bool:
        """Initialize pygame mixer for audio playback"""
        try:
            pygame.mixer.init(frequency=self.sample_rate, size=-16, channels=1, buffer=1024)
            self.is_initialized = True
            logger.info("Mock audio device initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize mock audio device: {e}")
            return False
    
    async def record(self, duration: float = 5.0) -> bytes:
        """Simulate recording by returning silence or test audio"""
        logger.info(f"Mock recording for {duration} seconds")
        
        # Generate silence or load test audio file
        num_samples = int(self.sample_rate * duration)
        silence = b'\x00' * (num_samples * 2)  # 16-bit samples
        
        # Create WAV format
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(silence)
        
        buffer.seek(0)
        return buffer.getvalue()
    
    async def play(self, audio_data: bytes) -> None:
        """Play audio using pygame"""
        try:
            # Load audio data into pygame
            audio_buffer = io.BytesIO(audio_data)
            sound = pygame.mixer.Sound(audio_buffer)
            sound.play()
            
            # Wait for playback to complete
            while pygame.mixer.get_busy():
                await asyncio.sleep(0.1)
                
            logger.info("Audio playback completed")
        except Exception as e:
            logger.error(f"Failed to play audio: {e}")
    
    async def is_available(self) -> bool:
        """Check if mock device is available"""
        return self.is_initialized
    
    async def cleanup(self) -> None:
        """Cleanup pygame mixer"""
        if self.is_initialized:
            pygame.mixer.quit()
            self.is_initialized = False
            logger.info("Mock audio device cleaned up")


class PowerConfS330Device(AudioInterface):
    """Anker PowerConf S330 audio device interface"""
    
    def __init__(self, sample_rate: int = 16000, chunk_size: int = 1024):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.audio = None
        self.input_device_index = None
        self.output_device_index = None
        
    async def initialize(self) -> bool:
        """Initialize PyAudio and find PowerConf S330 device"""
        try:
            import pyaudio
            self.audio = pyaudio.PyAudio()
            
            # Find PowerConf S330 device
            device_found = False
            for i in range(self.audio.get_device_count()):
                device_info = self.audio.get_device_info_by_index(i)
                device_name = device_info.get('name', '').lower()
                
                if 'powerconf' in device_name or 's330' in device_name:
                    if device_info['maxInputChannels'] > 0:
                        self.input_device_index = i
                    if device_info['maxOutputChannels'] > 0:
                        self.output_device_index = i
                    device_found = True
                    logger.info(f"Found PowerConf S330: {device_info['name']}")
            
            if not device_found:
                logger.warning("PowerConf S330 not found, using default audio device")
                
            return True
        except ImportError:
            logger.error("PyAudio not available, cannot use hardware audio")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize PowerConf S330: {e}")
            return False
    
    async def record(self, duration: float = 5.0) -> bytes:
        """Record audio from PowerConf S330 microphone"""
        if not self.audio:
            raise RuntimeError("Audio device not initialized")
            
        try:
            import pyaudio
            
            stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.input_device_index,
                frames_per_buffer=self.chunk_size
            )
            
            logger.info(f"Recording audio for {duration} seconds...")
            frames = []
            
            for _ in range(int(self.sample_rate / self.chunk_size * duration)):
                data = stream.read(self.chunk_size)
                frames.append(data)
            
            stream.stop_stream()
            stream.close()
            
            # Create WAV format
            buffer = io.BytesIO()
            with wave.open(buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(b''.join(frames))
            
            buffer.seek(0)
            logger.info("Audio recording completed")
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Failed to record audio: {e}")
            raise
    
    async def play(self, audio_data: bytes) -> None:
        """Play audio through PowerConf S330 speaker"""
        if not self.audio:
            raise RuntimeError("Audio device not initialized")
            
        try:
            import pyaudio
            
            # Parse WAV data
            audio_buffer = io.BytesIO(audio_data)
            with wave.open(audio_buffer, 'rb') as wav_file:
                frames = wav_file.readframes(wav_file.getnframes())
                
            stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                output=True,
                output_device_index=self.output_device_index,
                frames_per_buffer=self.chunk_size
            )
            
            # Play audio in chunks
            for i in range(0, len(frames), self.chunk_size * 2):
                chunk = frames[i:i + self.chunk_size * 2]
                stream.write(chunk)
            
            stream.stop_stream()
            stream.close()
            logger.info("Audio playback completed")
            
        except Exception as e:
            logger.error(f"Failed to play audio: {e}")
            raise
    
    async def is_available(self) -> bool:
        """Check if PowerConf S330 is available"""
        return self.audio is not None and (
            self.input_device_index is not None or 
            self.output_device_index is not None
        )
    
    async def cleanup(self) -> None:
        """Cleanup PyAudio resources"""
        if self.audio:
            self.audio.terminate()
            self.audio = None
            logger.info("PowerConf S330 device cleaned up")


class AudioManager:
    """Main audio manager that handles device selection and operation"""

    def __init__(self, device_type: str = "auto", sample_rate: int = 16000):
        self.device_type = device_type
        self.sample_rate = sample_rate
        self.device: Optional[AudioInterface] = None
        self.button_callback: Optional[Callable] = None
        self.push_to_talk = None

    async def initialize(self) -> bool:
        """Initialize the appropriate audio device"""
        if self.device_type == "mock":
            self.device = MockAudioDevice(self.sample_rate)
        elif self.device_type == "powerconf":
            self.device = PowerConfS330Device(self.sample_rate)
        else:  # auto
            # Try PowerConf first, fallback to mock
            hardware_device = PowerConfS330Device(self.sample_rate)
            if await hardware_device.initialize() and await hardware_device.is_available():
                self.device = hardware_device
                logger.info("Using PowerConf S330 hardware device")
            else:
                self.device = MockAudioDevice(self.sample_rate)
                logger.info("Using mock audio device")

        if self.device:
            init_result = await self.device.initialize()

            # Initialize push-to-talk if using hardware device
            if init_result and isinstance(self.device, PowerConfS330Device):
                await self._init_push_to_talk()

            return init_result
        return False

    async def _init_push_to_talk(self):
        """Initialize push-to-talk button handling"""
        try:
            from .button_handler import PushToTalkController
            self.push_to_talk = PushToTalkController(self)
            if await self.push_to_talk.start():
                logger.info("Push-to-talk enabled - use device button to record")
            else:
                logger.warning("Push-to-talk unavailable - button device not found")
                self.push_to_talk = None
        except ImportError as e:
            logger.warning(f"Push-to-talk unavailable: {e}")
            self.push_to_talk = None
        except Exception as e:
            logger.error(f"Failed to initialize push-to-talk: {e}")
            self.push_to_talk = None

    async def record_audio(self, duration: float = 5.0) -> bytes:
        """Record audio from the current device"""
        if not self.device:
            raise RuntimeError("Audio device not initialized")
        return await self.device.record(duration)

    async def play_audio(self, audio_data: bytes) -> None:
        """Play audio through the current device"""
        if not self.device:
            raise RuntimeError("Audio device not initialized")
        await self.device.play(audio_data)

    async def is_device_available(self) -> bool:
        """Check if current device is available"""
        if not self.device:
            return False
        return await self.device.is_available()

    def set_button_callback(self, callback: Callable) -> None:
        """Set callback for hardware button press (push-to-talk)"""
        self.button_callback = callback
        if self.push_to_talk:
            self.push_to_talk.set_conversation_callback(callback)
            logger.info("Push-to-talk callback registered")

    def is_push_to_talk_available(self) -> bool:
        """Check if push-to-talk is available"""
        return self.push_to_talk is not None

    async def cleanup(self) -> None:
        """Cleanup audio resources"""
        if self.push_to_talk:
            await self.push_to_talk.stop()
            self.push_to_talk = None
        if self.device:
            await self.device.cleanup()
            self.device = None