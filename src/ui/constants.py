#!/usr/bin/env python3

# ANSI color escape sequences used by the terminal UI
ANSI = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "green": "\033[32m",
    "cyan": "\033[36m",
    "yellow": "\033[33m",
    "dim": "\033[2m",
}

# Help menu content printed by the CLI when the user asks for help
COMMANDS_HELP = (
    "\nCommands:\n"
    "  S  - Show card\n"
    "  D  - Draw a number (auto-marks if on your card)\n"
    "  M  - Manually toggle mark at row,col (e.g., M 1,2)\n"
    "  B  - Call BINGO! (system validates)\n"
    "  I  - Show game info/status\n"
    "  R  - Reset (new card & reshuffled pool)\n"
    "  H  - Help\n"
    "  Q  - Quit\n"
)
