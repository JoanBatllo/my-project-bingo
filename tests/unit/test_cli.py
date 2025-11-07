import builtins
from typing import Iterator, List

import pytest

from src.ui import cli


def make_input_sequence(responses: List[str]):
    it: Iterator[str] = iter(responses)

    def _input(_prompt: str = "") -> str:
        return next(it)

    return _input


def test_color_known_and_unknown():
    text = "hello"
    green = cli.color(text, "green")
    # ANSI now lives in cli.ANSI
    assert cli.ANSI["green"] in green and text in green and cli.ANSI["reset"] in green
    same = cli.color(text, "nope")
    assert same == text


def test_ask_int_with_default_and_valid_set(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    # first call: "" -> default 5
    # second call: "7" (invalid for {10, 20}), then "10"
    monkeypatch.setattr(builtins, "input", make_input_sequence(["", "7", "10"]))

    assert cli.ask_int("? ", default=5) == 5
    assert cli.ask_int("? ", valid={10, 20}) == 10

    out = capsys.readouterr().out
    assert "Please choose one of:" in out


def test_ask_int_invalid_then_valid(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    # "x" -> triggers ValueError branch, then "5" is accepted
    monkeypatch.setattr(builtins, "input", make_input_sequence(["x", "5"]))
    assert cli.ask_int("? ") == 5
    out = capsys.readouterr().out
    assert "Please enter a valid integer." in out


def test_help_menu_outputs(capsys: pytest.CaptureFixture[str]):
    cli.help_menu()
    out = capsys.readouterr().out
    # Check key parts of the help text
    assert "Commands:" in out
    assert "Draw a number" in out
    assert "Quit" in out


def test_main_quick_quit(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    """
    Drive main() through the initial prompts and then quit immediately.

    Input sequence:
    1. player name -> ""  (becomes 'Anonymous')
    2. board size  -> ""  (default 5)
    3. pool_max    -> ""  (default based on board size)
    4. marking mode-> ""  (default 1 = auto)
    5. num_bots    -> ""  (default 0)
    6. first command -> "Q" (quit)
    """
    inputs = [
        "",  # player name
        "",  # board size
        "",  # pool_max
        "",  # marking mode
        "",  # num_bots
        "Q", # first command: quit
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
    """
    Simulate EOFError on the first command input after setup.
    """

    # Go through all setup inputs, then raise EOFError
    seq = iter([
        "",  # player name
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
