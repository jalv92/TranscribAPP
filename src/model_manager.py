import whisper
from transformers import pipeline, MarianMTModel, MarianTokenizer
import torch
import logging
import time
import threading
from typing import Optional, Tuple
import os
import gc
from src.simple_text_processor import get_simple_processor
from src.qwen_processor import get_qwen_processor
from src.technical_terms import process_technical_terms

logger = logging.getLogger(__name__)


class ModelManager:
    def __init__(self, config: dict):
        self.config = config
        self.whisper_model = None
        self.translation_pipeline = None
        self.qwen_processor = None
        self.simple_processor = get_simple_processor()
        self.model_lock = threading.Lock()
        self.is_initialized = False
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        logger.info(f"ModelManager initialized, using device: {self.device}")

    def initialize_models(self, progress_callback=None) -> bool:
        try:
            logger.info("Starting model initialization...")

            # Check if models are already loaded
            if self.is_initialized:
                logger.info("Models already initialized")
                if progress_callback:
                    progress_callback("Models ready", 100)
                return True

            if progress_callback:
                progress_callback("Loading Whisper model...", 0)

            # Load with timeout
            import concurrent.futures
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

            try:
                future = executor.submit(self._load_whisper_model)
                future.result(timeout=30)  # 30 second timeout
            except concurrent.futures.TimeoutError:
                logger.error("Whisper model loading timed out")
                raise TimeoutError("Whisper model loading timed out after 30 seconds")
            finally:
                executor.shutdown(wait=False)

            if progress_callback:
                progress_callback("Loading translation model...", 50)

            self._load_translation_model()

            if progress_callback:
                progress_callback("Loading LLM for text enhancement...", 75)

            # Load Qwen2.5-3B if enabled
            if self.config.get('llm', {}).get('enabled', True):
                self.qwen_processor = get_qwen_processor()
                if self.qwen_processor.initialize(progress_callback):
                    logger.info("Qwen2.5-3B loaded successfully")
                else:
                    logger.warning("Qwen2.5-3B not available, using simple processor")
                    self.qwen_processor = None
            else:
                logger.info("LLM disabled in config, using simple processor")

            if progress_callback:
                progress_callback("Models ready", 100)

            self.is_initialized = True
            logger.info("All models initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize models: {e}")
            self.is_initialized = False
            return False

    def _load_whisper_model(self):
        try:
            model_size = self.config['whisper']['model_size']
            logger.info(f"Loading Whisper model: {model_size}")

            # Set cache directory
            cache_dir = os.path.expanduser("~/.cache/whisper")
            os.makedirs(cache_dir, exist_ok=True)

            # Load model with timeout and proper error handling
            import warnings
            warnings.filterwarnings("ignore")

            # Try CUDA first, fallback to CPU if needed
            try:
                if torch.cuda.is_available():
                    self.whisper_model = whisper.load_model(
                        model_size,
                        device="cuda",
                        download_root=cache_dir
                    )
                    logger.info(f"Whisper model {model_size} loaded on CUDA")
                else:
                    raise RuntimeError("CUDA not available")
            except Exception as cuda_error:
                logger.warning(f"Could not load on CUDA: {cuda_error}, trying CPU...")
                self.whisper_model = whisper.load_model(
                    model_size,
                    device="cpu",
                    download_root=cache_dir
                )
                logger.info(f"Whisper model {model_size} loaded on CPU")

            logger.info(f"Whisper model {model_size} loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise

    def _load_translation_model(self):
        try:
            model_name = self.config['translation']['model_name']
            logger.info(f"Loading translation model: {model_name}")

            # Check for sentencepiece
            try:
                import sentencepiece
            except ImportError:
                logger.warning("sentencepiece not installed. Attempting to install...")
                import subprocess
                import sys
                subprocess.check_call([sys.executable, "-m", "pip", "install", "sentencepiece"])
                logger.info("sentencepiece installed successfully")

            self.translation_pipeline = pipeline(
                "translation",
                model=model_name,
                device=0 if self.device == "cuda" else -1,
                max_length=self.config['translation']['max_length']
            )

            logger.info(f"Translation model {model_name} loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load translation model: {e}")
            logger.info("You may need to manually install: pip install sentencepiece")
            raise

    def transcribe(self, audio_path: str) -> Tuple[str, float]:
        if not self.is_initialized:
            raise RuntimeError("Models not initialized")

        with self.model_lock:
            try:
                start_time = time.time()

                # Check if file exists
                if not os.path.exists(audio_path):
                    raise FileNotFoundError(f"Audio file not found: {audio_path}")

                # Try transcription with direct file path first
                try:
                    # Whisper's transcribe method handles long audio automatically
                    # It processes in 30-second chunks internally
                    result = self.whisper_model.transcribe(
                        audio_path,
                        language="es",  # Force Spanish language
                        task="transcribe",  # Keep original language, don't translate
                        fp16=self.config['whisper'].get('fp16', False) and self.device == "cuda",
                        verbose=False,
                        condition_on_previous_text=True  # Better context for long audio
                    )
                except Exception as e:
                    if "ffmpeg" in str(e).lower() or "WinError 2" in str(e):
                        logger.warning("FFmpeg not found. Using soundfile as fallback...")
                        # Load audio using soundfile
                        try:
                            import soundfile as sf
                            import torch
                            import numpy as np

                            # Read audio file
                            audio_data, sample_rate = sf.read(audio_path)

                            # Convert to 16kHz if needed
                            if sample_rate != 16000:
                                import scipy.signal
                                audio_data = scipy.signal.resample(audio_data, int(len(audio_data) * 16000 / sample_rate))
                                sample_rate = 16000

                            # Convert to float32
                            audio_data = audio_data.astype('float32')

                            # Process long audio by splitting into chunks
                            import whisper

                            # Calculate audio duration
                            duration = len(audio_data) / sample_rate
                            logger.info(f"Processing audio of {duration:.1f} seconds")

                            if duration <= 30:
                                # Short audio - process normally
                                audio = whisper.pad_or_trim(audio_data.flatten())
                                mel = whisper.log_mel_spectrogram(audio).to(self.whisper_model.device)

                                # Detect the spoken language
                                _, probs = self.whisper_model.detect_language(mel)

                                # Decode the audio
                                options = whisper.DecodingOptions(
                                    language="es",  # Force Spanish
                                    task="transcribe",  # Don't translate, just transcribe
                                    fp16=self.config['whisper'].get('fp16', False) and self.device == "cuda"
                                )
                                result = whisper.decode(self.whisper_model, mel, options)
                                transcribed_text = result.text.strip()
                            else:
                                # Long audio - process in chunks with overlap
                                chunk_duration = 25  # seconds per chunk
                                overlap_duration = 2  # seconds of overlap
                                chunk_samples = chunk_duration * sample_rate
                                overlap_samples = overlap_duration * sample_rate

                                chunks_text = []
                                offset = 0

                                while offset < len(audio_data):
                                    # Extract chunk
                                    end = min(offset + chunk_samples, len(audio_data))
                                    chunk = audio_data[offset:end]

                                    # Pad if necessary
                                    if len(chunk) < chunk_samples:
                                        chunk = np.pad(chunk, (0, chunk_samples - len(chunk)), mode='constant')

                                    # Process chunk
                                    audio = whisper.pad_or_trim(chunk.flatten())
                                    mel = whisper.log_mel_spectrogram(audio).to(self.whisper_model.device)

                                    options = whisper.DecodingOptions(
                                        language="es",
                                        task="transcribe",
                                        fp16=self.config['whisper'].get('fp16', False) and self.device == "cuda"
                                    )
                                    result = whisper.decode(self.whisper_model, mel, options)

                                    chunk_text = result.text.strip()
                                    if chunk_text:
                                        chunks_text.append(chunk_text)
                                        logger.info(f"Chunk {len(chunks_text)}: {chunk_text[:50]}...")

                                    # Move to next chunk with overlap
                                    offset += chunk_samples - overlap_samples

                                    # If we're at the end, break
                                    if offset >= len(audio_data) - overlap_samples:
                                        break

                                # Combine all chunks
                                transcribed_text = " ".join(chunks_text)
                                logger.info(f"Combined {len(chunks_text)} chunks into full transcription")

                            confidence = 0.8  # Default confidence for soundfile processing

                            elapsed_time = time.time() - start_time
                            logger.info(f"Transcription completed in {elapsed_time:.2f}s: {transcribed_text[:50]}...")

                            return transcribed_text, confidence

                        except ImportError:
                            logger.error("soundfile not installed. Please install: pip install soundfile")
                            logger.info("Or install ffmpeg: https://ffmpeg.org/download.html")
                            raise
                    else:
                        raise

                transcribed_text = result['text'].strip()

                # Apply technical terms correction if enabled
                if self.config.get('quality', {}).get('fix_technical_terms', True):
                    transcribed_text = process_technical_terms(transcribed_text)
                    logger.info(f"Applied technical terms correction")

                elapsed_time = time.time() - start_time
                logger.info(f"Raw transcription completed in {elapsed_time:.2f}s: {transcribed_text[:50]}...")

                # Clean up Spanish text with Qwen or simple processor
                try:
                    if self.qwen_processor and self.qwen_processor.is_initialized:
                        cleaned_text = self.qwen_processor.clean_spanish_text(transcribed_text)
                        # Validate cleaned text doesn't contain duplicates or role markers
                        if 'assistant' in cleaned_text.lower() or cleaned_text.count('\n') > 2:
                            logger.warning(f"Qwen output suspicious, using raw text")
                            cleaned_text = transcribed_text
                        else:
                            logger.info(f"Qwen2.5-3B cleaned text: {cleaned_text[:50]}...")
                    else:
                        cleaned_text = self.simple_processor.clean_spanish_text(transcribed_text)
                        logger.info(f"Simple cleaned text: {cleaned_text[:50]}...")
                    return cleaned_text, 1.0
                except Exception as e:
                    logger.warning(f"Text cleaning failed: {e}, using raw text")
                    return transcribed_text, 0.5

            except Exception as e:
                logger.error(f"Transcription failed: {e}")
                raise

    def translate(self, text: str, original_spanish: str = None) -> str:
        if not self.is_initialized:
            raise RuntimeError("Models not initialized")

        with self.model_lock:
            try:
                start_time = time.time()

                result = self.translation_pipeline(
                    text,
                    max_length=self.config['translation']['max_length'],
                    clean_up_tokenization_spaces=True
                )

                translated_text = result[0]['translation_text']

                elapsed_time = time.time() - start_time
                logger.info(f"Raw translation completed in {elapsed_time:.2f}s")

                # Check if enhancement is enabled
                enhance_enabled = self.config.get('llm', {}).get('enhance_translation', True)

                # Enhance translation with Qwen or simple processor
                if original_spanish and enhance_enabled:
                    try:
                        if self.qwen_processor and self.qwen_processor.is_initialized:
                            enhanced_text = self.qwen_processor.enhance_translation(
                                original_spanish, translated_text
                            )
                            # Validate enhancement doesn't contain duplicates
                            if 'assistant' in enhanced_text.lower():
                                logger.warning("Enhancement contains role markers, using raw translation")
                                return translated_text

                            # Check for obvious duplication
                            first_words = translated_text.split()[:5]
                            if len(first_words) > 2:
                                first_phrase = ' '.join(first_words[:3])
                                if enhanced_text.count(first_phrase) > 1:
                                    logger.warning("Enhancement contains duplication, using raw translation")
                                    return translated_text

                            logger.info(f"Qwen2.5-3B enhanced translation: {enhanced_text[:50]}...")
                            return enhanced_text
                        else:
                            enhanced_text = self.simple_processor.enhance_translation(
                                original_spanish, translated_text
                            )
                            logger.info(f"Simple enhanced translation: {enhanced_text[:50]}...")
                            return enhanced_text
                    except Exception as e:
                        logger.warning(f"Enhancement failed: {e}, using raw translation")
                        return translated_text
                else:
                    if not enhance_enabled:
                        logger.info("Translation enhancement disabled in config")
                    return translated_text

            except Exception as e:
                logger.error(f"Translation failed: {e}")
                raise

    def process_audio(self, audio_path: str) -> Tuple[str, str, dict]:
        try:
            transcribed_text, confidence = self.transcribe(audio_path)

            if not transcribed_text:
                return "", "", {"error": "No speech detected"}

            # Pass original Spanish for context-aware translation enhancement
            translated_text = self.translate(transcribed_text, original_spanish=transcribed_text)

            metadata = {
                "confidence": confidence,
                "original_text": transcribed_text,
                "translated_text": translated_text,
                "source_language": self.config['whisper']['language'],
                "target_language": "en",
                "llm_enhanced": self.qwen_processor and self.qwen_processor.is_initialized
            }

            logger.info(f"Returning from process_audio - Original: {transcribed_text[:50]}...")
            logger.info(f"Returning from process_audio - Translated: {translated_text[:50]}...")
            return transcribed_text, translated_text, metadata

        except Exception as e:
            logger.error(f"Audio processing failed: {e}", exc_info=True)
            return "", "", {"error": str(e)}

    def cleanup(self):
        try:
            if self.whisper_model:
                del self.whisper_model
                self.whisper_model = None

            if self.translation_pipeline:
                del self.translation_pipeline
                self.translation_pipeline = None

            gc.collect()
            torch.cuda.empty_cache() if torch.cuda.is_available() else None

            self.is_initialized = False
            logger.info("Model cleanup completed")

        except Exception as e:
            logger.error(f"Cleanup failed: {e}")


class ModelLoader:
    @staticmethod
    def download_models(config: dict, progress_callback=None):
        try:
            if progress_callback:
                progress_callback("Checking Whisper model...", 10)

            model_size = config['whisper']['model_size']
            whisper.load_model(model_size, download_root=os.path.expanduser("~/.cache/whisper"))

            if progress_callback:
                progress_callback("Checking translation model...", 50)

            from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
            model_name = config['translation']['model_name']

            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

            if progress_callback:
                progress_callback("All models ready", 100)

            return True

        except Exception as e:
            logger.error(f"Model download failed: {e}")
            return False