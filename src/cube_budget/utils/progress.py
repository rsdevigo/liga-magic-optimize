"""Rich progress bar wrappers."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator, Iterable, TypeVar

from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)

T = TypeVar("T")


@contextmanager
def create_progress(description: str = "Processing...") -> Generator[Progress, None, None]:
    """Create a Rich progress bar context manager."""
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        expand=True,
    )
    with progress:
        progress.add_task(description, total=None)
        yield progress


def track_iterable(
    items: Iterable[T],
    description: str = "Processing",
) -> Iterable[T]:
    """Wrap an iterable with a progress bar."""
    items_list = list(items)
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
    ) as progress:
        task = progress.add_task(description, total=len(items_list))
        for item in items_list:
            yield item
            progress.advance(task)
