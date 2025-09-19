import torch
import logging
from pathlib import Path
from typing import Optional
from src.technical_terms import process_technical_terms

logger = logging.getLogger(__name__)


class QwenProcessor:
    """Qwen2.5-3B-Instruct processor - High quality Spanish text processing"""

    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.device = None
        self.is_initialized = False
        # Use the exact path where user downloaded the model
        self.model_path = Path("LLM/Qwen2.5-3B-Instruct")

    def initialize(self, progress_callback=None) -> bool:
        """Initialize Qwen2.5-3B with optimal settings for RTX 3060"""
        try:
            if self.is_initialized:
                return True

            if not self.model_path.exists():
                logger.error(f"Model not found at {self.model_path}")
                logger.info("Expected path: LLM/Qwen2.5-3B-Instruct")
                return False

            logger.info("Initializing Qwen2.5-3B-Instruct...")

            from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Using device: {self.device}")

            if progress_callback:
                progress_callback("Loading Qwen2.5-3B tokenizer...", 30)

            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                str(self.model_path),
                trust_remote_code=False
            )

            # Set padding token if needed
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            if progress_callback:
                progress_callback("Loading Qwen2.5-3B model...", 50)

            if self.device == "cuda":
                # Use 4-bit quantization for even faster speed
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4"
                )

                self.model = AutoModelForCausalLM.from_pretrained(
                    str(self.model_path),
                    quantization_config=quantization_config,
                    device_map="auto",
                    torch_dtype=torch.float16,
                    trust_remote_code=False,
                    low_cpu_mem_usage=True
                )
                logger.info("Qwen2.5-3B loaded with 4-bit quantization on CUDA")
            else:
                # CPU fallback
                self.model = AutoModelForCausalLM.from_pretrained(
                    str(self.model_path),
                    torch_dtype=torch.float32,
                    trust_remote_code=False,
                    low_cpu_mem_usage=True
                )
                logger.info("Qwen2.5-3B loaded on CPU")

            self.model.eval()

            if progress_callback:
                progress_callback("Qwen2.5-3B ready", 100)

            self.is_initialized = True
            logger.info("Qwen2.5-3B-Instruct initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Qwen: {e}")
            return False

    def clean_spanish_text(self, text: str) -> str:
        """Clean Spanish transcription using Qwen's instruction format"""
        if not self.is_initialized:
            return text

        try:
            # Simpler prompt to avoid confusion
            messages = [
                {"role": "system", "content": "Corrige errores gramaticales y elimina muletillas. Responde SOLO con el texto corregido, sin explicaciones."},
                {"role": "user", "content": text}
            ]

            # Apply chat template
            prompt = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )

            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                truncation=True,
                max_length=256
            )

            if self.device == "cuda":
                inputs = {k: v.cuda() for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=len(text.split()) + 10,  # Slightly more than input
                    temperature=0.1,    # Low temperature for consistency
                    do_sample=False,    # Deterministic for consistency
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )

            # Decode only the new tokens (skip the prompt)
            generated_ids = outputs[0][len(inputs['input_ids'][0]):]
            response = self.tokenizer.decode(generated_ids, skip_special_tokens=True)

            # Clean up any role markers that might have slipped through
            response = response.replace('assistant', '').replace('Assistant', '')
            response = response.replace('\nassistant\n', ' ').replace('\nAssistant\n', ' ')
            response = response.strip()

            # Remove any duplicate lines
            lines = response.split('\n')
            unique_lines = []
            for line in lines:
                clean_line = line.strip()
                if clean_line and clean_line not in unique_lines:
                    unique_lines.append(clean_line)

            cleaned = ' '.join(unique_lines)

            # Final validation - if result is empty or too different, return original
            if not cleaned or len(cleaned) < 3:
                return text

            # Check if the cleaned text is reasonable (not too different from original)
            if len(cleaned) > len(text) * 2:
                logger.warning(f"Qwen output too long, using original")
                return text

            # Apply technical terms correction after cleaning
            cleaned = process_technical_terms(cleaned)

            logger.info(f"Qwen cleaned: '{text[:30]}...' -> '{cleaned[:30]}...'")
            return cleaned

        except Exception as e:
            logger.error(f"Spanish cleanup failed: {e}")
            return text

    def enhance_translation(self, spanish: str, english: str) -> str:
        """Enhance English translation using Qwen with context"""
        if not self.is_initialized:
            return english

        try:
            # Provide context for better translation
            messages = [
                {"role": "system", "content": "Improve the English translation to be more natural. Keep the meaning exact. Output ONLY the improved English, no explanations."},
                {"role": "user", "content": f"Spanish: {spanish}\nEnglish: {english}\nImproved English:"}
            ]

            prompt = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )

            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                truncation=True,
                max_length=400
            )

            if self.device == "cuda":
                inputs = {k: v.cuda() for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=len(english.split()) + 20,  # Similar length to input
                    temperature=0.1,  # Very low for consistency
                    do_sample=False,  # Deterministic
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )

            # Decode only the new tokens (skip the prompt)
            generated_ids = outputs[0][len(inputs['input_ids'][0]):]
            response = self.tokenizer.decode(generated_ids, skip_special_tokens=True)

            # Clean up any role markers
            response = response.replace('assistant', '').replace('Assistant', '')
            response = response.replace('\nassistant\n', ' ').replace('\nAssistant\n', ' ')

            # Remove any lines that look like prompts or instructions
            lines = response.split('\n')
            cleaned_lines = []
            for line in lines:
                line = line.strip()
                # Skip lines that look like prompts or role markers
                if line and not any(marker in line.lower() for marker in
                    ['spanish:', 'english:', 'improved:', 'translated:', 'corrected:', 'fixed:', 'here']):
                    cleaned_lines.append(line)

            enhanced = ' '.join(cleaned_lines).strip()

            # Remove quotes and extra whitespace
            enhanced = enhanced.strip('"').strip("'").strip()

            # Validation checks
            if not enhanced or len(enhanced) < 3:
                logger.debug("Enhancement too short, using original")
                return english

            # Check for Spanish contamination
            spanish_indicators = ['que', 'por', 'está', 'pero', 'como', 'cuando', 'donde', 'así', 'también']
            words = enhanced.lower().split()
            spanish_count = sum(1 for word in spanish_indicators if word in words)

            if len(words) > 0 and spanish_count / len(words) > 0.2:
                logger.warning("Enhancement contains Spanish, using original")
                return english

            # Check for duplication
            if enhanced.count(english[:20]) > 1:  # Check if beginning is repeated
                logger.warning("Enhancement contains duplication, using original")
                return english

            # Check length sanity (should not be too different)
            if len(enhanced) > len(english) * 1.5 or len(enhanced) < len(english) * 0.5:
                logger.warning(f"Enhancement length suspicious ({len(enhanced)} vs {len(english)}), using original")
                return english

            # Ensure key content is preserved
            english_words = set(english.lower().split())
            enhanced_words = set(enhanced.lower().split())

            # At least 50% of original words should be present
            if len(english_words) > 2:
                common = english_words.intersection(enhanced_words)
                if len(common) < len(english_words) * 0.5:
                    logger.warning("Enhancement diverged too much, using original")
                    return english

            # Apply technical terms correction to enhanced translation
            enhanced = process_technical_terms(enhanced)

            logger.info(f"Qwen enhanced: '{english[:30]}...' -> '{enhanced[:30]}...'")
            return enhanced

        except Exception as e:
            logger.error(f"Translation enhancement failed: {e}")
            return english

    def cleanup(self):
        """Clean up model from memory"""
        try:
            if self.model:
                del self.model
                self.model = None

            if self.tokenizer:
                del self.tokenizer
                self.tokenizer = None

            torch.cuda.empty_cache() if torch.cuda.is_available() else None

            self.is_initialized = False
            logger.info("Qwen cleanup completed")

        except Exception as e:
            logger.error(f"Cleanup failed: {e}")


# Singleton instance
_qwen_processor = None

def get_qwen_processor() -> QwenProcessor:
    """Get Qwen processor instance"""
    global _qwen_processor
    if _qwen_processor is None:
        _qwen_processor = QwenProcessor()
    return _qwen_processor