from __future__ import annotations
from typing import Callable, Iterable, Iterator, Optional
import fnmatch
import os
from . import _execute
from ._commit import Commit
from ._config import Config
from ._constants import _SENTINEL
from ._exceptions import GitError, _HandledError
from ._remote import Remote
from ._status import Status
from ._tag import Tag
from ._utils import _Peekable, _splitlines

_COMMIT_FIELD_MAP = {
    'sha': 'H',
    'tree': 'T',
    'parents': 'P',
    'author_name': 'an',
    'author_email': 'ae',
    'author_date': 'aD',
    'committer_name': 'cn',
    'committer_email': 'ce',
    'committer_date': 'cD',
    'refs': 'D',
    'subject': 's',
    'body': 'b',
    'raw_body': 'B',
    'notes': 'N',
    'patch': '',
    'changes': '',
}

_TAG_FIELD_MAP = {
    'name': 'refname',
    'sha': 'objectname',
    'target': 'object',
    'annotated': 'objecttype',
    'committer_name': 'committername',
    'committer_email': 'committeremail',
    'committer_date': 'committerdate',
    'tagger_name': 'taggername',
    'tagger_email': 'taggeremail',
    'tagger_date': 'taggerdate',
}

COMMIT_DEFAULT_FIELDS = [
    'sha', 'tree', 'parents', 'author_name', 'author_email', 'author_date',
    'committer_name', 'committer_email', 'committer_date', 'subject', 'body'
]


class Repository:
    """A generic git repository. The parameter is a file system path."""
    _COMMIT_TYPE: type[Commit] = Commit
    _FORCED_LOG_FIELDS: tuple[str, ...] = ('sha',)

    def __init__(self, path: str) -> None:
        """Opens the repository at the given path. Raises GitError if the path is not in a git
        repository."""
        try:
            self.path = os.path.realpath(path)
        except OSError:
            raise GitError(f'Path {path} does not exist.') from None
        self.config = Config(self)
        try:
            self._git_dir = self._run_git('rev-parse', ('--absolute-git-dir',))
        except GitError:
            raise GitError(f'No git repository in {path}') from None

    def _run_git_raw(self, command: str, args: Iterable[str] = (),
                     handled_errors: Iterable[int] = ()) -> bytes:
        return _execute._run_git_raw(self.path, command, args, handled_errors=handled_errors)

    def _run_git(self, command: str, args: Iterable[str] = (),
                 handled_errors: Iterable[int] = (),
                 progress: Optional[Callable[[str], None]] = None) -> str:
        if not progress:
            return _execute._run_git(self.path, command, args, handled_errors=handled_errors)
        return _execute._run_git_progress(self.path, command, args, progress,
                                          handled_errors=handled_errors)

    def _run_git_records(self, command: str, args: Iterable[str] = (),
                         separator: str = '\0') -> Iterator[str]:
        return _execute._run_git_records(self.path, command, args, separator)

    def _log(self, rev_range: str, fields: Iterable[str],
             args: list[str]) -> tuple[list[str], _Peekable]:
        """An internal only function to construct log related commands. Returns a tuple with
        the list of fields and an iterator over a running git."""
        patch = False
        changes = False
        full_fields_set: set[str] = set()
        full_fields_set.update(self._FORCED_LOG_FIELDS)
        full_fields_set.update(fields)
        if 'patch' in full_fields_set:
            full_fields_set.remove('patch')
            patch = True
        if 'changes' in full_fields_set:
            full_fields_set.remove('changes')
            changes = True
        full_fields = list(full_fields_set)
        formatted_fields = '%x00'.join(f'%{_COMMIT_FIELD_MAP[f]}' for f in full_fields)
        full_args = ['-z', f'--pretty=tformat:{_SENTINEL}%x00{formatted_fields}']
        # changes (--raw) and patch (--patch) must come last, in this order
        if changes:
            full_fields.append('changes')
            full_args.append('--raw')
        if patch:
            full_fields.append('patch')
            full_args.append('--patch')
        full_args.extend(args)
        full_args.append(rev_range)
        return full_fields, _Peekable(self._run_git_records('log', full_args))

    @classmethod
    def create(cls, path: str, *, bare: bool = False) -> Repository:
        """Create an empty repository in the given path. If `bare` is True, create a bare
        repository. Raises GitError if the repository cannot be created. If a repository
        at the given path already exists, the result is undefined."""
        args = []
        if bare:
            args.append('--bare')
        _execute._run_git(path, 'init', args)
        return cls(path)

    def resolve(self, id: str, type: str = 'object') -> Optional[str]:
        """Resolve the given `id` to the full sha. The `id` can be a sha, an abbreviated
        sha, a branch name, a tag, etc. You can further restrict the possible type of the
        returned object using `type`, e.g. `type='commit'`. Note this can be also used to
        resolve a tag to the underlying commit; just pass the tag with `type='commit'`.
        Returns the full sha or None."""
        args = ['--verify', '--quiet', '--end-of-options', f'{id}^{{{type}}}']
        try:
            return self._run_git('rev-parse', args)
        except GitError:
            return None

    def get_commit(self, id: str,
                   fields: Iterable[str] = COMMIT_DEFAULT_FIELDS) -> Optional[Commit]:
        """Returns the commit with the given `id` or None if such commit does not exist.
        The `id` can be any commit identifier: a sha, an abbreviated sha, a branch, etc."""
        full_fields, it = self._log(id, fields, ['-1'])
        try:
            return self._COMMIT_TYPE._construct(full_fields, it)
        except (StopIteration, GitError):
            return None

    def log(self, start: Optional[str], end: Optional[str],
            fields: Iterable[str] = COMMIT_DEFAULT_FIELDS, *,
            files: Optional[Iterable[str]] = None,
            include_merges: bool = True,
            topological: bool = False,
            reverse: bool = False) -> Iterator[Commit]:
        """Yields a Commit instance for every commit in the history from `start` to `end`.
        `fields` is a list of fields to include in the result. `files` can contain a list of
        file patterns to limit the log to. If `include_merges` is True (the default), merge
        commits are included in the result. If `topological` is True, the commits are ordered
        in the topological order, i.e. commits on different lines of history are not
        intermixed and parents are returned only after all of their children. If `reverse` is
        True, the commits are returned from the oldest to the newest.

        Note: it's generally faster to not specify `files` but add `'changes'` to `fields`
        and do your own filtering of commits in Python."""
        args = []
        if not include_merges:
            args.append('--no-merges')
        if topological:
            args.append('--topo-order')
        if reverse:
            args.append('--reverse')
        if files:
            args.append('--')
            args.extend(files)
        if start is None:
            if end is None:
                raise GitError('A start, end or both must be given')
            rev_range = end
        elif end is None:
            rev_range = f'{start}..'
        else:
            rev_range = f'{start}..{end}'
        full_fields, it = self._log(rev_range, fields, args)
        try:
            while True:
                yield self._COMMIT_TYPE._construct(full_fields, it)
        except StopIteration:
            return

    def get_file(self, path: str, id: Optional[str] = None) -> bytes:
        """Return the given file from the given point in history. `path` must be a relative
        path to the repository root. `id` is a commit-ish indicating the point in history. If
        `id` is None, the current HEAD is used."""
        args = (f'HEAD:{path}' if id is None else f'{id}:{path}',)
        return self._run_git_raw('show', args)

    def branch_names(self, *, local: bool = True, remote: bool = False,
                     patterns: Optional[Iterable[str]] = None) -> list[str]:
        """Returns a list of branch names, optionally matching a list of `patterns`.
        `local` and `remote` determine whether local or remote branches should be listed,
        respectively."""
        args = []
        if local:
            if remote:
                args.append('--all')
        elif remote:
            args.append('--remotes')
        else:
            # local is False and remote is False; no branches
            return []
        args.append('--list')
        if patterns:
            args.extend(patterns)
        return [s.lstrip().split(' ')[0] for s in self._run_git('branch', args).splitlines()]

    def tags(self, *, patterns: Optional[Iterable[str]] = None,
             merged_to: Optional[str] = None) -> Iterator[Tag]:
        """Yields a Tag instance for each tag, optionally matching a list of `patterns`. If
        `merged_to` is passed, return only the tags that are present in the history of (merged
        to) the given commit."""
        args = []
        if merged_to:
            args.append('--merged')
            args.append(merged_to)
        fields = list(_TAG_FIELD_MAP.keys())
        args.append('--format')
        args.append(''.join(f'%00%({_TAG_FIELD_MAP[f]})' for f in fields) + '%00')
        args.append('refs/tags/*')
        it = self._run_git_records('for-each-ref', args)
        try:
            # consume the first empty field
            next(it)
            while True:
                tag = Tag._construct(fields, it)
                if patterns and not any(fnmatch.fnmatchcase(tag.name, pat)
                                        for pat in patterns):
                    continue
                yield tag
        except StopIteration:
            return

    def remotes(self) -> list[Remote]:
        """Returns a list of all remotes. This may cache the config; see `gitplier.Config`
        for details."""
        result = []
        for name in _splitlines(self._run_git('remote')):
            remote = self.get_remote(name)
            if remote is None:
                raise GitError('Remote {name} does not have a URL configured')
            result.append(remote)
        return result

    def get_remote(self, name: str) -> Optional[Remote]:
        """Gets the remote with the given name. This may cache the config; see
        `gitplier.Config` for details."""
        urls = self.config.get_all('remote', name, 'url')
        if not urls:
            return None
        push_urls = self.config.get_all('remote', name, 'pushurl')
        refspecs = self.config.get_all('remote', name, 'fetch')
        return Remote(self, name, urls, push_urls, refspecs)

    def add_remote(self, name: str, url: str) -> Remote:
        """Add a remote."""
        self._run_git('remote', ('add', name, url))
        self.config.refresh()
        return Remote(self, name, [url], [], [f'+refs/heads/*:refs/remotes/{name}/*'])

    def fetch(self, remote_name: Optional[str] = None, *,
              progress: Optional[Callable[[str], None]] = None) -> None:
        """Fetch the given remote. If `remote_name` is not specified, fetch the upstream
        remote for the current branch, or 'origin'. If `progress` is given, it will be called
        with the progress of the fetching."""
        args = []
        if progress:
            args.append('--progress')
        else:
            args.append('--quiet')
        if remote_name:
            args.append(remote_name)
        self._run_git('fetch', args, progress=progress)

    def describe(self, id: str, *, long: bool = False) -> Optional[str]:
        """Describe the given `id`. The `id` can be a sha, an abbreviated sha, a branch name,
        a tag, etc. If `long` is True, the result will be always in the long format, that is,
        tag-number-sha, even if the number is zero. Returns the full sha or None."""
        args = []
        if long:
            args.append('--long')
        args.append('--end-of-options')
        args.append(id)
        try:
            return self._run_git('describe', args).rstrip('\n')
        except GitError:
            return None

    def merge_base(self, /, id1: str, id2: str) -> Optional[str]:
        """Find the best common ancestor of the given commits. Returns the full sha of the
        common ancestor or None if there's no such ancestor. Raises GitError if the ids cannot
        be resolved or when there's an error running git."""
        args = ('--end-of-options', id1, id2)
        try:
            return self._run_git('merge-base', args, handled_errors=(1,)).rstrip('\n')
        except _HandledError:
            return None

    def status(self, *, untracked: bool = False) -> list[Status]:
        """Get the working tree status. Returns a list containing status of modified files
        as subclasses of `gitplier.Status`. Untracked files are not included in the list,
        unless `untracked` argument is True."""
        args = ('--porcelain=v2', '-z', '--renames', '-unormal' if untracked else '-uno')
        it = self._run_git_records('status', args)
        result = []
        try:
            while True:
                result.append(Status._construct(it))
        except StopIteration:
            pass
        return result

    def checkout(self, id: Optional[str] = None, *, detach: bool = False,
                 progress: Optional[Callable[[str], None]] = None) -> None:
        """Check out the given commit-ish `id`. If the `id` is a branch name, that branch will
        be checked out (and later commits will advance it). However, if you pass `detach`
        = True, the tree will have a detached HEAD (pointing to `id`) instead. If `progress`
        is given, it will be called with the progress of the checkout."""
        args = ['--no-guess', '--progress' if progress else '--quiet']
        if id:
            args.append(id)
        self._run_git('checkout', args, progress=progress)

    def set_sparse_checkout(self, directories: Optional[Iterable[str]] = None,
                            progress: Optional[Callable[[str], None]] = None) -> None:
        """Sets the tree to use sparse checkouts. `directories` is the list of directories to
        include in the checkout; note that all files along each path are included in the
        checkout, not just leaf files. As a special case, the files in repository root are
        always included, even with `directories` = None.  Repeated calls to
        `set_sparse_checkout` will correctly update the list of sparse directories. This call
        will also take care of adjusting the files in the tree, with one exception: if the
        tree was never checked out (e.g. this is used after a call to `add_worktree(checkout
        = False)`), it will stay that way. Call `checkout()` without parameters in such case.
        Depending on what you pass in `directories`, this call may need to checkout a lot of
        files; pass `progress` if you want to get the progress of the call."""
        args = ['set', '--no-sparse-index', '--cone']
        if directories is not None:
            args.extend(directories)
        self._run_git('sparse-checkout', args, progress=progress)

    def disable_sparse_checkout(self,
                                progress: Optional[Callable[[str], None]] = None) -> None:
        """Restore the tree to include all files. Pass `progress` if you want to get the
        progress of the call."""
        self._run_git('sparse-checkout', ('disable',), progress=progress)

    def add_worktree(self, path: str, id: str, *, detach: bool = False,
                     checkout: bool = True) -> Repository:
        """Creates a new worktree in the given `path` pointing to the commit-ish `id`. If the
        `id` is a branch name, that branch will be checked out in the new worktree; this
        branch must not be checked out out in any other worktree. However, if you pass
        `detach` = True, the worktree will have a detached HEAD (pointing to `id`) instead. If
        `checkout` is False, do not check out the tree in the new worktree. Returns
        a `Repository` pointing to the newly created worktree."""
        # Currently, if `id` does not exist but a remote branch with that name exists,
        # "git worktree add" creates a tracking branch. There's no documented way to switch
        # off that behavior. We want to be on the safe side here to allow backward compatible
        # behavior of future versions of the library. Check the existence ourselves.
        if not self.resolve(id):
            raise GitError(f'Commit-ish {id} does not exist')
        args = ['add', '--checkout' if checkout else '--no-checkout']
        if detach:
            args.append('--detach')
        args.append(path)
        args.append(id)
        self._run_git('worktree', args)
        self.config.refresh()
        return type(self)(path)

    def remove_worktree(self, path: Optional[str] = None, *, force: bool = False) -> None:
        """Remove the current worktree. The main worktree cannot be removed. If the current
        worktree is not clean, this will fail unless `force` is True. Alternatively, specify
        `path` to remove the given worktree instead of the current one."""
        args = ['remove']
        if force:
            args.append('--force')
        args.append(self.path if path is None else path)
        self._run_git('worktree', args)
