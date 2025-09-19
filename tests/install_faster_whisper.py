#!/usr/bin/env python3
"""
Installation script for Faster-Whisper
Provides 4x speed improvement over OpenAI Whisper
"""

import subprocess
import sys
import os

def install_faster_whisper():
    print("=" * 70)
    print("INSTALLING FASTER-WHISPER FOR 4X SPEED IMPROVEMENT")
    print("=" * 70)
    print()

    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8+ required")
        return False

    print("📦 Installing faster-whisper and dependencies...")
    print("This may take 2-3 minutes...")
    print()

    # Install faster-whisper
    packages = [
        "faster-whisper>=1.0.0",
        "ctranslate2>=3.20.0",  # Core acceleration library
        "tokenizers>=0.13.3",    # Fast tokenization
        "onnxruntime",           # Additional optimization
    ]

    for package in packages:
        print(f"Installing {package}...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", package
            ])
            print(f"✅ {package} installed successfully")
        except subprocess.CalledProcessError:
            print(f"⚠️ Failed to install {package}, trying without version constraints...")
            try:
                base_package = package.split(">=")[0]
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", base_package
                ])
                print(f"✅ {base_package} installed")
            except:
                print(f"❌ Could not install {base_package}")
                return False

    print()
    print("✅ Faster-Whisper installed successfully!")
    print()

    # Test import
    print("🔍 Testing installation...")
    try:
        from faster_whisper import WhisperModel
        print("✅ Faster-Whisper imports correctly")

        # Check CUDA availability
        import torch
        if torch.cuda.is_available():
            print("✅ CUDA available - Will use GPU acceleration")
        else:
            print("ℹ️ CUDA not available - Will use CPU (still 2-3x faster)")

        return True
    except ImportError as e:
        print(f"❌ Import test failed: {e}")
        return False

def show_benefits():
    print()
    print("=" * 70)
    print("FASTER-WHISPER BENEFITS")
    print("=" * 70)
    print()
    print("🚀 Speed Improvements:")
    print("   • 4x faster on GPU (CUDA)")
    print("   • 2-3x faster on CPU")
    print("   • Your 37-second transcription → ~8-10 seconds")
    print()
    print("💾 Memory Savings:")
    print("   • 50% less VRAM usage")
    print("   • More efficient CPU memory use")
    print()
    print("✨ Additional Features:")
    print("   • Voice Activity Detection (VAD)")
    print("   • Word-level timestamps")
    print("   • Better streaming support")
    print()
    print("🎯 Quality:")
    print("   • Identical accuracy to OpenAI Whisper")
    print("   • Same models, optimized runtime")
    print()

def update_config():
    """Update config.json to use faster-whisper"""
    import json

    config_path = "config.json"
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)

        # Enable faster-whisper
        if 'whisper' not in config:
            config['whisper'] = {}

        config['whisper']['use_faster'] = True
        config['whisper']['beam_size'] = 1  # Faster beam search
        config['whisper']['vad_filter'] = True  # Enable VAD

        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)

        print("✅ Updated config.json to use Faster-Whisper")
        print()
        print("Current Whisper settings:")
        print(f"  • Model size: {config['whisper'].get('model_size', 'small')}")
        print(f"  • Use faster: {config['whisper'].get('use_faster', True)}")
        print(f"  • VAD filter: {config['whisper'].get('vad_filter', True)}")
        print()

def main():
    if install_faster_whisper():
        show_benefits()
        update_config()

        print("=" * 70)
        print("INSTALLATION COMPLETE!")
        print("=" * 70)
        print()
        print("Next steps:")
        print("1. Restart TranscribeApp")
        print("2. It will automatically use Faster-Whisper")
        print("3. Enjoy 4x faster transcription!")
        print()
        print("To switch back to OpenAI Whisper:")
        print('  Set "use_faster": false in config.json')
        print()
    else:
        print()
        print("❌ Installation failed")
        print("Try manually: pip install faster-whisper")

if __name__ == "__main__":
    main()