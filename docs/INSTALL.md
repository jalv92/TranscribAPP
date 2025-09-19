# 📦 TranscribeAPP - Detailed Installation Guide

This guide will help you install TranscribeAPP step by step, including all dependencies and models.

## 📋 Prerequisites Checklist

Before starting, make sure you have:
- ✅ Windows 10 or 11 (64-bit)
- ✅ At least 15GB free disk space
- ✅ Internet connection for downloading models
- ✅ Microphone connected and working

## 🐍 Step 1: Install Python

### Option A: Download from Python.org
1. Go to https://www.python.org/downloads/
2. Download Python 3.10 or 3.11 (NOT 3.12 - some packages aren't compatible yet)
3. Run installer and **CHECK "Add Python to PATH"**
4. Verify installation:
```bash
python --version
# Should show: Python 3.10.x or 3.11.x
```

### Option B: Using Microsoft Store
1. Open Microsoft Store
2. Search "Python 3.11"
3. Install Python 3.11 from Python Software Foundation
4. Verify in Command Prompt

## 📥 Step 2: Download TranscribeAPP

### Option A: Using Git
```bash
git clone https://github.com/yourusername/TranscribeAPP.git
cd TranscribeAPP
```

### Option B: Download ZIP
1. Go to the GitHub repository
2. Click green "Code" button → Download ZIP
3. Extract to a folder like `C:\TranscribeAPP`
4. Open Command Prompt in that folder

## 📚 Step 3: Install Python Dependencies

Open Command Prompt in the TranscribeAPP folder and run:

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate

# Install all required packages
pip install -r requirements.txt
```

### If you get errors:
```bash
# Update pip first
python -m pip install --upgrade pip

# Try installing one by one if needed
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install openai-whisper
pip install transformers
pip install accelerate
pip install bitsandbytes
pip install sounddevice
pip install PyQt5
```

## 🤖 Step 4: Download Qwen2.5-3B Model (REQUIRED)

The AI model is 6GB and must be downloaded separately.

### Option A: Manual Download (Easiest)
1. Go to: https://huggingface.co/Qwen/Qwen2.5-3B-Instruct
2. Click "Files and versions" tab
3. Download these files one by one:
   - `config.json` (small)
   - `generation_config.json` (small)
   - `merges.txt` (2MB)
   - `model.safetensors.index.json` (small)
   - `model-00001-of-00002.safetensors` (5GB)
   - `model-00002-of-00002.safetensors` (1GB)
   - `tokenizer.json` (7MB)
   - `tokenizer_config.json` (small)
   - `vocab.json` (2MB)

4. Create folder: `TranscribeAPP\LLM\Qwen2.5-3B-Instruct\`
5. Put all downloaded files in this folder

### Option B: Using Git LFS (Advanced)
```bash
# Install git-lfs first
git lfs install

# Navigate to LLM folder
cd TranscribeAPP\LLM

# Clone the model (6GB download)
git clone https://huggingface.co/Qwen/Qwen2.5-3B-Instruct
```

### Option C: Using Python
```python
# Run this Python script
from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="Qwen/Qwen2.5-3B-Instruct",
    local_dir="LLM/Qwen2.5-3B-Instruct",
    local_dir_use_symlinks=False
)
```

## 🎬 Step 5: Download FFmpeg

FFmpeg is needed for audio processing.

1. Go to: https://www.gyan.dev/ffmpeg/builds/
2. Download: `ffmpeg-git-essentials.7z` (about 80MB)
3. You'll need 7-Zip to extract (download from https://www.7-zip.org/)
4. Extract the contents
5. You'll get a folder like `ffmpeg-2025-09-18-git-xxxxx-essentials_build`
6. Create folder: `TranscribeAPP\tools\ffmpeg\`
7. Move the extracted folder into `tools\ffmpeg\`

Final path should look like:
```
TranscribeAPP\
  tools\
    ffmpeg\
      ffmpeg-2025-09-18-git-xxxxx-essentials_build\
        bin\
          ffmpeg.exe
```

## 🔧 Step 6: Configure Audio Input

1. Right-click the speaker icon in Windows system tray
2. Select "Sound settings"
3. Under "Input", select your microphone
4. Click on it and test that the level bar moves when you speak
5. Note the device name - you may need it later

## ✅ Step 7: Verify Installation

Create a test script `test_install.py`:

```python
print("Testing installations...")

# Test Python packages
try:
    import torch
    print("✓ PyTorch installed")
except:
    print("✗ PyTorch missing")

try:
    import whisper
    print("✓ Whisper installed")
except:
    print("✗ Whisper missing")

try:
    import transformers
    print("✓ Transformers installed")
except:
    print("✗ Transformers missing")

# Test model files
import os
if os.path.exists("LLM/Qwen2.5-3B-Instruct/config.json"):
    print("✓ Qwen model found")
else:
    print("✗ Qwen model not found - check LLM folder")

if os.path.exists("tools/ffmpeg"):
    print("✓ FFmpeg folder found")
else:
    print("✗ FFmpeg not found - check tools folder")

print("\nIf all show ✓, you're ready to go!")
```

Run it:
```bash
python test_install.py
```

## 🚀 Step 8: First Run

```bash
python main.py
```

### What happens on first run:
1. **Splash screen** appears showing loading progress
2. **Whisper model downloads** (~500MB) - happens only once
3. **Translation model downloads** (~300MB) - happens only once
4. **Models load into memory** - takes 30-60 seconds
5. **System tray icon appears** - look for the microphone icon
6. App is ready when tray icon shows green

### If the app doesn't start:
- Check `data/transcribe_app.log` for errors
- Make sure all models are downloaded
- Try running as Administrator
- Check Windows Defender isn't blocking it

## 🎯 Step 9: Test the App

1. Open Notepad
2. Press `Ctrl+Shift+R` to start recording
3. Say in Spanish: "Hola, esto es una prueba"
4. Press `Ctrl+Shift+R` again to stop
5. Wait 2-3 seconds
6. You should see: "Hello, this is a test" typed in Notepad

## 🔧 Optional: GPU Acceleration

If you have an NVIDIA GPU:

1. Check your GPU:
```bash
nvidia-smi
```

2. Install CUDA version of PyTorch:
```bash
pip uninstall torch torchvision torchaudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

3. Edit `config.json`:
```json
{
    "whisper": {
        "device": "cuda"  // Change from "cpu" to "cuda"
    }
}
```

## ❓ Common Installation Issues

### "pip is not recognized"
- Python wasn't added to PATH during installation
- Reinstall Python and check "Add to PATH"

### "No module named torch"
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### "Qwen model not found"
- Check folder structure: `LLM\Qwen2.5-3B-Instruct\`
- Ensure ALL files are downloaded (9 files total)

### "FFmpeg not found"
- Check path: `tools\ffmpeg\ffmpeg-xxx\bin\ffmpeg.exe`
- The exe must be in a `bin` subfolder

### Out of memory errors
- Close other applications
- Use smaller Whisper model in config.json ("tiny" or "base")
- Disable Qwen in config.json: `"llm": {"enabled": false}`

## 📞 Getting Help

If you're still stuck:
1. Check `data\transcribe_app.log` for specific errors
2. Open an issue on GitHub with the error message
3. Include your system specs (RAM, GPU, Windows version)

---

**Once everything is installed, the app works 100% offline!**