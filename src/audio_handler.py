import numpy as np
import sounddevice as sd
import threading
import queue
import time
from collections import deque
import logging
from typing import Optional, Callable, List, Dict
import wave
import tempfile
import os

logger = logging.getLogger(__name__)


class AudioRecorder:
    def __init__(self, config: dict):
        self.config = config['audio']
        self.sample_rate = self.config['sample_rate']
        self.channels = self.config['channels']
        self.buffer_duration = self.config['buffer_duration']
        self.silence_threshold = self.config['silence_threshold']
        self.silence_duration = self.config['silence_duration']

        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.audio_buffer = deque(maxlen=int(self.sample_rate * self.buffer_duration))
        self.recording_thread = None
        self.silence_start_time = None
        self.selected_device = self.config.get('input_device', None)

        self.callback_on_complete = None
        self.callback_on_error = None

        sd.default.samplerate = self.sample_rate
        sd.default.channels = self.channels
        sd.default.dtype = self.config['format']

        # Set selected device if specified
        if self.selected_device is not None:
            sd.default.device = self.selected_device

        logger.info(f"AudioRecorder initialized with sample_rate={self.sample_rate}, channels={self.channels}, device={self.selected_device}")

    def set_callbacks(self, on_complete: Callable = None, on_error: Callable = None):
        self.callback_on_complete = on_complete
        self.callback_on_error = on_error

    def start_recording(self) -> bool:
        if self.is_recording:
            logger.warning("Already recording")
            return False

        try:
            self.is_recording = True
            self.audio_buffer.clear()
            self.silence_start_time = None
            self.recording_thread = threading.Thread(target=self._recording_loop)
            self.recording_thread.daemon = True
            self.recording_thread.start()
            logger.info("Recording started")
            return True
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            self.is_recording = False
            if self.callback_on_error:
                self.callback_on_error(str(e))
            return False

    def stop_recording(self) -> Optional[np.ndarray]:
        if not self.is_recording:
            logger.warning("Not currently recording")
            return None

        self.is_recording = False

        # Don't try to join if we're in the same thread
        if self.recording_thread and self.recording_thread.is_alive():
            if threading.current_thread() != self.recording_thread:
                self.recording_thread.join(timeout=1.0)

        if len(self.audio_buffer) > 0:
            audio_data = np.array(self.audio_buffer)
            logger.info(f"Recording stopped, captured {len(audio_data)/self.sample_rate:.1f} seconds")
            return audio_data
        else:
            logger.warning("No audio data captured")
            return None

    def _recording_loop(self):
        try:
            with sd.InputStream(samplerate=self.sample_rate, channels=self.channels,
                               callback=self._audio_callback):
                while self.is_recording:
                    time.sleep(0.1)

                    if self.silence_start_time:
                        silence_elapsed = time.time() - self.silence_start_time
                        if silence_elapsed >= self.silence_duration:
                            logger.info("Auto-stopping due to silence")
                            self._handle_recording_complete()
                            break
        except Exception as e:
            logger.error(f"Recording error: {e}")
            self.is_recording = False
            if self.callback_on_error:
                self.callback_on_error(str(e))

    def _audio_callback(self, indata, frames, time_info, status):
        if status:
            logger.warning(f"Audio callback status: {status}")

        if self.is_recording:
            audio_chunk = indata[:, 0] if self.channels == 1 else indata
            self.audio_buffer.extend(audio_chunk.flatten())

            rms = np.sqrt(np.mean(audio_chunk**2))

            if rms < self.silence_threshold:
                if self.silence_start_time is None:
                    self.silence_start_time = time.time()
            else:
                self.silence_start_time = None

    def _handle_recording_complete(self):
        audio_data = self.stop_recording()
        if audio_data is not None and self.callback_on_complete:
            self.callback_on_complete(audio_data)

    def save_to_wav(self, audio_data: np.ndarray, filename: str = None) -> str:
        if filename is None:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            filename = temp_file.name
            temp_file.close()

        audio_int16 = (audio_data * 32767).astype(np.int16)

        with wave.open(filename, 'wb') as wav_file:
            wav_file.setnchannels(self.channels)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio_int16.tobytes())

        logger.info(f"Audio saved to {filename}")
        return filename

    def get_recording_status(self) -> dict:
        return {
            'is_recording': self.is_recording,
            'buffer_size': len(self.audio_buffer),
            'duration': len(self.audio_buffer) / self.sample_rate if self.audio_buffer else 0
        }

    @staticmethod
    def get_audio_devices() -> List[Dict]:
        """Get list of available audio input devices"""
        devices = []
        for i, device in enumerate(sd.query_devices()):
            if device['max_input_channels'] > 0:
                devices.append({
                    'index': i,
                    'name': device['name'],
                    'channels': device['max_input_channels'],
                    'default': i == sd.default.device
                })
        return devices

    def set_input_device(self, device_index: int):
        """Set the input device for recording"""
        self.selected_device = device_index
        sd.default.device = device_index
        self.config['input_device'] = device_index
        logger.info(f"Input device set to: {device_index}")


class AudioProcessor:
    def __init__(self):
        self.filters_enabled = True

    def process_audio(self, audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        if not self.filters_enabled:
            return audio_data

        audio_processed = self.remove_noise(audio_data, sample_rate)
        audio_processed = self.normalize_audio(audio_processed)

        return audio_processed

    def remove_noise(self, audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        from scipy.signal import butter, lfilter

        nyquist = sample_rate / 2
        low_cutoff = 100 / nyquist
        high_cutoff = min(3400 / nyquist, 0.99)

        b, a = butter(3, [low_cutoff, high_cutoff], btype='band')
        filtered = lfilter(b, a, audio_data)

        return filtered

    def normalize_audio(self, audio_data: np.ndarray) -> np.ndarray:
        max_val = np.max(np.abs(audio_data))
        if max_val > 0:
            return audio_data / max_val * 0.9
        return audio_data