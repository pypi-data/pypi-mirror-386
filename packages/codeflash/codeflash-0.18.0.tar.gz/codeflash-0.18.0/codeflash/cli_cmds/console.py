from __future__ import annotations

import logging
from contextlib import contextmanager
from itertools import cycle
from typing import TYPE_CHECKING, Optional

from rich.console import Console
from rich.logging import RichHandler
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

from codeflash.cli_cmds.console_constants import SPINNER_TYPES
from codeflash.cli_cmds.logging_config import BARE_LOGGING_FORMAT
from codeflash.lsp.helpers import is_LSP_enabled
from codeflash.lsp.lsp_logger import enhanced_log
from codeflash.lsp.lsp_message import LspCodeMessage, LspTextMessage

if TYPE_CHECKING:
    from collections.abc import Generator

    from rich.progress import TaskID

    from codeflash.lsp.lsp_message import LspMessage

DEBUG_MODE = logging.getLogger().getEffectiveLevel() == logging.DEBUG

console = Console()

if is_LSP_enabled():
    console.quiet = True

logging.basicConfig(
    level=logging.INFO,
    handlers=[RichHandler(rich_tracebacks=True, markup=False, console=console, show_path=False, show_time=False)],
    format=BARE_LOGGING_FORMAT,
)

logger = logging.getLogger("rich")
logging.getLogger("parso").setLevel(logging.WARNING)

# override the logger to reformat the messages for the lsp
for level in ("info", "debug", "warning", "error"):
    real_fn = getattr(logger, level)
    setattr(
        logger,
        level,
        lambda msg, *args, _real_fn=real_fn, _level=level, **kwargs: enhanced_log(
            msg, _real_fn, _level, *args, **kwargs
        ),
    )


def lsp_log(message: LspMessage) -> None:
    if not is_LSP_enabled():
        return
    json_msg = message.serialize()
    logger.info(json_msg)


def paneled_text(
    text: str, panel_args: dict[str, str | bool] | None = None, text_args: dict[str, str] | None = None
) -> None:
    """Print text in a panel."""
    from rich.panel import Panel
    from rich.text import Text

    panel_args = panel_args or {}
    text_args = text_args or {}

    rich_text_obj = Text(text, **text_args)
    panel = Panel(rich_text_obj, **panel_args)
    console.print(panel)


def code_print(code_str: str, file_name: Optional[str] = None, function_name: Optional[str] = None) -> None:
    if is_LSP_enabled():
        lsp_log(LspCodeMessage(code=code_str, file_name=file_name, function_name=function_name))
        return
    """Print code with syntax highlighting."""
    from rich.syntax import Syntax

    console.rule()
    console.print(Syntax(code_str, "python", line_numbers=True, theme="github-dark"))
    console.rule()


spinners = cycle(SPINNER_TYPES)


@contextmanager
def progress_bar(
    message: str, *, transient: bool = False, revert_to_print: bool = False
) -> Generator[TaskID, None, None]:
    """Display a progress bar with a spinner and elapsed time.

    If revert_to_print is True, falls back to printing a single logger.info message
    instead of showing a progress bar.
    """
    if is_LSP_enabled():
        lsp_log(LspTextMessage(text=message, takes_time=True))
        yield
        return

    if revert_to_print:
        logger.info(message)

        # Create a fake task ID since we still need to yield something
        class DummyTask:
            def __init__(self) -> None:
                self.id = 0

        yield DummyTask().id
    else:
        progress = Progress(
            SpinnerColumn(next(spinners)),
            *Progress.get_default_columns(),
            TimeElapsedColumn(),
            console=console,
            transient=transient,
        )
        task = progress.add_task(message, total=None)
        with progress:
            yield task


@contextmanager
def test_files_progress_bar(total: int, description: str) -> Generator[tuple[Progress, TaskID], None, None]:
    """Progress bar for test files."""
    with Progress(
        SpinnerColumn(next(spinners)),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(complete_style="cyan", finished_style="green", pulse_style="yellow"),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        transient=True,
    ) as progress:
        task_id = progress.add_task(description, total=total)
        yield progress, task_id
