import sys
import os
import json
import logging
import tempfile
import threading
import time
from pathlib import Path
from typing import Optional
import numpy as np

# Add ffmpeg to PATH if it exists locally
ffmpeg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "tools", "ffmpeg",
                           "ffmpeg-2025-09-18-git-c373636f55-essentials_build",
                           "bin")
if os.path.exists(ffmpeg_path):
    os.environ["PATH"] = ffmpeg_path + os.pathsep + os.environ.get("PATH", "")
    print(f"Added local ffmpeg to PATH: {ffmpeg_path}")

# Fix working directory for packaged executable
if getattr(sys, 'frozen', False):
    # If running as compiled executable
    app_dir = os.path.dirname(sys.executable)
    os.chdir(app_dir)
    log_file = os.path.join(app_dir, 'transcribe_app.log')
else:
    # If running as script
    log_file = os.path.join('data', 'transcribe_app.log')

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from audio_handler import AudioRecorder, AudioProcessor
from model_manager import ModelManager, ModelLoader
from text_injector import SafeTextInjector
from hotkey_manager import HotkeyManager
from ui_manager import TrayApp, SettingsWindow
from splash_screen import SplashScreen

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class TranscribeApp:
    def __init__(self, splash=None):
        self.splash = splash
        self.update_splash("Loading configuration...", 10, "Step 1/6: Configuration")

        self.config = self.load_config()
        self.is_recording = False
        self.enabled = True
        self.processing_lock = threading.Lock()

        self.update_splash("Initializing audio system...", 20, "Step 2/6: Audio devices")
        self.audio_recorder = AudioRecorder(self.config)
        self.audio_processor = AudioProcessor()

        self.update_splash("Preparing AI models...", 30, "Step 3/6: AI system")
        self.model_manager = ModelManager(self.config)

        self.update_splash("Setting up text injection...", 40, "Step 4/6: Text system")
        self.text_injector = SafeTextInjector()

        self.update_splash("Configuring hotkeys...", 50, "Step 5/6: Keyboard shortcuts")
        self.hotkey_manager = HotkeyManager()

        self.update_splash("Creating system tray...", 60, "Step 6/6: User interface")
        self.tray_app = TrayApp(self.config)

        self.temp_dir = tempfile.mkdtemp(prefix="transcribe_")

        self.setup_callbacks()
        self.register_hotkeys()

        logger.info("TranscribeApp initialized")

    def update_splash(self, status, progress, step):
        """Update splash screen if it exists"""
        if self.splash:
            self.splash.update_status(status)
            self.splash.update_progress(progress)
            self.splash.update_step(step)

    def load_config(self) -> dict:
        # Look for config in same directory as executable
        if getattr(sys, 'frozen', False):
            config_path = Path(os.path.dirname(sys.executable)) / "config.json"
        else:
            config_path = Path("config.json")

        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        else:
            logger.error(f"Config file not found at: {config_path}")
            sys.exit(1)

    def setup_callbacks(self):
        self.audio_recorder.set_callbacks(
            on_complete=self.on_recording_complete,
            on_error=self.on_recording_error
        )

        self.tray_app.set_callbacks(
            record=self.toggle_recording,
            settings=self.show_settings,
            exit_app=self.shutdown
        )

    def register_hotkeys(self):
        self.hotkey_manager.register_hotkey(
            self.config['hotkeys']['record'],
            self.toggle_recording,
            "Toggle recording"
        )

        self.hotkey_manager.register_hotkey(
            self.config['hotkeys']['toggle_enabled'],
            self.toggle_enabled,
            "Enable/Disable app"
        )

        self.hotkey_manager.start()
        logger.info("Hotkeys registered")

    def initialize_models(self):
        self.tray_app.update_status('processing', 'Loading models...')

        def progress_callback(message, progress):
            logger.info(f"Model loading: {message} ({progress}%)")
            self.tray_app.update_status('processing', message)
            # Update splash screen during model loading
            if self.splash:
                actual_progress = 70 + (progress * 0.25)  # Map to 70-95%
                self.splash.update_status(f"Loading AI models: {message}")
                self.splash.update_progress(actual_progress)
                self.splash.update_step("Loading AI models (this may take 15-30 seconds)")

        success = self.model_manager.initialize_models(progress_callback)

        if success:
            if self.splash:
                self.splash.update_status("Ready to start!")
                self.splash.update_progress(100)
                self.splash.update_step("Initialization complete!")
                # Close splash after short delay
                def close_splash():
                    time.sleep(1)
                    if self.splash:
                        try:
                            self.splash.close()
                        except:
                            pass
                        self.splash = None
                threading.Thread(target=close_splash, daemon=True).start()

            self.tray_app.update_status('ready', 'Models loaded successfully')
            logger.info("Models initialized successfully")
        else:
            if self.splash:
                self.splash.close()
                self.splash = None

            self.tray_app.update_status('error', 'Failed to load models')
            logger.error("Failed to initialize models")
            return False

        return True

    def toggle_recording(self):
        if not self.enabled:
            logger.warning("App is disabled")
            return

        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self):
        if self.is_recording:
            return

        if not self.model_manager.is_initialized:
            self.tray_app.update_status('error', 'Models not loaded')
            threading.Thread(target=self.initialize_models, daemon=True).start()
            return

        self.is_recording = True
        self.tray_app.update_status('recording', 'Recording...')

        if self.audio_recorder.start_recording():
            logger.info("Recording started")
        else:
            self.is_recording = False
            self.tray_app.update_status('error', 'Failed to start recording')

    def stop_recording(self):
        if not self.is_recording:
            return

        self.is_recording = False
        self.tray_app.update_status('processing', 'Processing...')

        audio_data = self.audio_recorder.stop_recording()
        if audio_data is not None:
            threading.Thread(
                target=self.process_audio,
                args=(audio_data,),
                daemon=True
            ).start()
        else:
            self.tray_app.update_status('error', 'No audio captured')

    def on_recording_complete(self, audio_data: np.ndarray):
        self.is_recording = False
        self.tray_app.update_status('processing', 'Processing...')
        threading.Thread(
            target=self.process_audio,
            args=(audio_data,),
            daemon=True
        ).start()

    def on_recording_error(self, error: str):
        self.is_recording = False
        self.tray_app.update_status('error', f'Recording error: {error}')
        logger.error(f"Recording error: {error}")

    def process_audio(self, audio_data: np.ndarray):
        with self.processing_lock:
            try:
                logger.info("Processing audio...")

                processed_audio = self.audio_processor.process_audio(
                    audio_data,
                    self.config['audio']['sample_rate']
                )

                wav_path = os.path.join(self.temp_dir, f"audio_{time.time()}.wav")
                self.audio_recorder.save_to_wav(processed_audio, wav_path)

                logger.info("Calling model_manager.process_audio...")
                original_text, translated_text, metadata = self.model_manager.process_audio(wav_path)
                logger.info(f"Got results - Original: {original_text[:50] if original_text else 'None'}...")
                logger.info(f"Translated: {translated_text[:50] if translated_text else 'None'}...")

                try:
                    os.remove(wav_path)
                except:
                    pass

                if translated_text:
                    # Check if LLM enhanced the text
                    llm_enhanced = metadata.get('llm_enhanced', False)

                    logger.info(f"About to inject text: {translated_text[:100]}...")
                    success = self.text_injector.inject_text_safe(translated_text)
                    logger.info(f"Injection result: {success}")

                    if success:
                        status_msg = 'AI-enhanced text injected' if llm_enhanced else 'Text injected successfully'
                        self.tray_app.update_status('success', status_msg)
                        logger.info(f"Successfully processed: {original_text[:50]}... -> {translated_text[:50]}...")
                    else:
                        self.tray_app.update_status('success', 'Text copied to clipboard')
                        logger.info("Text copied to clipboard")

                    self.save_to_history(original_text, translated_text, metadata)
                else:
                    self.tray_app.update_status('error', 'No speech detected')
                    logger.warning("No speech detected in audio")

            except Exception as e:
                self.tray_app.update_status('error', f'Processing failed: {str(e)}')
                logger.error(f"Audio processing failed: {e}", exc_info=True)

            finally:
                time.sleep(3)
                self.tray_app.update_status('ready', None)
                logger.info("Process audio thread completed")

    def save_to_history(self, original: str, translated: str, metadata: dict):
        try:
            history_file = Path("data/transcription_history.json")
            history = []

            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)

            entry = {
                'timestamp': time.time(),
                'datetime': time.strftime('%Y-%m-%d %H:%M:%S'),
                'original': original,
                'translated': translated,
                'metadata': metadata
            }

            history.append(entry)

            if len(history) > 100:
                history = history[-100:]

            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)

            logger.info("History saved")

        except Exception as e:
            logger.error(f"Failed to save history: {e}")

    def toggle_enabled(self):
        self.enabled = not self.enabled
        status = 'ready' if self.enabled else 'disabled'
        message = 'App enabled' if self.enabled else 'App disabled'
        self.tray_app.update_status(status, message, disabled=not self.enabled)
        logger.info(message)

    def show_settings(self):
        def on_settings_saved(new_config):
            self.config = new_config
            self.apply_config_changes()

        settings_window = SettingsWindow(self.config, on_settings_saved)
        threading.Thread(target=settings_window.show, daemon=True).start()

    def apply_config_changes(self):
        logger.info("Applying configuration changes...")

        # Apply audio device change if specified
        if 'input_device' in self.config['audio']:
            device_id = self.config['audio']['input_device']
            if device_id is not None:
                self.audio_recorder.set_input_device(device_id)
                logger.info(f"Audio input device set to: {device_id}")

        # Apply LLM configuration changes
        llm_enabled = self.config.get('llm', {}).get('enabled', True)
        if self.model_manager:
            self.model_manager.config = self.config

            # If LLM was disabled, clean up the Qwen processor
            if not llm_enabled and self.model_manager.qwen_processor:
                logger.info("Disabling Qwen2.5-3B LLM enhancement")
                self.model_manager.qwen_processor = None

                # Force garbage collection to free memory
                import gc
                gc.collect()
                if torch.cuda.is_available():
                    import torch
                    torch.cuda.empty_cache()
                logger.info("LLM memory freed")

            # If LLM was enabled and not loaded, offer to load it
            elif llm_enabled and not self.model_manager.qwen_processor:
                logger.info("LLM enhancement enabled but model not loaded")
                # Note: We don't auto-load here as it's resource intensive
                # User will get the enhancement on next app restart

        # Update tray menu to reflect AI status
        if self.tray_app and self.tray_app.icon:
            self.tray_app.icon.menu = self.tray_app.setup_menu()
            logger.info(f"Tray menu updated - AI Enhancement: {'ON' if llm_enabled else 'OFF'}")

    def run(self):
        logger.info("Starting TranscribeApp...")

        self.update_splash("Loading AI models...", 70, "Loading AI models (15-30 seconds)")
        threading.Thread(target=self.initialize_models, daemon=True).start()

        self.tray_app.run()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.shutdown()

    def shutdown(self):
        logger.info("Shutting down TranscribeApp...")

        self.hotkey_manager.stop()
        self.tray_app.stop()
        self.model_manager.cleanup()

        try:
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except:
            pass

        logger.info("Shutdown complete")
        sys.exit(0)


def main():
    try:
        if not sys.platform.startswith('win'):
            logger.error("This application only runs on Windows")
            sys.exit(1)

        # Create and show splash screen (disabled for now due to threading issues)
        splash = None
        # Splash screen disabled temporarily - causes threading issues with Tcl
        # Will work fine when packaged with PyInstaller
        logger.info("Splash screen disabled in development mode")

        # Create app with splash screen reference
        app = TranscribeApp(splash)
        app.run()

    except Exception as e:
        logger.critical(f"Critical error: {e}")
        if splash:
            try:
                splash.close()
            except:
                pass
        sys.exit(1)


if __name__ == "__main__":
    main()