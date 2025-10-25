# The gitplier library

A Python library for easy and performant querying and parsing of Git repositories.

* When used correctly, it's fast. See the example below.
* Understands specific types of repositories (stable kernel, RHEL kernel) and offers
  specialized methods for them.
* Has no Python dependencies. At run time, it requires the `git` binary in the system.
* Unlike naive attempts to execute `git`, gitplier runs correctly even with exotic git
  configurations.

## Goals

The intention of this library is to become a kitchen sink of useful functions. Still, the
functions should be as generic as possible. When making a function more generic requires more
verbosity at the function call sites, we opt for more verbosity.

We aim for backward compatible API. Making the development of the library easier is never an
excuse for breaking users.

## The API

Anything starting with an underscore does not constitute API and should not be used. Always
import the `gitplier` module and use the symbols from it. E. g., use only
`gitplier.GitError`, despite internally it being `gitplier._exceptions.GitError`.

Do not depend on the `GitError` message content. It's meant for human consumption, not for
programmatic parsing.

## Example

Calculate how many per cent of stable commits were backported to CentOS Stream 9.
This completes in about 6 seconds on a moderate machine.

```python
import gitplier
import os

# Open the kernel stable repository.
stable = gitplier.kernel.KernelStableRepository(os.path.expanduser('~/git/stable'))
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
cs9 = gitplier.kernel.KernelRHELRepository(os.path.expanduser('~/git/centos-stream-9'))
# Count the upstream references in the CS9 tree that are also backported to stable.
count = sum(
    len(set(commit.upstream).intersection(in_stable))
    for commit in cs9.log('v5.14', 'main', fields=(), include_merges=False)
)

print(f'{count / len(in_stable) * 100:.1f}%')
```

## Why not pygit2?

All git operations in gitplier are performed by executing the external `git` command. The
disadvantages of that are clear but the advantages outweight them:

1. No compatibility problems. libgit2 (and thus pygit2) does not support new git features and
   sometimes exhibits compatibility bugs.

2. Easier to use API. Where pygit2 has a specific Oid type, gitplier has just a string. Etc.

3. No dependency problems. While pygit2 and libgit2 do better job than most libraries out
   there, they do not have a stable API. You need to use the right versions when working with
   them.

4. Performance. As surprising as it is, libgit2 is so slow that doing tons of fork/exec calls
   is significantly faster for most operations.
