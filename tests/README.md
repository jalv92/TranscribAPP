# 🧪 TranscribeAPP Test Suite

This folder contains all test scripts for the TranscribeAPP project.

## Available Tests

### 1. `test_qwen_fix.py` - Qwen LLM Validation
Tests the Qwen2.5-3B model integration to ensure:
- Spanish text cleaning works without role markers
- Translation enhancement produces natural English
- No text duplication in the pipeline
- Proper handling of filler words (este, eh, mmm)

**Run:**
```bash
cd ..
python tests/test_qwen_fix.py
```

### 2. `test_whatsapp_fix.py` - WhatsApp Injection Test
Tests text injection specifically for WhatsApp Desktop to verify:
- No text duplication when typing
- Proper clipboard handling
- Correct timing between keystrokes

**Run:**
```bash
cd ..
python tests/test_whatsapp_fix.py
```

## Running Tests

All test scripts should be run from the **project root directory**:

```bash
# From TranscribeAPP folder
python tests/test_qwen_fix.py
python tests/test_whatsapp_fix.py
```

## Test Requirements

- Python 3.10 or 3.11
- All project dependencies installed (`pip install -r requirements.txt`)
- Qwen2.5-3B model downloaded to `LLM/Qwen2.5-3B-Instruct/`
- For WhatsApp test: WhatsApp Desktop installed and logged in

## Adding New Tests

When creating new test files:
1. Place them in this `tests/` folder
2. Add the parent directory to path:
```python
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```
3. Import modules from `src.` namespace
4. Update this README with test description

## Continuous Testing

Before committing changes, run:
```bash
python tests/test_qwen_fix.py
```

This ensures the core functionality remains intact.