#!/usr/bin/env python3
"""🌟 THE ULTIMATE SNAZZY HELLO WORLD V8 🌟.

Prepare for the most epic hello world experience of your life!
"""

import os
import random
import time
from itertools import cycle

try:
    from colorama import Back, Fore, Style, init

    init(autoreset=True)
    COLORS_AVAILABLE = True
except ImportError:
    COLORS_AVAILABLE = False

    # Fallback for no colorama
    class Fore:
        """Fallback Fore class when colorama is not available."""

        RED = YELLOW = GREEN = CYAN = BLUE = MAGENTA = WHITE = BLACK = ""
        LIGHTRED_EX = LIGHTYELLOW_EX = LIGHTGREEN_EX = LIGHTCYAN_EX = ""
        LIGHTBLUE_EX = LIGHTMAGENTA_EX = LIGHTWHITE_EX = ""

    class Back:
        """Fallback Back class when colorama is not available."""

        RED = YELLOW = GREEN = CYAN = BLUE = MAGENTA = WHITE = BLACK = ""

    class Style:
        """Fallback Style class when colorama is not available."""

        BRIGHT = DIM = NORMAL = RESET_ALL = ""


# ASCII Art definitions
HELLO_ASCII = r"""
██╗  ██╗███████╗██╗     ██╗      ██████╗
██║  ██║██╔════╝██║     ██║     ██╔═══██╗
███████║█████╗  ██║     ██║     ██║   ██║
██╔══██║██╔══╝  ██║     ██║     ██║   ██║
██║  ██║███████╗███████╗███████╗╚██████╔╝
╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝ ╚═════╝
"""

WORLD_ASCII = r"""
██╗    ██╗ ██████╗ ██████╗ ██╗     ██████╗
██║    ██║██╔═══██╗██╔══██╗██║     ██╔══██╗
██║ █╗ ██║██║   ██║██████╔╝██║     ██║  ██║
██║███╗██║██║   ██║██╔══██╗██║     ██║  ██║
╚███╔███╔╝╚██████╔╝██║  ██║███████╗██████╔╝
 ╚══╝╚══╝  ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═════╝
"""

V8_ASCII = r"""
██╗   ██╗ █████╗
██║   ██║██╔══██╗
██║   ██║╚█████╔╝
╚██╗ ██╔╝██╔══██╗
 ╚████╔╝ ╚█████╔╝
  ╚═══╝   ╚════╝
"""

EARTH_ASCII = r"""
        _____
     ,o88888888o,
   ,8888888888888,
  ,88888888888888,
  88888888888888888
  88888888888888888
  `8888888888888'
   `888888888888'
     `"88888"'
"""

ROCKET_ASCII = r"""
     /\
    /  \
   |    |
   | V8 |
   |    |
  /|/\/\|\
 /_||  ||_\
    ||||
   / || \
  /  \/  \
 /__/  \__\
"""

FIREWORKS = [
    r"""
    . * .  . *       *
  *  * . * BOOM! * .  *
    . * .  . *       *
""",
    r"""
       \  |  /
     --  ★  --
       /  |  \
""",
    r"""
    ✨ ✨ ✨
   ✨  🎆  ✨
    ✨ ✨ ✨
""",
]


def clear_screen():
    """Clear the terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


def print_centered(text: str, color: str = ""):
    """Print text centered on the screen."""
    terminal_width = os.get_terminal_size().columns
    for line in text.split("\n"):
        if line.strip():
            padding = (terminal_width - len(line)) // 2
            print(" " * padding + color + line + Style.RESET_ALL)
        else:
            print()


def type_text(text: str, delay: float = 0.05, color: str = ""):
    """Type text character by character with delay."""
    for char in text:
        print(color + char, end="", flush=True)
        time.sleep(delay)
    print(Style.RESET_ALL)


def rainbow_text(text: str, delay: float = 0.01):
    """Print text with rainbow colors."""
    colors = [Fore.RED, Fore.YELLOW, Fore.GREEN, Fore.CYAN, Fore.BLUE, Fore.MAGENTA]
    color_cycle = cycle(colors)

    for char in text:
        print(next(color_cycle) + Style.BRIGHT + char, end="", flush=True)
        time.sleep(delay)
    print(Style.RESET_ALL)


def matrix_rain(duration: float = 2.0):
    """Create a matrix-like rain effect."""
    width = os.get_terminal_size().columns
    clear_screen()

    chars = "01ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝ"
    columns = [random.randint(0, 20) for _ in range(width)]

    start_time = time.time()
    while time.time() - start_time < duration:
        output = []
        for i in range(20):
            line = ""
            for j in range(width):
                if columns[j] > i:
                    char = random.choice(chars)
                    if columns[j] - i < 3:
                        line += Fore.LIGHTGREEN_EX + char
                    else:
                        line += Fore.GREEN + Style.DIM + char
                else:
                    line += " "
            output.append(line)

        clear_screen()
        print("\n".join(output))

        for j in range(width):
            if random.random() > 0.95:
                columns[j] = 0
            else:
                columns[j] += 1
                if columns[j] > 25:
                    columns[j] = 0

        time.sleep(0.05)


def loading_animation(message: str = "Loading V8 Engine", duration: float = 2.0):
    """Show a loading animation."""
    animation = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    start_time = time.time()
    i = 0

    while time.time() - start_time < duration:
        print(f"\r{Fore.CYAN}{animation[i % len(animation)]} {message}...", end="", flush=True)
        time.sleep(0.1)
        i += 1
    print("\r" + " " * (len(message) + 10) + "\r", end="", flush=True)


def particle_explosion(x: int, y: int):
    """Create a particle explosion effect."""
    particles = ["*", "✦", "✧", "⋆", "○", "◉", "◎", "◈"]
    colors = [Fore.RED, Fore.YELLOW, Fore.GREEN, Fore.CYAN, Fore.MAGENTA, Fore.WHITE]

    for frame in range(5):
        clear_screen()
        radius = frame * 2 + 1

        for dy in range(-radius, radius + 1):
            for dx in range(-radius * 2, radius * 2 + 1, 2):
                dist = (dx / 2) ** 2 + dy**2
                if dist <= radius**2 and dist >= (radius - 1) ** 2:
                    px, py = x + dx, y + dy
                    if 0 <= px < 80 and 0 <= py < 20:
                        print(
                            f"\033[{py};{px}H{random.choice(colors)}{random.choice(particles)}",
                            end="",
                        )

        time.sleep(0.1)


def show_fireworks():
    """Display animated fireworks."""
    for _ in range(3):
        firework = random.choice(FIREWORKS)
        color = random.choice([Fore.RED, Fore.YELLOW, Fore.GREEN, Fore.CYAN, Fore.MAGENTA])
        clear_screen()
        print_centered(firework, color + Style.BRIGHT)
        time.sleep(0.3)


def rotating_globe(duration: float = 3.0):
    """Show a rotating globe animation."""
    globe_frames = ["🌍", "🌎", "🌏"]

    start_time = time.time()
    i = 0

    while time.time() - start_time < duration:
        frame = globe_frames[i % len(globe_frames)]
        print(f"\r{' ' * 35}{frame} Spinning the world... {frame}", end="", flush=True)
        time.sleep(0.3)
        i += 1
    print("\r" + " " * 80 + "\r", end="", flush=True)


def epic_countdown():
    """Show an epic countdown."""
    for i in range(3, 0, -1):
        clear_screen()
        number = {
            3: "███████╗\n╚════██║\n ██████╔╝\n ╚═══██║\n███████║\n╚══════╝",
            2: "██████╗ \n╚════██╗\n █████╔╝\n██╔═══╝ \n███████╗\n╚══════╝",
            1: " ██╗\n███║\n╚██║\n ██║\n ██║\n ╚═╝",
        }
        print_centered(number[i], Fore.YELLOW + Style.BRIGHT)
        time.sleep(0.8)


def main():
    """The main show."""
    clear_screen()

    # Introduction
    print_centered("Welcome to...", Fore.CYAN)
    time.sleep(1)

    # Matrix effect
    if COLORS_AVAILABLE:
        matrix_rain(1.5)

    # Loading animation
    clear_screen()
    loading_animation("Initializing V8 Engine", 2.0)

    # Countdown
    epic_countdown()

    # Main title reveal with effects
    clear_screen()
    print_centered(HELLO_ASCII, Fore.RED + Style.BRIGHT)
    time.sleep(0.5)

    print_centered(WORLD_ASCII, Fore.BLUE + Style.BRIGHT)
    time.sleep(0.5)

    print_centered(V8_ASCII, Fore.GREEN + Style.BRIGHT)
    time.sleep(1)

    # Fireworks
    if COLORS_AVAILABLE:
        show_fireworks()

    # Rotating globe
    clear_screen()
    print_centered(EARTH_ASCII, Fore.CYAN)
    rotating_globe(2.0)

    # Rocket launch
    clear_screen()
    for i in range(15, -5, -1):
        clear_screen()
        print("\n" * i)
        print_centered(ROCKET_ASCII, Fore.RED + Style.BRIGHT)
        if i < 10:
            # Add flame effect
            flame = "   🔥🔥🔥" if i % 2 == 0 else "  🔥🔥🔥🔥"
            print_centered(flame)
        time.sleep(0.1)

    # Final message with rainbow effect
    clear_screen()
    print("\n" * 8)

    final_message = "✨ HELLO WORLD V8 - MAXIMUM SNAZZINESS ACHIEVED! ✨"

    if COLORS_AVAILABLE:
        # Rainbow effect
        print_centered("")
        terminal_width = os.get_terminal_size().columns
        padding = (terminal_width - len(final_message)) // 2
        print(" " * padding, end="")
        rainbow_text(final_message, 0.05)
    else:
        print_centered(final_message)

    print("\n")
    type_text("🎉 Thanks for experiencing the snazziest hello world ever! 🎉", 0.03, Fore.MAGENTA)
    print("\n")

    # Interactive prompt
    type_text("Press Enter to see it again, or 'q' to quit: ", 0.02, Fore.YELLOW)
    response = input()

    if response.lower() != "q":
        main()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        clear_screen()
        print_centered("\n👋 Goodbye from V8! 👋", Fore.CYAN)
        print()
