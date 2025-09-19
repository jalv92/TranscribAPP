=====================================
TranscribeApp v1.0 - Quick Start Guide
=====================================

WHAT IT DOES:
-------------
TranscribeApp captures your Spanish voice input and automatically
translates it to English text using advanced AI technology.

HOW TO USE:
-----------
1. Launch TranscribeApp from desktop icon
2. Wait for "Ready" in system tray (15 seconds)
3. Press Ctrl+Shift+R to start recording
4. Speak in Spanish
5. Stop speaking (3 seconds silence)
6. English text appears automatically!

REQUIREMENTS:
-------------
• Windows 10/11 64-bit
• NVIDIA GPU (RTX 3060 or better)
• 16GB RAM
• Microphone
• Qwen2.5-3B AI Model (see below)

IMPORTANT - AI MODEL REQUIRED:
-------------------------------
This app needs the Qwen2.5-3B model to work.

To download:
1. Go to: https://huggingface.co/Qwen/Qwen2.5-3B-Instruct
2. Download ALL files (~7GB)
3. Place in: C:\Program Files\TranscribeApp\LLM\Qwen2.5-3B-Instruct\

FIRST RUN:
----------
• Model loading takes ~15 seconds
• System tray icon appears near clock
• Wait for "Ready" status

HOTKEYS:
--------
• Ctrl+Shift+R - Start/Stop recording
• Ctrl+Shift+T - Enable/Disable app
• Right-click tray icon for menu

TROUBLESHOOTING:
----------------
"Model not found":
- Download Qwen2.5-3B model
- Place in LLM\Qwen2.5-3B-Instruct folder

"CUDA error":
- Update NVIDIA drivers
- Install CUDA 11.8+

"Out of memory":
- Close other applications
- Need 6GB+ free GPU memory

FEATURES:
---------
• Real-time Spanish transcription
• AI-enhanced translation
• Automatic text injection
• Handles unclear speech
• Works offline (after model download)

PERFORMANCE:
------------
• Processing: ~3 seconds
• Accuracy: 95%+ for clear speech
• GPU Usage: ~5GB VRAM

For support: Check GitHub repository

=====================================