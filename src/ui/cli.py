#!/usr/bin/env python3
#!/usr/bin/env python3
from typing import Optional, Set

from game import BingoCard
from game import NumberDrawer
from game import has_bingo

# ANSI helpers solo para la UI
ANSI = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "green": "\033[32m",
    "cyan": "\033[36m",
    "yellow": "\033[33m",
    "dim": "\033[2m",
}
def color(text: str, c: Optional[str] = None) -> str:
    if not c or c not in ANSI:
        return f"{text}"
    return f"{ANSI[c]}{text}{ANSI['reset']}"

def ask_int(prompt: str, default: Optional[int] = None, valid: Optional[Set[int]] = None) -> int:
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

def help_menu() -> None:
    print(
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

def main() -> None:
    print(color("\n=== Terminal Bingo MVP ===\n", "bold"))
    n = ask_int("Choose board size N (3/4/5) [default 5]: ", default=5, valid={3,4,5})
    default_pool = {5: 75, 4: 60, 3: 30}[n]
    pool_max = ask_int(f"Max number in pool [default {default_pool}]: ", default=default_pool)

    card = BingoCard(n=n, pool_max=pool_max)
    drawer = NumberDrawer(pool_max=pool_max)

    help_menu()
    print(card.render(color_fn=color))

    while True:
        try:
            raw = input(color("\n> ", "cyan")).strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break
        if not raw:
            continue

        cmd = raw.split()[0].upper()

        if cmd == "Q":
            print("Bye!")
            break
        elif cmd == "H":
            help_menu()
        elif cmd == "S":
            print("\n" + card.render(color_fn=color))
        elif cmd == "I":
            recent = ", ".join(map(str, drawer.drawn[-10:])) if drawer.drawn else "—"
            print("\n" + f"Board: {n}x{n} | Pool: 1..{pool_max}\n"
                        f"Numbers drawn ({len(drawer.drawn)}): {recent}\n"
                        f"Remaining in pool: {drawer.remaining()}")
        elif cmd == "R":
            card = BingoCard(n=n, pool_max=pool_max)
            drawer = NumberDrawer(pool_max=pool_max)
            print(color("\nNew card generated.", "yellow"))
            print(card.render(color_fn=color))
        elif cmd == "D":
            num = drawer.draw()
            if num is None:
                print(color("No numbers left to draw.", "yellow"))
            else:
                hit = card.auto_mark_if_present(num)
                msg = f"Drew: {num}" + ("  (HIT! auto-marked)" if hit else "")
                print(color(msg, "green" if hit else "yellow"))
        elif cmd == "M":
            parts = raw[1:].strip().replace(" ", "")
            if not parts or "," not in parts:
                print("Usage: M r,c   (e.g., M 1,2)")
                continue
            try:
                r_str, c_str = parts.split(",", 1)
                r, c = int(r_str), int(c_str)
            except ValueError:
                print("Please provide valid coordinates like: M 1,2")
                continue
            card.toggle_mark(r, c)
            print(card.render(color_fn=color))
        elif cmd == "B":
            if has_bingo(card.marked, card.n):
                print(color("\nBINGO! ✅", "green"))
            else:
                print(color("\nNot yet. Keep going!", "yellow"))
        else:
            print("Unknown command. Type H for help.")

if __name__ == "__main__":
    main()
