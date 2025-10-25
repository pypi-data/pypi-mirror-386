import re
from typing import Optional
from .._commit import Commit


class KernelCommit(Commit):
    """A commit from the kernel tree. If `body` is present, `fixes` will be present as well.
    It is a list (possibly empty) of shas of commits there are fixed by this commit. Note the
    shas will be abbreviated and may not point to an existing commit; they're just parsed from
    the commit description."""

    def _set_field(self, field: str, value: str) -> None:
        if field == 'body':
            self.fixes = re.findall(r'^Fixes: ([0-9a-f]{8,40}) \(".*"\)$', value,
                                    re.MULTILINE)
        super()._set_field(field, value)


class KernelStableCommit(KernelCommit):
    """A commit from the kernel stable tree. Contains an upstream reference in the `upstream`
    attribute. For stable specific commits, `upstream` is None. Also contains the `fixes`
    attribute; see `KernelCommit` for details."""

    def __init__(self) -> None:
        """The constructor is private. Never create instances directly; access them via
        methods of KernelStableRepository."""
        self.upstream: Optional[str] = None
        self.fixes: list[str] = []

    def _set_field(self, field: str, value: str) -> None:
        if field == 'body':
            first_line = value.split('\n', maxsplit=1)[0]
            m = re.fullmatch(r'commit ([0-9a-f]{40}) upstream\.', first_line)
            if m is None:
                m = re.fullmatch(r'\[ Upstream commit ([0-9a-f]{40}) \]', first_line)
            if m is not None:
                self.upstream = m[1]
        super()._set_field(field, value)


class KernelRHELCommit(Commit):
    """A commit from a RHEL or a CentOS Stream kernel repository. Contains a list of upstream
    references in the `upstream` attribute. If no upstream references are detected, `upstream`
    is []. For commits that are explicitly marked as RHEL only, `rhel_only` is True. For
    commits that are explicitly marked as posted, `posted` is the link (or the free text that
    the developer entered). The list of fixed commits is in the `fixes` attribute; see
    `KernelCommit` for details and note it's undefined whether the shas are for RHEL or
    an upstream kernel."""

    def __init__(self) -> None:
        """The constructor is private. Never create instances directly; access them via
        methods of KernelRHELRepository."""
        self.upstream: list[str] = []
        self.rhel_only = False
        self.posted: Optional[str] = None
        self.fixes: list[str] = []

    def _set_field(self, field: str, value: str) -> None:
        if field == 'body':
            upstream_refs = re.findall(r'^commit ([0-9a-f]{40})(?: \(.*\))?$|^\(cherry picked from commit ([0-9a-f]{40})\)$',
                                       value, re.MULTILINE)
            self.upstream = list(set(a or b for a, b in upstream_refs))
            m = re.search(r'^upstream(?:[ -]status)?: *rhel[ -]*[0-9.]*[ -]only', value,
                          re.MULTILINE | re.IGNORECASE)
            self.rhel_only = m is not None
            if not self.rhel_only:
                m = re.search(r'^upstream(?:[ -]status)?: *posted *(.*)$', value,
                              re.MULTILINE | re.IGNORECASE)
                if m is not None:
                    self.posted = m[1]
            self.fixes = re.findall(r'^(?:    )?Fixes: ([0-9a-f]{8,40}) \(".*"\)$', value,
                                    re.MULTILINE)
        super()._set_field(field, value)
