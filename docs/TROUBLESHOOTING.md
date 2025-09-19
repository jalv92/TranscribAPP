# 🔧 TranscribeAPP - Troubleshooting Guide

## 🚨 Most Common Issues & Quick Fixes

### 1. ❌ App Won't Start

**Symptoms:**
- Nothing happens when running `python main.py`
- Window closes immediately
- Error messages flash and disappear

**Solutions:**
```bash
# Check Python version (needs 3.10 or 3.11)
python --version

# Check error log
type data\transcribe_app.log

# Run with detailed output
python -u main.py
```

### 2. 🎤 No Audio Captured / Recording Issues

**Problem:** "No audio captured" or recordings are silent

**Fix Audio Input:**
1. Check Windows Settings → System → Sound → Input
2. Select correct microphone
3. Test microphone (speak and watch level bar)
4. Grant microphone permission to Python

**Adjust Sensitivity:**
Edit `config.json`:
```json
{
    "audio": {
        "silence_threshold": 0.01,    // Lower = more sensitive
        "silence_duration": 5.0        // Wait longer before auto-stop
    }
}
```

### 3. 🤖 "Model Not Found" Errors

**Error:** `FileNotFoundError: LLM/Qwen2.5-3B-Instruct/config.json`

**Solution:**
1. Check folder structure:
```
TranscribeAPP\
  LLM\
    Qwen2.5-3B-Instruct\
      config.json          ← Must have this
      model-00001-of-00002.safetensors
      model-00002-of-00002.safetensors
      tokenizer.json
      ... (9 files total)
```

2. Download missing files from:
   https://huggingface.co/Qwen/Qwen2.5-3B-Instruct/tree/main

### 4. 🎬 FFmpeg Not Found

**Error:** `FFmpeg not found. Using soundfile as fallback...`

**Fix:**
1. Download: https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-essentials.7z
2. Extract with 7-Zip
3. Place in: `tools\ffmpeg\[extracted-folder]\bin\ffmpeg.exe`

**Verify:**
```bash
tools\ffmpeg\ffmpeg-2025-09-18-git-c373636f55-essentials_build\bin\ffmpeg.exe -version
```

### 5. 💾 Out of Memory Errors

**Error:** `RuntimeError: CUDA out of memory` or app crashes

**Solutions:**

**Option A: Use smaller models**
Edit `config.json`:
```json
{
    "whisper": {
        "model_size": "tiny"    // Change from "small" to "tiny"
    },
    "llm": {
        "enabled": false        // Disable Qwen if needed
    }
}
```

**Option B: Force CPU mode** (slower but works)
```json
{
    "whisper": {
        "device": "cpu"
    },
    "translation": {
        "device": "cpu"
    }
}
```

### 6. ⌨️ Text Not Appearing in Target App

**Problem:** Translation completes but text doesn't appear

**Try these:**
1. **Test with Notepad first** - some apps block automation
2. **Run as Administrator** - right-click main.py → Run as admin
3. **Check app focus** - target app must be active window
4. **Alternative method** - text is also copied to clipboard

**Apps that may block typing:**
- Some games with anti-cheat
- Banking applications
- Secure browsers in private mode

### 7. 🔥 Long Audio Gets Cut Off

**Problem:** Recordings longer than 30 seconds are truncated

**Fixed in latest version!** Update your code or adjust:
```json
{
    "audio": {
        "buffer_duration": 300,          // 5 minutes max
        "max_recording_duration": 300
    }
}
```

### 8. 🌐 Translation Quality Issues

**Problem:** Translations are literal, awkward, or contain duplicated text

**Solutions:**
1. **Enable Qwen enhancement** (now fixed for duplications):
```json
{
    "llm": {
        "enabled": true,
        "enhance_translation": true,  // Re-enabled after fixes
        "temperature": 0.1    // Low = more consistent
    }
}
```

2. **If you see "assistant" in output or duplicated text:**
   - The latest version includes fixes for this
   - Run `python test_qwen_fix.py` to verify fixes are working
   - The system now filters out role markers and validates output

3. **Speak more clearly** with pauses between sentences
4. **Reduce background noise**

**Recent Fixes (Sept 2025):**
- ✅ Fixed Qwen outputting "assistant" role markers
- ✅ Fixed text duplication in translations
- ✅ Improved prompt engineering for better Spanish cleaning
- ✅ Added validation to reject malformed LLM outputs
- ✅ WhatsApp-specific injection method to prevent duplicates
- ✅ Technical terms auto-correction (README, GitHub, npm, etc.)

## 🛠️ Advanced Debugging

### Enable Debug Logging

Edit `main.py` line ~38:
```python
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO to DEBUG
    ...
)
```

### Test Components Individually

Create `test_components.py`:
```python
# Test audio
from src.audio_handler import AudioRecorder
recorder = AudioRecorder({'audio': {...}})
devices = recorder.get_audio_devices()
print(f"Audio devices: {devices}")

# Test models
import whisper
model = whisper.load_model("tiny")
print("Whisper works!")

# Test Qwen
import os
if os.path.exists("LLM/Qwen2.5-3B-Instruct"):
    print("Qwen model found!")
```

### Check GPU/CUDA

```python
import torch
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA version: {torch.version.cuda}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
```

## 📊 Performance Optimization

### For Faster Processing:
- Use `"whisper": {"model_size": "tiny"}` (5x faster, slightly less accurate)
- Enable GPU: `"device": "cuda"` (requires NVIDIA GPU)
- Disable Qwen: `"llm": {"enabled": false}` (instant but basic translation)

### For Better Quality:
- Use `"whisper": {"model_size": "medium"}` (slower but more accurate)
- Enable Qwen: `"llm": {"enabled": true}`
- Increase `"temperature": 0.5` for more natural translations

### 9. 💻 Technical Terms Getting Misheard

**Problem:** Programming terms like "README" become "trinme" or "trime"

**Solution:** The app now includes automatic technical terms correction!

**Common corrections:**
- "trinme/trime" → "README"
- "git jab" → "GitHub"
- "enpiem instal" → "npm install"
- "packash.yasón" → "package.json"
- "faison/paiton" → "Python"
- "comit" → "commit"
- "douker" → "Docker"

**To disable if causing issues:**
```json
{
    "quality": {
        "fix_technical_terms": false
    }
}
```

**To test technical terms:**
```bash
python tests/test_technical_terms.py
```

## 🆘 Getting Help

### Before asking for help, gather:
1. **Error message** from `data\transcribe_app.log`
2. **System info**: Windows version, RAM, GPU
3. **Python version**: `python --version`
4. **Config file**: your `config.json` settings

### Where to get help:
- **GitHub Issues**: Best for bugs and feature requests
- **Logs**: Check `data\transcribe_app.log` first
- **This guide**: 90% of issues are covered here

## ✅ Quick Health Check

Run this to verify everything:
```bash
# In TranscribeAPP folder
python -c "
import os, sys
print('Python:', sys.version)
print('Qwen:', os.path.exists('LLM/Qwen2.5-3B-Instruct'))
print('FFmpeg:', os.path.exists('tools/ffmpeg'))
print('Config:', os.path.exists('config.json'))
try:
    import torch, whisper, transformers
    print('Packages: OK')
except:
    print('Packages: Missing - run: pip install -r requirements.txt')
"
```

## 🎯 Success Checklist

Your installation is working when:
- ✅ System tray icon appears (green microphone)
- ✅ `Ctrl+Shift+R` starts recording (icon turns red)
- ✅ Speaking in Spanish produces English text
- ✅ Text appears in target application
- ✅ No errors in `data\transcribe_app.log`

---

**Still stuck?** Open an issue on GitHub with your error log!