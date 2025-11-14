import builtins
from typing import Iterator, List

import pytest

from src.ui import cli


def make_input_sequence(responses: List[str]):
    """Creates a fake input() function that returns predefined responses.

    This utility is used to simulate user input in tests by replacing the
    built-in input() function. Each call to the returned function yields the
    next string in `responses`.

    Args:
        responses (List[str]): A list of strings to be returned sequentially
            as simulated user input.

    Returns:
        Callable[[str], str]: A function that mimics input() and yields the
        next value from the provided response list.
    """
    it: Iterator[str] = iter(responses)

    def _input(_prompt: str = "") -> str:
        return next(it)

    return _input


def test_color_known_and_unknown():
    """Tests the color() helper for known and unknown color names.

    Validates:
        - Known colors wrap text with the correct ANSI sequences.
        - Unknown colors return the original unmodified text.

    Raises:
        AssertionError: If ANSI wrapping is incorrect or fallback behavior fails.
    """
    text = "hello"
    green = cli.color(text, "green")

    assert cli.ANSI["green"] in green
    assert text in green
    assert cli.ANSI["reset"] in green

    same = cli.color(text, "nope")
    assert same == text


def test_ask_int_with_default_and_valid_set(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    """Tests ask_int() with defaults and a restricted valid set.

    Input sequence:
        1. ""  → uses default value (5)
        2. "7" → invalid for {10, 20}
        3. "10" → valid

    Validates that:
        - Defaults are applied on empty input.
        - Invalid selections prompt a message.
        - Valid values from a restricted set are accepted.

    Raises:
        AssertionError: On incorrect return values or missing validation output.
    """
    monkeypatch.setattr(builtins, "input", make_input_sequence(["", "7", "10"]))

    assert cli.ask_int("? ", default=5) == 5
    assert cli.ask_int("? ", valid={10, 20}) == 10

    out = capsys.readouterr().out
    assert "Please choose one of:" in out


def test_ask_int_invalid_then_valid(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    """Tests ask_int() when the first input is invalid and the second is valid.

    Input sequence:
        - "x" → triggers ValueError handling
        - "5" → valid integer

    Validates that:
        - Error message appears for invalid input.
        - A valid integer is accepted on retry.

    Raises:
        AssertionError: If feedback message is missing or return value incorrect.
    """
    monkeypatch.setattr(builtins, "input", make_input_sequence(["x", "5"]))

    assert cli.ask_int("? ") == 5
    out = capsys.readouterr().out
    assert "Please enter a valid integer." in out


def test_help_menu_outputs(capsys: pytest.CaptureFixture[str]):
    """Tests that help_menu() prints the expected help text structure.

    Validates presence of:
        - Section header "Commands:"
        - A line describing number drawing
        - A line describing quit behavior

    Raises:
        AssertionError: If expected help content is missing.
    """
    cli.help_menu()
    out = capsys.readouterr().out

    assert "Commands:" in out
    assert "Draw a number" in out
    assert "Quit" in out


def test_main_quick_quit(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    """Runs main() through setup prompts and then quits immediately.

    Input sequence:
        1. Player name → "" (defaults to "Anonymous")
        2. Board size  → "" (default = 5)
        3. pool_max    → "" (defaults based on board size)
        4. Marking mode → "" (default = auto)
        5. num_bots    → "" (default = 0)
        6. First command → "Q" (quit)

    Validates:
        - Main menu displays correctly.
        - The program exits cleanly on "Q".

    Raises:
        AssertionError: If main menu sections are missing or quit flow fails.
    """
    inputs = [
        "",  # player name
        "",  # board size
        "",  # pool_max
        "",  # marking mode
        "",  # num_bots
        "Q",  # quit
    ]
    monkeypatch.setattr(builtins, "input", make_input_sequence(inputs))

    cli.main()
    out = capsys.readouterr().out

    assert "Terminal Bingo MVP" in out
    assert "Commands:" in out


def test_main_handles_eof(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    """Tests that main() gracefully handles EOFError during the game loop.

    Simulated behavior:
        - Setup questions receive default-generating empty strings.
        - After setup, next input attempt raises EOFError.

    Expected result:
        - Program should print "Bye!" and exit cleanly.

    Raises:
        AssertionError: If EOFError does not produce the expected exit behavior.
    """
    seq = iter([
        "",  # player
        "",  # board size
        "",  # pool_max
        "",  # marking mode
        "",  # num_bots
    ])

    def _input(_prompt: str = "") -> str:
        try:
            return next(seq)
        except StopIteration:
            raise EOFError

    monkeypatch.setattr(builtins, "input", _input)

    cli.main()
    out = capsys.readouterr().out
    assert "Bye!" in out
