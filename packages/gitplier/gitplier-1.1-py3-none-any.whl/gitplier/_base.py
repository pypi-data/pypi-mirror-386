class GitObject:
    """An abstract class representing a Git object. The only attribute you can rely on to be
    present is `sha`."""
    sha: str
