import time
import threading
import os
import sys
import random
from datetime import datetime
from typing import Optional, List, Dict, Any, Union, Callable


class ConsoleColors:
    """Erweiterte Farbdefinitionen für Rich Console"""
    
    # Basis Farben
    RED = "red"
    GREEN = "green"
    BLUE = "blue"
    YELLOW = "yellow"
    CYAN = "cyan"
    MAGENTA = "magenta"
    WHITE = "white"
    BLACK = "black"
    
    # Erweiterte Farben
    ORANGE = "orange1"
    PURPLE = "purple"
    PINK = "pink1"
    LIME = "lime"
    GOLD = "gold1"
    SILVER = "grey70"
    BRONZE = "orange3"
    
    # Spezielle Farben
    ERROR = "bright_red"
    SUCCESS = "bright_green"
    WARNING = "bright_yellow"
    INFO = "bright_blue"
    DEBUG = "bright_magenta"
    
    # Gradient Farben
    GRADIENT_FIRE = ["red", "orange1", "yellow"]
    GRADIENT_OCEAN = ["blue", "cyan", "bright_blue"]
    GRADIENT_FOREST = ["green", "lime", "bright_green"]
    GRADIENT_SUNSET = ["purple", "pink1", "orange1"]
    GRADIENT_NEON = ["bright_magenta", "bright_cyan", "bright_green"]


class ConsoleStyles:
    """Styling-Definitionen für Console-Ausgaben"""
    
    # Text Styles
    BOLD = "bold"
    ITALIC = "italic"
    UNDERLINE = "underline"
    STRIKETHROUGH = "strike"
    BLINK = "blink"
    REVERSE = "reverse"
    
    # Kombinationen
    BOLD_UNDERLINE = "bold underline"
    ITALIC_BOLD = "italic bold"
    
    # Spezielle Styles
    HEADER_STYLE = "bold bright_white on blue"
    SUBHEADER_STYLE = "bold bright_yellow"
    CODE_STYLE = "bold green on black"
    HIGHLIGHT_STYLE = "bold black on yellow"


class ConsoleIcons:
    """Unicode Icons für verschiedene Zwecke"""
    
    # Status Icons
    SUCCESS = "✅"
    ERROR = "❌"
    WARNING = "⚠️"
    INFO = "ℹ️"
    DEBUG = "🐛"
    
    # Action Icons
    LOADING = "⏳"
    PROCESSING = "⚙️"
    DOWNLOAD = "⬇️"
    UPLOAD = "⬆️"
    SAVE = "💾"
    DELETE = "🗑️"
    
    # Navigation Icons
    ARROW_RIGHT = "➡️"
    ARROW_LEFT = "⬅️"
    ARROW_UP = "⬆️"
    ARROW_DOWN = "⬇️"
    
    # Special Icons
    FIRE = "🔥"
    STAR = "⭐"
    ROCKET = "🚀"
    CROWN = "👑"
    GEM = "💎"
    LIGHTNING = "⚡"
    
    # Gaming Icons
    GAME = "🎮"
    TROPHY = "🏆"
    MEDAL = "🏅"
    TARGET = "🎯"
    DICE = "🎲"
    
    # Tech Icons
    CPU = "🖥️"
    MEMORY = "💿"
    NETWORK = "🌐"
    DATABASE = "🗄️"
    CODE = "💻"


class AnimationFrames:
    """Vordefinierte Animationsframes"""
    
    SPINNER_DOTS = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    SPINNER_LINE = ["|", "/", "-", "\\"]
    SPINNER_ARROWS = ["←", "↖", "↑", "↗", "→", "↘", "↓", "↙"]
    SPINNER_BLOCKS = ["▁", "▃", "▄", "▅", "▆", "▇", "█", "▇", "▆", "▅", "▄", "▃"]
    SPINNER_BOUNCE = ["⠁", "⠂", "⠄", "⠂"]
    SPINNER_PULSE = ["●", "○", "●", "○"]
    SPINNER_WAVE = ["▰", "▱", "▰", "▱"]
    
    LOADING_BARS = [
        "[    ]",
        "[=   ]",
        "[==  ]",
        "[=== ]",
        "[====]",
        "[ ===]",
        "[  ==]",
        "[   =]",
        "[    ]"
    ]
    
    PROGRESS_BLOCKS = ["□", "▢", "▣", "■"]
    PROGRESS_CIRCLES = ["○", "◔", "◑", "◕", "●"]
    
    # Matrix-Style Animation
    MATRIX_CHARS = ["0", "1", "⠀", "⠁", "⠃", "⠇", "⠏", "⠟", "⠿", "⡿", "⣿"]
    
    # Fire Animation
    FIRE_FRAMES = ["🔥", "🔶", "🔸", "⭐", "✨", "💫", "🌟"]
    
    # Water Animation
    WATER_FRAMES = ["💧", "💦", "🌊", "💨", "💫"]


class ConsoleAnimations:
    """Erweiterte Animationsklasse mit vielen verschiedenen Animationen"""
    
    def __init__(self, console_editor):
        self.console = console_editor
        self.rich = console_editor.rich
        self.is_running = False
        self.animation_thread = None
        
    def _clear_line(self):
        """Löscht die aktuelle Zeile"""
        print("\r" + " " * 100 + "\r", end="")
    
    def _animate_frame(self, frames: List[str], text: str, duration: float, 
                      color: str = "white", style: str = "bold"):
        """Basis-Animation mit Frames"""
        start_time = time.time()
        frame_index = 0
        
        while time.time() - start_time < duration and self.is_running:
            frame = frames[frame_index % len(frames)]
            self._clear_line()
            self.rich.print(f"[{style} {color}]{frame} {text}[/{style} {color}]", end="")
            time.sleep(0.1)
            frame_index += 1
        
        self._clear_line()
    
    def loading_spinner(self, text: str = "Loading", duration: float = 3.0, 
                       spinner_type: str = "dots", color: str = "cyan"):
        """Erweiterte Spinner-Animation"""
        self.is_running = True
        
        spinner_frames = {
            "dots": AnimationFrames.SPINNER_DOTS,
            "line": AnimationFrames.SPINNER_LINE,
            "arrows": AnimationFrames.SPINNER_ARROWS,
            "blocks": AnimationFrames.SPINNER_BLOCKS,
            "bounce": AnimationFrames.SPINNER_BOUNCE,
            "pulse": AnimationFrames.SPINNER_PULSE,
            "wave": AnimationFrames.SPINNER_WAVE
        }
        
        frames = spinner_frames.get(spinner_type, AnimationFrames.SPINNER_DOTS)
        self._animate_frame(frames, text, duration, color)
        self.is_running = False
    
    def loading_bar(self, text: str = "Processing", duration: float = 3.0, 
                   color: str = "green", width: int = 30):
        """Fortschrittsbalken-Animation"""
        self.is_running = True
        start_time = time.time()
        
        while time.time() - start_time < duration and self.is_running:
            elapsed = time.time() - start_time
            progress = min(elapsed / duration, 1.0)
            filled = int(progress * width)
            bar = "█" * filled + "░" * (width - filled)
            percentage = int(progress * 100)
            
            self._clear_line()
            self.rich.print(f"[bold {color}]{text} [{bar}] {percentage}%[/bold {color}]", end="")
            time.sleep(0.05)
        
        self._clear_line()
        self.is_running = False
    
    def loading_terminal(self, text: str = "Initializing", duration: float = 2.0):
        """Terminal-Style Loading Animation"""
        self.is_running = True
        
        terminal_frames = [
            f"$ {text}",
            f"$ {text}.",
            f"$ {text}..",
            f"$ {text}...",
            f"$ {text}....",
            f"$ {text}.....",
        ]
        
        start_time = time.time()
        frame_index = 0
        
        while time.time() - start_time < duration and self.is_running:
            self._clear_line()
            self.rich.print(f"[bold green]{terminal_frames[frame_index % len(terminal_frames)]}[/bold green]", end="")
            time.sleep(0.3)
            frame_index += 1
        
        self._clear_line()
        self.rich.print(f"[bold green]$ {text} ✓ Complete[/bold green]")
        self.is_running = False
    
    def matrix_rain(self, duration: float = 5.0, intensity: int = 50):
        """Matrix-Style Rain Animation"""
        self.is_running = True
        
        def animate():
            start_time = time.time()
            while time.time() - start_time < duration and self.is_running:
                lines = []
                for _ in range(intensity):
                    chars = ''.join(random.choice(AnimationFrames.MATRIX_CHARS) for _ in range(80))
                    color = random.choice(["green", "bright_green", "dim green"])
                    lines.append(f"[{color}]{chars}[/{color}]")
                
                os.system("cls" if os.name == "nt" else "clear")
                for line in lines[:20]:  # Limit to screen height
                    self.rich.print(line)
                time.sleep(0.1)
        
        self.animation_thread = threading.Thread(target=animate)
        self.animation_thread.start()
    
    def fire_animation(self, text: str = "SYSTEM OVERLOAD", duration: float = 3.0):
        """Feuer-Animation"""
        self.is_running = True
        start_time = time.time()
        frame_index = 0
        
        while time.time() - start_time < duration and self.is_running:
            frame = AnimationFrames.FIRE_FRAMES[frame_index % len(AnimationFrames.FIRE_FRAMES)]
            intensity = random.choice(["red", "bright_red", "orange1", "yellow"])
            
            self._clear_line()
            self.rich.print(f"[bold {intensity}]{frame} {text} {frame}[/bold {intensity}]", end="")
            time.sleep(0.2)
            frame_index += 1
        
        self._clear_line()
        self.is_running = False
    
    def typewriter(self, text: str, speed: float = 0.1, color: str = "white"):
        """Schreibmaschinen-Effekt"""
        for char in text:
            self.rich.print(f"[{color}]{char}[/{color}]", end="")
            time.sleep(speed)
        print()  # Neue Zeile am Ende
    
    def wave_text(self, text: str, duration: float = 3.0, color: str = "cyan"):
        """Wellen-Text-Animation"""
        self.is_running = True
        start_time = time.time()
        
        while time.time() - start_time < duration and self.is_running:
            wave_text = ""
            for i, char in enumerate(text):
                offset = int(time.time() * 5 + i) % 4
                if offset == 0:
                    wave_text += f"[bold bright_{color}]{char}[/bold bright_{color}]"
                elif offset == 1:
                    wave_text += f"[{color}]{char}[/{color}]"
                else:
                    wave_text += f"[dim {color}]{char}[/dim {color}]"
            
            self._clear_line()
            self.rich.print(wave_text, end="")
            time.sleep(0.1)
        
        self._clear_line()
        self.is_running = False
    
    def glitch_effect(self, text: str, duration: float = 2.0):
        """Glitch-Effekt Animation"""
        self.is_running = True
        start_time = time.time()
        original_text = text
        
        while time.time() - start_time < duration and self.is_running:
            if random.random() < 0.3:  # 30% Chance für Glitch
                glitch_text = ""
                for char in original_text:
                    if random.random() < 0.2:
                        glitch_text += random.choice("!@#$%^&*()_+-=[]{}|;:,.<>?")
                    else:
                        glitch_text += char
                
                color = random.choice(["bright_red", "bright_cyan", "bright_magenta"])
                self._clear_line()
                self.rich.print(f"[bold {color}]{glitch_text}[/bold {color}]", end="")
            else:
                self._clear_line()
                self.rich.print(f"[bold white]{original_text}[/bold white]", end="")
            
            time.sleep(0.05)
        
        self._clear_line()
        self.rich.print(f"[bold white]{original_text}[/bold white]")
        self.is_running = False
    
    def rainbow_text(self, text: str, duration: float = 3.0):
        """Regenbogen-Text Animation"""
        colors = ["red", "orange1", "yellow", "green", "cyan", "blue", "magenta"]
        self.is_running = True
        start_time = time.time()
        color_offset = 0
        
        while time.time() - start_time < duration and self.is_running:
            rainbow_text = ""
            for i, char in enumerate(text):
                color = colors[(i + color_offset) % len(colors)]
                rainbow_text += f"[bold {color}]{char}[/bold {color}]"
            
            self._clear_line()
            self.rich.print(rainbow_text, end="")
            time.sleep(0.1)
            color_offset += 1
        
        self._clear_line()
        self.is_running = False
    
    def loading_dots(self, text: str = "Loading", duration: float = 3.0, 
                    max_dots: int = 3, color: str = "yellow"):
        """Punkte-Loading Animation"""
        self.is_running = True
        start_time = time.time()
        dot_count = 0
        
        while time.time() - start_time < duration and self.is_running:
            dots = "." * dot_count
            self._clear_line()
            self.rich.print(f"[bold {color}]{text}{dots}[/bold {color}]", end="")
            time.sleep(0.5)
            dot_count = (dot_count + 1) % (max_dots + 1)
        
        self._clear_line()
        self.is_running = False
    
    def pulsing_text(self, text: str, duration: float = 3.0, color: str = "cyan"):
        """Pulsierender Text"""
        self.is_running = True
        start_time = time.time()
        
        while time.time() - start_time < duration and self.is_running:
            intensity = abs(int(time.time() * 3) % 4)
            
            if intensity == 0:
                style = f"dim {color}"
            elif intensity == 1:
                style = color
            elif intensity == 2:
                style = f"bold {color}"
            else:
                style = f"bold bright_{color}"
            
            self._clear_line()
            self.rich.print(f"[{style}]{text}[/{style}]", end="")
            time.sleep(0.2)
        
        self._clear_line()
        self.is_running = False
    
    def stop(self):
        """Stoppt alle laufenden Animationen"""
        self.is_running = False
        if self.animation_thread and self.animation_thread.is_alive():
            self.animation_thread.join()


class ConsoleParts:
    """Klasse für das Erstellen komplexer Console-Layouts"""
    
    def __init__(self, console_editor):
        self.console = console_editor
        self.rich = console_editor.rich
    
    def create_header(self, title: str, subtitle: str = None, 
                     color: str = "bright_blue", style: str = "bold"):
        """Erstellt einen formatierten Header"""
        border = "=" * 60
        
        self.rich.print(f"[{style} {color}]{border}[/{style} {color}]")
        self.rich.print(f"[{style} {color}]{title.center(60)}[/{style} {color}]")
        
        if subtitle:
            self.rich.print(f"[{color}]{subtitle.center(60)}[/{color}]")
        
        self.rich.print(f"[{style} {color}]{border}[/{style} {color}]")
        print()
    
    def create_section(self, header: str, content: List[str], 
                      header_color: str = "bright_yellow", 
                      content_color: str = "white"):
        """Erstellt einen Abschnitt mit Header und Inhalt"""
        self.rich.print(f"[bold {header_color}]▶ {header}[/bold {header_color}]")
        
        for item in content:
            self.rich.print(f"[{content_color}]  • {item}[/{content_color}]")
        print()
    
    def create_table(self, headers: List[str], rows: List[List[str]], 
                    title: str = None):
        """Erstellt eine formatierte Tabelle"""
        from rich.table import Table
        
        table = Table(title=title, show_header=True, header_style="bold magenta")
        
        for header in headers:
            table.add_column(header)
        
        for row in rows:
            table.add_row(*row)
        
        self.rich.print(table)
    
    def create_progress_display(self, tasks: Dict[str, float], 
                               title: str = "Progress Overview"):
        """Erstellt eine Fortschrittsanzeige für mehrere Tasks"""
        from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
        
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
        ) as progress:
            
            task_ids = {}
            for task_name, total in tasks.items():
                task_ids[task_name] = progress.add_task(task_name, total=total)
            
            # Simuliere Fortschritt
            for i in range(100):
                for task_name in tasks:
                    progress.update(task_ids[task_name], advance=1)
                time.sleep(0.05)
    
    def create_notification(self, message: str, notification_type: str = "info", 
                           duration: float = 3.0):
        """Erstellt eine temporäre Benachrichtigung"""
        icons = {
            "success": ConsoleIcons.SUCCESS,
            "error": ConsoleIcons.ERROR,
            "warning": ConsoleIcons.WARNING,
            "info": ConsoleIcons.INFO
        }
        
        colors = {
            "success": "bright_green",
            "error": "bright_red",
            "warning": "bright_yellow",
            "info": "bright_blue"
        }
        
        icon = icons.get(notification_type, ConsoleIcons.INFO)
        color = colors.get(notification_type, "bright_blue")
        
        self.rich.print(f"[bold {color}]{icon} {message}[/bold {color}]")
        
        if duration > 0:
            time.sleep(duration)
    
    def create_menu(self, title: str, options: List[str], 
                   selected_index: int = 0):
        """Erstellt ein interaktives Menü"""
        self.rich.print(f"[bold bright_cyan]{'='*50}[/bold bright_cyan]")
        self.rich.print(f"[bold bright_cyan]{title.center(50)}[/bold bright_cyan]")
        self.rich.print(f"[bold bright_cyan]{'='*50}[/bold bright_cyan]")
        print()
        
        for i, option in enumerate(options):
            if i == selected_index:
                self.rich.print(f"[bold bright_yellow]➤ {option}[/bold bright_yellow]")
            else:
                self.rich.print(f"[white]  {option}[/white]")
        print()
    
    def create_status_panel(self, title: str, status_items: Dict[str, str]):
        """Erstellt ein Status-Panel"""
        from rich.panel import Panel
        from rich.columns import Columns
        
        status_text = "\n".join([f"{key}: {value}" for key, value in status_items.items()])
        panel = Panel(status_text, title=title, border_style="bright_blue")
        self.rich.print(panel)
    
    def create_code_block(self, code: str, language: str = "python", 
                         title: str = None):
        """Erstellt einen formatierten Code-Block"""
        from rich.syntax import Syntax
        
        syntax = Syntax(code, language, theme="monokai", line_numbers=True)
        if title:
            from rich.panel import Panel
            panel = Panel(syntax, title=title, border_style="bright_green")
            self.rich.print(panel)
        else:
            self.rich.print(syntax)
    
    def create_alert_box(self, message: str, alert_type: str = "warning", 
                        width: int = 60):
        """Erstellt eine Alert-Box"""
        from rich.panel import Panel
        
        styles = {
            "error": ("bright_red", "❌ ERROR"),
            "warning": ("bright_yellow", "⚠️ WARNING"),
            "success": ("bright_green", "✅ SUCCESS"),
            "info": ("bright_blue", "ℹ️ INFO")
        }
        
        color, prefix = styles.get(alert_type, styles["info"])
        
        panel = Panel(
            f"[bold]{prefix}[/bold]\n\n{message}",
            border_style=color,
            width=width
        )
        self.rich.print(panel)


class ConsoleTemplates:
    """Vorgefertigte Templates für häufige Console-Ausgaben"""
    
    def __init__(self, console_editor):
        self.console = console_editor
        self.rich = console_editor.rich
        self.parts = ConsoleParts(console_editor)
    
    def startup_sequence(self, app_name: str, version: str = "1.0.0"):
        """Startup-Sequenz Template"""
        self.console.clear()
        
        # ASCII Art Header
        self.rich.print(f"""[bold bright_cyan]
╔══════════════════════════════════════════════════════════════╗
║                     {app_name.center(32)}                     ║
║                     Version {version.center(32)}                   ║
╚══════════════════════════════════════════════════════════════╝
[/bold bright_cyan]""")
        
        # Loading sequence
        self.console.animations.loading_terminal("Initializing system", 1.5)
        self.console.animations.loading_spinner("Loading modules", 2.0, "dots", "cyan")
        self.console.animations.loading_bar("Starting services", 1.5, "green")
        
        self.console.success("System ready!")
        print()
    
    def shutdown_sequence(self, app_name: str):
        """Shutdown-Sequenz Template"""
        self.console.warning("Initiating shutdown sequence...")
        
        self.console.animations.loading_spinner("Saving data", 1.0, "pulse", "yellow")
        self.console.animations.loading_spinner("Closing connections", 1.0, "wave", "orange")
        self.console.animations.loading_terminal("Cleanup", 1.0)
        
        self.rich.print(f"[bold bright_red]{'='*60}[/bold bright_red]")
        self.rich.print(f"[bold bright_red]{f'{app_name} SHUTDOWN COMPLETE'.center(60)}[/bold bright_red]")
        self.rich.print(f"[bold bright_red]{'='*60}[/bold bright_red]")
    
    def error_report(self, error_title: str, error_message: str, 
                    stack_trace: str = None):
        """Error Report Template"""
        self.console.animations.glitch_effect("SYSTEM ERROR DETECTED", 1.0)
        
        self.parts.create_alert_box(
            f"{error_title}\n\n{error_message}",
            "error",
            80
        )
        
        if stack_trace:
            self.parts.create_code_block(stack_trace, "python", "Stack Trace")
    
    def loading_screen(self, tasks: List[str]):
        """Loading Screen Template"""
        self.console.clear()
        
        for i, task in enumerate(tasks, 1):
            self.console.info(f"Step {i}/{len(tasks)}: {task}")
            self.console.animations.loading_bar(task, 2.0, "cyan")
            time.sleep(0.5)
        
        self.console.animations.fire_animation("LOADING COMPLETE", 2.0)
    
    def system_monitor(self, cpu_usage: float, memory_usage: float, 
                      disk_usage: float, network_status: str):
        """System Monitor Template"""
        status_items = {
            f"{ConsoleIcons.CPU} CPU Usage": f"{cpu_usage}%",
            f"{ConsoleIcons.MEMORY} Memory": f"{memory_usage}%",
            f"{ConsoleIcons.DATABASE} Disk": f"{disk_usage}%",
            f"{ConsoleIcons.NETWORK} Network": network_status
        }
        
        self.parts.create_status_panel("System Monitor", status_items)


class ConsoleSounds:
    """Sound-Effekte für Console (falls verfügbar)"""
    
    def __init__(self):
        self.sounds_enabled = self._check_sound_support()
    
    def _check_sound_support(self) -> bool:
        """Prüft ob Sound-Support verfügbar ist"""
        try:
            import winsound
            return True
        except ImportError:
            return False
    
    def beep(self, frequency: int = 1000, duration: int = 200):
        """Einfacher Beep-Sound"""
        if self.sounds_enabled and os.name == 'nt':
            import winsound
            winsound.Beep(frequency, duration)
    
    def success_sound(self):
        """Success Sound"""
        if self.sounds_enabled:
            self.beep(800, 200)
            time.sleep(0.1)
            self.beep(1000, 200)
    
    def error_sound(self):
        """Error Sound"""
        if self.sounds_enabled:
            self.beep(400, 500)
    
    def notification_sound(self):
        """Notification Sound"""
        if self.sounds_enabled:
            self.beep(600, 100)
            time.sleep(0.05)
            self.beep(800, 100)


class ConsoleEditor:
    """Erweiterte Console-Editor-Klasse mit umfangreichen Features"""
    
    def __init__(self, enable_sounds: bool = False):
        """
        Initialisiert den Console Editor
        
        Args:
            enable_sounds: Aktiviert Sound-Effekte (nur Windows)
        """
        try:
            from rich.console import Console
            from rich import print as rich_print
            self.rich = Console()
            self.rich_print = rich_print
        except ImportError:
            raise ImportError("Rich library is required. Install with: pip install rich")
        
        # Komponenten initialisieren
        self.animations = ConsoleAnimations(self)
        self.parts = ConsoleParts(self)
        self.templates = ConsoleTemplates(self)
        self.sounds = ConsoleSounds() if enable_sounds else None
        
        # Interne Variablen
        self.message = ""
        self.last_message_type = ""
        self.message_history = []
        self.debug_mode = False
        
        # Style-Konfiguration
        self.colors = ConsoleColors()
        self.styles = ConsoleStyles()
        self.icons = ConsoleIcons()
    
    # ==================== ERWEITERTE BASISFUNKTIONEN ====================
    
    def set_debug_mode(self, enabled: bool):
        """Aktiviert/Deaktiviert Debug-Modus"""
        self.debug_mode = enabled
        if enabled:
            self.debug("Debug mode activated")
    
    def log_message(self, message: str, message_type: str):
        """Protokolliert Nachrichten"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.message_history.append({
            "timestamp": timestamp,
            "type": message_type,
            "message": message
        })
        
        # Begrenze History auf 100 Einträge
        if len(self.message_history) > 100:
            self.message_history.pop(0)
    
    def get_message_history(self) -> List[Dict[str, str]]:
        """Gibt die Nachrichten-Historie zurück"""
        return self.message_history.copy()
    
    def clear_history(self):
        """Löscht die Nachrichten-Historie"""
        self.message_history.clear()
    
    # ==================== ERWEITERTE LOGGING-FUNKTIONEN ====================
    
    def error(self, message: str, play_sound: bool = True):
        """Erweiterte Error-Ausgabe"""
        self.message = message
        self.last_message_type = "error"
        self.log_message(message, "error")
        
        if play_sound and self.sounds:
            self.sounds.error_sound()
        
        self.rich_print(f"[bold {self.colors.ERROR}]{self.icons.ERROR} Error:[/bold {self.colors.ERROR}] [{self.colors.ERROR}]{message}[/{self.colors.ERROR}]")
    
    def success(self, message: str, play_sound: bool = True):
        """Erweiterte Success-Ausgabe"""
        self.message = message
        self.last_message_type = "success"
        self.log_message(message, "success")
        
        if play_sound and self.sounds:
            self.sounds.success_sound()
        
        self.rich_print(f"[bold {self.colors.SUCCESS}]{self.icons.SUCCESS} Success:[/bold {self.colors.SUCCESS}] [{self.colors.SUCCESS}]{message}[/{self.colors.SUCCESS}]")
    
    def warning(self, message: str):
        """Erweiterte Warning-Ausgabe"""
        self.message = message
        self.last_message_type = "warning"
        self.log_message(message, "warning")
        
        self.rich_print(f"[bold {self.colors.WARNING}]{self.icons.WARNING} Warning:[/bold {self.colors.WARNING}] [{self.colors.WARNING}]{message}[/{self.colors.WARNING}]")
    
    def info(self, message: str, play_sound: bool = False):
        """Erweiterte Info-Ausgabe"""
        self.message = message
        self.last_message_type = "info"
        self.log_message(message, "info")
        
        if play_sound and self.sounds:
            self.sounds.notification_sound()
        
        self.rich_print(f"[bold {self.colors.INFO}]{self.icons.INFO} Info:[/bold {self.colors.INFO}] [{self.colors.INFO}]{message}[/{self.colors.INFO}]")
    
    def debug(self, message: str):
        """Debug-Ausgabe (nur wenn Debug-Modus aktiv)"""
        if not self.debug_mode:
            return
        
        self.message = message
        self.last_message_type = "debug"
        self.log_message(message, "debug")
        
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.rich_print(f"[bold {self.colors.DEBUG}]{self.icons.DEBUG} DEBUG [{timestamp}]:[/bold {self.colors.DEBUG}] [{self.colors.DEBUG}]{message}[/{self.colors.DEBUG}]")
    
    # ==================== FARBFUNKTIONEN ====================
    
    def _color_print(self, message: str, color: str, style: str = "bold"):
        """Interne Farbdruck-Funktion"""
        self.message = message
        self.rich_print(f"[{style} {color}]{message}[/{style} {color}]")
    
    def red(self, message: str, style: str = "bold"):
        """Rote Ausgabe"""
        self._color_print(message, self.colors.RED, style)
    
    def green(self, message: str, style: str = "bold"):
        """Grüne Ausgabe"""
        self._color_print(message, self.colors.GREEN, style)
    
    def blue(self, message: str, style: str = "bold"):
        """Blaue Ausgabe"""
        self._color_print(message, self.colors.BLUE, style)
    
    def yellow(self, message: str, style: str = "bold"):
        """Gelbe Ausgabe"""
        self._color_print(message, self.colors.YELLOW, style)
    
    def cyan(self, message: str, style: str = "bold"):
        """Cyan Ausgabe"""
        self._color_print(message, self.colors.CYAN, style)
    
    def magenta(self, message: str, style: str = "bold"):
        """Magenta Ausgabe"""
        self._color_print(message, self.colors.MAGENTA, style)
    
    def orange(self, message: str, style: str = "bold"):
        """Orange Ausgabe"""
        self._color_print(message, self.colors.ORANGE, style)
    
    def purple(self, message: str, style: str = "bold"):
        """Lila Ausgabe"""
        self._color_print(message, self.colors.PURPLE, style)
    
    def pink(self, message: str, style: str = "bold"):
        """Rosa Ausgabe"""
        self._color_print(message, self.colors.PINK, style)
    
    def gold(self, message: str, style: str = "bold"):
        """Gold Ausgabe"""
        self._color_print(message, self.colors.GOLD, style)
    
    def silver(self, message: str, style: str = "bold"):
        """Silber Ausgabe"""
        self._color_print(message, self.colors.SILVER, style)
    
    # ==================== GRADIENT-FUNKTIONEN ====================
    
    def gradient_text(self, text: str, colors: List[str], style: str = "bold"):
        """Erstellt Gradient-Text"""
        if len(colors) < 2:
            self.rich_print(f"[{style} {colors[0] if colors else 'white'}]{text}[/{style} {colors[0] if colors else 'white'}]")
            return
        
        text_length = len(text)
        gradient_text = ""
        
        for i, char in enumerate(text):
            # Berechne Position im Gradient (0.0 bis 1.0)
            position = i / max(text_length - 1, 1)
            
            # Finde die zwei Farben zwischen denen interpoliert wird
            color_position = position * (len(colors) - 1)
            color_index = int(color_position)
            
            if color_index >= len(colors) - 1:
                color = colors[-1]
            else:
                color = colors[color_index]
            
            gradient_text += f"[{style} {color}]{char}[/{style} {color}]"
        
        self.rich_print(gradient_text)
    
    def fire_gradient(self, text: str):
        """Feuer-Gradient"""
        self.gradient_text(text, self.colors.GRADIENT_FIRE)
    
    def ocean_gradient(self, text: str):
        """Ozean-Gradient"""
        self.gradient_text(text, self.colors.GRADIENT_OCEAN)
    
    def forest_gradient(self, text: str):
        """Wald-Gradient"""
        self.gradient_text(text, self.colors.GRADIENT_FOREST)
    
    def sunset_gradient(self, text: str):
        """Sonnenuntergang-Gradient"""
        self.gradient_text(text, self.colors.GRADIENT_SUNSET)
    
    def neon_gradient(self, text: str):
        """Neon-Gradient"""
        self.gradient_text(text, self.colors.GRADIENT_NEON)
    
    # ==================== ERWEITERTE CREATE-FUNKTIONEN ====================
    
    def create(self, header: str = None, subline: str = None, 
              messages: List[str] = None, header_color: str = "bright_blue",
              subline_color: str = "cyan", message_color: str = "white",
              separator: str = " | "):
        """
        Erweiterte Create-Funktion für komplexe Ausgaben
        
        Args:
            header: Hauptüberschrift
            subline: Unterüberschrift
            messages: Liste von Nachrichten
            header_color: Farbe der Hauptüberschrift
            subline_color: Farbe der Unterüberschrift
            message_color: Farbe der Nachrichten
            separator: Trennzeichen zwischen Nachrichten
        """
        
        if header:
            self.rich_print(f"[bold {header_color}]{'='*60}[/bold {header_color}]")
            self.rich_print(f"[bold {header_color}]{header.center(60)}[/bold {header_color}]")
            
            if subline:
                self.rich_print(f"[{subline_color}]{subline.center(60)}[/{subline_color}]")
            
            self.rich_print(f"[bold {header_color}]{'='*60}[/bold {header_color}]")
            print()
        
        if messages:
            if len(messages) == 1:
                self.rich_print(f"[{message_color}]{messages[0]}[/{message_color}]")
            else:
                combined_message = separator.join(messages)
                self.rich_print(f"[{message_color}]{combined_message}[/{message_color}]")
    
    def create_advanced(self, **kwargs):
        """
        Erweiterte Create-Funktion mit vielen Optionen
        
        Kwargs:
            title: Titel
            content: Inhalt (str oder List[str])
            style: Stil (header, panel, simple)
            color: Hauptfarbe
            border: Border-Stil (für Panel)
            icon: Icon vor dem Titel
            timestamp: Zeitstempel hinzufügen
            highlight: Text hervorheben
        """
        
        title = kwargs.get('title', '')
        content = kwargs.get('content', '')
        style = kwargs.get('style', 'simple')
        color = kwargs.get('color', 'white')
        border = kwargs.get('border', 'bright_blue')
        icon = kwargs.get('icon', '')
        timestamp = kwargs.get('timestamp', False)
        highlight = kwargs.get('highlight', False)
        
        # Zeitstempel hinzufügen
        if timestamp:
            current_time = datetime.now().strftime("%H:%M:%S")
            title = f"[{current_time}] {title}"
        
        # Icon hinzufügen
        if icon:
            title = f"{icon} {title}"
        
        if style == 'header':
            self.parts.create_header(title, content if isinstance(content, str) else None, color)
            if isinstance(content, list):
                for item in content:
                    self.rich_print(f"[{color}]  • {item}[/{color}]")
        
        elif style == 'panel':
            from rich.panel import Panel
            
            if isinstance(content, list):
                content_text = '\n'.join(content)
            else:
                content_text = str(content)
            
            if highlight:
                content_text = f"[bold]{content_text}[/bold]"
            
            panel = Panel(content_text, title=title, border_style=border)
            self.rich_print(panel)
        
        else:  # simple
            if title:
                style_str = f"bold {color}" if highlight else color
                self.rich_print(f"[{style_str}]{title}[/{style_str}]")
            
            if isinstance(content, list):
                for item in content:
                    self.rich_print(f"[{color}]  {item}[/{color}]")
            elif content:
                self.rich_print(f"[{color}]{content}[/{color}]")
    
    # ==================== UTILITY-FUNKTIONEN ====================
    
    def clear(self):
        """Löscht die Konsole"""
        os.system("cls" if os.name == "nt" else "clear")
    
    def pause(self, message: str = "Press Enter to continue..."):
        """Wartet auf Benutzereingabe"""
        self.rich_print(f"[dim yellow]{message}[/dim yellow]")
        input()
    
    def countdown(self, seconds: int, message: str = "Starting in"):
        """Countdown-Timer"""
        for i in range(seconds, 0, -1):
            print(f"\r[bold yellow]{message} {i}s...[/bold yellow]", end="")
            time.sleep(1)
        print(f"\r[bold green]{message} NOW!    [/bold green]")
    
    def separator(self, char: str = "=", length: int = 60, color: str = "bright_blue"):
        """Erstellt eine Trennlinie"""
        self.rich_print(f"[{color}]{char * length}[/{color}]")
    
    def banner(self, text: str, char: str = "*", color: str = "bright_cyan"):
        """Erstellt einen Banner um Text"""
        length = len(text) + 4
        border = char * length
        
        self.rich_print(f"[bold {color}]{border}[/bold {color}]")
        self.rich_print(f"[bold {color}]{char} {text} {char}[/bold {color}]")
        self.rich_print(f"[bold {color}]{border}[/bold {color}]")
    
    def progress_indicator(self, current: int, total: int, 
                          prefix: str = "Progress", 
                          suffix: str = "Complete", 
                          length: int = 30):
        """Einfacher Fortschrittsindikator"""
        percent = round(100 * (current / float(total)), 1)
        filled_length = int(length * current // total)
        bar = '█' * filled_length + '-' * (length - filled_length)
        
        self.rich_print(f"[cyan]{prefix} |{bar}| {percent}% {suffix}[/cyan]")
    
    # ==================== INTERAKTIVE FUNKTIONEN ====================
    
    def ask_choice(self, question: str, choices: List[str], 
                  default: int = 0) -> int:
        """Stellt eine Multiple-Choice-Frage"""
        self.rich_print(f"[bold bright_cyan]{question}[/bold bright_cyan]")
        print()
        
        for i, choice in enumerate(choices):
            marker = "●" if i == default else "○"
            self.rich_print(f"[yellow]{i+1}.[/yellow] [{marker}] {choice}")
        
        print()
        while True:
            try:
                answer = input("Your choice (number): ").strip()
                if not answer:
                    return default
                
                choice_num = int(answer) - 1
                if 0 <= choice_num < len(choices):
                    return choice_num
                else:
                    self.error("Invalid choice. Please try again.")
            except ValueError:
                self.error("Please enter a valid number.")
    
    def ask_yes_no(self, question: str, default: bool = True) -> bool:
        """Stellt eine Ja/Nein-Frage"""
        default_str = "Y/n" if default else "y/N"
        
        while True:
            answer = input(f"{question} ({default_str}): ").strip().lower()
            
            if not answer:
                return default
            elif answer in ['y', 'yes', 'ja', 'j']:
                return True
            elif answer in ['n', 'no', 'nein']:
                return False
            else:
                self.error("Please answer with yes/no (y/n)")
    
    def ask_input(self, question: str, default: str = None, 
                 required: bool = True) -> str:
        """Fragt nach Benutzereingabe"""
        prompt = question
        if default:
            prompt += f" (default: {default})"
        prompt += ": "
        
        while True:
            answer = input(prompt).strip()
            
            if answer:
                return answer
            elif default is not None:
                return default
            elif not required:
                return ""
            else:
                self.error("This field is required.")
    
    # ==================== SPEZIAL-EFFEKTE ====================
    
    def celebration(self, message: str = "SUCCESS!", duration: float = 3.0):
        """Feier-Animation"""
        self.animations.fire_animation(message, duration)
        if self.sounds:
            self.sounds.success_sound()
    
    def dramatic_reveal(self, text: str, delay: float = 0.1):
        """Dramatische Text-Enthüllung"""
        self.animations.typewriter(text, delay, "bright_white")
    
    def system_alert(self, message: str, level: str = "warning"):
        """System-Alert mit Animation"""
        if level == "critical":
            self.animations.glitch_effect(f"CRITICAL: {message}", 2.0)
        else:
            self.animations.pulsing_text(f"ALERT: {message}", 2.0, "bright_red")
    
    # ==================== VORLAGEN & TEMPLATES ====================
    
    def loading_sequence(self, tasks: List[str]):
        """Standard Loading-Sequenz"""
        self.templates.loading_screen(tasks)
    
    def startup(self, app_name: str, version: str = "1.0.0"):
        """Standard Startup-Sequenz"""
        self.templates.startup_sequence(app_name, version)
    
    def shutdown(self, app_name: str):
        """Standard Shutdown-Sequenz"""
        self.templates.shutdown_sequence(app_name)
    
    def show_system_info(self):
        """Zeigt System-Informationen"""
        import platform
        import psutil
        
        info = {
            "System": platform.system(),
            "Platform": platform.platform(),
            "Processor": platform.processor(),
            "Python": platform.python_version(),
            "CPU Cores": str(psutil.cpu_count()),
            "Memory": f"{psutil.virtual_memory().total // (1024**3)} GB"
        }
        
        self.parts.create_status_panel("System Information", info)
    
    # ==================== ERWEITERTE DEBUGGING-FUNKTIONEN ====================
    
    def debug_trace(self, function_name: str, args: tuple = (), 
                   kwargs: dict = None):
        """Debug-Trace für Funktionsaufrufe"""
        if not self.debug_mode:
            return
        
        kwargs = kwargs or {}
        args_str = ', '.join(map(str, args))
        kwargs_str = ', '.join(f"{k}={v}" for k, v in kwargs.items())
        
        all_args = ', '.join(filter(None, [args_str, kwargs_str]))
        self.debug(f"TRACE: {function_name}({all_args})")
    
    def debug_var(self, name: str, value: Any):
        """Debug-Ausgabe für Variablen"""
        if not self.debug_mode:
            return
        
        self.debug(f"VAR: {name} = {repr(value)} (type: {type(value).__name__})")
    
    def debug_section(self, section_name: str):
        """Debug-Sektion-Marker"""
        if not self.debug_mode:
            return
        
        self.debug(f"SECTION: {section_name}")
        self.separator("-", 40, "dim magenta")
    
    # ==================== PERFORMANCE-MONITORING ====================
    
    def performance_monitor(self):
        """Einfacher Performance-Monitor"""
        try:
            import psutil
            
            cpu = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            self.templates.system_monitor(
                cpu_usage=cpu,
                memory_usage=memory.percent,
                disk_usage=disk.percent,
                network_status="Connected"
            )
        except ImportError:
            self.warning("psutil not available. Install with: pip install psutil")
    
    # ==================== KONFIGURATION ====================
    
    def set_theme(self, theme_name: str):
        """Setzt ein vordefiniertes Farbthema"""
        themes = {
            "dark": {
                "primary": "bright_white",
                "secondary": "bright_blue",
                "success": "bright_green",
                "warning": "bright_yellow",
                "error": "bright_red"
            },
            "neon": {
                "primary": "bright_cyan",
                "secondary": "bright_magenta",
                "success": "bright_green",
                "warning": "bright_yellow",
                "error": "bright_red"
            },
            "retro": {
                "primary": "bright_green",
                "secondary": "green",
                "success": "bright_green",
                "warning": "yellow",
                "error": "red"
            }
        }
        
        if theme_name in themes:
            theme = themes[theme_name]
            self.colors.SUCCESS = theme["success"]
            self.colors.WARNING = theme["warning"]
            self.colors.ERROR = theme["error"]
            self.colors.INFO = theme["secondary"]
            
            self.success(f"Theme '{theme_name}' activated!")
        else:
            self.error(f"Unknown theme: {theme_name}")
            self.info(f"Available themes: {', '.join(themes.keys())}")


# ==================== HAUPTKLASSEN-ALIASE ====================

# Für Rückwärtskompatibilität
Console = ConsoleEditor
Animations = ConsoleAnimations
Parts = ConsoleParts
Templates = ConsoleTemplates


# ==================== BEISPIEL-USAGE ====================

if __name__ == "__main__":
    # Beispiel für die Verwendung des erweiterten Console Editors
    console = ConsoleEditor(enable_sounds=True)
    console.set_debug_mode(True)
    
    # Startup-Sequenz
    console.startup("Advanced Console System", "2.0.0")
    
    # Verschiedene Nachrichten-Typen
    console.success("System initialized successfully!")
    console.warning("This is a warning message")
    console.error("This is an error message")
    console.info("This is an info message")
    console.debug("This is a debug message")
    
    # Farbige Ausgaben
    console.fire_gradient("FIRE GRADIENT TEXT")
    console.ocean_gradient("OCEAN GRADIENT TEXT")
    console.neon_gradient("NEON GRADIENT TEXT")
    
    # Animationen
    console.animations.loading_spinner("Loading data", 2.0, "dots", "cyan")
    console.animations.loading_bar("Processing", 2.0, "green")
    console.animations.rainbow_text("RAINBOW ANIMATION", 3.0)
    console.animations.typewriter("This text appears character by character", 0.05)
    
    # Komplexe Ausgaben
    console.create_advanced(
        title="System Status",
        content=["All systems operational", "Performance: Optimal", "Security: Active"],
        style="panel",
        color="bright_green",
        icon=console.icons.SUCCESS,
        timestamp=True
    )
    
    # Alert-Box
    console.parts.create_alert_box(
        "This is an important system notification!",
        "info"
    )
    
    # Performance-Monitor (falls psutil verfügbar)
    try:
        console.performance_monitor()
    except:
        console.info("Performance monitoring requires psutil")
    
    # Interaktive Eingabe
    # user_choice = console.ask_choice("What would you like to do?", 
    #                                 ["Option 1", "Option 2", "Option 3"])
    # console.info(f"You selected option {user_choice + 1}")
    
    # Shutdown-Sequenz
    console.pause("Press Enter to shutdown...")
    console.shutdown("Advanced Console System")
