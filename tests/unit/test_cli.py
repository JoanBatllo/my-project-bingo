import builtins
from typing import Iterator, List

import pytest

from src.ui import cli
from src.ui.constants import ANSI


def make_input_sequence(responses: List[str]):
    it: Iterator[str] = iter(responses)

    def _input(_prompt: str = "") -> str:
        return next(it)

    return _input


def test_color_known_and_unknown():
    text = "hello"
    green = cli.color(text, "green")
    assert ANSI["green"] in green and text in green and ANSI["reset"] in green
    same = cli.color(text, "nope")
    assert same == text


def test_ask_int_with_default_and_valid_set(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    monkeypatch.setattr(builtins, "input", make_input_sequence(["", "7", "10"]))
    # blank returns default
    assert cli.ask_int("? ", default=5) == 5
    # rejects not-in-set, accepts valid
    assert cli.ask_int("? ", valid={10, 20}) == 10
    out = capsys.readouterr().out
    assert "Please choose one of:" in out


def test_ask_yes_no_variants(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(builtins, "input", make_input_sequence(["", "y", "n"]))
    assert cli.ask_yes_no("? ", default=True) is True
    assert cli.ask_yes_no("? ", default=False) is True
    assert cli.ask_yes_no("? ", default=True) is False


def test_ask_optional_int(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    monkeypatch.setattr(builtins, "input", make_input_sequence(["", "x", "12"]))
    assert cli.ask_optional_int("? ") is None
    assert cli.ask_optional_int("? ") == 12
    out = capsys.readouterr().out
    assert "valid integer" in out


def test_ask_int_invalid_then_valid(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    # Triggers ValueError branch (29-31) then returns a valid integer
    monkeypatch.setattr(builtins, "input", make_input_sequence(["x", "5"]))
    assert cli.ask_int("? ") == 5
    out = capsys.readouterr().out
    assert "Please enter a valid integer." in out


def test_ask_yes_no_invalid_then_default(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    # Triggers invalid response message then falls back to default on blank
    monkeypatch.setattr(builtins, "input", make_input_sequence(["maybe", ""]))
    assert cli.ask_yes_no("? ", default=False) is False
    out = capsys.readouterr().out
    assert "Please answer with 'y' or 'n'." in out


def test_help_menu_outputs(capsys: pytest.CaptureFixture[str]):
    cli.help_menu()
    out = capsys.readouterr().out
    assert "Commands:" in out and "Draw a number" in out and "Quit" in out


def test_main_quick_quit(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    # Sequence to navigate prompts quickly, then quit:
    # N -> blank (default 5), pool_max -> blank (default 75),
    # free_center -> blank (default True), seed -> blank (None), then command 'Q'
    inputs = ["", "", "", "", "Q"]
    monkeypatch.setattr(builtins, "input", make_input_sequence(inputs))
    cli.main()
    out = capsys.readouterr().out
    assert "Terminal Bingo MVP" in out
    assert "Commands:" in out


def test_main_command_paths_real(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    # has_bingo returns False then True to cover both branches
    outcomes = iter([False, True])

    def fake_has_bingo(_marked, _n):
        return next(outcomes)

    monkeypatch.setattr(cli, "has_bingo", fake_has_bingo)

    # Inputs:
    # N=3, pool=0 (invalid) then 9 (valid), free_center default, seed blank
    # Commands: blank, H, S, I, D, M (usage error), M 1,2, B(False), B(True), R, Q
    inputs = [
        "3", "0", "9", "", "",
        "", "H", "S", "I", "D", "M", "M 1,2", "B", "B", "R", "Q",
    ]
    monkeypatch.setattr(builtins, "input", make_input_sequence(inputs))

    cli.main()
    out = capsys.readouterr().out
    assert "Pool must be at least" in out
    assert "Commands:" in out
    assert "Usage: M r,c" in out
    assert "BINGO!" in out


def test_main_handles_eof(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    # Cause EOFError on first command input to exercise the except path
    seq = iter(["", "", "", ""])  # get through the setup prompts

    def _input(prompt: str = "") -> str:
        try:
            return next(seq)
        except StopIteration:
            raise EOFError

    monkeypatch.setattr(builtins, "input", _input)
    cli.main()
    out = capsys.readouterr().out
    assert "Bye!" in out
