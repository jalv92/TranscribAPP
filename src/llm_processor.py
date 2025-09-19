"""
Universal LLM Processor - Supports multiple models dynamically
Works with Qwen, Llama, Phi, Gemma, and other instruction-tuned models
"""

import logging
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from typing import Optional, Dict
import gc
import os

logger = logging.getLogger(__name__)

class UniversalLLMProcessor:
    """Universal processor for multiple LLM models"""

    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.is_initialized = False
        self.current_model_path = None
        self.current_model_id = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    def initialize(self, model_path: str = None, model_id: str = None, progress_callback=None) -> bool:
        """Initialize with specified model or default"""
        try:
            # Default to Qwen if not specified
            if not model_path:
                model_path = "LLM/Qwen2.5-3B-Instruct"
                model_id = "Qwen2.5-3B-Instruct"

            # Check if already loaded with same model
            if self.is_initialized and self.current_model_path == model_path:
                logger.info(f"Model {model_id} already loaded")
                return True

            # Clean up previous model if different
            if self.is_initialized and self.current_model_path != model_path:
                self.cleanup()

            logger.info(f"Loading LLM model: {model_id} from {model_path}")

            if progress_callback:
                progress_callback(f"Loading {model_id}...", 0)

            # Check if model path exists
            if not os.path.exists(model_path):
                logger.error(f"Model path not found: {model_path}")
                return False

            # Configure quantization for memory efficiency
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4"
            )

            try:
                # Load tokenizer
                self.tokenizer = AutoTokenizer.from_pretrained(
                    model_path,
                    trust_remote_code=True,
                    local_files_only=True
                )

                if progress_callback:
                    progress_callback(f"Loading {model_id} weights...", 50)

                # Load model with 4-bit quantization
                if self.device == "cuda":
                    self.model = AutoModelForCausalLM.from_pretrained(
                        model_path,
                        quantization_config=quantization_config,
                        device_map="auto",
                        trust_remote_code=True,
                        local_files_only=True,
                        torch_dtype=torch.float16
                    )
                else:
                    # CPU fallback without quantization
                    self.model = AutoModelForCausalLM.from_pretrained(
                        model_path,
                        trust_remote_code=True,
                        local_files_only=True,
                        torch_dtype=torch.float32,
                        low_cpu_mem_usage=True
                    )

                self.current_model_path = model_path
                self.current_model_id = model_id
                self.is_initialized = True

                if progress_callback:
                    progress_callback(f"{model_id} ready", 100)

                logger.info(f"Successfully loaded {model_id}")
                return True

            except Exception as e:
                logger.error(f"Failed to load model with quantization: {e}")
                logger.info("Attempting to load without quantization...")

                # Fallback to non-quantized loading
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_path,
                    trust_remote_code=True,
                    local_files_only=True,
                    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                    low_cpu_mem_usage=True
                )

                if self.device == "cuda":
                    self.model = self.model.cuda()

                self.current_model_path = model_path
                self.current_model_id = model_id
                self.is_initialized = True

                logger.info(f"Loaded {model_id} without quantization")
                return True

        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            return False

    def get_prompt_template(self, instruction: str, model_id: str = None) -> str:
        """Get appropriate prompt template for the model"""
        if not model_id:
            model_id = self.current_model_id

        # Model-specific templates
        if "Qwen" in model_id:
            return f"<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n<|im_start|>user\n{instruction}<|im_end|>\n<|im_start|>assistant\n"
        elif "Llama" in model_id or "Meta" in model_id:
            return f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\nYou are a helpful assistant.<|eot_id|><|start_header_id|>user<|end_header_id|>\n{instruction}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n"
        elif "Phi" in model_id:
            return f"<|system|>You are a helpful assistant.<|end|>\n<|user|>\n{instruction}<|end|>\n<|assistant|>\n"
        elif "gemma" in model_id.lower():
            return f"<start_of_turn>user\n{instruction}<end_of_turn>\n<start_of_turn>model\n"
        else:
            # Generic instruction format
            return f"### Instruction:\n{instruction}\n\n### Response:\n"

    def clean_spanish_text(self, text: str) -> str:
        """Clean and improve Spanish transcription"""
        # Check for empty or invalid input
        if not text or not text.strip():
            logger.warning("Empty text received, skipping LLM processing")
            return text

        if not self.is_initialized:
            logger.warning("LLM not initialized, returning original text")
            return text

        try:
            instruction = f"""Fix this Spanish transcription, correcting only obvious errors. Keep it natural and conversational:
"{text}"

Provide only the corrected text without explanations."""

            prompt = self.get_prompt_template(instruction)

            inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
            if self.device == "cuda":
                inputs = inputs.to("cuda")

            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=100,
                    temperature=0.1,
                    do_sample=True,
                    top_p=0.9,
                    repetition_penalty=1.1
                )

            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

            # Extract only the response part
            if "<|assistant|>" in response:
                cleaned = response.split("<|assistant|>")[-1].strip()
            elif "### Response:" in response:
                cleaned = response.split("### Response:")[-1].strip()
            elif "<start_of_turn>model" in response:
                cleaned = response.split("<start_of_turn>model")[-1].strip()
            else:
                # Find where the instruction ends
                if text and text in response:
                    # Only split if text is not empty
                    parts = response.split(text)
                    if len(parts) > 1:
                        cleaned = parts[-1].strip()
                    else:
                        cleaned = response.strip()
                else:
                    cleaned = response.strip()

            # Clean up any remaining artifacts
            cleaned = cleaned.replace("<|im_end|>", "").strip()
            cleaned = cleaned.replace("<|eot_id|>", "").strip()
            cleaned = cleaned.replace("<end_of_turn>", "").strip()

            # Validate it's not empty or duplicate
            if not cleaned or cleaned == text or len(cleaned) < 5:
                return text

            return cleaned

        except Exception as e:
            logger.error(f"Spanish text cleaning failed: {e}")
            return text

    def enhance_translation(self, original_spanish: str, english_translation: str) -> str:
        """Enhance English translation for better fluency"""
        if not self.is_initialized:
            logger.warning("LLM not initialized, returning original translation")
            return english_translation

        try:
            instruction = f"""Given this Spanish text: "{original_spanish}"
And its translation: "{english_translation}"

Provide a more natural and fluent English version. Keep the same meaning but make it sound native.
Output only the improved translation."""

            prompt = self.get_prompt_template(instruction)

            inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
            if self.device == "cuda":
                inputs = inputs.to("cuda")

            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=150,
                    temperature=0.3,
                    do_sample=True,
                    top_p=0.9,
                    repetition_penalty=1.1
                )

            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

            # Extract enhanced translation
            if "<|assistant|>" in response:
                enhanced = response.split("<|assistant|>")[-1].strip()
            elif "### Response:" in response:
                enhanced = response.split("### Response:")[-1].strip()
            elif "<start_of_turn>model" in response:
                enhanced = response.split("<start_of_turn>model")[-1].strip()
            else:
                if english_translation in response:
                    enhanced = response.split(english_translation)[-1].strip()
                else:
                    enhanced = response.strip()

            # Clean up
            enhanced = enhanced.replace("<|im_end|>", "").strip()
            enhanced = enhanced.replace("<|eot_id|>", "").strip()
            enhanced = enhanced.replace("<end_of_turn>", "").strip()

            # Validate
            if not enhanced or len(enhanced) < 5:
                return english_translation

            return enhanced

        except Exception as e:
            logger.error(f"Translation enhancement failed: {e}")
            return english_translation

    def switch_model(self, model_path: str, model_id: str, progress_callback=None) -> bool:
        """Switch to a different model"""
        logger.info(f"Switching from {self.current_model_id} to {model_id}")

        # Clean up current model
        self.cleanup()

        # Load new model
        return self.initialize(model_path, model_id, progress_callback)

    def cleanup(self):
        """Clean up model from memory"""
        try:
            if self.model:
                del self.model
                self.model = None

            if self.tokenizer:
                del self.tokenizer
                self.tokenizer = None

            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            self.is_initialized = False
            self.current_model_path = None
            self.current_model_id = None

            logger.info("LLM processor cleaned up")

        except Exception as e:
            logger.error(f"Cleanup failed: {e}")

# Global instance
_universal_processor = None

def get_universal_processor() -> UniversalLLMProcessor:
    """Get or create the universal processor instance"""
    global _universal_processor
    if _universal_processor is None:
        _universal_processor = UniversalLLMProcessor()
    return _universal_processor