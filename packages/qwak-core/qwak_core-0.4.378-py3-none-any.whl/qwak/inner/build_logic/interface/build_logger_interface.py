from __future__ import annotations

from abc import ABC, abstractmethod


class BuildLogger(ABC):
    verbose: int
    json_logs: bool

    @abstractmethod
    def error(self, line: str) -> None:
        pass

    @abstractmethod
    def exception(self, line: str, e: BaseException) -> None:
        pass

    @abstractmethod
    def warning(self, line: str) -> None:
        pass

    @abstractmethod
    def info(self, line: str) -> None:
        pass

    @abstractmethod
    def debug(self, line: str) -> None:
        pass
