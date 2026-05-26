import os
import sys
import time
import threading
import shutil

# Force stdout/stderr to UTF-8 for emoji support on Windows consoles
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

# Initialize ANSI processing on Windows console
if os.name == "nt":
    try:
        os.system("")
    except Exception:
        pass

# Sleek ANSI Palette (Sleek Dark Mode / Vibrant accents)
class Colors:
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    MAGENTA = "\033[95m"
    BLUE = "\033[94m"
    GRAY = "\033[90m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    RESET = "\033[0m"
    CLEAR_LINE = "\033[K"
    HIDE_CURSOR = "\033[?25l"
    SHOW_CURSOR = "\033[?25h"

# Premium Log Helpers
def print_logo():
    logo = f"""
{Colors.CYAN}{Colors.BOLD}  _____         {Colors.MAGENTA} _____  _     
{Colors.CYAN}{Colors.BOLD} |  __ \\        {Colors.MAGENTA}|  __ \\| |    
{Colors.CYAN}{Colors.BOLD} | |__) | _   _ {Colors.MAGENTA}| |  \\/| | __ 
{Colors.CYAN}{Colors.BOLD} |  ___/ | | | |{Colors.MAGENTA}| | __ | |/ / 
{Colors.CYAN}{Colors.BOLD} | |     | |_| |{Colors.MAGENTA}| |__\\ \\   <  
{Colors.CYAN}{Colors.BOLD} |_|      \\__, |{Colors.MAGENTA} \\____/|_|\\_\\ 
{Colors.CYAN}{Colors.BOLD}           __/ |                      
{Colors.CYAN}{Colors.BOLD}          |___/                       {Colors.RESET}
{Colors.GRAY}⚡ Modern Python Package Manager & Runtime Toolkit{Colors.RESET}
"""
    print(logo)

def log_success(msg):
    print(f"{Colors.GREEN}✔{Colors.RESET} {msg}")

def log_info(msg):
    print(f"{Colors.BLUE}ℹ{Colors.RESET} {msg}")

def log_warning(msg):
    print(f"{Colors.YELLOW}⚠{Colors.RESET} {msg}")

def log_error(msg):
    print(f"{Colors.RED}✖{Colors.RESET} {Colors.RED}{msg}{Colors.RESET}")

def log_step(step, total, msg):
    print(f"{Colors.GRAY}[{step}/{total}]{Colors.RESET} {msg}")

# Animated Console Spinner (Threaded)
class Spinner:
    def __init__(self, message="Working..."):
        self.message = message
        self.frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.running = False
        self._thread = None

    def _spin(self):
        idx = 0
        sys.stdout.write(Colors.HIDE_CURSOR)
        while self.running:
            frame = self.frames[idx % len(self.frames)]
            sys.stdout.write(f"\r{Colors.CYAN}{frame}{Colors.RESET} {self.message}")
            sys.stdout.flush()
            idx += 1
            time.sleep(0.08)
        # Clean line on stop
        sys.stdout.write(f"\r{Colors.CLEAR_LINE}")
        sys.stdout.write(Colors.SHOW_CURSOR)
        sys.stdout.flush()

    def start(self, new_message=None):
        if new_message:
            self.message = new_message
        if not self.running:
            self.running = True
            self._thread = threading.Thread(target=self._spin, daemon=True)
            self._thread.start()

    def stop(self, success=True, finish_message=None):
        if self.running:
            self.running = False
            if self._thread:
                self._thread.join()
            
            # Print final status line
            if finish_message:
                if success:
                    log_success(finish_message)
                else:
                    log_error(finish_message)

# Arrow Key Grabber (Cross-Platform)
def get_key():
    if os.name == "nt":
        import msvcrt
        ch = msvcrt.getch()
        if ch in (b"\x00", b"\xe0"):  # Windows arrow keys prefix
            ch2 = msvcrt.getch()
            if ch2 == b"H": return "up"
            if ch2 == b"P": return "down"
            if ch2 == b"K": return "left"
            if ch2 == b"M": return "right"
        if ch == b"\r": return "enter"
        if ch == b"\x03": raise KeyboardInterrupt()
        try:
            return ch.decode("utf-8", errors="ignore")
        except Exception:
            return ""
    else:
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
            if ch == "\x1b":
                ch2 = sys.stdin.read(2)
                if ch2 == "[A": return "up"
                if ch2 == "[B": return "down"
                if ch2 == "[D": return "left"
                if ch2 == "[C": return "right"
            if ch in ("\r", "\n"): return "enter"
            if ch == "\x03": raise KeyboardInterrupt()
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

# Interactive Vite-like prompts
def ask_text(prompt_text, default=""):
    try:
        suffix = f" {Colors.GRAY}({default}){Colors.RESET}" if default else ""
        sys.stdout.write(f"{Colors.BOLD}?{Colors.RESET} {prompt_text}{suffix}: ")
        sys.stdout.flush()
        user_val = input().strip()
        return user_val if user_val else default
    except (KeyboardInterrupt, EOFError):
        print()
        log_error("Operation aborted.")
        sys.exit(1)

def ask_confirm(prompt_text, default=True):
    try:
        opts = " [Y/n] " if default else " [y/N] "
        sys.stdout.write(f"{Colors.BOLD}?{Colors.RESET} {prompt_text}{Colors.CYAN}{opts}{Colors.RESET}")
        sys.stdout.flush()
        user_val = input().strip().lower()
        if not user_val:
            return default
        return user_val.startswith("y")
    except (KeyboardInterrupt, EOFError):
        print()
        log_error("Operation aborted.")
        sys.exit(1)

def ask_select(prompt_text, options, default_idx=0):
    """
    Renders a stunning interactive keyboard menu where options are selected
    with UP/DOWN arrow keys, featuring dynamic text changes!
    """
    current_idx = default_idx
    sys.stdout.write(Colors.HIDE_CURSOR)
    sys.stdout.flush()
    
    try:
        # We will loop and rewrite the menu on arrow-key actions
        while True:
            # Render menu
            print(f"{Colors.CYAN}?{Colors.RESET} {Colors.BOLD}{prompt_text}{Colors.RESET} {Colors.GRAY}(Use arrow keys){Colors.RESET}")
            for idx, opt in enumerate(options):
                if idx == current_idx:
                    print(f" {Colors.CYAN}❯ {Colors.BOLD}{Colors.UNDERLINE}{opt}{Colors.RESET}")
                else:
                    print(f"   {Colors.GRAY}{opt}{Colors.RESET}")
            
            # Flush changes
            sys.stdout.flush()
            
            # Wait for keystroke
            key = get_key()
            
            # Clear printed lines for redraw (number of options + prompt line)
            lines_to_clear = len(options) + 1
            sys.stdout.write(f"\033[{lines_to_clear}A")
            for _ in range(lines_to_clear):
                sys.stdout.write(Colors.CLEAR_LINE + "\n")
            sys.stdout.write(f"\033[{lines_to_clear}A")
            sys.stdout.flush()
            
            # Handle key logic
            if key == "up":
                current_idx = (current_idx - 1) % len(options)
            elif key == "down":
                current_idx = (current_idx + 1) % len(options)
            elif key == "enter":
                # Confirm and show selection
                print(f"{Colors.GREEN}✔{Colors.RESET} {Colors.BOLD}{prompt_text}{Colors.RESET} {Colors.CYAN}❯ {options[current_idx]}{Colors.RESET}")
                sys.stdout.write(Colors.SHOW_CURSOR)
                sys.stdout.flush()
                return options[current_idx]
    except KeyboardInterrupt:
        # Restore cursor and exit
        sys.stdout.write(Colors.SHOW_CURSOR)
        sys.stdout.write("\n")
        sys.stdout.flush()
        log_error("Operation aborted.")
        sys.exit(1)
