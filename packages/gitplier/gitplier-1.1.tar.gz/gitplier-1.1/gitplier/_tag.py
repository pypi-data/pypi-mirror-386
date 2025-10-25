from __future__ import annotations
from typing import Any, Iterator, Sequence
import datetime
import email.utils
from ._base import GitObject
from ._exceptions import GitError


class Tag(GitObject):
    """A single tag. Available attributes are `sha`, `target`, `name`, 'annotated',
    `creator_name`, `creator_email` and `creator_date`."""
    target: str
    name: str
    annotated: bool
    creator_name: str
    creator_email: str
    creator_date: datetime.datetime

    @classmethod
    def _construct(cls, fields: Sequence[str], iterator: Iterator[str]) -> Tag:
        """An internal method to construct the commit from a list of fields and an iterator
        yielding the fields in order."""
        result = cls()
        for field in fields:
            result._set_field(field, next(iterator))
        sep = next(iterator)
        if sep != '\n':
            # git for-each-ref always adds a terminating newline
            raise GitError(f'Unexpected output from git: "{sep}"')
        assert hasattr(result, 'sha')
        assert hasattr(result, 'name')
        if not result.target:
            # Unannotated tags do not have a target, since they're just a ref to a commit.
            # Set the target ourselves.
            result.target = result.sha
        return result

    def _set_field(self, field: str, value: str) -> None:
        """An internal method to populate an attribute. Can be overriden in subclasses for
        specialized field handling."""
        converted: Any = value
        if field.endswith('_date') and value:
            converted = email.utils.parsedate_to_datetime(value)
        if field == 'name':
            # strip the 'refs/tags/'
            converted = value[10:]
        elif field == 'annotated':
            converted = value == 'tag'
        elif field.startswith('committer_'):
            # unannotated tag
            if not value:
                return
            field = 'creator_' + field[10:]
        elif field.startswith('tagger_'):
            # annotated tag
            if not value:
                return
            field = 'creator_' + field[7:]
        setattr(self, field, converted)

    def __str__(self) -> str:
        return self.name
