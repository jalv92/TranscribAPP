"""
Faster Whisper Processor - 4x faster than OpenAI Whisper
Uses CTranslate2 for optimized inference
"""

import logging
import time
import os
import numpy as np
from typing import Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import faster-whisper
try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False
    logger.warning("faster-whisper not installed. Install with: pip install faster-whisper")

class FasterWhisperProcessor:
    """Optimized Whisper implementation using CTranslate2"""

    def __init__(self, config: dict):
        self.config = config
        self.model = None
        self.is_initialized = False
        self.model_size = config['whisper']['model_size']

        # Determine device and compute type
        import torch
        if torch.cuda.is_available():
            self.device = "cuda"
            self.compute_type = "float16"  # or "int8_float16" for even faster
        else:
            self.device = "cpu"
            self.compute_type = "int8"  # or "float32" for better quality

        logger.info(f"FasterWhisperProcessor initialized - Device: {self.device}, Compute: {self.compute_type}")

    def initialize(self, progress_callback=None) -> bool:
        """Initialize faster-whisper model"""
        if not FASTER_WHISPER_AVAILABLE:
            logger.error("faster-whisper not available")
            return False

        try:
            if progress_callback:
                progress_callback("Loading Faster Whisper model...", 0)

            logger.info(f"Loading Faster Whisper model: {self.model_size}")

            # Set cache directory for models
            cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
            cache_dir.mkdir(parents=True, exist_ok=True)

            # Initialize model with optimal settings
            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
                cpu_threads=4,  # For CPU inference
                num_workers=1,  # For GPU inference
                download_root=str(cache_dir)
            )

            if progress_callback:
                progress_callback("Faster Whisper ready", 100)

            self.is_initialized = True
            logger.info(f"Faster Whisper {self.model_size} loaded successfully on {self.device}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Faster Whisper: {e}")
            if progress_callback:
                progress_callback("Failed to load Whisper model", 0)
            return False

    def transcribe(self, audio_path: str) -> Tuple[str, float]:
        """Transcribe audio using faster-whisper"""
        if not self.is_initialized:
            raise RuntimeError("Faster Whisper not initialized")

        try:
            start_time = time.time()

            # Check if file exists
            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"Audio file not found: {audio_path}")

            # Transcribe with optimal settings for speed
            segments, info = self.model.transcribe(
                audio_path,
                language="es",  # Force Spanish
                task="transcribe",  # Don't translate
                beam_size=1,  # Faster than default 5
                best_of=1,  # Single pass for speed
                temperature=0,  # Greedy decoding for speed
                vad_filter=True,  # Voice Activity Detection - speeds up processing
                vad_parameters=dict(
                    threshold=0.5,
                    min_speech_duration_ms=250,
                    max_speech_duration_s=float('inf'),
                    min_silence_duration_ms=2000,
                    speech_pad_ms=400
                ),
                word_timestamps=False,  # Disable for speed
                condition_on_previous_text=False,  # Faster but may reduce quality slightly
                compression_ratio_threshold=2.4,
                log_prob_threshold=-1.0,
                no_speech_threshold=0.6,
                initial_prompt=None  # Can add context here if needed
            )

            # Combine all segments
            transcribed_text = " ".join([segment.text.strip() for segment in segments])

            # Calculate confidence from average log probability
            total_log_prob = 0
            segment_count = 0
            for segment in segments:
                if segment.avg_logprob:
                    total_log_prob += segment.avg_logprob
                    segment_count += 1

            confidence = 1.0  # Default
            if segment_count > 0:
                avg_log_prob = total_log_prob / segment_count
                # Convert log probability to confidence score (0-1)
                confidence = min(1.0, max(0.0, 1.0 + (avg_log_prob / 2.0)))

            elapsed_time = time.time() - start_time

            # Log performance metrics
            audio_duration = info.duration if hasattr(info, 'duration') else 0
            rtf = elapsed_time / audio_duration if audio_duration > 0 else 0
            logger.info(f"Transcription completed in {elapsed_time:.2f}s")
            logger.info(f"Audio duration: {audio_duration:.1f}s, RTF: {rtf:.2f}x")
            logger.info(f"Detected language: {info.language} with probability {info.language_probability:.2f}")

            return transcribed_text, confidence

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise

    def transcribe_with_timestamps(self, audio_path: str) -> dict:
        """Transcribe with word-level timestamps (slower but more detailed)"""
        if not self.is_initialized:
            raise RuntimeError("Faster Whisper not initialized")

        try:
            segments, info = self.model.transcribe(
                audio_path,
                language="es",
                word_timestamps=True,  # Enable for detailed timing
                vad_filter=True
            )

            result = {
                "text": "",
                "segments": [],
                "language": info.language,
                "duration": info.duration
            }

            for segment in segments:
                segment_dict = {
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text,
                    "words": []
                }

                if segment.words:
                    for word in segment.words:
                        segment_dict["words"].append({
                            "word": word.word,
                            "start": word.start,
                            "end": word.end,
                            "probability": word.probability
                        })

                result["segments"].append(segment_dict)
                result["text"] += segment.text + " "

            result["text"] = result["text"].strip()
            return result

        except Exception as e:
            logger.error(f"Transcription with timestamps failed: {e}")
            raise

    def cleanup(self):
        """Clean up model from memory"""
        try:
            if self.model:
                del self.model
                self.model = None

            self.is_initialized = False
            logger.info("Faster Whisper processor cleaned up")

        except Exception as e:
            logger.error(f"Cleanup failed: {e}")

# Global instance
_faster_whisper_processor = None

def get_faster_whisper_processor(config: dict) -> FasterWhisperProcessor:
    """Get or create the faster whisper processor instance"""
    global _faster_whisper_processor
    if _faster_whisper_processor is None:
        _faster_whisper_processor = FasterWhisperProcessor(config)
    return _faster_whisper_processor