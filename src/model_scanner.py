"""
Model Scanner - Detects available LLM models in the LLM folder
Supports multiple model formats and provides model metadata
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# Model profiles with their characteristics
MODEL_PROFILES = {
    "Qwen2.5-3B-Instruct": {
        "name": "Qwen 2.5 3B",
        "description": "Excellent general-purpose model with good multilingual support",
        "size_gb": 6,
        "memory_required_gb": 8,
        "speed": "medium",
        "quality": "excellent",
        "provider": "Alibaba",
        "type": "instruction",
        "supports_4bit": True
    },
    "Llama-3.2-3B-Instruct": {
        "name": "Llama 3.2 3B",
        "description": "Meta's latest model with superior English fluency",
        "size_gb": 6,
        "memory_required_gb": 8,
        "speed": "medium",
        "quality": "excellent",
        "provider": "Meta",
        "type": "instruction",
        "supports_4bit": True
    },
    "Llama-3.2-1B-Instruct": {
        "name": "Llama 3.2 1B",
        "description": "Lightweight model for resource-constrained systems",
        "size_gb": 2,
        "memory_required_gb": 4,
        "speed": "fast",
        "quality": "good",
        "provider": "Meta",
        "type": "instruction",
        "supports_4bit": True
    },
    "Phi-3.5-mini-instruct": {
        "name": "Phi 3.5 Mini",
        "description": "Microsoft's efficient small model",
        "size_gb": 3,
        "memory_required_gb": 5,
        "speed": "fast",
        "quality": "good",
        "provider": "Microsoft",
        "type": "instruction",
        "supports_4bit": True
    },
    "gemma-2-2b-it": {
        "name": "Gemma 2 2B",
        "description": "Google's efficient instruction-tuned model",
        "size_gb": 4,
        "memory_required_gb": 6,
        "speed": "fast",
        "quality": "good",
        "provider": "Google",
        "type": "instruction",
        "supports_4bit": True
    }
}

class ModelScanner:
    """Scans and manages available LLM models"""

    def __init__(self, llm_folder: str = "LLM"):
        self.llm_folder = Path(llm_folder)
        self.available_models = []

    def scan_models(self) -> List[Dict]:
        """Scan LLM folder for available models"""
        models = []

        if not self.llm_folder.exists():
            logger.warning(f"LLM folder not found: {self.llm_folder}")
            return models

        # Scan each subdirectory in LLM folder
        for model_dir in self.llm_folder.iterdir():
            if model_dir.is_dir():
                model_info = self._get_model_info(model_dir)
                if model_info:
                    models.append(model_info)

        self.available_models = models
        logger.info(f"Found {len(models)} available models")
        return models

    def _get_model_info(self, model_dir: Path) -> Optional[Dict]:
        """Extract model information from directory"""
        model_name = model_dir.name

        # Check if model has required files
        config_file = model_dir / "config.json"

        if not config_file.exists():
            logger.debug(f"No config.json found in {model_dir}")
            return None

        # Get model profile if available
        profile = MODEL_PROFILES.get(model_name, {})

        # Try to read model config
        model_size = self._get_model_size(model_dir)

        model_info = {
            "id": model_name,
            "path": str(model_dir),
            "name": profile.get("name", model_name),
            "description": profile.get("description", "Custom model"),
            "size_gb": model_size,
            "memory_required_gb": profile.get("memory_required_gb", model_size * 1.5),
            "provider": profile.get("provider", "Unknown"),
            "quality": profile.get("quality", "unknown"),
            "speed": profile.get("speed", "unknown"),
            "type": profile.get("type", "unknown"),
            "supports_4bit": profile.get("supports_4bit", False),
            "is_installed": self._check_model_complete(model_dir)
        }

        return model_info

    def _get_model_size(self, model_dir: Path) -> float:
        """Calculate total size of model files in GB"""
        total_size = 0

        for file_path in model_dir.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size

        return round(total_size / (1024**3), 1)  # Convert to GB

    def _check_model_complete(self, model_dir: Path) -> bool:
        """Check if model has all required files"""
        required_files = ["config.json", "tokenizer.json", "tokenizer_config.json"]

        for file_name in required_files:
            if not (model_dir / file_name).exists():
                return False

        # Check for model weights (various formats)
        model_files = list(model_dir.glob("*.safetensors")) + \
                     list(model_dir.glob("*.bin")) + \
                     list(model_dir.glob("*.gguf"))

        return len(model_files) > 0

    def get_recommended_model(self, available_ram_gb: int = 16) -> Optional[str]:
        """Get recommended model based on system resources"""
        suitable_models = [
            m for m in self.available_models
            if m["memory_required_gb"] <= available_ram_gb and m["is_installed"]
        ]

        if not suitable_models:
            return None

        # Sort by quality (prioritize quality over speed for recommendations)
        quality_order = {"excellent": 0, "good": 1, "unknown": 2}
        suitable_models.sort(
            key=lambda x: (quality_order.get(x["quality"], 3), -x["size_gb"])
        )

        return suitable_models[0]["id"] if suitable_models else None

    def get_model_path(self, model_id: str) -> Optional[str]:
        """Get full path for a model by ID"""
        for model in self.available_models:
            if model["id"] == model_id:
                return model["path"]
        return None

    def add_model_profile(self, model_name: str, profile: Dict):
        """Add or update a model profile"""
        MODEL_PROFILES[model_name] = profile
        logger.info(f"Added profile for {model_name}")

# Helper function to get available models
def get_available_models(llm_folder: str = "LLM") -> List[Dict]:
    """Quick function to get list of available models"""
    scanner = ModelScanner(llm_folder)
    return scanner.scan_models()

# Helper function to get system memory
def get_system_memory_gb() -> int:
    """Get available system RAM in GB"""
    try:
        import psutil
        return round(psutil.virtual_memory().total / (1024**3))
    except:
        return 16  # Default assumption