"""Behaviour-layer stories: every helper, a single note."""

from __future__ import annotations

from dataclasses import dataclass
from io import StringIO

import pytest

from keep_github_workflows_active import behaviors


@pytest.mark.os_agnostic
def test_when_the_greeting_is_sung_it_reaches_the_buffer() -> None:
    buffer = StringIO()

    behaviors.emit_greeting(stream=buffer)

    assert buffer.getvalue() == "Hello World\n"


@pytest.mark.os_agnostic
def test_when_no_stream_is_named_stdout_hears_the_song(capsys: pytest.CaptureFixture[str]) -> None:
    behaviors.emit_greeting()

    captured = capsys.readouterr()

    assert captured.out == "Hello World\n"
    assert captured.err == ""


@pytest.mark.os_agnostic
def test_when_flush_is_possible_the_stream_is_polished() -> None:
    @dataclass
    class MemoryStream:
        ledger: list[str]
        flushed: bool = False

        def write(self, text: str) -> None:
            self.ledger.append(text)

        def flush(self) -> None:
            self.flushed = True

    stream = MemoryStream([])

    behaviors.emit_greeting(stream=stream)  # type: ignore[arg-type]

    assert stream.ledger == ["Hello World\n"]
    assert stream.flushed is True


@pytest.mark.os_agnostic
def test_when_failure_is_invoked_a_runtime_error_rises() -> None:
    with pytest.raises(RuntimeError, match="I should fail"):
        behaviors.raise_intentional_failure()


@pytest.mark.os_agnostic
def test_when_no_work_is_requested_the_placeholder_sits_still() -> None:
    assert behaviors.noop_main() is None
