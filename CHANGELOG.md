# Changelog

All notable changes to TranscribeAPP will be documented in this file.

## [2.0.0] - 2025-09-19

### 🚀 Major Performance Improvements

#### Faster-Whisper Integration
- **14x faster transcription** - From 37 seconds to 2.7 seconds
- **50% less VRAM usage** - More efficient memory management
- **Voice Activity Detection (VAD)** - Automatically removes silence
- **Real-time factor: 0.11x** - Processes 25s audio in just 2.7s

### ✨ New Features

#### Multi-Model Support
- **Model Selector UI** - Choose between different LLM models in Settings
- **Automatic Model Detection** - Scans LLM folder for available models
- **Supported Models**:
  - Qwen 2.5 3B (Best overall)
  - Llama 3.2 3B (Best English fluency)
  - Llama 3.2 1B (Lightweight, 2GB)
  - Phi 3.5 Mini (Microsoft)
  - Gemma 2 2B (Google)

#### AI Enhancement Toggle
- **Enable/Disable AI** - Toggle LLM enhancement via Settings UI
- **Memory Savings** - Save 6GB RAM when AI is disabled
- **Fallback System** - Automatic fallback to simple text processor
- **System Tray Indicator** - Shows AI status (ON/OFF)

### 🔧 Technical Improvements

#### Architecture
- Universal LLM Processor for multi-model support
- Dynamic model loading and switching
- Improved error handling and fallbacks
- Better memory management with cleanup

#### Configuration
- New `whisper.use_faster` flag for Faster-Whisper
- New `whisper.vad_filter` for Voice Activity Detection
- New `llm.model_path` for model selection
- New `llm.model_id` for model identification

### 📊 Performance Metrics

| Component | Before | After | Improvement |
|-----------|--------|-------|-------------|
| Whisper Load | 5s | 1.5s | 3x faster |
| Transcription | 37s | 2.7s | **14x faster** |
| Total Processing | 40s | 15s | 62% faster |
| Memory Usage | 2GB | 1GB | 50% less |

### 🐛 Bug Fixes
- Fixed import order in model_manager.py
- Fixed VAD parameters compatibility
- Fixed model switching memory leaks
- Fixed LLM output validation

### 📝 Documentation
- Updated README with new features
- Added performance metrics
- Created installation guides for models
- Added troubleshooting for Faster-Whisper

## [1.0.0] - 2025-09-18

### Initial Release
- Spanish to English voice transcription and translation
- OpenAI Whisper integration
- Qwen 2.5 3B LLM for text enhancement
- System tray application
- Hotkey support (Ctrl+Shift+R)
- Auto-typing into active window
- Technical terms correction
- Offline operation after setup