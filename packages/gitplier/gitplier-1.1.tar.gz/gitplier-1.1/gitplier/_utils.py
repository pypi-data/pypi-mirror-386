from __future__ import annotations
import io
import re
from typing import Any, Callable, Iterable, Iterator, Optional

class _Peekable:
    def __init__(self, iterator: Iterator[Any]):
        self._iterator = iterator
        self._buffer: list[Any] = []
        self._exhausted = False

    def __iter__(self) -> _Peekable:
        return self

    def peek(self) -> Any:
        if len(self._buffer) == 0:
            if self._exhausted:
                raise StopIteration
            try:
                self._buffer.append(next(self._iterator))
            except StopIteration:
                self._exhausted = True
                raise
        return self._buffer[-1]

    def peek_match(self, f: Callable[[Any], bool]) -> bool:
        try:
            item = self.peek()
            return f(item)
        except StopIteration:
            return False

    def pushback(self, item: Any) -> None:
        self._buffer.append(item)

    def __next__(self) -> Any:
        if len(self._buffer) > 0:
            result = self._buffer.pop()
            return result
        if self._exhausted:
            raise StopIteration
        try:
            return next(self._iterator)
        except StopIteration:
            self._exhausted = True
            raise


def _natural_sort(data: Iterable[Any], key: Optional[Callable[[Any], str]] = None) -> list[Any]:
    """Sorts the given iterable in natural order, i.e. treat the text parts as text and
    numerical parts as numbers."""
    if key is None:
        def key(x: str) -> str:
            return x
    nums = re.compile('([0-9]+)')
    names = []
    for d in data:
        name = [int(comp) if i & 1 else comp for i, comp in enumerate(nums.split(key(d)))]
        names.append((name, d))
    names.sort(key=lambda x: x[0])
    return [d for _, d in names]


def _splitlines(s: str) -> list[str]:
    """Split string to lines, not keeping the newline characters. Unlike str.splitlines, this
    function splits only on '\\n'. Although it tries to be as efficient as possible, it still
    does two copies for each line."""
    return [line.rstrip('\n') for line in io.StringIO(s)]
