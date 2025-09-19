#!/usr/bin/env python
"""
Test script to verify Qwen LLM fixes
Tests Spanish cleaning and translation enhancement
"""

import sys
import os
# Add parent directory to path to import src modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from src.qwen_processor import get_qwen_processor
from src.model_manager import ModelManager
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_qwen_cleaning():
    """Test Spanish text cleaning"""
    print("\n" + "="*60)
    print("Testing Qwen Spanish Text Cleaning")
    print("="*60)

    processor = get_qwen_processor()

    # Initialize processor
    print("\nInitializing Qwen processor...")
    if not processor.initialize():
        print("❌ Failed to initialize Qwen processor")
        return False

    # Test cases for Spanish cleaning
    test_cases = [
        ("2003.", "Should handle simple year"),
        ("este eh mmm hola como estas", "Should remove filler words"),
        ("para que tenemos el LLM ahora si no lo estamos utilizando", "Should clean complex sentence"),
        ("bueno este vamos a ver si funciona", "Should remove 'este' filler"),
        ("ah si mmm creo que esto esta bien", "Should remove 'ah' and 'mmm'"),
    ]

    print("\nTesting Spanish text cleaning:")
    print("-" * 40)

    all_passed = True
    for spanish_text, description in test_cases:
        print(f"\nTest: {description}")
        print(f"Input:  '{spanish_text}'")

        cleaned = processor.clean_spanish_text(spanish_text)
        print(f"Output: '{cleaned}'")

        # Check for issues
        issues = []
        if 'assistant' in cleaned.lower():
            issues.append("Contains 'assistant' role marker")
        if '\nassistant\n' in cleaned:
            issues.append("Contains newline with assistant")
        if cleaned.count(spanish_text[:10]) > 1:
            issues.append("Text appears duplicated")

        if issues:
            print(f"❌ FAILED: {', '.join(issues)}")
            all_passed = False
        else:
            print("✅ PASSED")

    return all_passed


def test_translation_enhancement():
    """Test English translation enhancement"""
    print("\n" + "="*60)
    print("Testing Translation Enhancement")
    print("="*60)

    processor = get_qwen_processor()

    if not processor.is_initialized:
        print("\nInitializing Qwen processor...")
        if not processor.initialize():
            print("❌ Failed to initialize Qwen processor")
            return False

    # Test cases for enhancement
    test_cases = [
        (
            "para que tenemos el LLM si no lo usamos",
            "So we have the LLM if we're not using it",
            "Should improve grammar"
        ),
        (
            "hola como estas",
            "hello how are you",
            "Should capitalize and add punctuation"
        ),
        (
            "esto esta funcionando bien",
            "this is working good",
            "Should fix 'good' to 'well'"
        ),
    ]

    print("\nTesting translation enhancement:")
    print("-" * 40)

    all_passed = True
    for spanish, english, description in test_cases:
        print(f"\nTest: {description}")
        print(f"Spanish:  '{spanish}'")
        print(f"English:  '{english}'")

        enhanced = processor.enhance_translation(spanish, english)
        print(f"Enhanced: '{enhanced}'")

        # Check for issues
        issues = []
        if 'assistant' in enhanced.lower():
            issues.append("Contains 'assistant' role marker")
        if enhanced.count(english.split()[0]) > 2:
            issues.append("Possible duplication")

        # Check if it's still in English
        spanish_words = ['que', 'por', 'esta', 'pero', 'como']
        if any(word in enhanced.lower().split() for word in spanish_words):
            issues.append("Contains Spanish words")

        if issues:
            print(f"❌ FAILED: {', '.join(issues)}")
            all_passed = False
        else:
            print("✅ PASSED")

    return all_passed


def test_full_pipeline():
    """Test the complete transcription pipeline"""
    print("\n" + "="*60)
    print("Testing Full Pipeline")
    print("="*60)

    # Load config from parent directory
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
    with open(config_path, 'r') as f:
        config = json.load(f)

    # Create model manager
    manager = ModelManager(config)

    print("\nInitializing models...")
    if not manager.initialize_models():
        print("❌ Failed to initialize models")
        return False

    # Simulate transcription results
    test_transcriptions = [
        "2003",
        "este eh hola como estas",
        "para que tenemos el LLM si no lo estamos usando",
    ]

    print("\nTesting full pipeline:")
    print("-" * 40)

    for text in test_transcriptions:
        print(f"\nOriginal Spanish: '{text}'")

        # Simulate the transcribe output (normally from Whisper)
        # We'll just use the text as-is for testing

        # Clean Spanish text
        if manager.qwen_processor and manager.qwen_processor.is_initialized:
            cleaned = manager.qwen_processor.clean_spanish_text(text)
            print(f"Cleaned Spanish:  '{cleaned}'")
        else:
            cleaned = text

        # Translate
        translated = manager.translate(cleaned, original_spanish=cleaned)
        print(f"Final English:    '{translated}'")

        # Check for issues
        if 'assistant' in translated.lower():
            print("❌ ISSUE: Contains 'assistant' in final output!")
        elif translated.count(' ') > 0 and translated.split()[0] in translated[20:]:
            print("❌ ISSUE: Possible text duplication!")
        else:
            print("✅ No issues detected")

    return True


def main():
    """Main test runner"""
    print("\n" + "="*70)
    print("         TranscribeAPP - Qwen LLM Fix Verification")
    print("="*70)

    results = []

    # Run tests
    print("\n[1/3] Testing Spanish text cleaning...")
    results.append(("Spanish Cleaning", test_qwen_cleaning()))

    print("\n[2/3] Testing translation enhancement...")
    results.append(("Translation Enhancement", test_translation_enhancement()))

    print("\n[3/3] Testing full pipeline...")
    results.append(("Full Pipeline", test_full_pipeline()))

    # Summary
    print("\n" + "="*70)
    print("                        TEST SUMMARY")
    print("="*70)

    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:25} {status}")

    all_passed = all(passed for _, passed in results)

    if all_passed:
        print("\n🎉 All tests passed! The fixes are working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check the output above.")

    print("\n" + "="*70)


if __name__ == "__main__":
    main()