#!/usr/bin/env python3
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, simpledialog
from typing import Tuple, Dict

from src.game.bingo_card import BingoCard
from src.game.number_drawer import NumberDrawer
from src.game.win_checker import has_bingo


class BingoGUI:
    """Simple GUI window for playing Bingo using Tkinter."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Bingo")

        # Ask user for board config using simple dialogs
        self.n, self.pool_max = self._ask_config()

        # Game state
        self.card = BingoCard(n=self.n, pool_max=self.pool_max)
        self.drawer = NumberDrawer(pool_max=self.pool_max)

        # (row, col) -> Label widget
        self.cells: Dict[Tuple[int, int], tk.Label] = {}

        # UI elements
        self.info_label = tk.Label(self.root, text="", anchor="w", justify="left")
        self.info_label.pack(padx=10, pady=5, fill="x")

        self.board_frame = tk.Frame(self.root, bg="#dddddd")
        self.board_frame.pack(padx=10, pady=5)

        controls_frame = tk.Frame(self.root)
        controls_frame.pack(padx=10, pady=10)

        self.draw_button = tk.Button(controls_frame, text="Draw", command=self.draw_number)
        self.draw_button.grid(row=0, column=0, padx=5)

        self.new_game_button = tk.Button(controls_frame, text="New Game", command=self.new_game)
        self.new_game_button.grid(row=0, column=1, padx=5)

        self.bingo_button = tk.Button(controls_frame, text="Bingo!", command=self.check_bingo)
        self.bingo_button.grid(row=0, column=2, padx=5)

        self.highlight_button = tk.Button(
            controls_frame,
            text="Highlight number",
            command=self.highlight_cell,
        )
        self.highlight_button.grid(row=0, column=3, padx=5)

        self.quit_button = tk.Button(controls_frame, text="Quit", command=self.root.destroy)
        self.quit_button.grid(row=0, column=4, padx=5)

        self.last_number_label = tk.Label(self.root, text="Last number: —")
        self.last_number_label.pack(padx=10, pady=5)

        # Build initial board & info
        self._build_board()
        self._update_info()

    # ---------- Config dialog ----------

    def _ask_config(self) -> Tuple[int, int]:
        """Ask the user for board size and pool max using dialogs."""
        while True:
            n = simpledialog.askinteger(
                "Board size",
                "Choose board size N (3, 4, or 5):",
                minvalue=3,
                maxvalue=5,
                parent=self.root,
            )
            if n is None:
                # Cancel -> default to 5x5
                n = 5
            if n not in (3, 4, 5):
                messagebox.showerror("Error", "Board size must be 3, 4, or 5.")
                continue

            default_pool = {5: 75, 4: 60, 3: 30}[n]
            pool_max = simpledialog.askinteger(
                "Pool max",
                f"Max number in pool [default {default_pool}]:",
                minvalue=n * n,
                parent=self.root,
            )
            if pool_max is None:
                pool_max = default_pool

            if pool_max < n * n:
                messagebox.showerror(
                    "Error",
                    f"Pool max must be at least {n * n} to ensure unique values.",
                )
                continue

            return n, pool_max

    # ---------- UI construction ----------

    def _build_board(self) -> None:
        """Create the grid of labels for the bingo card."""
        # Clear old cells
        for widget in self.board_frame.winfo_children():
            widget.destroy()
        self.cells.clear()

        for r in range(self.card.n):
            for c in range(self.card.n):
                num = self.card.grid[r][c]
                label_text = "FREE" if self.card.free_center and num == 0 else str(num)

                lbl = tk.Label(
                    self.board_frame,
                    text=label_text,
                    width=6,
                    height=2,
                    borderwidth=1,
                    relief="solid",
                    bg="white",
                )
                lbl.grid(row=r, column=c, padx=2, pady=2)

                # Bind left click to toggle mark
                lbl.bind("<Button-1>", lambda event, rr=r, cc=c: self.toggle_mark(rr, cc))

                self.cells[(r, c)] = lbl

        self._refresh_marks()

    def _refresh_marks(self) -> None:
        """
        Update cell styles according to the card's marked cells.
        Marked cells: green background, bold text.
        Unmarked cells: white background, normal text.
        """
        for (r, c), lbl in self.cells.items():
            if (r, c) in self.card.marked:
                lbl.config(bg="#90ee90", font=("TkDefaultFont", 10, "bold"))
            else:
                lbl.config(bg="white", font=("TkDefaultFont", 10, "normal"))

    def _update_info(self) -> None:
        """Update info label (board size, pool, numbers drawn / remaining)."""
        drawn_count = len(self.drawer.drawn)
        text = (
            f"Board: {self.card.n}×{self.card.n}\n"
            f"Pool: 1–{self.pool_max}\n"
            f"Numbers drawn: {drawn_count}\n"
            f"Remaining in pool: {self.drawer.remaining()}"
        )
        self.info_label.config(text=text)

    # ---------- Game actions ----------

    def toggle_mark(self, r: int, c: int) -> None:
        """Toggle REAL game mark at the given cell (affects bingo) and repaint."""
        # Use the existing BingoCard logic
        self.card.toggle_mark(r, c)
        self._refresh_marks()

    def draw_number(self) -> None:
        """Draw the next number from the pool and auto-mark if present."""
        num = self.drawer.draw()
        if num is None:
            messagebox.showinfo("Bingo", "No numbers left in the pool. Start a new game.")
            return

        hit = self.card.auto_mark_if_present(num)
        if hit:
            self._refresh_marks()

        self.last_number_label.config(text=f"Last number: {num} ({'HIT' if hit else 'MISS'})")
        self._update_info()

    def new_game(self) -> None:
        """Start a new game (asks for config again)."""
        self.n, self.pool_max = self._ask_config()
        self.card = BingoCard(n=self.n, pool_max=self.pool_max)
        self.drawer = NumberDrawer(pool_max=self.pool_max)
        self._build_board()
        self._update_info()
        self.last_number_label.config(text="Last number: —")

    def check_bingo(self) -> None:
        """Check whether the current marks form a bingo."""
        if has_bingo(self.card.marked, self.card.n):
            messagebox.showinfo("Bingo", "BINGO! 🎉")
        else:
            messagebox.showinfo("Bingo", "Not yet, keep going!")

    def highlight_cell(self) -> None:
        """
        Ask for a number and mark that cell (same effect as clicking it).

        This WILL change card.marked and affects bingo logic.
        """
        num = simpledialog.askinteger(
            "Highlight number",
            "Number to mark:",
            parent=self.root,
        )
        if num is None:
            return

        loc = self.card.find(num)
        if loc is None:
            messagebox.showinfo("Highlight", f"Number {num} is not on this card.")
            return

        r, c = loc

        # Mark it (do not toggle, just ensure it's marked)
        self.card.marked.add((r, c))
        self._refresh_marks()


def run_bingo_gui() -> None:
    """Entry point for launching the Bingo GUI window."""
    root = tk.Tk()
    app = BingoGUI(root)
    root.mainloop()