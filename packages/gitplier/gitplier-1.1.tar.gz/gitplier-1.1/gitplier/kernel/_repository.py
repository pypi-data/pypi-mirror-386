import re
from typing import Optional
from .._exceptions import GitError
from .._repository import Repository
from .._utils import _natural_sort
from ._commit import KernelCommit, KernelStableCommit, KernelRHELCommit


class KernelRepository(Repository):
    """A kernel git repository. The parameter is a file system path."""
    _COMMIT_TYPE = KernelCommit

    def in_version(self, id: str, *, include_rc: bool = False) -> Optional[str]:
        """Returns the kernel version where the given `id` got merged. If `include_rc` is
        True, include also the "-rcX" part of the version. If the given `id` does not exist
        or is not a part of any version, return None. Warning: this is a slow operation."""
        args = ('--match', 'v[1-9]*.*', '--contains', id)
        try:
            ver = self._run_git('describe', args).rstrip()
        except GitError:
            return None
        if not ver:
            return None
        ver = ver.split('~', maxsplit=1)[0]
        ver = ver.split('^', maxsplit=1)[0]
        if not include_rc:
            ver = ver.split('-', maxsplit=1)[0]
        return ver

    def versions(self, *, include_rc: bool = False, include_stable: bool = False,
                 since: Optional[str] = None) -> list[str]:
        """Returns the list of kernel versions, sorted. If `include_rc` is True, also the -rc
        versions are included. If `include_stable` is True and the repo is a stable repo,
        the stable versions are included. If `since` is given, only versions starting from
        this version (inclusive) are returned."""
        versions = []
        for ver in self.tags(patterns=['v[1-9]*.*']):
            if '-' in ver.name:
                # this is a -rc or similar
                if not include_rc or '-rc' not in ver.name:
                    continue
            if not include_stable:
                if ver.name.startswith('v2.'):
                    if ver.name.count('.') >= 3:
                        # this is a stable version
                        continue
                elif ver.name.count('.') >= 2:
                    # this is a stable version
                    continue
            versions.append(ver.name)
        versions = _natural_sort(versions)
        if since:
            versions = versions[versions.index(since) :]
        return versions


class KernelStableRepository(KernelRepository):
    """A kernel stable git repository. The parameter is a file system path. The returned
    commits have `upstream` attribute present."""
    _COMMIT_TYPE = KernelStableCommit
    _FORCED_LOG_FIELDS = ('sha', 'body')

    def stable_branches(self, *, since: Optional[str] = None) -> list[tuple[str, str]]:
        """Return information about stable branches. The returned value is a list of tuples
        `(branch_name, upstream_tag)`. The `branch_name` is the full stable branch name,
        the `upstream_tag` is the upstream (vanilla) tag the branch is based on. The list
        is sorted from the oldest version to the newest. If `since` is given, only branches
        starting from this upstream version are returned."""
        branches = {}
        for b in self.branch_names(local=False, remote=True):
            m = re.fullmatch(r'[^ /]*/linux-([1-9][0-9.]+)\.y', b)
            if m is None:
                continue
            tag = f'v{m[1]}'
            if not self.resolve(tag, 'tag'):
                continue
            key = tuple(map(int, m[1].split('.')))
            branches[key] = (m[0], tag)
        if since:
            since = since.removeprefix('v')
            since_expanded = tuple(map(int, since.split('.')))
            return [branches[key] for key in sorted(branches.keys()) if key >= since_expanded]
        else:
            return [branches[key] for key in sorted(branches.keys())]


class KernelRHELRepository(Repository):
    """A RHEL or CentOS Stream kernel repository. The parameter is a file system path. The
    returned commits have `upstream` attribute present."""
    _COMMIT_TYPE = KernelRHELCommit
    _FORCED_LOG_FIELDS = ('sha', 'body')
