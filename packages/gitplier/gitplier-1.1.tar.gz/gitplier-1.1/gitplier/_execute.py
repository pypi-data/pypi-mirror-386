from __future__ import annotations
from typing import Callable, Iterable, Iterator
import os
import subprocess
from ._exceptions import GitExecError, _HandledError


def _get_sanitized_git_env() -> dict[str, str]:
    env = { k: v for k, v in os.environ.items() if not k.startswith('GIT_') }
    env['GIT_CONFIG_GLOBAL'] = '/dev/null'
    env['GIT_CONFIG_SYSTEM'] = '/dev/null'
    return env

_sanitized_git_env = _get_sanitized_git_env()


def _sanitized_git_args(repo_path: str, command: str, args: Iterable[str]) -> list[str]:
    full_args = ['git', '-C', repo_path, command]
    if command in ('diff', 'show', 'log'):
        full_args.extend(('--diff-algorithm=default', '--find-renames',
                            '--inter-hunk-context=0', '--no-notes', '--pretty=medium',
                            '--word-diff=none', '-O/dev/null'))
    full_args.extend(args)
    return full_args


def _run_git_raw(repo_path: str, command: str, args: Iterable[str],
                 handled_errors: Iterable[int] = ()) -> bytes:
    """Runs an external git command `command`, passing `args` to it.
    Returns stdout of the git command (as bytes).
    Raises GitError on failure. If `handled_errors` is provided, raises _HandledError for
    return codes specified in `handled_errors`."""
    full_args = _sanitized_git_args(repo_path, command, args)
    result = subprocess.run(full_args, env=_sanitized_git_env,
                            check=False, text=False,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode == 0:
        return result.stdout
    if result.returncode in handled_errors:
        raise _HandledError(result.returncode, result.stdout)
    raise GitExecError(full_args, result.stderr)


def _run_git(repo_path: str, command: str, args: Iterable[str],
             handled_errors: Iterable[int] = ()) -> str:
    """Runs an external git command `command`, passing `args` to it.
    Returns stdout of the git command (as a string).
    For more details, see `_run_git_raw`."""
    return (_run_git_raw(repo_path, command, args, handled_errors)
            .decode('utf-8', errors='replace'))


def _run_git_progress(repo_path: str, command: str, args: Iterable[str],
                      progress: Callable[[str], None],
                      handled_errors: Iterable[int] = ()) -> str:
    """Runs an external git command `command`, passing `args` to it.
    Passes parts of the stderr until the comand finishes.
    Returns stdout of the git command (as a string).
    Raises GitError on failure or _HandledError for return codes in `handled_errors`."""
    full_args = _sanitized_git_args(repo_path, command, args)
    o_r, o_w = os.pipe2(os.O_NONBLOCK)
    e_r, e_w = os.pipe()
    result = subprocess.Popen(full_args, env=_sanitized_git_env,
                              text=False, stdout=o_w, stderr=e_w)
    os.close(e_w)
    os.close(o_w)
    output = bytearray()
    buf = bytearray()
    while True:
        result.poll()
        while True:
            try:
                read = os.read(o_r, 1024)
            except BlockingIOError:
                break
            if not read:
                break
            output.extend(read)
        read = os.read(e_r, 1024)
        if not read and result.returncode is not None:
            break
        buf.extend(read)
        while buf:
            # we need to handle splits in the middle of a utf-8 character
            try:
                data = buf.decode('utf-8', errors='strict')
                buf.clear()
                progress(data)
                break
            except UnicodeDecodeError as e:
                start, end = e.start, e.end
            data = buf[:start].decode('utf-8', errors='strict')
            del buf[:start]
            progress(data)
            if len(buf) < 4:
                break
            # this is not a mid split; it's an invalid character
            del buf[:end - start]
            progress('\ufffd')
    os.close(e_r)
    while True:
        try:
            read = os.read(o_r, 1024)
        except BlockingIOError:
            break
        if not read:
            break
        output.extend(read)
    os.close(o_r)
    if len(buf) > 0:
        progress(buf.decode('utf-8', errors='replace'))
    if result.returncode == 0:
        return output.decode('utf-8', errors='replace')
    if result.returncode in handled_errors:
        raise _HandledError(result.returncode, output)
    raise GitExecError(full_args)


def _run_git_records(repo_path: str, command: str, args: Iterable[str],
                    separator: str = '\0',
                    handled_errors: Iterable[int] = ()) -> Iterator[str]:
    """Runs an external git command `command`, passing `args` to it.
    Yields the output split by the separator; the separator is not included.
    Raises GitError on failure or _HandledError for return codes in `handled_errors`."""
    full_args = _sanitized_git_args(repo_path, command, args)
    o_r, o_w = os.pipe()
    e_r, e_w = os.pipe2(os.O_NONBLOCK)
    result = subprocess.Popen(full_args, env=_sanitized_git_env,
                                text=False,
                                stdout=o_w, stderr=e_w)
    os.close(e_w)
    os.close(o_w)
    bin_separator = separator.encode()
    buf = bytearray()
    stderr = bytearray()
    while True:
        pos = buf.find(bin_separator)
        if pos < 0:
            result.poll()
            while True:
                try:
                    read = os.read(e_r, 1024)
                except BlockingIOError:
                    break
                if not read:
                    break
                stderr.extend(read)
            read = os.read(o_r, 1024)
            if not read and result.returncode is not None:
                break
            buf.extend(read)
            continue
        yield buf[:pos].decode('utf-8', errors='replace')
        del buf[:pos+1]
    os.close(o_r)
    while True:
        try:
            read = os.read(e_r, 1024)
        except BlockingIOError:
            break
        if not read:
            break
        stderr.extend(read)
    os.close(e_r)
    if len(buf) > 0:
        yield buf.decode('utf-8', errors='replace')
    if result.returncode == 0:
        return
    if result.returncode in handled_errors:
        raise _HandledError(result.returncode)
    raise GitExecError(full_args, stderr)
