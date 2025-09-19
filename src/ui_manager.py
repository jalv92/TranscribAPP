import pystray
from PIL import Image, ImageDraw, ImageFont
import threading
import customtkinter as ctk
from typing import Optional, Callable
import logging
import json
import os
from datetime import datetime
import queue
import tkinter as tk
from tkinter import messagebox

logger = logging.getLogger(__name__)


class TrayApp:
    def __init__(self, config: dict):
        self.config = config
        self.icon = None
        self.status = "ready"
        self.callback_record = None
        self.callback_settings = None
        self.callback_exit = None
        self.is_recording = False

        self.status_icons = {
            'ready': '⚪',
            'recording': '🔴',
            'processing': '⚙️',
            'success': '✅',
            'error': '❌'
        }

        logger.info("TrayApp initialized")

    def create_icon(self, status: str = 'ready', disabled: bool = False) -> Image.Image:
        width = 64
        height = 64
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        colors = {
            'ready': (100, 100, 100, 255),
            'recording': (255, 0, 0, 255),
            'processing': (255, 165, 0, 255),
            'success': (0, 255, 0, 255),
            'error': (255, 0, 0, 255),
            'disabled': (50, 50, 50, 255)
        }

        color = colors.get(status, colors['ready'])

        # Override color if disabled
        if disabled:
            color = colors['disabled']

        draw.ellipse([8, 8, 56, 56], fill=color, outline=(255, 255, 255, 255))

        if status == 'recording' and not disabled:
            draw.ellipse([24, 24, 40, 40], fill=(255, 255, 255, 255))
        elif disabled:
            # Draw an X for disabled state
            draw.line([20, 20, 44, 44], fill=(255, 255, 255, 255), width=3)
            draw.line([44, 20, 20, 44], fill=(255, 255, 255, 255), width=3)

        return image

    def update_status(self, status: str, message: str = None, disabled: bool = False):
        self.status = status
        if self.icon:
            self.icon.icon = self.create_icon(status, disabled)

            if message and self.config['ui']['show_notifications']:
                self.icon.notify(message, "TranscribeApp")

        logger.info(f"Status updated: {status} - {message} (disabled: {disabled})")

    def on_record_click(self, icon, item):
        if self.callback_record:
            self.callback_record()

    def on_settings_click(self, icon, item):
        if self.callback_settings:
            self.callback_settings()

    def on_exit_click(self, icon, item):
        if self.callback_exit:
            self.callback_exit()
        self.stop()

    def setup_menu(self):
        # Get AI status from config
        ai_enabled = self.config.get('llm', {}).get('enabled', True)
        ai_status = "🤖 AI Enhancement: ON" if ai_enabled else "🔧 AI Enhancement: OFF"

        return pystray.Menu(
            pystray.MenuItem(
                "🎤 Record (Ctrl+Shift+R)",
                self.on_record_click,
                default=True
            ),
            pystray.MenuItem(ai_status, None, enabled=False),  # Status indicator (non-clickable)
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("⚙️ Settings", self.on_settings_click),
            pystray.MenuItem("📋 History", self.show_history),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("❓ Help", self.show_help),
            pystray.MenuItem("ℹ️ About", self.show_about),
            pystray.MenuItem("❌ Exit", self.on_exit_click)
        )

    def show_history(self, icon, item):
        logger.info("Showing history")

    def show_help(self, icon, item):
        """Show help dialog with usage instructions"""
        def create_help_window():
            help_window = tk.Tk()
            help_window.withdraw()  # Hide the main window

            help_text = """TranscribeApp - Quick Help Guide

HOW TO USE:
1. Click the system tray icon or press Ctrl+Shift+R to start recording
2. Speak clearly in Spanish
3. Stop speaking (3 seconds of silence ends recording)
4. English translation appears automatically in active window

KEYBOARD SHORTCUTS:
• Ctrl+Shift+R - Start/Stop recording
• Ctrl+Shift+T - Enable/Disable app

REQUIREMENTS:
• Qwen2.5-3B AI Model must be installed
• Place model files in: C:\\Program Files\\TranscribeApp\\LLM\\Qwen2.5-3B-Instruct\\
• Download from: https://huggingface.co/Qwen/Qwen2.5-3B-Instruct

TIPS:
• Speak clearly for best results
• Wait for "Ready" status before recording
• Processing takes ~3 seconds
• Text is automatically typed where cursor is

TROUBLESHOOTING:
• "Model not found" - Download and install AI model
• "CUDA error" - Update NVIDIA drivers
• "Out of memory" - Close other applications
• No text appearing - Check if cursor is in text field

For more help, check README.txt in installation folder."""

            messagebox.showinfo("TranscribeApp Help", help_text)
            help_window.destroy()

        # Run in thread to avoid blocking
        threading.Thread(target=create_help_window, daemon=True).start()
        logger.info("Showing help dialog")

    def show_about(self, icon, item):
        """Show about dialog with app information"""
        def create_about_window():
            about_window = tk.Tk()
            about_window.withdraw()  # Hide the main window

            about_text = """TranscribeApp v1.0

AI-Powered Spanish to English Voice Translation

Features:
• Real-time Spanish speech recognition
• AI-enhanced translation using Qwen2.5-3B
• Automatic text injection into active window
• System-wide hotkey support
• Handles unclear speech intelligently

System Requirements:
• Windows 10/11 64-bit
• NVIDIA GPU with CUDA support
• 16GB RAM minimum
• 10GB disk space

© 2024 TranscribeApp
Licensed under MIT License

For support and documentation:
Check README.txt in installation folder"""

            messagebox.showinfo("About TranscribeApp", about_text)
            about_window.destroy()

        # Run in thread to avoid blocking
        threading.Thread(target=create_about_window, daemon=True).start()
        logger.info("Showing about dialog")

    def run(self):
        self.icon = pystray.Icon(
            "TranscribeApp",
            self.create_icon(self.status),
            menu=self.setup_menu()
        )

        threading.Thread(target=self.icon.run, daemon=True).start()
        logger.info("System tray icon started")

    def stop(self):
        if self.icon:
            self.icon.stop()
            logger.info("System tray icon stopped")

    def set_callbacks(self, record: Callable = None, settings: Callable = None, exit_app: Callable = None):
        self.callback_record = record
        self.callback_settings = settings
        self.callback_exit = exit_app


class SettingsWindow:
    def __init__(self, config: dict, save_callback: Callable = None):
        self.config = config
        self.save_callback = save_callback
        self.window = None
        self.widgets = {}

    def show(self):
        if self.window is not None and self.window.winfo_exists():
            self.window.lift()
            return

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.window = ctk.CTk()
        self.window.title("TranscribeApp Settings")
        self.window.geometry("600x700")
        self.window.resizable(False, False)

        self.create_widgets()

        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        self.window.mainloop()

    def create_widgets(self):
        notebook = ctk.CTkTabview(self.window, width=580, height=650)
        notebook.pack(padx=10, pady=10)

        audio_tab = notebook.add("Audio")
        self.create_audio_tab(audio_tab)

        model_tab = notebook.add("Models")
        self.create_model_tab(model_tab)

        hotkey_tab = notebook.add("Hotkeys")
        self.create_hotkey_tab(hotkey_tab)

        advanced_tab = notebook.add("Advanced")
        self.create_advanced_tab(advanced_tab)

        button_frame = ctk.CTkFrame(self.window)
        button_frame.pack(fill="x", padx=10, pady=(0, 10))

        save_btn = ctk.CTkButton(button_frame, text="Save", command=self.save_settings, width=100)
        save_btn.pack(side="right", padx=5)

        cancel_btn = ctk.CTkButton(button_frame, text="Cancel", command=self.on_close, width=100)
        cancel_btn.pack(side="right")

    def create_audio_tab(self, parent):
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(frame, text="Audio Settings", font=("Arial", 16, "bold")).pack(pady=10)

        # Microphone selection
        ctk.CTkLabel(frame, text="Input Device:").pack(anchor="w", padx=20, pady=(10, 0))

        # Get available audio devices
        try:
            from audio_handler import AudioRecorder
            devices = AudioRecorder.get_audio_devices()
            device_names = [f"{d['name']} (ID: {d['index']})" for d in devices]
            current_device = self.config['audio'].get('input_device', None)
        except:
            device_names = ["Default Device"]
            current_device = None

        self.widgets['input_device'] = ctk.CTkComboBox(
            frame,
            values=device_names if device_names else ["Default Device"],
            width=400
        )

        if current_device is not None:
            for i, d in enumerate(devices):
                if d['index'] == current_device:
                    self.widgets['input_device'].set(device_names[i])
                    break
        else:
            self.widgets['input_device'].set("Default Device")

        self.widgets['input_device'].pack(padx=20, pady=5)

        ctk.CTkLabel(frame, text="Sample Rate:").pack(anchor="w", padx=20, pady=(10, 0))
        self.widgets['sample_rate'] = ctk.CTkComboBox(
            frame,
            values=["16000", "22050", "44100", "48000"],
            width=200
        )
        self.widgets['sample_rate'].set(str(self.config['audio']['sample_rate']))
        self.widgets['sample_rate'].pack(padx=20, pady=5)

        ctk.CTkLabel(frame, text="Buffer Duration (seconds):").pack(anchor="w", padx=20, pady=(10, 0))
        self.widgets['buffer_duration'] = ctk.CTkSlider(
            frame,
            from_=10,
            to=60,
            number_of_steps=50,
            width=400
        )
        self.widgets['buffer_duration'].set(self.config['audio']['buffer_duration'])
        self.widgets['buffer_duration'].pack(padx=20, pady=5)

        self.buffer_label = ctk.CTkLabel(frame, text=f"Buffer: {self.config['audio']['buffer_duration']}s")
        self.buffer_label.pack()

        self.widgets['buffer_duration'].configure(
            command=lambda v: self.buffer_label.configure(text=f"Buffer: {int(v)}s")
        )

        ctk.CTkLabel(frame, text="Silence Threshold:").pack(anchor="w", padx=20, pady=(10, 0))
        self.widgets['silence_threshold'] = ctk.CTkSlider(
            frame,
            from_=0.001,
            to=0.1,
            number_of_steps=99,
            width=400
        )
        self.widgets['silence_threshold'].set(self.config['audio']['silence_threshold'])
        self.widgets['silence_threshold'].pack(padx=20, pady=5)

        ctk.CTkLabel(frame, text="Silence Duration (seconds):").pack(anchor="w", padx=20, pady=(10, 0))
        self.widgets['silence_duration'] = ctk.CTkSlider(
            frame,
            from_=0.5,
            to=5.0,
            number_of_steps=45,
            width=400
        )
        self.widgets['silence_duration'].set(self.config['audio']['silence_duration'])
        self.widgets['silence_duration'].pack(padx=20, pady=5)

    def create_model_tab(self, parent):
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(frame, text="Model Settings", font=("Arial", 16, "bold")).pack(pady=10)

        ctk.CTkLabel(frame, text="Whisper Model Size:").pack(anchor="w", padx=20, pady=(10, 0))
        self.widgets['whisper_model'] = ctk.CTkComboBox(
            frame,
            values=["tiny", "base", "small", "medium", "large"],
            width=200
        )
        self.widgets['whisper_model'].set(self.config['whisper']['model_size'])
        self.widgets['whisper_model'].pack(padx=20, pady=5)

        ctk.CTkLabel(frame, text="Translation Model:").pack(anchor="w", padx=20, pady=(10, 0))
        self.widgets['translation_model'] = ctk.CTkEntry(frame, width=400)
        self.widgets['translation_model'].insert(0, self.config['translation']['model_name'])
        self.widgets['translation_model'].pack(padx=20, pady=5)

        # AI Enhancement Section
        ai_frame = ctk.CTkFrame(frame)
        ai_frame.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(ai_frame, text="AI Enhancement Settings", font=("Arial", 14, "bold")).pack(pady=10)

        self.widgets['llm_enabled'] = ctk.CTkCheckBox(
            ai_frame,
            text="Enable AI Enhancement for translations",
            command=self.toggle_llm_options
        )
        if self.config.get('llm', {}).get('enabled', True):
            self.widgets['llm_enabled'].select()
        self.widgets['llm_enabled'].pack(padx=20, pady=5)

        # Model selector
        model_frame = ctk.CTkFrame(ai_frame)
        model_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(model_frame, text="LLM Model:").pack(anchor="w", pady=(5, 0))

        # Scan for available models
        from model_scanner import ModelScanner
        scanner = ModelScanner("LLM")
        available_models = scanner.scan_models()

        # Create model dropdown
        model_options = []
        self.model_details = {}  # Store full model info

        if available_models:
            for model in available_models:
                display_name = f"{model['name']} ({model['size_gb']}GB)"
                if not model['is_installed']:
                    display_name += " [Incomplete]"
                model_options.append(display_name)
                self.model_details[display_name] = model
        else:
            model_options = ["No models found - Add models to LLM folder"]

        self.widgets['llm_model'] = ctk.CTkComboBox(
            model_frame,
            values=model_options,
            width=400,
            command=self.on_model_selected
        )

        # Set current model
        current_model = self.config.get('llm', {}).get('model_path', 'LLM/Qwen2.5-3B-Instruct')
        current_model_name = os.path.basename(current_model)

        # Find and select current model in dropdown
        for display_name, details in self.model_details.items():
            if details['id'] == current_model_name:
                self.widgets['llm_model'].set(display_name)
                break
        else:
            if model_options:
                self.widgets['llm_model'].set(model_options[0])

        self.widgets['llm_model'].pack(pady=5)

        # Model info label
        self.model_info_label = ctk.CTkLabel(
            model_frame,
            text="",
            justify="left",
            font=("Arial", 10),
            text_color="gray"
        )
        self.model_info_label.pack(pady=5)

        # Update model info for selected model
        self.on_model_selected(self.widgets['llm_model'].get())

        # Download models button
        download_btn = ctk.CTkButton(
            model_frame,
            text="📥 Download More Models",
            command=self.show_download_guide,
            width=200
        )
        download_btn.pack(pady=10)

        self.widgets['enhance_translation'] = ctk.CTkCheckBox(
            ai_frame,
            text="Enhance translations with AI (better fluency)"
        )
        if self.config.get('llm', {}).get('enhance_translation', True):
            self.widgets['enhance_translation'].select()
        self.widgets['enhance_translation'].pack(padx=20, pady=5)

        # Info label about AI enhancement
        info_text = """When AI Enhancement is disabled:
• Basic text cleaning will still work
• Translations will be more literal
• Processing will be faster
• Less memory usage"""

        info_label = ctk.CTkLabel(
            ai_frame,
            text=info_text,
            justify="left",
            font=("Arial", 10),
            text_color="gray"
        )
        info_label.pack(padx=20, pady=10)

        # Update the state of enhance_translation based on llm_enabled
        self.toggle_llm_options()

        self.widgets['use_gpu'] = ctk.CTkCheckBox(
            frame,
            text="Use GPU acceleration (if available)"
        )
        self.widgets['use_gpu'].pack(padx=20, pady=20)

    def create_hotkey_tab(self, parent):
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(frame, text="Hotkey Settings", font=("Arial", 16, "bold")).pack(pady=10)

        ctk.CTkLabel(frame, text="Record Hotkey:").pack(anchor="w", padx=20, pady=(10, 0))
        self.widgets['record_hotkey'] = ctk.CTkEntry(frame, width=200)
        self.widgets['record_hotkey'].insert(0, self.config['hotkeys']['record'])
        self.widgets['record_hotkey'].pack(padx=20, pady=5)

        ctk.CTkLabel(frame, text="Toggle Enable/Disable:").pack(anchor="w", padx=20, pady=(10, 0))
        self.widgets['toggle_hotkey'] = ctk.CTkEntry(frame, width=200)
        self.widgets['toggle_hotkey'].insert(0, self.config['hotkeys']['toggle_enabled'])
        self.widgets['toggle_hotkey'].pack(padx=20, pady=5)

    def on_model_selected(self, selected_value):
        """Update model info when a model is selected"""
        if hasattr(self, 'model_details') and selected_value in self.model_details:
            model = self.model_details[selected_value]
            info_text = f"""Provider: {model['provider']}
Quality: {model['quality'].capitalize()} | Speed: {model['speed'].capitalize()}
Memory Required: {model['memory_required_gb']}GB RAM
{model['description']}"""

            if not model['is_installed']:
                info_text += "\n⚠️ Model files incomplete - download required"

            if hasattr(self, 'model_info_label'):
                self.model_info_label.configure(text=info_text)

    def show_download_guide(self):
        """Show guide for downloading additional models"""
        def create_download_window():
            download_window = tk.Tk()
            download_window.withdraw()

            guide_text = """Model Download Guide

RECOMMENDED MODELS:

1. Llama 3.2 3B (Meta) - Best English fluency
   • Download: https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct
   • Size: 6GB
   • Place in: LLM/Llama-3.2-3B-Instruct/

2. Llama 3.2 1B (Meta) - Lightweight option
   • Download: https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct
   • Size: 2GB (saves 4GB vs Qwen)
   • Place in: LLM/Llama-3.2-1B-Instruct/

3. Phi 3.5 Mini (Microsoft) - Good balance
   • Download: https://huggingface.co/microsoft/Phi-3.5-mini-instruct
   • Size: 3GB
   • Place in: LLM/Phi-3.5-mini-instruct/

4. Gemma 2 2B (Google) - Efficient
   • Download: https://huggingface.co/google/gemma-2-2b-it
   • Size: 4GB
   • Place in: LLM/gemma-2-2b-it/

HOW TO DOWNLOAD:
1. Click the HuggingFace link
2. Click "Files and versions" tab
3. Download ALL files to the model folder
4. Restart TranscribeApp
5. Select the model in Settings

Using Git LFS (easier):
git lfs install
cd LLM
git clone [huggingface-url]"""

            messagebox.showinfo("Download Models", guide_text)
            download_window.destroy()

        threading.Thread(target=create_download_window, daemon=True).start()

    def toggle_llm_options(self):
        """Enable/disable LLM-related options based on main toggle"""
        if hasattr(self, 'widgets') and 'llm_enabled' in self.widgets:
            is_enabled = self.widgets['llm_enabled'].get()

            # Enable/disable model selector
            if 'llm_model' in self.widgets:
                if is_enabled:
                    self.widgets['llm_model'].configure(state="normal")
                else:
                    self.widgets['llm_model'].configure(state="disabled")

            # Enable/disable enhance translation
            if 'enhance_translation' in self.widgets:
                if is_enabled:
                    self.widgets['enhance_translation'].configure(state="normal")
                else:
                    self.widgets['enhance_translation'].configure(state="disabled")

    def create_advanced_tab(self, parent):
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(frame, text="Advanced Settings", font=("Arial", 16, "bold")).pack(pady=10)

        self.widgets['show_notifications'] = ctk.CTkCheckBox(
            frame,
            text="Show notifications"
        )
        if self.config['ui']['show_notifications']:
            self.widgets['show_notifications'].select()
        self.widgets['show_notifications'].pack(padx=20, pady=10)

        self.widgets['model_cache'] = ctk.CTkCheckBox(
            frame,
            text="Keep models in memory"
        )
        if self.config['performance']['model_cache']:
            self.widgets['model_cache'].select()
        self.widgets['model_cache'].pack(padx=20, pady=10)

        ctk.CTkLabel(frame, text="Max Recording Duration (seconds):").pack(anchor="w", padx=20, pady=(10, 0))
        self.widgets['max_recording'] = ctk.CTkSlider(
            frame,
            from_=30,
            to=300,
            number_of_steps=27,
            width=400
        )
        self.widgets['max_recording'].set(self.config['performance']['max_recording_duration'])
        self.widgets['max_recording'].pack(padx=20, pady=5)

    def save_settings(self):
        try:
            # Save audio device selection
            selected_device = self.widgets['input_device'].get()
            if "ID:" in selected_device:
                device_id = int(selected_device.split("ID: ")[1].split(")")[0])
                self.config['audio']['input_device'] = device_id
            else:
                self.config['audio']['input_device'] = None

            self.config['audio']['sample_rate'] = int(self.widgets['sample_rate'].get())
            self.config['audio']['buffer_duration'] = int(self.widgets['buffer_duration'].get())
            self.config['audio']['silence_threshold'] = float(self.widgets['silence_threshold'].get())
            self.config['audio']['silence_duration'] = float(self.widgets['silence_duration'].get())

            self.config['whisper']['model_size'] = self.widgets['whisper_model'].get()
            self.config['translation']['model_name'] = self.widgets['translation_model'].get()

            # Save LLM settings
            if 'llm' not in self.config:
                self.config['llm'] = {}
            self.config['llm']['enabled'] = self.widgets['llm_enabled'].get()
            self.config['llm']['enhance_translation'] = self.widgets['enhance_translation'].get()

            # Save selected model
            if 'llm_model' in self.widgets:
                selected_model = self.widgets['llm_model'].get()
                if hasattr(self, 'model_details') and selected_model in self.model_details:
                    model_info = self.model_details[selected_model]
                    self.config['llm']['model_path'] = model_info['path']
                    self.config['llm']['model_id'] = model_info['id']

            self.config['hotkeys']['record'] = self.widgets['record_hotkey'].get()
            self.config['hotkeys']['toggle_enabled'] = self.widgets['toggle_hotkey'].get()

            self.config['ui']['show_notifications'] = self.widgets['show_notifications'].get()
            self.config['performance']['model_cache'] = self.widgets['model_cache'].get()
            self.config['performance']['max_recording_duration'] = int(self.widgets['max_recording'].get())

            with open('config.json', 'w') as f:
                json.dump(self.config, f, indent=4)

            if self.save_callback:
                self.save_callback(self.config)

            logger.info("Settings saved successfully")
            self.on_close()

        except Exception as e:
            logger.error(f"Failed to save settings: {e}")

    def on_close(self):
        if self.window:
            self.window.destroy()
            self.window = None