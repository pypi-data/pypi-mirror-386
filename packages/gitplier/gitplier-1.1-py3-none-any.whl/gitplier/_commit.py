from __future__ import annotations
from typing import Any, Sequence
import email.utils
from ._base import GitObject
from ._constants import _SENTINEL
from ._diff import Change
from ._exceptions import GitError
from ._utils import _Peekable


class Commit(GitObject):
    """A single commit. It will always have the `sha` attribute populated. It may have also
    other attributes, depending on how it was obtained."""

    @classmethod
    def _construct(cls, fields: Sequence[str], iterator: _Peekable) -> Commit:
        """An internal method to construct the commit from a list of fields and an iterator
        yielding the fields in order."""
        sentinel = next(iterator)
        if sentinel != _SENTINEL:
            raise GitError(f'Unexpected output from git: "{sentinel}"')
        result = cls()
        for field in fields:
            if field == 'changes':
                result._set_changes(iterator)
            elif field == 'patch':
                result._set_patch(iterator)
            else:
                result._set_field(field, next(iterator))
        assert hasattr(result, 'sha')
        return result

    def _set_changes(self, iterator: _Peekable) -> None:
        """An internal method to populate the `changes` attribute."""
        self.changes = []
        while iterator.peek_match(lambda val: val.startswith(':') or val.startswith('\n:')):
            flags = next(iterator).lstrip('\n:').split(' ')
            score = None
            status = flags[4]
            if len(status) > 1:
                score = int(status[1:])
                status = status[0]
            src_path = dst_path = next(iterator)
            if status in ('C', 'R'):
                dst_path = next(iterator)
            self.changes.append(Change(src_path, dst_path, flags[0], flags[1], status, score))

    def _set_patch(self, iterator: _Peekable) -> None:
        """An internal method to populate the `patch` attribute."""
        if iterator.peek_match(lambda val: val == ''):
            # If there is both --raw and --patch, git inserts an empty record between the
            # whatchanged output and the patch. Consume it.
            next(iterator)
        if iterator.peek_match(lambda val: val.startswith('diff') or val.startswith('\ndiff')):
            # If there's only --patch (without --raw), git inserts a newline before the patch.
            # Delete it.
            patch = next(iterator).removeprefix('\n')
            while True:
                # Patch is not zero terminated. Detect the sentinel at the start of the next
                # commit.
                if patch.endswith(f'\n{_SENTINEL}'):
                    patch = patch.removesuffix(_SENTINEL)
                    iterator.pushback(_SENTINEL)
                    break
                # No sentinel. This is either the last record, or there's a null byte in the
                # patch.
                try:
                    cont = next(iterator)
                except StopIteration:
                    # It is the last record.
                    break
                # There was a null byte in the patch. Continue reading.
                patch = f'{patch}\0{cont}'
            self.patch = patch
        else:
            # no patch present
            self.patch = ''

    def _set_field(self, field: str, value: str) -> None:
        """An internal method to populate an attribute. Can be overriden in subclasses for
        specialized field handling."""
        converted: Any = value
        if field == 'parents':
            converted = value.split(' ')
        elif field.endswith('_date'):
            converted = email.utils.parsedate_to_datetime(value)
        setattr(self, field, converted)

    def __str__(self) -> str:
        if hasattr(self, 'subject'):
            return f'{self.sha} ("{self.subject}")'
        else:
            return self.sha
