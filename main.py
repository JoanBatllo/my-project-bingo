#!/usr/bin/env python3
import sys
from typing import Optional, Set

from src.ui.cli import main as cli_main


def ask_int(prompt: str, default: Optional[int] = None, valid: Optional[Set[int]] = None) -> int:
    """Simple integer prompt with optional default and allowed values."""
    while True:
        raw = input(prompt).strip()
        if raw == "" and default is not None:
            return default
        try:
            val = int(raw)
        except ValueError:
            print("Please enter a valid integer.")
            continue
        if valid and val not in valid:
            print(f"Please choose one of: {sorted(valid)}")
            continue
        return val


def choose_mode() -> str:
    """Show the main menu and return 'CLI', 'GUI' or 'QUIT'."""
    while True:
        print("\n=== Bingo ===\n")
        print("1) Play in terminal (classic CLI)")
        print("2) Play in separate window (GUI)")
        print("Q) Quit\n")

        choice = input("Choose an option [1]: ").strip().upper()
        if choice == "":
            choice = "1"

        if choice == "1":
            return "CLI"
        elif choice == "2":
            return "GUI"
        elif choice == "Q":
            return "QUIT"
        else:
            print("Please enter 1, 2 or Q.")


def run_cli() -> None:
    """Run the classic command-based terminal UI."""
    cli_main()


def run_gui() -> None:
    """Run the Tkinter-based GUI in a separate window."""
    from src.ui.gui import run_bingo_gui  # lazy import
    run_bingo_gui()


def main() -> None:
    """
    Project entrypoint.

    - No flags: show menu and let the user choose CLI or GUI.
    - --cli   : skip menu and go directly to CLI.
    - --gui   : skip menu and go directly to GUI.
    """
    args = set(sys.argv[1:])

    if "--cli" in args:
        run_cli()
        return

    if "--gui" in args:
        run_gui()
        return

    mode = choose_mode()
    if mode == "CLI":
        run_cli()
    elif mode == "GUI":
        run_gui()
    else:  # QUIT
        print("Bye!")


if __name__ == "__main__":
    main()
