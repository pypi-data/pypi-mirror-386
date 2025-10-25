from __future__ import annotations
from typing import Iterator, Optional, Type
from ._exceptions import GitError


_xy_mapping = {
    '.': None,
    'M': 'modified',
    'T': 'type changed',
    'A': 'added',
    'D': 'deleted',
    'R': 'renamed',
    'C': 'copied',
    'U': 'updated',
}


class Status:
    """A base class for file status. The only attribute you can rely on to be present is
    `path`."""
    path: str

    def __init__(self, path: str) -> None:
        self.path = path

    @classmethod
    def _construct(cls, iterator: Iterator[str]) -> Status:
        """An internal method to construct an appropriate subclass from an iterator."""
        data = next(iterator)
        while data.startswith('# '):
            # An extended header. We haven't requested any extended headers but the git
            # documentation says to ignore headers we don't recognize. Better assume
            # headers can appear with future git versions.
            data = next(iterator)
        if data.startswith('1 '):
            return StatusChanged._construct_changed(data[2:])
        if data.startswith('2 '):
            try:
                orig_path = next(iterator)
            except StopIteration:
                raise GitError('Unexpected end of git output')
            return StatusMoved._construct_moved(data[2:], orig_path)
        if data.startswith('u '):
            return StatusConflict._construct_conflict(data[2:])
        if data.startswith('? '):
            return StatusUntracked(data[2:])
        # There's also '! ' for ignored items but we don't implement this currently.
        raise GitError(f'Unexpected output from git: "{data}"')


class StatusChanged(Status):
    """A changed file. The available attributes are `status_index`, `status_worktree` (each is
    one of 'modified', 'type changed', 'added', 'deleted', 'renamed', 'copied' or None for
    unmodified), `mode_head`, `mode_index`, `mode_worktree` (those are integers containing the
    file mode), `sha_head`, `sha_index` and `path`."""

    def __init__(self, status_index: Optional[str], status_worktree: Optional[str],
                 mode_head: int, mode_index: int, mode_worktree: int,
                 sha_head: str, sha_index: str, path: str) -> None:
        self.status_index = status_index
        self.status_worktree = status_worktree
        self.mode_head = mode_head
        self.mode_index = mode_index
        self.mode_worktree = mode_worktree
        self.sha_head = sha_head
        self.sha_index = sha_index
        self.path = path

    @classmethod
    def _construct_changed(cls, data: str) -> StatusChanged:
        try:
            (xy, sub, mode_head, mode_index, mode_worktree, sha_head, sha_index,
             path) = data.split(' ', 8)
        except ValueError:
            raise GitError('Git returned a wrong number of fields for a changed file')
        return StatusChanged(_xy_mapping[xy[0]], _xy_mapping[xy[1]],
                             int(mode_head, 8), int(mode_index, 8), int(mode_worktree, 8),
                             sha_head, sha_index, path)
        # We're ignoring the submodule info (sub) currently.


class StatusMoved(StatusChanged):
    """A renamed or copied file. In addition to the attributes in `StatusChanged` also
    contains `score` and `orig_path`. This is an abstract base type for `StatusRenamed` and
    `StatusCopied` and is never returned directly."""

    def __init__(self, status_index: Optional[str], status_worktree: Optional[str],
                 mode_head: int, mode_index: int, mode_worktree: int,
                 sha_head: str, sha_index: str, score: int, path: str,
                 orig_path: str) -> None:
        super().__init__(status_index, status_worktree, mode_head, mode_index, mode_worktree,
                         sha_head, sha_index, path)
        self.score = score
        self.orig_path = orig_path

    @classmethod
    def _construct_moved(cls, data: str, orig_path: str) -> StatusMoved:
        try:
            (xy, sub, mode_head, mode_index, mode_worktree, sha_head, sha_index,
             score, path) = data.split(' ', 9)
        except ValueError:
            raise GitError('Git returned a wrong number of fields for a renamed/copied file')
        if score.startswith('R'):
            result_cls: Type[StatusMoved] = StatusRenamed
        elif score.startswith('C'):
            result_cls = StatusCopied
        else:
            raise GitError(f'Unknown score type: {score}')
        return result_cls(_xy_mapping[xy[0]], _xy_mapping[xy[1]],
                          int(mode_head, 8), int(mode_index, 8), int(mode_worktree, 8),
                          sha_head, sha_index, int(score[1:]), path, orig_path)


class StatusRenamed(StatusMoved):
    """A renamed file."""
    pass


class StatusCopied(StatusMoved):
    """A copied file."""
    pass


class StatusConflict(Status):
    """A file with an umerged conflict. The available attributes are `status_ours`,
    `status_theirs` (each is one of 'added', 'deleted', 'updated'), `mode_base`, `mode_ours`,
    `mode_theirs` (an integer representing the file mode of the common ancestor, HEAD and
    MERGE_HEAD, respectively), `mode_worktree`, `sha_base`, `sha_ours`, `sha_theirs` and
    `path`."""

    def __init__(self, status_ours: str, status_theirs: str,
                 mode_base: int, mode_ours: int, mode_theirs: int, mode_worktree: int,
                 sha_base: str, sha_ours: str, sha_theirs: str, path: str) -> None:
        self.status_ours = status_ours
        self.status_theirs = status_theirs
        self.mode_base = mode_base
        self.mode_ours = mode_ours
        self.mode_theirs = mode_theirs
        self.mode_worktree = mode_worktree
        self.sha_base = sha_base
        self.sha_ours = sha_ours
        self.sha_theirs = sha_theirs
        self.path = path

    @classmethod
    def _construct_conflict(cls, data: str) -> StatusConflict:
        try:
            (xy, sub, mode_base, mode_ours, mode_theirs, mode_worktree, sha_base, sha_ours,
             sha_theirs, path) = data.split(' ', 10)
        except ValueError:
            raise GitError('Git returned a wrong number of fields for an unmerged file')
        status_ours = _xy_mapping[xy[0]]
        status_theirs = _xy_mapping[xy[1]]
        if status_ours is None or status_theirs is None:
            raise GitError(f'Git returned unexpected status for a conflict: {xy}')
        return StatusConflict(status_ours, status_theirs,
                              int(mode_base, 8), int(mode_ours, 8), int(mode_theirs, 8),
                              int(mode_worktree, 8), sha_base, sha_ours, sha_theirs,
                              path)


class StatusUntracked(Status):
    """An untracked file. The only available attribute is `path`."""
    pass
