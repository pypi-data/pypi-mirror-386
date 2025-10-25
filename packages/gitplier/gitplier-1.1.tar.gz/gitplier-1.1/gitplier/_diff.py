from typing import Optional


class Change:
    """Information about a single changed file. This is parsed information from git
    whatchanged. Request the `changes` field to get the list of changes. The attributes are:
    `src_path`, `dst_path`, `src_mode`, `dst_mode`, `status` and `score`."""
    def __init__(self, src_path: str, dst_path: str, src_mode: str, dst_mode: str,
                 status: str, score: Optional[int]) -> None:
        """The constructor is private. Never create instances directly; access them via
        Commit.changes."""
        self.src_path = src_path
        self.dst_path = dst_path
        self.src_mode = src_mode
        self.dst_mode = dst_mode
        self.status = status
        self.score = score

    def __str__(self) -> str:
        score = '' if self.score is None else f'({self.score}%)'
        path = (self.src_path if self.src_path == self.dst_path
                else f'{self.src_path} -> {self.dst_path}')
        return f'{self.status}{score} {path}'
