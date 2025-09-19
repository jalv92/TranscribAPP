import tkinter as tk
from tkinter import ttk
import threading
import queue
import time
from PIL import Image, ImageTk
import os
import sys

class SplashScreen:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("TranscribeApp - Loading")
        self.root.overrideredirect(True)  # Remove window decorations

        # Center the window
        window_width = 500
        window_height = 350
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # Set colors
        bg_color = "#1e1e1e"
        fg_color = "#ffffff"
        accent_color = "#4CAF50"

        self.root.configure(bg=bg_color)

        # Main frame
        main_frame = tk.Frame(self.root, bg=bg_color)
        main_frame.pack(expand=True, fill="both", padx=30, pady=30)

        # Title
        title = tk.Label(
            main_frame,
            text="TranscribeApp",
            font=("Segoe UI", 24, "bold"),
            bg=bg_color,
            fg=fg_color
        )
        title.pack(pady=(0, 5))

        # Subtitle
        subtitle = tk.Label(
            main_frame,
            text="AI-Powered Voice Translation",
            font=("Segoe UI", 12),
            bg=bg_color,
            fg="#888888"
        )
        subtitle.pack(pady=(0, 30))

        # Status label
        self.status_label = tk.Label(
            main_frame,
            text="Starting application...",
            font=("Segoe UI", 11),
            bg=bg_color,
            fg=fg_color
        )
        self.status_label.pack(pady=(0, 10))

        # Progress bar
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            "green.Horizontal.TProgressbar",
            background=accent_color,
            troughcolor=bg_color,
            bordercolor=bg_color,
            darkcolor=accent_color,
            lightcolor=accent_color
        )

        self.progress = ttk.Progressbar(
            main_frame,
            style="green.Horizontal.TProgressbar",
            length=400,
            mode='determinate',
            maximum=100
        )
        self.progress.pack(pady=(0, 10))

        # Progress percentage
        self.progress_label = tk.Label(
            main_frame,
            text="0%",
            font=("Segoe UI", 10),
            bg=bg_color,
            fg="#888888"
        )
        self.progress_label.pack()

        # Loading steps info
        self.step_label = tk.Label(
            main_frame,
            text="",
            font=("Segoe UI", 9),
            bg=bg_color,
            fg="#666666"
        )
        self.step_label.pack(pady=(20, 0))

        # Footer
        footer = tk.Label(
            main_frame,
            text="Please wait while components are loading...",
            font=("Segoe UI", 9),
            bg=bg_color,
            fg="#666666"
        )
        footer.pack(side="bottom", pady=(20, 0))

        # Update queue for thread-safe updates
        self.update_queue = queue.Queue()
        self.root.after(100, self.check_queue)

        # Close flag
        self.should_close = False

    def check_queue(self):
        """Check for updates from other threads"""
        try:
            while True:
                msg = self.update_queue.get_nowait()

                if msg[0] == 'status':
                    self.status_label.config(text=msg[1])

                elif msg[0] == 'progress':
                    value = msg[1]
                    self.progress['value'] = value
                    self.progress_label.config(text=f"{int(value)}%")

                elif msg[0] == 'step':
                    self.step_label.config(text=msg[1])

                elif msg[0] == 'close':
                    self.close()
                    return

        except queue.Empty:
            pass

        if not self.should_close:
            self.root.after(50, self.check_queue)

    def update_status(self, text):
        """Update status text (thread-safe)"""
        self.update_queue.put(('status', text))

    def update_progress(self, value):
        """Update progress bar (thread-safe)"""
        self.update_queue.put(('progress', value))

    def update_step(self, text):
        """Update step info (thread-safe)"""
        self.update_queue.put(('step', text))

    def close(self):
        """Close the splash screen"""
        self.should_close = True
        self.root.destroy()

    def close_after_delay(self, delay=1000):
        """Close splash screen after a delay"""
        self.root.after(delay, self.close)

    def show(self):
        """Show the splash screen"""
        self.root.mainloop()


def create_splash():
    """Create and return a splash screen instance"""
    splash = SplashScreen()
    # Run splash screen in separate thread
    splash_thread = threading.Thread(target=splash.show, daemon=True)
    splash_thread.start()

    # Give it time to initialize
    time.sleep(0.5)

    return splash


if __name__ == "__main__":
    # Test the splash screen
    splash = create_splash()

    # Simulate loading steps
    steps = [
        ("Initializing components...", 10, "Step 1/5: Core systems"),
        ("Loading configuration...", 25, "Step 2/5: Configuration"),
        ("Connecting audio devices...", 40, "Step 3/5: Audio system"),
        ("Loading AI models...", 70, "Step 4/5: AI models (this may take a while)"),
        ("Finalizing setup...", 90, "Step 5/5: Final setup"),
        ("Ready to start!", 100, "Completed!")
    ]

    for status, progress, step in steps:
        splash.update_status(status)
        splash.update_progress(progress)
        splash.update_step(step)
        time.sleep(2)  # Simulate work

    splash.close_after_delay(1000)
    time.sleep(2)