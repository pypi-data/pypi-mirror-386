from os import PathLike
from pathlib import Path
from colorama import Fore, Style


# Custom log level: NOTICE (between INFO and WARNING)
NOTICE_LEVEL = 25

# Log level colors
LOG_COLORS = {
    "DEBUG": Fore.BLUE,
    "INFO": Fore.WHITE,
    "NOTICE": Fore.GREEN,  # Blanc pour NOTICE
    "WARNING": Fore.YELLOW,
    "ERROR": Fore.RED,
    "CRITICAL": Fore.MAGENTA,
}

# Attribute colors for console (BRIGHT for visibility)
ATTR_COLORS = {
    str: Fore.MAGENTA + Style.BRIGHT,  # Bright Violet
    Path: Fore.CYAN + Style.BRIGHT,  # Bright Cyan
    PathLike: Fore.CYAN + Style.BRIGHT,  # Bright Cyan
    int: Fore.YELLOW + Style.BRIGHT,  # Bright Yellow
    float: Fore.YELLOW + Style.BRIGHT,  # Bright Yellow
    bool: Fore.WHITE + Style.BRIGHT,  # Bright White
}
