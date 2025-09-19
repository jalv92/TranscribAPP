#!/usr/bin/env python
"""
Test script to verify WhatsApp text injection fix
Run this while WhatsApp Desktop is open with a chat selected
"""

import sys
import os
# Add parent directory to path to import src modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.text_injector import TextInjector
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_whatsapp_injection():
    """Test text injection to WhatsApp"""
    injector = TextInjector()

    print("\n=== WhatsApp Text Injection Test ===")
    print("1. Open WhatsApp Desktop")
    print("2. Click on any chat")
    print("3. Click in the message input field")
    print("4. Press Enter to start test...")
    input()

    # Check if WhatsApp is active
    hwnd, window_title = injector.get_active_window()
    active_app = injector.get_active_application()

    print(f"\nActive Window: {window_title}")
    print(f"Detected App: {active_app}")

    if active_app != 'whatsapp':
        print("\n⚠️  WhatsApp is not the active window!")
        print("Please click on WhatsApp and try again.")
        return

    # Test messages
    test_messages = [
        "Test 1: Short message",
        "Test 2: This is a longer message to check if duplication happens with multiple words",
        "Test 3: ¿Hola cómo estás? Testing special characters",
    ]

    for i, message in enumerate(test_messages, 1):
        print(f"\n--- Test {i}/3 ---")
        print(f"Injecting: {message}")

        # Inject text
        success = injector.inject_text(message, method='auto')

        if success:
            print("✅ Injection successful")
            print("Check WhatsApp - is the text correct and NOT duplicated?")
        else:
            print("❌ Injection failed")

        if i < len(test_messages):
            print("\nPress Enter to send and continue to next test...")
            input()
            # Send the message (Enter key)
            injector._send_key(0x0D)  # VK_RETURN
            time.sleep(1)

    print("\n=== Test Complete ===")
    print("If text appeared correctly without duplication, the fix is working!")
    print("\nKnown issues and solutions:")
    print("- If still duplicating: Try increasing delays in _inject_whatsapp_safe()")
    print("- If not appearing: Check if WhatsApp has focus")
    print("- If partial text: WhatsApp may be processing too slowly")

def test_injection_methods():
    """Compare different injection methods"""
    injector = TextInjector()

    print("\n=== Injection Method Comparison ===")
    print("Testing different methods with Notepad...")
    print("Open Notepad and press Enter...")
    input()

    test_text = "Hello World Test"

    methods = ['clipboard', 'paste', 'sendkeys']

    for method in methods:
        print(f"\nTesting method: {method}")
        print(f"Injecting: '{test_text}'")

        success = injector.inject_text(test_text + f" ({method})", method=method)

        if success:
            print(f"✅ {method} successful")
        else:
            print(f"❌ {method} failed")

        time.sleep(2)
        # Add newline for next test
        injector._send_key(0x0D)  # VK_RETURN

if __name__ == "__main__":
    print("TranscribeAPP - WhatsApp Fix Test")
    print("=" * 40)

    while True:
        print("\nSelect test:")
        print("1. Test WhatsApp injection")
        print("2. Compare injection methods")
        print("3. Exit")

        choice = input("\nChoice (1-3): ").strip()

        if choice == '1':
            test_whatsapp_injection()
        elif choice == '2':
            test_injection_methods()
        elif choice == '3':
            print("Goodbye!")
            break
        else:
            print("Invalid choice!")