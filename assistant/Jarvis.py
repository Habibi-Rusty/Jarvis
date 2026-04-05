"""
JARVIS - Just A Rather Very Intelligent System
A local AI assistant with system control capabilities.
"""

import os
import sys
import json
import time
import math
import queue
import threading
import subprocess
import platform
import datetime
import webbrowser
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
from pathlib import Path

SYSTEM = platform.system()  # "Windows", "Darwin", "Linux"

# ─── Optional imports (graceful fallback) ────────────────────────────────────
try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

try:
    import speech_recognition as sr
    STT_AVAILABLE = True
except ImportError:
    STT_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    import anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False

# ─── Config ──────────────────────────────────────────────────────────────────
CONFIG_FILE = Path.home() / ".jarvis_config.json"

def load_config():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"api_key": "", "voice_enabled": True, "theme": "dark", "wake_word": "jarvis"}

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)

# ─── System Control Functions ─────────────────────────────────────────────────
class SystemController:
    def open_app(self, app_name):
        app = app_name.lower().strip()
        try:
            if SYSTEM == "Windows":
                apps = {
                    "notepad": "notepad", "calculator": "calc", "paint": "mspaint",
                    "browser": "start chrome", "chrome": "start chrome",
                    "firefox": "start firefox", "explorer": "explorer",
                    "cmd": "start cmd", "terminal": "start cmd",
                    "word": "start winword", "excel": "start excel",
                    "vlc": "start vlc", "spotify": "start spotify",
                    "task manager": "taskmgr", "settings": "start ms-settings:",
                    "snipping tool": "snippingtool",
                }
                cmd = apps.get(app, f"start {app}")
                subprocess.Popen(cmd, shell=True)
            elif SYSTEM == "Darwin":
                apps = {
                    "browser": "Safari", "chrome": "Google Chrome",
                    "firefox": "Firefox", "terminal": "Terminal",
                    "finder": "Finder", "spotify": "Spotify",
                    "vlc": "VLC", "calculator": "Calculator",
                    "textedit": "TextEdit", "notes": "Notes",
                    "mail": "Mail", "calendar": "Calendar",
                }
                app_name_mac = apps.get(app, app.title())
                subprocess.Popen(["open", "-a", app_name_mac])
            else:  # Linux
                apps = {
                    "browser": "xdg-open https://google.com",
                    "chrome": "google-chrome",
                    "firefox": "firefox",
                    "terminal": "x-terminal-emulator",
                    "files": "nautilus",
                    "calculator": "gnome-calculator",
                    "text editor": "gedit",
                    "vlc": "vlc",
                    "spotify": "spotify",
                }
                cmd = apps.get(app, app)
                subprocess.Popen(cmd.split(), env=os.environ)
            return f"Opening {app_name}..."
        except Exception as e:
            return f"Couldn't open {app_name}: {e}"

    def list_files(self, path=None):
        try:
            p = Path(path) if path else Path.home()
            items = list(p.iterdir())
            dirs = sorted([x.name for x in items if x.is_dir()])
            files = sorted([x.name for x in items if x.is_file()])
            result = f"📁 {p}\n"
            for d in dirs[:15]:
                result += f"  📁 {d}/\n"
            for f in files[:15]:
                result += f"  📄 {f}\n"
            total = len(items)
            if total > 30:
                result += f"  ... and {total - 30} more items"
            return result
        except Exception as e:
            return f"Error listing files: {e}"

    def search_files(self, query, start_dir=None):
        try:
            base = Path(start_dir) if start_dir else Path.home()
            results = []
            for p in base.rglob(f"*{query}*"):
                if len(results) >= 20:
                    break
                results.append(str(p))
            if not results:
                return f"No files found matching '{query}'"
            return "Found:\n" + "\n".join(results[:20])
        except Exception as e:
            return f"Search error: {e}"

    def get_system_info(self):
        info = f"🖥️  System: {platform.system()} {platform.release()}\n"
        info += f"💻  Machine: {platform.machine()}\n"
        info += f"🐍  Python: {platform.python_version()}\n"
        info += f"🕐  Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        if PSUTIL_AVAILABLE:
            cpu = psutil.cpu_percent(interval=0.5)
            ram = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            info += f"⚡  CPU: {cpu}%\n"
            info += f"🧠  RAM: {ram.percent}% used ({ram.used//1024//1024}MB / {ram.total//1024//1024}MB)\n"
            info += f"💾  Disk: {disk.percent}% used ({disk.free//1024//1024//1024}GB free)\n"
        return info

    def music_control(self, action):
        action = action.lower()
        try:
            if SYSTEM == "Windows":
                # Use keyboard media keys via PowerShell
                key_map = {
                    "play": "PlayPause", "pause": "PlayPause",
                    "play pause": "PlayPause", "stop": "Stop",
                    "next": "MediaNextTrack", "previous": "MediaPreviousTrack",
                    "volume up": "VolumeUp", "volume down": "VolumeDown",
                    "mute": "VolumeMute",
                }
                key = key_map.get(action)
                if key:
                    ps = f"$wsh = New-Object -ComObject WScript.Shell; $wsh.SendKeys([char]179)"
                    media_keys = {
                        "PlayPause": "[char]179", "Stop": "[char]178",
                        "MediaNextTrack": "[char]176", "MediaPreviousTrack": "[char]177",
                        "VolumeUp": "[char]175", "VolumeDown": "[char]174",
                        "VolumeMute": "[char]173",
                    }
                    ps = f"$wsh = New-Object -ComObject WScript.Shell; $wsh.SendKeys({media_keys.get(key, '[char]179')})"
                    subprocess.run(["powershell", "-Command", ps], capture_output=True)
            elif SYSTEM == "Darwin":
                # AppleScript for macOS
                scripts = {
                    "play": 'tell application "Music" to play',
                    "pause": 'tell application "Music" to pause',
                    "play pause": 'tell application "Music" to playpause',
                    "next": 'tell application "Music" to next track',
                    "previous": 'tell application "Music" to previous track',
                }
                script = scripts.get(action, 'tell application "Music" to playpause')
                subprocess.run(["osascript", "-e", script], capture_output=True)
            else:  # Linux
                cmd_map = {
                    "play": ["playerctl", "play"],
                    "pause": ["playerctl", "pause"],
                    "play pause": ["playerctl", "play-pause"],
                    "next": ["playerctl", "next"],
                    "previous": ["playerctl", "previous"],
                    "volume up": ["amixer", "-D", "pulse", "sset", "Master", "10%+"],
                    "volume down": ["amixer", "-D", "pulse", "sset", "Master", "10%-"],
                    "mute": ["amixer", "-D", "pulse", "sset", "Master", "toggle"],
                }
                cmd = cmd_map.get(action, ["playerctl", "play-pause"])
                subprocess.run(cmd, capture_output=True)
            return f"Music: {action} ✓"
        except Exception as e:
            return f"Music control error: {e}"

    def set_volume(self, level):
        try:
            level = max(0, min(100, int(level)))
            if SYSTEM == "Windows":
                ps = f"$wsh=New-Object -ComObject WScript.Shell; [audio]::Volume={level/100}"
                subprocess.run(["powershell", "-Command", ps], capture_output=True)
            elif SYSTEM == "Darwin":
                subprocess.run(["osascript", "-e", f"set volume output volume {level}"], capture_output=True)
            else:
                subprocess.run(["amixer", "-D", "pulse", "sset", "Master", f"{level}%"], capture_output=True)
            return f"Volume set to {level}%"
        except Exception as e:
            return f"Volume error: {e}"

    def take_screenshot(self):
        try:
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            path = str(Path.home() / f"jarvis_screenshot_{ts}.png")
            if SYSTEM == "Windows":
                subprocess.Popen(f'snippingtool /clip', shell=True)
                return "Screenshot tool opened."
            elif SYSTEM == "Darwin":
                subprocess.run(["screencapture", path])
            else:
                subprocess.run(["scrot", path])
            return f"Screenshot saved: {path}"
        except Exception as e:
            return f"Screenshot error: {e}"

    def open_url(self, url):
        if not url.startswith("http"):
            url = "https://" + url
        webbrowser.open(url)
        return f"Opening: {url}"

    def get_time(self):
        now = datetime.datetime.now()
        return f"🕐 {now.strftime('%A, %B %d %Y – %H:%M:%S')}"

    def get_weather_url(self, city=""):
        url = f"https://wttr.in/{city.replace(' ', '+')}" if city else "https://wttr.in"
        webbrowser.open(url)
        return f"Opening weather for {city or 'your location'}..."

# ─── Command Parser ────────────────────────────────────────────────────────────
class CommandParser:
    def __init__(self, controller: SystemController):
        self.sc = controller

    def parse(self, text: str) -> str | None:
        """Returns response string if command matched, else None (fall through to AI)."""
        t = text.lower().strip()

        # Time & date
        if any(w in t for w in ["what time", "current time", "what's the time", "tell me the time"]):
            return self.sc.get_time()

        # System info
        if any(w in t for w in ["system info", "cpu usage", "ram usage", "disk space", "system status"]):
            return self.sc.get_system_info()

        # Screenshots
        if "screenshot" in t:
            return self.sc.take_screenshot()

        # Music/media controls
        if any(w in t for w in ["play music", "pause music", "stop music", "next song", "previous song",
                                  "next track", "previous track", "play pause", "skip song",
                                  "volume up", "volume down", "mute"]):
            if "next" in t:
                return self.sc.music_control("next")
            elif "previous" in t or "prev" in t or "back" in t:
                return self.sc.music_control("previous")
            elif "pause" in t or "stop" in t:
                return self.sc.music_control("pause")
            elif "mute" in t:
                return self.sc.music_control("mute")
            elif "volume up" in t:
                return self.sc.music_control("volume up")
            elif "volume down" in t:
                return self.sc.music_control("volume down")
            else:
                return self.sc.music_control("play pause")

        # Volume set
        if "set volume" in t or "volume to" in t:
            for word in t.split():
                if word.isdigit():
                    return self.sc.set_volume(int(word))

        # Open app
        if t.startswith("open "):
            app = t[5:].strip()
            if any(url_kw in app for url_kw in ["http", "www.", ".com", ".org", ".net", ".io"]):
                return self.sc.open_url(app)
            return self.sc.open_app(app)

        # Open URL
        if "go to " in t:
            url = t.split("go to ", 1)[1].strip()
            return self.sc.open_url(url)

        # List files
        if "list files" in t or "show files" in t or "what's in" in t:
            if "in " in t:
                parts = t.split("in ", 1)
                path = parts[-1].strip()
                return self.sc.list_files(path)
            return self.sc.list_files()

        # Search files
        if "find file" in t or "search file" in t or "locate file" in t:
            query = t.split("file", 1)[-1].strip().strip("s").strip()
            if "named" in query:
                query = query.split("named", 1)[-1].strip()
            return self.sc.search_files(query)

        # Weather
        if "weather" in t:
            city = ""
            if "in " in t:
                city = t.split("in ", 1)[-1].strip().rstrip("?")
            return self.sc.get_weather_url(city)

        return None  # Not a system command, fall through to AI

# ─── TTS Engine ───────────────────────────────────────────────────────────────
class VoiceEngine:
    def __init__(self):
        self.engine = None
        self.enabled = False
        if TTS_AVAILABLE:
            try:
                self.engine = pyttsx3.init()
                self.engine.setProperty("rate", 180)
                voices = self.engine.getProperty("voices")
                if voices:
                    self.engine.setProperty("voice", voices[0].id)
                self.enabled = True
            except Exception:
                pass

    def speak(self, text):
        if not self.enabled or not self.engine:
            return
        clean = text.replace("🖥️", "").replace("💻", "").replace("🕐", "")
        clean = clean.replace("⚡", "").replace("🧠", "").replace("💾", "")
        clean = clean.replace("📁", "").replace("📄", "")
        # Remove markdown-ish
        clean = " ".join(clean.split())
        try:
            self.engine.say(clean[:500])
            self.engine.runAndWait()
        except Exception:
            pass

# ─── AI Brain ─────────────────────────────────────────────────────────────────
class AIBrain:
    def __init__(self, api_key=""):
        self.api_key = api_key
        self.history = []
        self.system_prompt = (
            "You are JARVIS, a smart, concise local AI assistant. "
            "You help with tasks, answer questions, and assist with system control. "
            "Keep responses brief and helpful. If asked about capabilities, mention: "
            "open apps, list/search files, system info, music control, screenshots, "
            "weather, time, web browsing, and general knowledge. "
            "Be conversational and friendly but concise."
        )

    def chat(self, user_msg):
        if not self.api_key:
            return ("I need an API key to answer general questions. "
                    "Set it in Settings (gear icon). For system commands, "
                    "I work without one — try 'open calculator' or 'system info'.")
        if not CLAUDE_AVAILABLE:
            return "anthropic package not installed. Run: pip install anthropic"
        try:
            client = anthropic.Anthropic(api_key=self.api_key)
            self.history.append({"role": "user", "content": user_msg})
            if len(self.history) > 20:
                self.history = self.history[-20:]
            resp = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=600,
                system=self.system_prompt,
                messages=self.history,
            )
            answer = resp.content[0].text
            self.history.append({"role": "assistant", "content": answer})
            return answer
        except Exception as e:
            return f"AI error: {e}"

# ─── Main GUI ─────────────────────────────────────────────────────────────────
class JarvisApp(tk.Tk):
    # ── Color Themes ──────────────────────────────────────────────────────────
    THEMES = {
        "dark": {
            "bg": "#0a0e1a",
            "panel": "#0f1629",
            "input_bg": "#141c2e",
            "border": "#1e2d4a",
            "accent": "#00d4ff",
            "accent2": "#0088cc",
            "text": "#e0f0ff",
            "text_dim": "#5a7a9a",
            "text_muted": "#304060",
            "jarvis_bubble": "#0d1f3a",
            "user_bubble": "#0a2040",
            "jarvis_text": "#c0e8ff",
            "user_text": "#80c8ff",
            "button_bg": "#0d2040",
            "button_hover": "#1a3a60",
            "status_ok": "#00ff88",
            "status_warn": "#ffaa00",
            "scrollbar": "#1e2d4a",
        },
    }

    def __init__(self):
        super().__init__()
        self.config_data = load_config()
        self.theme = self.THEMES["dark"]
        self.controller = SystemController()
        self.parser = CommandParser(self.controller)
        self.voice = VoiceEngine()
        self.brain = AIBrain(self.config_data.get("api_key", ""))
        self.voice_enabled = self.config_data.get("voice_enabled", False) and TTS_AVAILABLE
        self.task_queue = queue.Queue()
        self.listening = False
        self.pulse_angle = 0

        self._build_window()
        self._build_ui()
        self._start_workers()
        self._animate()
        self.after(500, self._welcome)

    # ── Window Setup ──────────────────────────────────────────────────────────
    def _build_window(self):
        self.title("JARVIS — Local AI Assistant")
        self.geometry("900x700")
        self.minsize(700, 550)
        self.configure(bg=self.theme["bg"])
        # Attempt dark title bar on Windows
        if SYSTEM == "Windows":
            try:
                self.wm_attributes("-transparentcolor", "")
            except Exception:
                pass

    # ── UI Layout ─────────────────────────────────────────────────────────────
    def _build_ui(self):
        T = self.theme

        # ── Header ──────────────────────────────────────────────────────────
        header = tk.Frame(self, bg=T["panel"], height=64)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)

        # Animated logo canvas
        self.logo_canvas = tk.Canvas(header, width=48, height=48,
                                     bg=T["panel"], highlightthickness=0)
        self.logo_canvas.pack(side=tk.LEFT, padx=(16, 8), pady=8)

        title_frame = tk.Frame(header, bg=T["panel"])
        title_frame.pack(side=tk.LEFT, pady=8)
        tk.Label(title_frame, text="JARVIS", font=("Courier", 20, "bold"),
                 fg=T["accent"], bg=T["panel"]).pack(anchor=tk.W)
        tk.Label(title_frame, text="Just A Rather Very Intelligent System",
                 font=("Courier", 8), fg=T["text_dim"], bg=T["panel"]).pack(anchor=tk.W)

        # Status indicator
        self.status_frame = tk.Frame(header, bg=T["panel"])
        self.status_frame.pack(side=tk.RIGHT, padx=16)
        self.status_dot = tk.Canvas(self.status_frame, width=10, height=10,
                                    bg=T["panel"], highlightthickness=0)
        self.status_dot.pack(side=tk.LEFT, padx=(0, 6))
        self.status_dot.create_oval(2, 2, 9, 9, fill=T["status_ok"], outline="")
        self.status_label = tk.Label(self.status_frame, text="ONLINE",
                                     font=("Courier", 8, "bold"), fg=T["status_ok"],
                                     bg=T["panel"])
        self.status_label.pack(side=tk.LEFT)

        # Settings button
        tk.Button(header, text="⚙", font=("Arial", 14), fg=T["text_dim"],
                  bg=T["panel"], activebackground=T["panel"], activeforeground=T["accent"],
                  relief=tk.FLAT, cursor="hand2",
                  command=self._open_settings).pack(side=tk.RIGHT, padx=4)

        # Voice toggle
        self.voice_btn_text = tk.StringVar(value="🔊" if self.voice_enabled else "🔇")
        tk.Button(header, textvariable=self.voice_btn_text, font=("Arial", 14),
                  fg=T["text_dim"], bg=T["panel"], activebackground=T["panel"],
                  activeforeground=T["accent"], relief=tk.FLAT, cursor="hand2",
                  command=self._toggle_voice).pack(side=tk.RIGHT, padx=4)

        # ── Main Area ────────────────────────────────────────────────────────
        main_area = tk.Frame(self, bg=T["bg"])
        main_area.pack(fill=tk.BOTH, expand=True)

        # ── Sidebar ─────────────────────────────────────────────────────────
        sidebar = tk.Frame(main_area, bg=T["panel"], width=180)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="QUICK ACTIONS", font=("Courier", 8, "bold"),
                 fg=T["text_dim"], bg=T["panel"]).pack(pady=(16, 8), padx=12, anchor=tk.W)

        self._quick_btn(sidebar, "📊  System Info", "system info")
        self._quick_btn(sidebar, "📁  Home Files", "list files")
        self._quick_btn(sidebar, "▶   Play/Pause", "play pause music")
        self._quick_btn(sidebar, "⏭   Next Track", "next song")
        self._quick_btn(sidebar, "📸  Screenshot", "screenshot")
        self._quick_btn(sidebar, "🌐  Weather", "weather")
        self._quick_btn(sidebar, "🕐  Time", "what time is it")
        self._quick_btn(sidebar, "🔍  Find File", "find file")

        tk.Frame(sidebar, bg=T["border"], height=1).pack(fill=tk.X, pady=12, padx=12)

        tk.Label(sidebar, text="APPS", font=("Courier", 8, "bold"),
                 fg=T["text_dim"], bg=T["panel"]).pack(pady=(0, 8), padx=12, anchor=tk.W)
        self._quick_btn(sidebar, "🌐  Browser", "open browser")
        self._quick_btn(sidebar, "📝  Notepad", "open notepad")
        self._quick_btn(sidebar, "🎵  Spotify", "open spotify")
        self._quick_btn(sidebar, "🖩   Calculator", "open calculator")

        # ── Chat Area ────────────────────────────────────────────────────────
        chat_frame = tk.Frame(main_area, bg=T["bg"])
        chat_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Chat display
        self.chat_display = scrolledtext.ScrolledText(
            chat_frame, wrap=tk.WORD, state=tk.DISABLED,
            bg=T["bg"], fg=T["text"], font=("Courier", 11),
            relief=tk.FLAT, padx=16, pady=12,
            insertbackground=T["accent"],
            selectbackground=T["accent2"],
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        # Tag styles
        self.chat_display.tag_configure("jarvis_name", foreground=T["accent"],
                                         font=("Courier", 9, "bold"))
        self.chat_display.tag_configure("jarvis_text", foreground=T["jarvis_text"],
                                         font=("Courier", 11))
        self.chat_display.tag_configure("user_name", foreground=T["user_text"],
                                         font=("Courier", 9, "bold"))
        self.chat_display.tag_configure("user_text", foreground=T["text"],
                                         font=("Courier", 11))
        self.chat_display.tag_configure("system_text", foreground=T["text_dim"],
                                         font=("Courier", 9, "italic"))
        self.chat_display.tag_configure("divider", foreground=T["text_muted"],
                                         font=("Courier", 8))

        # ── Input Bar ────────────────────────────────────────────────────────
        input_bar = tk.Frame(self, bg=T["input_bg"], height=60)
        input_bar.pack(fill=tk.X, side=tk.BOTTOM)
        input_bar.pack_propagate(False)

        # Mic button (if STT available)
        if STT_AVAILABLE:
            self.mic_btn = tk.Button(input_bar, text="🎤", font=("Arial", 16),
                                     fg=T["text_dim"], bg=T["input_bg"],
                                     activebackground=T["input_bg"], activeforeground=T["accent"],
                                     relief=tk.FLAT, cursor="hand2",
                                     command=self._start_listening)
            self.mic_btn.pack(side=tk.LEFT, padx=(12, 0))

        # Text input
        self.input_var = tk.StringVar()
        self.input_field = tk.Entry(input_bar, textvariable=self.input_var,
                                    font=("Courier", 12), bg=T["input_bg"],
                                    fg=T["text"], insertbackground=T["accent"],
                                    relief=tk.FLAT, highlightthickness=1,
                                    highlightcolor=T["accent"],
                                    highlightbackground=T["border"])
        self.input_field.pack(side=tk.LEFT, fill=tk.BOTH, expand=True,
                              padx=12, pady=14)
        self.input_field.bind("<Return>", self._on_send)
        self.input_field.bind("<Up>", self._history_up)
        self.input_field.bind("<Down>", self._history_down)
        self.input_field.focus_set()

        # Send button
        send_btn = tk.Button(input_bar, text="SEND ▶", font=("Courier", 10, "bold"),
                             fg=T["accent"], bg=T["button_bg"],
                             activebackground=T["button_hover"], activeforeground=T["accent"],
                             relief=tk.FLAT, cursor="hand2", padx=12,
                             command=self._on_send)
        send_btn.pack(side=tk.RIGHT, padx=12)

        # Input history
        self.input_history = []
        self.history_idx = -1

        # ── Hint bar ─────────────────────────────────────────────────────────
        hint = tk.Label(self,
                        text='Try: "open chrome" · "system info" · "play music" · "find file report" · "what time is it"',
                        font=("Courier", 8), fg=T["text_muted"], bg=T["bg"])
        hint.pack(side=tk.BOTTOM, pady=(0, 2))

    # ── Quick Action Buttons ───────────────────────────────────────────────────
    def _quick_btn(self, parent, label, command):
        T = self.theme
        btn = tk.Button(parent, text=label, font=("Courier", 9),
                        fg=T["text_dim"], bg=T["panel"],
                        activebackground=T["button_hover"], activeforeground=T["accent"],
                        relief=tk.FLAT, cursor="hand2", anchor=tk.W, padx=12, pady=4,
                        command=lambda c=command: self._inject_command(c))
        btn.pack(fill=tk.X, padx=6, pady=1)

        def on_enter(e):
            btn.config(fg=T["accent"], bg=T["button_hover"])
        def on_leave(e):
            btn.config(fg=T["text_dim"], bg=T["panel"])
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

    # ── Animated Logo ─────────────────────────────────────────────────────────
    def _animate(self):
        self.pulse_angle = (self.pulse_angle + 3) % 360
        c = self.logo_canvas
        c.delete("all")
        cx, cy, r = 24, 24, 18
        T = self.theme

        # Outer ring segments
        for i in range(8):
            start = self.pulse_angle + i * 45
            brightness = abs(math.sin(math.radians(start + self.pulse_angle)))
            alpha = int(brightness * 255)
            color = f"#{0:02x}{int(brightness * 212):02x}{int(brightness * 255):02x}"
            x1 = cx + (r - 2) * math.cos(math.radians(start))
            y1 = cy + (r - 2) * math.sin(math.radians(start))
            x2 = cx + r * math.cos(math.radians(start + 30))
            y2 = cy + r * math.sin(math.radians(start + 30))
            c.create_arc(cx - r, cy - r, cx + r, cy + r,
                         start=start, extent=35,
                         outline=color, width=2, style=tk.ARC)

        # Inner J
        c.create_text(cx, cy, text="J", font=("Courier", 14, "bold"),
                      fill=T["accent"])

        self.after(50, self._animate)

    # ── Workers ───────────────────────────────────────────────────────────────
    def _start_workers(self):
        # Response thread
        self.response_thread = threading.Thread(target=self._response_worker, daemon=True)
        self.response_thread.start()

    def _response_worker(self):
        while True:
            try:
                text = self.task_queue.get(timeout=0.5)
                self._set_status("THINKING...", self.theme["status_warn"])
                response = self._process(text)
                self._append_jarvis(response)
                if self.voice_enabled:
                    threading.Thread(target=self.voice.speak, args=(response,), daemon=True).start()
                self._set_status("ONLINE", self.theme["status_ok"])
            except queue.Empty:
                continue
            except Exception as e:
                self._append_system(f"Error: {e}")
                self._set_status("ONLINE", self.theme["status_ok"])

    # ── Command Processing ────────────────────────────────────────────────────
    def _process(self, text):
        # Try local commands first
        result = self.parser.parse(text)
        if result:
            return result
        # Fall back to AI
        return self.brain.chat(text)

    # ── Send / Input ──────────────────────────────────────────────────────────
    def _on_send(self, event=None):
        text = self.input_var.get().strip()
        if not text:
            return
        self.input_var.set("")
        self.input_history.append(text)
        self.history_idx = -1
        self._append_user(text)
        self.task_queue.put(text)

    def _inject_command(self, cmd):
        self._append_user(cmd)
        self.task_queue.put(cmd)

    def _history_up(self, event):
        if not self.input_history:
            return
        self.history_idx = min(self.history_idx + 1, len(self.input_history) - 1)
        self.input_var.set(self.input_history[-(self.history_idx + 1)])

    def _history_down(self, event):
        if self.history_idx <= 0:
            self.history_idx = -1
            self.input_var.set("")
            return
        self.history_idx -= 1
        self.input_var.set(self.input_history[-(self.history_idx + 1)])

    # ── Chat Display ──────────────────────────────────────────────────────────
    def _append_user(self, text):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, "\n")
        self.chat_display.insert(tk.END, "  YOU  ", "user_name")
        self.chat_display.insert(tk.END, f"  {text}\n", "user_text")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)

    def _append_jarvis(self, text):
        self.after(0, self.__append_jarvis_safe, text)

    def __append_jarvis_safe(self, text):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, "\n")
        self.chat_display.insert(tk.END, "  JARVIS  ", "jarvis_name")
        self.chat_display.insert(tk.END, f"  {text}\n", "jarvis_text")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)

    def _append_system(self, text):
        self.after(0, self.__append_system_safe, text)

    def __append_system_safe(self, text):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"\n  {text}\n", "system_text")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)

    # ── Status ────────────────────────────────────────────────────────────────
    def _set_status(self, text, color):
        self.after(0, lambda: (
            self.status_label.config(text=text, fg=color),
            self.status_dot.itemconfig(1, fill=color),
        ))

    # ── Voice ─────────────────────────────────────────────────────────────────
    def _toggle_voice(self):
        self.voice_enabled = not self.voice_enabled
        self.voice_btn_text.set("🔊" if self.voice_enabled else "🔇")
        self.config_data["voice_enabled"] = self.voice_enabled
        save_config(self.config_data)
        self._append_system(f"Voice {'enabled' if self.voice_enabled else 'disabled'}")

    def _start_listening(self):
        if self.listening:
            return
        if not STT_AVAILABLE:
            self._append_system("speech_recognition not installed.")
            return
        self.listening = True
        self.mic_btn.config(fg="#ff4444")
        self._append_system("Listening... (speak now)")
        threading.Thread(target=self._listen_thread, daemon=True).start()

    def _listen_thread(self):
        r = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                r.adjust_for_ambient_noise(source, duration=0.5)
                audio = r.listen(source, timeout=5, phrase_time_limit=8)
            text = r.recognize_google(audio)
            self.after(0, lambda: self._inject_command(text))
        except sr.WaitTimeoutError:
            self._append_system("Listening timed out.")
        except sr.UnknownValueError:
            self._append_system("Couldn't understand audio.")
        except Exception as e:
            self._append_system(f"Mic error: {e}")
        finally:
            self.listening = False
            if STT_AVAILABLE:
                self.after(0, lambda: self.mic_btn.config(fg=self.theme["text_dim"]))

    # ── Settings Dialog ───────────────────────────────────────────────────────
    def _open_settings(self):
        win = tk.Toplevel(self)
        win.title("JARVIS Settings")
        win.geometry("480x340")
        win.configure(bg=self.theme["panel"])
        win.transient(self)
        win.grab_set()

        T = self.theme

        tk.Label(win, text="JARVIS SETTINGS", font=("Courier", 13, "bold"),
                 fg=T["accent"], bg=T["panel"]).pack(pady=(20, 4))
        tk.Label(win, text="Configure your assistant", font=("Courier", 9),
                 fg=T["text_dim"], bg=T["panel"]).pack(pady=(0, 20))

        # API Key
        tk.Label(win, text="Anthropic API Key (for AI chat):",
                 font=("Courier", 9), fg=T["text_dim"], bg=T["panel"]).pack(anchor=tk.W, padx=24)
        api_var = tk.StringVar(value=self.config_data.get("api_key", ""))
        api_entry = tk.Entry(win, textvariable=api_var, font=("Courier", 11),
                             bg=T["input_bg"], fg=T["text"], insertbackground=T["accent"],
                             relief=tk.FLAT, show="•", width=40,
                             highlightthickness=1, highlightcolor=T["accent"],
                             highlightbackground=T["border"])
        api_entry.pack(padx=24, pady=(4, 16), fill=tk.X)

        # Show/hide key
        show_var = tk.BooleanVar(value=False)
        def toggle_show():
            api_entry.config(show="" if show_var.get() else "•")
        tk.Checkbutton(win, text="Show key", variable=show_var, command=toggle_show,
                       font=("Courier", 9), fg=T["text_dim"], bg=T["panel"],
                       selectcolor=T["input_bg"], activebackground=T["panel"],
                       activeforeground=T["text_dim"]).pack(anchor=tk.W, padx=24)

        tk.Label(win, text="Get your key at: console.anthropic.com",
                 font=("Courier", 8), fg=T["text_muted"], bg=T["panel"]).pack(anchor=tk.W, padx=24, pady=(2, 16))

        # Voice
        voice_var = tk.BooleanVar(value=self.voice_enabled)
        tk.Checkbutton(win, text="Enable voice responses (requires pyttsx3)",
                       variable=voice_var, font=("Courier", 9),
                       fg=T["text_dim"], bg=T["panel"],
                       selectcolor=T["input_bg"], activebackground=T["panel"],
                       activeforeground=T["text_dim"]).pack(anchor=tk.W, padx=24)

        def save_settings():
            self.config_data["api_key"] = api_var.get().strip()
            self.config_data["voice_enabled"] = voice_var.get()
            self.brain.api_key = self.config_data["api_key"]
            self.voice_enabled = voice_var.get() and TTS_AVAILABLE
            self.voice_btn_text.set("🔊" if self.voice_enabled else "🔇")
            save_config(self.config_data)
            self._append_system("Settings saved.")
            win.destroy()

        tk.Button(win, text="SAVE SETTINGS", font=("Courier", 10, "bold"),
                  fg=T["accent"], bg=T["button_bg"], activebackground=T["button_hover"],
                  activeforeground=T["accent"], relief=tk.FLAT, padx=16, pady=8,
                  cursor="hand2", command=save_settings).pack(pady=20)

    # ── Welcome Message ───────────────────────────────────────────────────────
    def _welcome(self):
        has_key = bool(self.config_data.get("api_key"))
        msg = (
            "JARVIS online. All systems operational.\n\n"
            f"  Platform: {SYSTEM}\n"
            f"  Voice: {'Ready' if TTS_AVAILABLE else 'Install pyttsx3'}\n"
            f"  Microphone: {'Ready' if STT_AVAILABLE else 'Install speechrecognition'}\n"
            f"  AI Chat: {'Ready' if has_key else 'Set API key in Settings ⚙'}\n\n"
            "Use the sidebar for quick actions, or type any command below.\n"
            "Say 'help' to see what I can do."
        )
        self._append_jarvis(msg)
        if self.voice_enabled:
            threading.Thread(target=self.voice.speak,
                             args=("JARVIS online. All systems ready.",), daemon=True).start()


# ── Entry Point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = JarvisApp()
    app.mainloop()