from __future__ import annotations
from ._exceptions import MultipleValuesError
from typing import Iterable, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from ._repository import Repository


class Config:
    """A git config. It's always tied to a particular repository. Supports both setting and
    getting of values using the array syntax ([]). The key is a tuple of strings, forming
    a path to the value. The same key can be present multiple times in the config and you must
    take that into account when working with config. The array access operation returns the
    last value in the config (or raises KeyError). The array assignment operation raises
    MultipleValuesError when the key is present in the config multiple times. There are
    specialized methods available for working with multi value keys.

    Note the config is cached after the first access; subsequent external changes to the
    config will not be visible. Internal config changes are correctly accounted for, either by
    modifying the config or by invalidating the cache."""

    def __init__(self, repository: Repository) -> None:
        """The constructor is private. Never create instances directly; access them via
        Repository.config."""
        self._repository = repository
        self._data: Optional[list[tuple[str, str]]] = None

    def _get_data(self) -> list[tuple[str, str]]:
        # Unfortunatelly, we cannot parse the keys here. The output from git config list is
        # ambiguous, sinnce '.' is a permitted part of a subsection name. This can happen for
        # example for remotes with '.' in the remote name. Meaning we cannot split the key to
        # individual parts. Ideally, we would store the result in a trie for fast lookups. But
        # configs tend to be short and it doesn't justify bringing in a 3rd party dependency.
        if self._data is None:
            self._data = []
            for entry in self._repository._run_git_records('config', ('list', '-z')):
                k, v = entry.split('\n', 1)
                self._data.append((k, v))
        return self._data

    def refresh(self) -> None:
        """Invalidates the config cache. A subsequent config access will reload the config."""
        self._data = None

    def get_all(self, *args: str) -> list[str]:
        """Lookup the given key in the config, returning all values found."""
        real_key = '.'.join(args)
        return [v for k, v in self._get_data() if k == real_key]

    def __getitem__(self, key: Iterable[str]) -> str:
        args = tuple(key)
        result = self.get_all(*args)
        if not result:
            raise KeyError(f'Config key {".".join(args)} not present')
        return result[-1]

    def __setitem__(self, key: Iterable[str], value: str) -> None:
        real_key = '.'.join(key)
        real_value = str(value)
        data = self._get_data()
        indexes = [i for i, (k, v) in enumerate(data) if k == real_key]
        if len(indexes) > 1:
            raise MultipleValuesError(f'Multiple values for key {real_key}')
        self._repository._run_git('config', ('set', '--local', real_key, real_value))
        if not indexes:
            data.append((real_key, real_value))
        else:
            data[indexes[0]] = (real_key, real_value)
