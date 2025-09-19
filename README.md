# TranscribeAPP 🎙️ - Ultra-Fast Spanish Voice Transcription & Translation

An AI-powered Windows desktop application that captures Spanish speech, transcribes it in real-time using **Faster-Whisper** (14x faster!), translates it to English with customizable AI enhancement, and automatically types the translation into any active application.

## 🌟 What Does This App Do?

TranscribeAPP is designed for Spanish speakers who need to communicate in English. Simply press a hotkey, speak in Spanish, and watch as your words are:
1. **Transcribed** from speech to Spanish text
2. **Translated** to English
3. **Enhanced** by AI for natural, fluent English
4. **Typed automatically** into whatever app you're using (Discord, Teams, WhatsApp, etc.)

Perfect for:
- 🎮 Gaming with international teams
- 💼 Business meetings and presentations
- 📚 Language learning and practice
- 💬 Social media and messaging
- 📧 Writing emails in English

## ✨ Key Features

- **⚡ Ultra-Fast**: Transcribes in 2.7 seconds using Faster-Whisper (14x faster than before!)
- **🎤 Voice Activation**: Press `Ctrl+Shift+R` to start/stop recording
- **🤖 Multi-Model Support**: Choose between Qwen, Llama, Phi, Gemma models
- **🎯 AI Toggle**: Enable/disable AI enhancement based on your needs
- **🔧 Technical Terms**: Automatically corrects programming terms (README, GitHub, npm, etc.)
- **💾 Memory Efficient**: 50% less VRAM usage with Faster-Whisper
- **🔒 100% Offline**: After initial setup, works completely offline
- **🖥️ System Tray**: Runs quietly in the background
- **⌨️ Auto-typing**: Automatically types translation into active window
- **🎯 Smart VAD**: Voice Activity Detection skips silence automatically

## 💻 System Requirements

### Minimum:
- Windows 10/11 (64-bit)
- 8GB RAM
- 10GB free disk space
- Any microphone
- Python 3.10+

### Recommended:
- Windows 10/11 (64-bit)
- 16GB RAM
- NVIDIA GPU with 6GB+ VRAM (RTX 3060 or better)
- 15GB free disk space
- Good quality microphone
- CUDA 11.7+ for GPU acceleration

## 🚀 Quick Start Guide

### Step 1: Clone the Repository
```bash
git clone https://github.com/yourusername/TranscribeAPP.git
cd TranscribeAPP
```

### Step 2: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Install Faster-Whisper (for 14x speed boost)
```bash
pip install faster-whisper
# Or use the installer script:
python install_faster_whisper.py
```

### Step 4: Download an LLM Model (Choose One)
Models are automatically detected from the `LLM/` folder:

**Option A: Qwen 2.5 3B (Best overall - 6GB)**
```bash
cd LLM
git lfs install
git clone https://huggingface.co/Qwen/Qwen2.5-3B-Instruct
```

**Option B: Llama 3.2 3B (Best English - 6GB)**
```bash
cd LLM
git clone https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct
```

**Option C: Llama 3.2 1B (Lightweight - 2GB)**
```bash
cd LLM
git clone https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct
```

### Step 5: Download FFmpeg
1. Go to: https://www.gyan.dev/ffmpeg/builds/
2. Download: `ffmpeg-git-essentials.7z`
3. Extract to: `TranscribeAPP/tools/ffmpeg/`

### Step 6: Run the App
```bash
python main.py
```

## 📖 How to Use

1. **Start the App**: Run `python main.py` - it will appear in your system tray
2. **Open any app**: Discord, WhatsApp, Notepad, etc.
3. **Press `Ctrl+Shift+R`**: Start recording (tray icon turns red)
4. **Speak in Spanish**: Talk naturally in Spanish
5. **Press `Ctrl+Shift+R` again**: Stop recording (or wait 3 seconds of silence)
6. **Watch the magic**: Your English translation appears automatically!

### System Tray Menu
- Right-click the tray icon for:
  - ⚙️ Settings - Configure audio, models, hotkeys
  - 📜 History - View past transcriptions
  - ❌ Exit - Close the app

## 📁 Project Structure

```
TranscribeAPP/
├── main.py                      # Start here - main application
├── config.json                  # Settings (edit this to customize)
├── requirements.txt             # Python packages needed
├── src/                         # Source code
│   ├── audio_handler.py        # Records your voice
│   ├── model_manager.py        # Manages AI models
│   ├── text_injector.py        # Types text automatically
│   └── ...                     # Other modules
├── LLM/                         # ⚠️ Download Qwen model here (6GB)
│   └── Qwen2.5-3B-Instruct/    # Model files go here
├── tools/                       # ⚠️ Download FFmpeg here
│   └── ffmpeg/                  # FFmpeg binaries
└── data/                        # App data (logs, history)
```

## ⚙️ Configuration

Edit `config.json` to customize:

```json
{
    "audio": {
        "silence_threshold": 0.02,    // Voice detection sensitivity
        "silence_duration": 3.0,      // Seconds before auto-stop
        "buffer_duration": 120         // Max recording length
    },
    "whisper": {
        "model_size": "small",         // tiny/base/small/medium/large
        "language": "spanish",
        "use_faster": true,            // Enable Faster-Whisper (14x speed)
        "vad_filter": true             // Voice Activity Detection
    },
    "llm": {
        "enabled": true,               // Toggle AI enhancement
        "model_path": "LLM/Llama-3.2-3B-Instruct",  // Select model
        "enhance_translation": true    // Improve translation fluency
    },
    "hotkeys": {
        "record": "ctrl+shift+r",      // Recording hotkey
        "toggle_enabled": "ctrl+shift+t"
    }
}
```

## 🚀 Performance

With the latest optimizations:

| Metric | Time | Improvement |
|--------|------|-------------|
| **Transcription** | 2.7 seconds | 14x faster |
| **Translation** | 2.0 seconds | Same |
| **Total Processing** | ~15 seconds | 62% faster |
| **Memory Usage** | 50% less VRAM | More efficient |

- **Real-time factor**: 0.11x (processes 25s audio in 2.7s)
- **Voice Activity Detection**: Automatically removes silence
- **Multi-model support**: Switch between models via Settings UI

## 🔧 Troubleshooting

### Model Not Loading?
- Ensure Qwen2.5-3B-Instruct is in `LLM/Qwen2.5-3B-Instruct/`
- Check you have all model files (config.json, model.safetensors, etc.)
- Verify 6GB+ free RAM

### No Audio Captured?
- Check Windows microphone permissions
- Verify default recording device in Windows Settings
- Try adjusting `silence_threshold` in config.json

### Text Not Appearing?
- Some apps block automated typing (try Notepad first)
- Make sure the target app has focus
- Check the app is running with proper permissions

### FFmpeg Not Found?
- Download from: https://www.gyan.dev/ffmpeg/builds/
- Extract `ffmpeg-git-essentials.7z`
- Place in `tools/ffmpeg/` folder

See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for more solutions.

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## 📄 License

MIT License - see [LICENSE.txt](LICENSE.txt)

## 🙏 Acknowledgments

- **OpenAI Whisper** - Speech recognition
- **Qwen Team** - Qwen2.5-3B language model
- **Helsinki-NLP** - Translation models
- **FFmpeg** - Audio processing

## ⚠️ Important Notes

1. **First run downloads models** (~500MB for Faster-Whisper) - needs internet
2. **LLM models** (2-6GB) must be downloaded separately from HuggingFace
3. **After setup**, works 100% offline
4. **GPU recommended** but not required (CPU mode available)
5. **Faster-Whisper** provides 14x speed improvement over OpenAI Whisper
6. **Multiple models supported** - Choose based on your needs and system

## 📞 Support

- **Issues**: Open an issue on GitHub
- **Questions**: Check docs/ folder first
- **Updates**: Watch this repo for new features

---

**Made with ❤️ for the Spanish-speaking community**

*Transform your Spanish voice into fluent English text instantly!*# TranscribAPP
