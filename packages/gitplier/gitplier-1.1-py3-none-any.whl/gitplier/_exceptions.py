from typing import Optional, Union


class GitError(Exception):
    """An exception raised when something goes wrong while running the git operation."""
    pass


class GitExecError(GitError):
    """An error executing git. Contains two attributes: `command` is a list with the command
    and arguments. `stderr` is the standard error output or None if the stderr was consumed
    by the progress callback."""
    def __init__(self, command: list[str], stderr: Optional[Union[str, bytes, bytearray]] = None):
        super().__init__('Failed to run git.')
        self.command = command
        if isinstance(stderr, (bytes, bytearray)):
            stderr_str: Optional[str] = stderr.decode('utf-8', errors='replace')
        else:
            stderr_str = stderr
        self.stderr = stderr_str

    def __str__(self) -> str:
        msg = super().__str__()
        cmd = ' '.join(self.command)
        err = ''
        if self.stderr:
            nl = self.stderr.find('\n')
            if nl < 0 or nl == len(self.stderr) - 1:
                # If there's only one line on stderr, add it to the message.
                err = f' and the error was: "{self.stderr.rstrip()}"'
        return f'{msg} The command was: "{cmd}"{err}'


class MultipleValuesError(GitError):
    """Multiple values for a key encountered in an operation that supports only a single
    value."""
    pass


class _HandledError(GitError):
    """An internal indication of a git error to be handled."""
    def __init__(self, code: int, stdout: Optional[Union[bytes, bytearray]] = None):
        self.code = code
        self.stdout = stdout
        super().__init__()
