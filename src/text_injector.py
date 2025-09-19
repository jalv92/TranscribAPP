import win32api
import win32gui
import win32con
import win32clipboard
import win32process
import pyperclip
import time
import logging
from typing import Optional, List, Tuple
import ctypes
from ctypes import wintypes
import threading

logger = logging.getLogger(__name__)


class TextInjector:
    def __init__(self):
        self.supported_apps = {
            'discord': ['Discord', 'discord.exe'],
            'teams': ['Microsoft Teams', 'Teams.exe'],
            'whatsapp': ['WhatsApp', 'WhatsApp.exe', 'WhatsAppDesktop.exe'],
            'telegram': ['Telegram', 'Telegram.exe'],
            'slack': ['Slack', 'slack.exe'],
            'chrome': ['Google Chrome', 'chrome.exe'],
            'edge': ['Microsoft Edge', 'msedge.exe'],
            'firefox': ['Mozilla Firefox', 'firefox.exe'],
            'notepad': ['Notepad', 'notepad.exe'],
            'word': ['Microsoft Word', 'WINWORD.EXE']
        }

        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32

        logger.info("TextInjector initialized")

    def get_active_window(self) -> Tuple[Optional[int], Optional[str]]:
        try:
            hwnd = win32gui.GetForegroundWindow()
            if hwnd:
                window_title = win32gui.GetWindowText(hwnd)
                return hwnd, window_title
            return None, None
        except Exception as e:
            logger.error(f"Failed to get active window: {e}")
            return None, None

    def get_active_application(self) -> Optional[str]:
        try:
            hwnd, window_title = self.get_active_window()
            if not hwnd:
                return None

            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            handle = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ, 0, pid)

            if handle:
                exe_name = win32process.GetModuleFileNameEx(handle, 0)
                win32api.CloseHandle(handle)
                app_name = exe_name.split('\\')[-1].lower()

                for app_key, app_identifiers in self.supported_apps.items():
                    if any(identifier.lower() in app_name or identifier.lower() in window_title.lower()
                          for identifier in app_identifiers):
                        logger.info(f"Detected application: {app_key}")
                        return app_key

            return 'unknown'

        except Exception as e:
            logger.error(f"Failed to get active application: {e}")
            return None

    def inject_text(self, text: str, method: str = 'auto') -> bool:
        if not text:
            logger.warning("Empty text, nothing to inject")
            return False

        try:
            active_app = self.get_active_application()
            logger.info(f"Injecting text to {active_app} using method: {method}")

            if method == 'auto':
                if active_app in ['chrome', 'edge', 'firefox']:
                    return self._inject_via_clipboard_paste(text)
                elif active_app == 'whatsapp':
                    # Special handling for WhatsApp to avoid duplication
                    return self._inject_whatsapp_safe(text)
                elif active_app in ['discord', 'teams', 'slack']:
                    return self._inject_via_clipboard_paste(text)
                else:
                    return self._inject_via_sendkeys(text)

            elif method == 'clipboard':
                return self._inject_via_clipboard(text)

            elif method == 'paste':
                return self._inject_via_clipboard_paste(text)

            elif method == 'sendkeys':
                return self._inject_via_sendkeys(text)

            else:
                logger.warning(f"Unknown injection method: {method}")
                return False

        except Exception as e:
            logger.error(f"Text injection failed: {e}")
            return False

    def _inject_via_clipboard(self, text: str) -> bool:
        try:
            pyperclip.copy(text)
            logger.info(f"Text copied to clipboard: {text[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Clipboard injection failed: {e}")
            return False

    def _inject_via_clipboard_paste(self, text: str) -> bool:
        try:
            original_clipboard = pyperclip.paste()

            pyperclip.copy(text)
            time.sleep(0.1)

            self._send_key_combination(win32con.VK_CONTROL, ord('V'))
            time.sleep(0.2)

            if original_clipboard:
                threading.Timer(1.0, lambda: pyperclip.copy(original_clipboard)).start()

            logger.info("Text injected via clipboard paste")
            return True

        except Exception as e:
            logger.error(f"Clipboard paste injection failed: {e}")
            return False

    def _inject_whatsapp_safe(self, text: str) -> bool:
        """Special injection method for WhatsApp to prevent duplication"""
        try:
            # Store original clipboard
            original_clipboard = pyperclip.paste()

            # Clear any existing text selection first
            self._send_key_combination(win32con.VK_CONTROL, ord('A'))
            time.sleep(0.1)

            # Copy text to clipboard
            pyperclip.copy(text)
            time.sleep(0.15)  # Slightly longer wait for WhatsApp

            # Paste using Ctrl+V
            self._send_key_combination(win32con.VK_CONTROL, ord('V'))
            time.sleep(0.3)  # Wait for paste to complete

            # Restore original clipboard after a delay
            if original_clipboard:
                threading.Timer(2.0, lambda: pyperclip.copy(original_clipboard)).start()

            logger.info("Text injected to WhatsApp safely")
            return True

        except Exception as e:
            logger.error(f"WhatsApp injection failed: {e}")
            return False

    def _inject_via_sendkeys(self, text: str) -> bool:
        try:
            hwnd, _ = self.get_active_window()
            if not hwnd:
                logger.warning("No active window found")
                return False

            # Add a small delay before typing to ensure the window is ready
            time.sleep(0.1)

            for char in text:
                if char == '\n':
                    self._send_key(win32con.VK_RETURN)
                elif char == '\t':
                    self._send_key(win32con.VK_TAB)
                else:
                    self._send_char(char)
                time.sleep(0.005)  # Reduced delay between chars

            logger.info("Text injected via sendkeys")
            return True

        except Exception as e:
            logger.error(f"Sendkeys injection failed: {e}")
            return False

    def _send_key(self, key_code: int):
        self.user32.keybd_event(key_code, 0, 0, 0)
        time.sleep(0.01)
        self.user32.keybd_event(key_code, 0, win32con.KEYEVENTF_KEYUP, 0)

    def _send_char(self, char: str):
        vk = win32api.VkKeyScan(char)
        if vk == -1:
            return

        shift_state = (vk >> 8) & 1

        if shift_state:
            self.user32.keybd_event(win32con.VK_SHIFT, 0, 0, 0)

        self.user32.keybd_event(vk & 0xFF, 0, 0, 0)
        time.sleep(0.01)
        self.user32.keybd_event(vk & 0xFF, 0, win32con.KEYEVENTF_KEYUP, 0)

        if shift_state:
            self.user32.keybd_event(win32con.VK_SHIFT, 0, win32con.KEYEVENTF_KEYUP, 0)

    def _send_key_combination(self, modifier: int, key: int):
        """Send key combination with proper timing"""
        # Press modifier
        self.user32.keybd_event(modifier, 0, 0, 0)
        time.sleep(0.05)

        # Press key
        self.user32.keybd_event(key, 0, 0, 0)
        time.sleep(0.05)

        # Release key first
        self.user32.keybd_event(key, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(0.05)

        # Release modifier
        self.user32.keybd_event(modifier, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(0.05)  # Extra delay after release

    def is_text_field_active(self) -> bool:
        try:
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return False

            class_name = win32gui.GetClassName(hwnd)

            text_field_classes = ['Edit', 'RichEdit', 'Scintilla', 'TMemo', 'TEdit']

            focused_control = win32gui.GetFocus()
            if focused_control:
                control_class = win32gui.GetClassName(focused_control)
                if any(tc in control_class for tc in text_field_classes):
                    return True

            return False

        except Exception as e:
            logger.debug(f"Failed to check if text field is active: {e}")
            return False


class SafeTextInjector(TextInjector):
    def __init__(self):
        super().__init__()
        self.injection_history = []
        self.max_history = 10

    def inject_text_safe(self, text: str, confirm: bool = False) -> bool:
        if len(text) > 5000:
            logger.warning("Text too long for safe injection")
            return self._inject_via_clipboard(text)

        if confirm:
            logger.info("Confirmation required before injection")

        result = self.inject_text(text)

        if result:
            self.injection_history.append({
                'timestamp': time.time(),
                'text': text[:100],
                'success': True
            })

            if len(self.injection_history) > self.max_history:
                self.injection_history.pop(0)

        return result

    def get_injection_history(self) -> List[dict]:
        return self.injection_history.copy()