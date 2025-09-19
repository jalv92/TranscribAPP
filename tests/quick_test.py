#!/usr/bin/env python
"""Quick test for technical terms corrections"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.technical_terms import TechnicalTermsProcessor, process_technical_terms

processor = TechnicalTermsProcessor()

# Test the failing cases
test_cases = [
    ("archivo packash.yasón", "archivo package.json"),
    ("archivo requaierments.txt", "archivo requirements.txt"),
    ("vamos a crear un nuevo bransh en git jab", "vamos a crear un nuevo branch en GitHub"),
    ("el archivo packash.yasón tiene un error", "el archivo package.json tiene un error"),
    ("ejecuta pib instal requaierments.txt", "ejecuta pip install requirements.txt"),
]

print("Testing Technical Terms Corrections:")
print("-" * 50)

all_passed = True
for input_text, expected in test_cases:
    result = processor.process_text(input_text)
    passed = result == expected

    print(f"\nInput:    '{input_text}'")
    print(f"Expected: '{expected}'")
    print(f"Result:   '{result}'")
    print(f"Status:   {'✅ PASSED' if passed else '❌ FAILED'}")

    if not passed:
        all_passed = False

print("\n" + "=" * 50)
if all_passed:
    print("✅ All tests passed!")
else:
    print("❌ Some tests failed - need more fixes")