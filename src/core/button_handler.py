"""
Button handler for USB audio devices (Anker PowerConf S330)

The PowerConf S330 exposes its mute button as a HID input device on Linux.
This module monitors that button for push-to-talk functionality.
"""
import asyncio
import logging
from typing import Callable, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class ButtonHandler:
    """Handles button events from USB audio devices"""

    def __init__(self):
        self.device = None
        self.running = False
        self.on_button_press: Optional[Callable] = None
        self.on_button_release: Optional[Callable] = None
        self._monitor_task: Optional[asyncio.Task] = None

    async def find_device(self) -> bool:
        """Find the PowerConf S330 input device"""
        try:
            import evdev

            devices = [evdev.InputDevice(path) for path in evdev.list_devices()]

            for device in devices:
                device_name = device.name.lower()
                logger.debug(f"Found input device: {device.name}")

                # Look for Anker PowerConf or S330
                if 'powerconf' in device_name or 's330' in device_name or 'anker' in device_name:
                    self.device = device
                    logger.info(f"Found PowerConf S330 button device: {device.name} at {device.path}")
                    return True

            # Also check for generic USB audio controller buttons
            for device in devices:
                caps = device.capabilities()
                # Look for devices with KEY events (buttons)
                if 1 in caps:  # EV_KEY
                    keys = caps[1]
                    # Check for mute key (113) or other media keys
                    if 113 in keys or 163 in keys:  # KEY_MUTE or KEY_NEXTSONG
                        device_name = device.name.lower()
                        if 'audio' in device_name or 'usb' in device_name:
                            self.device = device
                            logger.info(f"Found USB audio button device: {device.name}")
                            return True

            logger.warning("No PowerConf S330 button device found")
            return False

        except ImportError:
            logger.error("evdev not installed - button detection unavailable")
            return False
        except Exception as e:
            logger.error(f"Error finding button device: {e}")
            return False

    async def start_monitoring(self) -> bool:
        """Start monitoring button events"""
        if not self.device:
            if not await self.find_device():
                return False

        self.running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Button monitoring started")
        return True

    async def _monitor_loop(self):
        """Main monitoring loop for button events"""
        try:
            import evdev

            async for event in self.device.async_read_loop():
                if not self.running:
                    break

                # EV_KEY events (button press/release)
                if event.type == evdev.ecodes.EV_KEY:
                    key_event = evdev.categorize(event)

                    logger.debug(f"Button event: {key_event.keycode} state={key_event.keystate}")

                    # keystate: 0=release, 1=press, 2=hold
                    if key_event.keystate == 1:  # Press
                        logger.info(f"Button pressed: {key_event.keycode}")
                        if self.on_button_press:
                            await self._safe_callback(self.on_button_press)

                    elif key_event.keystate == 0:  # Release
                        logger.info(f"Button released: {key_event.keycode}")
                        if self.on_button_release:
                            await self._safe_callback(self.on_button_release)

        except asyncio.CancelledError:
            logger.info("Button monitoring cancelled")
        except Exception as e:
            logger.error(f"Button monitoring error: {e}")

    async def _safe_callback(self, callback: Callable):
        """Safely execute a callback (sync or async)"""
        try:
            result = callback()
            if asyncio.iscoroutine(result):
                await result
        except Exception as e:
            logger.error(f"Button callback error: {e}")

    def set_callbacks(self, on_press: Optional[Callable] = None,
                      on_release: Optional[Callable] = None):
        """Set button press/release callbacks"""
        self.on_button_press = on_press
        self.on_button_release = on_release

    async def stop(self):
        """Stop monitoring button events"""
        self.running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        if self.device:
            self.device.close()
            self.device = None
        logger.info("Button monitoring stopped")


class PushToTalkController:
    """
    Push-to-talk controller that integrates button handling with audio recording.

    Usage:
        controller = PushToTalkController(audio_manager)
        controller.set_conversation_callback(handle_conversation)
        await controller.start()

    The mute button on PowerConf S330 works as push-to-talk:
    - Press and hold: Start recording
    - Release: Stop recording and process speech
    """

    def __init__(self, audio_manager):
        self.audio_manager = audio_manager
        self.button_handler = ButtonHandler()
        self.is_recording = False
        self.recording_task: Optional[asyncio.Task] = None
        self.on_conversation: Optional[Callable] = None
        self.recorded_audio: bytes = b''
        self._record_start_event = asyncio.Event()
        self._record_stop_event = asyncio.Event()

    def set_conversation_callback(self, callback: Callable):
        """Set callback for when recording completes: callback(audio_bytes)"""
        self.on_conversation = callback

    async def start(self) -> bool:
        """Start the push-to-talk controller"""
        self.button_handler.set_callbacks(
            on_press=self._on_button_press,
            on_release=self._on_button_release
        )

        if await self.button_handler.start_monitoring():
            logger.info("Push-to-talk controller started")
            return True
        else:
            logger.warning("Push-to-talk unavailable - button device not found")
            return False

    def _on_button_press(self):
        """Handle button press - start recording"""
        if not self.is_recording:
            logger.info("Push-to-talk: Starting recording")
            self.is_recording = True
            self._record_start_event.set()
            self.recording_task = asyncio.create_task(self._record_audio())

    def _on_button_release(self):
        """Handle button release - stop recording"""
        if self.is_recording:
            logger.info("Push-to-talk: Stopping recording")
            self.is_recording = False
            self._record_stop_event.set()

    async def _record_audio(self):
        """Record audio while button is held"""
        try:
            self._record_stop_event.clear()
            chunks = []

            # Record in small chunks until button is released
            while self.is_recording:
                try:
                    # Record 0.5 second chunks
                    chunk = await asyncio.wait_for(
                        self.audio_manager.record_audio(duration=0.5),
                        timeout=1.0
                    )
                    chunks.append(chunk)
                except asyncio.TimeoutError:
                    continue

                # Check if we should stop
                if self._record_stop_event.is_set():
                    break

                # Safety limit: max 30 seconds
                if len(chunks) >= 60:
                    logger.warning("Recording reached 30 second limit")
                    break

            # Combine audio chunks
            if chunks:
                self.recorded_audio = self._combine_wav_chunks(chunks)
                logger.info(f"Recording complete: {len(self.recorded_audio)} bytes")

                # Trigger callback
                if self.on_conversation and self.recorded_audio:
                    await self._safe_callback(self.on_conversation, self.recorded_audio)

        except Exception as e:
            logger.error(f"Recording error: {e}")
        finally:
            self.is_recording = False
            self._record_start_event.clear()

    def _combine_wav_chunks(self, chunks: list) -> bytes:
        """Combine multiple WAV chunks into a single WAV file"""
        import wave
        import io

        if not chunks:
            return b''

        # Read first chunk to get parameters
        first_chunk = io.BytesIO(chunks[0])
        with wave.open(first_chunk, 'rb') as wav:
            params = wav.getparams()

        # Extract raw audio data from each chunk
        all_frames = []
        for chunk in chunks:
            chunk_buffer = io.BytesIO(chunk)
            with wave.open(chunk_buffer, 'rb') as wav:
                all_frames.append(wav.readframes(wav.getnframes()))

        # Create combined WAV
        output = io.BytesIO()
        with wave.open(output, 'wb') as wav:
            wav.setparams(params)
            wav.writeframes(b''.join(all_frames))

        output.seek(0)
        return output.getvalue()

    async def _safe_callback(self, callback: Callable, *args):
        """Safely execute a callback"""
        try:
            result = callback(*args)
            if asyncio.iscoroutine(result):
                await result
        except Exception as e:
            logger.error(f"Conversation callback error: {e}")

    async def stop(self):
        """Stop the push-to-talk controller"""
        if self.recording_task:
            self.recording_task.cancel()
            try:
                await self.recording_task
            except asyncio.CancelledError:
                pass
        await self.button_handler.stop()
        logger.info("Push-to-talk controller stopped")
