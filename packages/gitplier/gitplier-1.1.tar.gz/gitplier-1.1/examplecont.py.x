import gitplier
import os

# Open the kernel stable repository.
stable = gitplier.kernel.KernelStableRepository(os.path.expanduser('/home/jbenc/git/stable'))
# Create a set that will hold all upstream commits referenced from the stable commits.
in_stable = set()
# Examine all stable branches from v5.14 on.
for branch_name, upstream_tag in stable.stable_branches(since='v5.14'):
    in_stable.update(
        commit.upstream
        for commit in stable.log(upstream_tag, branch_name, fields=(), include_merges=False)
        # Walk all commits in the branch. Ignore merges. To speed up the walking, do not
        # fetch any additional field.
    )

# Open the CentOS Stream 9 repository.
cs9 = gitplier.kernel.KernelRHELRepository(os.path.expanduser('/home/jbenc/git/rhel9'))
# Count the upstream references in the CS9 tree that are also backported to stable.
count = sum(
    len(set(commit.upstream).intersection(in_stable))
    for commit in cs9.log('v5.14', 'main', fields=(), include_merges=False)
)

print(f'{count / len(in_stable) * 100:.1f}%')
