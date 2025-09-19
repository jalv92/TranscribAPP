#!/usr/bin/env python
"""
Test script to verify technical terms correction
Tests common programming terms misheard in Spanish context
"""

import sys
import os
# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.technical_terms import TechnicalTermsProcessor, process_technical_terms
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_basic_corrections():
    """Test basic technical term corrections"""
    print("\n" + "="*60)
    print("Testing Basic Technical Term Corrections")
    print("="*60)

    processor = TechnicalTermsProcessor()

    test_cases = [
        # (input, expected output, description)
        ("actualizar el trinme", "actualizar el README", "README file correction"),
        ("hacer un comit", "hacer un commit", "git commit correction"),
        ("subir a git jab", "subir a GitHub", "GitHub correction"),
        ("enpiem instal", "npm install", "npm install command"),
        ("archivo packash.yasón", "archivo package.json", "package.json file"),
        ("usar faison", "usar Python", "Python language"),
        ("base de dita", "base de data", "database correction"),
        ("instalar douker", "instalar Docker", "Docker correction"),
        ("código en riact", "código en React", "React framework"),
        ("archivo requaierments.txt", "archivo requirements.txt", "requirements file"),
    ]

    print("\nBasic corrections:")
    print("-" * 40)

    all_passed = True
    for input_text, expected, description in test_cases:
        result = processor.process_text(input_text)

        passed = result == expected
        status = "✅" if passed else "❌"

        print(f"\n{description}:")
        print(f"  Input:    '{input_text}'")
        print(f"  Expected: '{expected}'")
        print(f"  Result:   '{result}' {status}")

        if not passed:
            all_passed = False

    return all_passed


def test_contextual_corrections():
    """Test corrections in context"""
    print("\n" + "="*60)
    print("Testing Contextual Corrections")
    print("="*60)

    test_cases = [
        (
            "necesito actualizar el trinme y hacer un comit",
            "necesito actualizar el README y hacer un commit",
            "Multiple corrections in sentence"
        ),
        (
            "voy a hacer enpiem instal y luego subir a git jab",
            "voy a hacer npm install y luego subir a GitHub",
            "Command sequence"
        ),
        (
            "el archivo packash.yasón tiene un error",
            "el archivo package.json tiene un error",
            "File name with extension"
        ),
        (
            "estamos usando faison con diango",
            "estamos usando Python con Django",
            "Frameworks and languages"
        ),
    ]

    print("\nContextual corrections:")
    print("-" * 40)

    all_passed = True
    for input_text, expected, description in test_cases:
        result = process_technical_terms(input_text)

        passed = result == expected
        status = "✅" if passed else "❌"

        print(f"\n{description}:")
        print(f"  Input:    '{input_text}'")
        print(f"  Expected: '{expected}'")
        print(f"  Result:   '{result}' {status}")

        if not passed:
            all_passed = False

    return all_passed


def test_real_world_examples():
    """Test with real transcription examples"""
    print("\n" + "="*60)
    print("Testing Real-World Transcription Examples")
    print("="*60)

    examples = [
        (
            "lo único que queda es actualizar el trinme",
            "lo único que queda es actualizar el README",
            "Your actual example"
        ),
        (
            "vamos a crear un nuevo bransh en git jab",
            "vamos a crear un nuevo branch en GitHub",
            "Git workflow"
        ),
        (
            "el problema está en el archivo config.yasón",
            "el problema está en el archivo config.json",
            "Configuration file"
        ),
        (
            "ejecuta pib instal requaierments.txt",
            "ejecuta pip install requirements.txt",
            "Python dependency installation"
        ),
        (
            "necesitamos configurar douker para el sérver",
            "necesitamos configurar Docker para el server",
            "Docker setup"
        ),
    ]

    print("\nReal-world examples:")
    print("-" * 40)

    all_passed = True
    for input_text, expected, description in examples:
        result = process_technical_terms(input_text)

        passed = result == expected
        status = "✅" if passed else "❌"

        print(f"\n{description}:")
        print(f"  Input:    '{input_text}'")
        print(f"  Expected: '{expected}'")
        print(f"  Result:   '{result}' {status}")

        if not passed:
            all_passed = False

    return all_passed


def test_code_context_detection():
    """Test detection of code/technical context"""
    print("\n" + "="*60)
    print("Testing Code Context Detection")
    print("="*60)

    processor = TechnicalTermsProcessor()

    test_cases = [
        ("vamos a escribir código", True, "Spanish code mention"),
        ("necesito debuggear este error", True, "Debug mention"),
        ("el archivo no funciona", True, "File mention"),
        ("hola como estas", False, "Regular conversation"),
        ("vamos a comer pizza", False, "Non-technical"),
        ("hay un bug en la función", True, "Bug mention"),
        ("ejecutar el comando", True, "Command mention"),
    ]

    print("\nCode context detection:")
    print("-" * 40)

    all_passed = True
    for text, expected, description in test_cases:
        result = processor.detect_code_context(text)

        passed = result == expected
        status = "✅" if passed else "❌"

        print(f"\n{description}:")
        print(f"  Text:     '{text}'")
        print(f"  Expected: {expected}")
        print(f"  Result:   {result} {status}")

        if not passed:
            all_passed = False

    return all_passed


def main():
    """Main test runner"""
    print("\n" + "="*70)
    print("      TranscribeAPP - Technical Terms Correction Test")
    print("="*70)

    results = []

    # Run tests
    print("\n[1/4] Testing basic corrections...")
    results.append(("Basic Corrections", test_basic_corrections()))

    print("\n[2/4] Testing contextual corrections...")
    results.append(("Contextual Corrections", test_contextual_corrections()))

    print("\n[3/4] Testing real-world examples...")
    results.append(("Real-World Examples", test_real_world_examples()))

    print("\n[4/4] Testing code context detection...")
    results.append(("Code Context Detection", test_code_context_detection()))

    # Summary
    print("\n" + "="*70)
    print("                        TEST SUMMARY")
    print("="*70)

    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:25} {status}")

    all_passed = all(passed for _, passed in results)

    if all_passed:
        print("\n🎉 All tests passed! Technical terms correction is working.")
        print("\nThis feature will help when you say technical terms like:")
        print("  • 'README' (often heard as 'trinme' or 'trime')")
        print("  • 'GitHub' (often heard as 'git jab')")
        print("  • 'npm install' (often heard as 'enpiem instal')")
        print("  • 'package.json' (often heard as 'packash.yasón')")
    else:
        print("\n⚠️  Some tests failed. Please check the output above.")

    print("\n" + "="*70)


if __name__ == "__main__":
    main()