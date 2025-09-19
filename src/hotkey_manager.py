import keyboard
import win32api
import win32con
import ctypes
from ctypes import wintypes
import threading
import logging
from typing import Callable, Dict, Optional

logger = logging.getLogger(__name__)


class HotkeyManager:
    def __init__(self):
        self.hotkeys = {}
        self.hotkey_callbacks = {}
        self.hotkey_thread = None
        self.running = False
        self.hotkey_id_counter = 1

        self.MOD_ALT = win32con.MOD_ALT
        self.MOD_CONTROL = win32con.MOD_CONTROL
        self.MOD_SHIFT = win32con.MOD_SHIFT
        self.MOD_WIN = win32con.MOD_WIN

        logger.info("HotkeyManager initialized")

    def register_hotkey(self, key_combination: str, callback: Callable, description: str = "") -> bool:
        try:
            hotkey_id = self.hotkey_id_counter
            self.hotkey_id_counter += 1

            modifiers, key = self._parse_key_combination(key_combination)

            self.hotkeys[hotkey_id] = {
                'combination': key_combination,
                'modifiers': modifiers,
                'key': key,
                'callback': callback,
                'description': description
            }

            keyboard.add_hotkey(key_combination, lambda: self._handle_hotkey(hotkey_id))

            logger.info(f"Registered hotkey: {key_combination} (ID: {hotkey_id})")
            return True

        except Exception as e:
            logger.error(f"Failed to register hotkey {key_combination}: {e}")
            return False

    def unregister_hotkey(self, key_combination: str) -> bool:
        try:
            hotkey_id = None
            for hid, info in self.hotkeys.items():
                if info['combination'] == key_combination:
                    hotkey_id = hid
                    break

            if hotkey_id is None:
                logger.warning(f"Hotkey not found: {key_combination}")
                return False

            keyboard.remove_hotkey(key_combination)

            del self.hotkeys[hotkey_id]

            logger.info(f"Unregistered hotkey: {key_combination}")
            return True

        except Exception as e:
            logger.error(f"Failed to unregister hotkey {key_combination}: {e}")
            return False

    def _parse_key_combination(self, combination: str) -> tuple:
        parts = combination.lower().replace(' ', '').split('+')
        modifiers = 0
        key = None

        for part in parts:
            if part in ['ctrl', 'control']:
                modifiers |= self.MOD_CONTROL
            elif part == 'alt':
                modifiers |= self.MOD_ALT
            elif part == 'shift':
                modifiers |= self.MOD_SHIFT
            elif part in ['win', 'windows', 'super']:
                modifiers |= self.MOD_WIN
            else:
                if part.startswith('f') and part[1:].isdigit():
                    key = getattr(win32con, f'VK_F{part[1:]}', None)
                else:
                    key = ord(part.upper()) if len(part) == 1 else None

        return modifiers, key

    def _handle_hotkey(self, hotkey_id: int):
        if hotkey_id in self.hotkeys:
            callback = self.hotkeys[hotkey_id]['callback']
            if callback:
                threading.Thread(target=callback, daemon=True).start()
                logger.debug(f"Hotkey triggered: {self.hotkeys[hotkey_id]['combination']}")

    def start(self):
        if self.running:
            logger.warning("HotkeyManager already running")
            return

        self.running = True
        self.hotkey_thread = threading.Thread(target=self._hotkey_listener, daemon=True)
        self.hotkey_thread.start()
        logger.info("HotkeyManager started")

    def stop(self):
        if not self.running:
            return

        self.running = False
        keyboard.unhook_all()

        logger.info("HotkeyManager stopped")

    def _hotkey_listener(self):
        try:
            while self.running:
                keyboard.wait()
        except Exception as e:
            logger.error(f"Hotkey listener error: {e}")
            self.running = False

    def get_registered_hotkeys(self) -> Dict:
        return {
            info['combination']: info['description']
            for info in self.hotkeys.values()
        }


class GlobalHotkeyManager(HotkeyManager):
    def __init__(self):
        super().__init__()
        self.hwnd = None
        self.message_thread = None

    def start(self):
        if self.running:
            return

        self.running = True
        self.message_thread = threading.Thread(target=self._message_loop, daemon=True)
        self.message_thread.start()
        logger.info("GlobalHotkeyManager started")

    def _message_loop(self):
        try:
            HOTKEY_ID = 1

            byref = ctypes.byref
            user32 = ctypes.windll.user32

            for hotkey_id, info in self.hotkeys.items():
                if info['modifiers'] and info['key']:
                    if user32.RegisterHotKey(None, hotkey_id, info['modifiers'], info['key']):
                        logger.info(f"Registered global hotkey: {info['combination']}")
                    else:
                        logger.error(f"Failed to register global hotkey: {info['combination']}")

            msg = wintypes.MSG()
            while self.running:
                bRet = user32.GetMessageW(byref(msg), None, 0, 0)

                if bRet == 0:
                    break
                elif bRet == -1:
                    logger.error("Error in message loop")
                    break
                else:
                    if msg.message == win32con.WM_HOTKEY:
                        hotkey_id = msg.wParam
                        self._handle_hotkey(hotkey_id)

                    user32.TranslateMessage(byref(msg))
                    user32.DispatchMessageW(byref(msg))

        except Exception as e:
            logger.error(f"Message loop error: {e}")
        finally:
            for hotkey_id in self.hotkeys:
                user32.UnregisterHotKey(None, hotkey_id)

    def stop(self):
        super().stop()
        if self.hwnd:
            win32api.PostMessage(self.hwnd, win32con.WM_QUIT, 0, 0)