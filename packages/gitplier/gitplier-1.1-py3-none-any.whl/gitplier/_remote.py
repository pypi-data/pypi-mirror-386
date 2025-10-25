from __future__ import annotations
from typing import Callable, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from ._repository import Repository


class Remote:
    """A single remote of the git repository. Contains `name`, `urls`, `push_urls` and
    `refspecs` attributes."""
    def __init__(self, repository: Repository, name: str, urls: list[str],
                 push_urls: list[str], refspecs: list[str]) -> None:
        """The constructor is private. Never create instances directly; access them via
        Repository.remotes."""
        self._repository = repository
        self.name = name
        self.urls = urls
        self.push_urls = urls
        self.refspecs = refspecs

    def _update_first_url(self, target: list[str], new_url: str) -> None:
        self._repository.config.refresh()
        if not target:
            target.append(new_url)
        else:
            target[0] = new_url

    def rename(self, new_name: str) -> None:
        """Renames the remote."""
        self._repository._run_git('remote', ('rename', self.name, new_name))
        self._repository.config.refresh()
        self.name = new_name

    def set_url(self, new_url: str) -> None:
        """Sets the first url of the remote to new_url."""
        self._repository._run_git('remote', ('set-url', self.name, new_url))
        self._update_first_url(self.urls, new_url)

    def set_push_url(self, new_url: str) -> None:
        """Sets the first push_url of the remote to new_url."""
        self._repository._run_git('remote', ('set-url', '--push', self.name, new_url))
        self._update_first_url(self.push_urls, new_url)

    def fetch(self, *, progress: Optional[Callable[[str], None]] = None) -> None:
        """Fetch the remote. If `progress` is given, it will be called with the progress of
        the fetching."""
        self._repository.fetch(self.name, progress=progress)
