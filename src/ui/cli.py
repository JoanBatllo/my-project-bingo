#!/usr/bin/env python3
from src.persistence.repository import BingoRepository
from typing import Optional, Set

from src.game.bingo_card import BingoCard
from src.game.number_drawer import NumberDrawer
from src.game.win_checker import has_bingo


def has_full_card_bingo(marked, n: int) -> bool:
    """Returns True only if ALL cells on the card are marked."""
    return len(marked) == n * n

# --- NEW: Player class ---
class Player:
    def __init__(self, name: str, card: BingoCard, is_bot: bool = False, auto_mark: bool = True):
        self.name = name
        self.card = card
        self.is_bot = is_bot
        self.auto_mark = auto_mark

    def mark_number(self, num: int) -> bool:
        """Marks the number automatically if mode is auto-mark."""
        if self.auto_mark:
            return self.card.auto_mark_if_present(num)
        return False  # manual mode means player must mark manually



# ANSI helpers only for the UI
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
        "  L  - Show leaderboard\n"
        "  R  - Reset (new card & reshuffled pool)\n"
        "  H  - Help\n"
        "  Q  - Quit\n"
    )

def main() -> None:
    print(color("\n=== Terminal Bingo MVP ===\n", "bold"))

    # --- new: player name and repository ---
    player_name = input("Enter your player name: ").strip() or "Anonymous"
    # --- NEW: choose marking mode ---
    mark_mode = ask_int("Marking mode: 1) Auto  2) Manual [default 1]: ", default=1, valid={1, 2})
    auto_mark_mode = True if mark_mode == 1 else False

    # --- NEW: create player and bots ---
    players = []
    human = Player(name=player_name, card=None, is_bot=False, auto_mark=auto_mark_mode)
    players.append(human)

    num_bots = ask_int("How many computer opponents? [0-3, default 0]: ", default=0, valid={0, 1, 2, 3})
    for i in range(num_bots):
        bot = Player(name=f"Bot{i + 1}", card=None, is_bot=True, auto_mark=True)
        players.append(bot)

    repo = BingoRepository()  # saves to bingo.db

    n = ask_int("Choose board size N (3/4/5) [default 5]: ", default=5, valid={3,4,5})
    default_pool = {5: 75, 4: 60, 3: 30}[n]
    pool_max = ask_int(f"Max number in pool [default {default_pool}]: ", default=default_pool)

    drawer = NumberDrawer(pool_max=pool_max)

    for p in players:
        p.card = BingoCard(n=n, pool_max=pool_max)

    human = players[0]  # the first player is always the human
    draws_this_game = 0

    help_menu()


    while True:
        try:
            raw = input(color("\n> ", "cyan")).strip()
        except (EOFError, KeyboardInterrupt):
            if draws_this_game > 0 and not has_bingo(card.marked, card.n):
                repo.record_game_result(player_name, n, pool_max, False, draws_this_game)
                print(color("\nCurrent game saved as a loss.", "dim"))
            print("\nBye!")
            break

        if not raw:
            continue

        cmd = raw.split()[0].upper()

        if cmd == "Q":
            if draws_this_game > 0 and not has_bingo(card.marked, card.n):
                repo.record_game_result(player_name, n, pool_max, False, draws_this_game)
                print(color("\nCurrent game saved as a loss.", "dim"))
            print("Bye!")
            break

        elif cmd == "H":
            help_menu()


        elif cmd == "S":

            for p in players:
                print(color(f"\n{p.name}'s card:", "cyan"))

                print(p.card.render(color_fn=color))

        elif cmd == "I":
            recent = ", ".join(map(str, drawer.drawn[-10:])) if drawer.drawn else "—"
            print("\n" + f"Board: {n}x{n} | Pool: 1..{pool_max}\n"
                        f"Numbers drawn ({len(drawer.drawn)}): {recent}\n"
                        f"Remaining in pool: {drawer.remaining()}")

        elif cmd == "R":
            if draws_this_game > 0:
                won = has_bingo(card.marked, card.n)
                repo.record_game_result(player_name, n, pool_max, won, draws_this_game)
                msg = "Previous game saved as WIN." if won else "Previous game saved as LOSS."
                print(color(msg, "yellow"))
            card = BingoCard(n=n, pool_max=pool_max)
            drawer = NumberDrawer(pool_max=pool_max)
            draws_this_game = 0
            print(color("\nNew card generated.", "yellow"))
            print(card.render(color_fn=color))


        elif cmd == "D":

            num = drawer.draw()

            if num is None:

                print(color("No numbers left to draw.", "yellow"))

            else:

                print(color(f"Drew: {num}", "yellow"))

                for p in players:

                    hit = p.card.auto_mark_if_present(num) if p.auto_mark else False

                    if hit:
                        print(color(f"{p.name} marked {num} automatically!", "green"))

                # check winners

                winners = [p for p in players if has_full_card_bingo(p.card.marked, p.card.n)]

                if winners:

                    names = ", ".join([w.name for w in winners])

                    print(color(f"\nBINGO! 🎉 Winner(s): {names}", "green"))

                    # if the human is one of them → win, else loss

                    human_won = any(w.name == human.name for w in winners)

                    # Here you could save results (record_game_result) later

                    # For now, just restart new cards:

                    for p in players:
                        p.card = BingoCard(n=n, pool_max=pool_max)

                    drawer = NumberDrawer(pool_max=pool_max)

                    print(color("\nNew cards generated.", "yellow"))




        elif cmd == "M":

            # Manual mark for the human player only (0-based indices)

            parts = raw[1:].strip().replace(" ", "")

            if not parts or "," not in parts:
                print("Usage: M row,col   (e.g., M 0,2)")

                print("Rows and columns start at 0 (top-left is 0,0).")

                continue

            try:

                r_str, c_str = parts.split(",", 1)

                r, c = int(r_str), int(c_str)

            except ValueError:

                print("Please provide valid coordinates like: M 0,2")

                continue

            # 1) Check range (0-based)

            if not (0 <= r < human.card.n and 0 <= c < human.card.n):
                print(f"Coordinates out of range. Use values between 0 and {human.card.n - 1}.")

                continue

            # 2) ANTI-CHEAT: only allow marking numbers that have been drawn

            num_at_cell = human.card.grid[r][c]

            if num_at_cell not in drawer.drawn:
                print(color(

                    f"You cannot mark {num_at_cell} at ({r},{c}) yet: it has not been drawn.",

                    "yellow",

                ))

                continue

            # 3) Valid manual toggle

            human.card.toggle_mark(r, c)

            print(human.card.render(color_fn=color))


        elif cmd == "B":

            # Human explicitly calls Bingo
            if has_full_card_bingo(human.card.marked, human.card.n):
                print(color("\nBINGO! ✅ You have full-card bingo!", "green"))
                # Save win for the human player
                repo.record_game_result(player_name, n, pool_max, True, draws_this_game)
                print(color("Your win has been saved to the leaderboard.", "yellow"))
                # Start a new game: new cards for all players, reset drawer and counter
                for p in players:
                    p.card = BingoCard(n=n, pool_max=pool_max)
                drawer = NumberDrawer(pool_max=pool_max)
                draws_this_game = 0
                print(color("\nNew cards generated.", "yellow"))
                for p in players:
                    print(color(f"\n{p.name}'s card:", "cyan"))
                    print(p.card.render(color_fn=color))
            else:

                print(color("\nNot yet. You don't have full-card bingo.", "yellow"))

        elif cmd == "L":
            leaderboard = repo.get_leaderboard(limit=10)
            if not leaderboard:
                print(color("\nNo games played yet.", "yellow"))
            else:
                print("\nLeaderboard:")
                print("Rank | Player         | Wins | Games | Win%")
                print("-------------------------------------------")
                for idx, row in enumerate(leaderboard, start=1):
                    print(
                        f"{idx:>4} | "
                        f"{row['name']:<13} | "
                        f"{row['wins']:>4} | "
                        f"{row['games_played']:>5} | "
                        f"{row['win_rate']:>4.1f}"
                    )

        else:
            print("Unknown command. Type H for help.")
if __name__ == "__main__":
    main()
