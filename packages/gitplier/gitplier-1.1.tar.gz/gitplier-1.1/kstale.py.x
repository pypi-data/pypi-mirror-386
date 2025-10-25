import collections
import gitplier
import os

in_upstream = collections.defaultdict(set)
upstream = gitplier.kernel.KernelRepository(os.path.expanduser('~/git/vanilla'))
for commit in upstream.log('v5.14', 'master', fields=('changes',)):
    for change in commit.changes:
        in_upstream[change.src_path].add(commit.sha)
        if change.dst_path != change.src_path:
            in_upstream[change.dst_path].add(commit.sha)
in_cs9 = collections.defaultdict(set)
cs9 = gitplier.kernel.KernelRHELRepository(os.path.expanduser('~/git/rhel9'))
for commit in cs9.log('v5.14', 'main', fields=('changes',)):
    for change in commit.changes:
        in_cs9[change.src_path].update(commit.upstream)
        if change.dst_path != change.src_path:
            in_cs9[change.dst_path].update(commit.upstream)
for fn, commits in in_upstream.items():
    if fn not in in_cs9:
        # ignore files not in RHEL
        continue
    else:
        commits.difference_update(in_cs9[fn])
        print(f'{fn} {len(commits)}')
        del in_cs9[fn]
for fn in in_cs9:
    print(f'only in RHEL: {fn}')
