# colorfy/core.py
import sys

# === ANSI escape codes ===
RESET = "\033[0m"
BOLD = "\033[1m"
UNDERLINE = "\033[4m"

# Основные цвета (ANSI 8-bit)
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"


def text(message: str, color: str = WHITE, bold: bool = False, underline: bool = False, end: str = "\n"):
    """Печатает текст в указанном цвете со стилями."""
    style = ""
    if bold:
        style += BOLD
    if underline:
        style += UNDERLINE
    styled_text = f"{style}{color}{message}{RESET}"
    print(styled_text, end=end)


def fade(message: str, start_color: str, end_color: str, bold: bool = False, underline: bool = False, end: str = "\n"):
    """
    Градиентный вывод текста: плавный переход цвета от start_color к end_color.
    Работает с TrueColor (24-bit) ANSI кодами.
    """
    # Получаем RGB из ANSI-кода (если переданы стандартные цвета)
    def parse_ansi_to_rgb(ansi_code: str):
        color_map = {
            RED: (255, 0, 0),
            GREEN: (0, 255, 0),
            YELLOW: (255, 255, 0),
            BLUE: (0, 0, 255),
            MAGENTA: (255, 0, 255),
            CYAN: (0, 255, 255),
            WHITE: (255, 255, 255),
        }
        return color_map.get(ansi_code, (255, 255, 255))

    r1, g1, b1 = parse_ansi_to_rgb(start_color)
    r2, g2, b2 = parse_ansi_to_rgb(end_color)

    n = max(1, len(message))
    styled = ""

    for i, ch in enumerate(message):
        t = i / (n - 1) if n > 1 else 0
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        ansi_rgb = f"\033[38;2;{r};{g};{b}m"

        prefix = ""
        if bold:
            prefix += BOLD
        if underline:
            prefix += UNDERLINE

        styled += f"{prefix}{ansi_rgb}{ch}"

    print(f"{styled}{RESET}", end=end)