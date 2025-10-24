from typing import Iterable, Self


class Enumerate[T]:
    def __init__(
        self,
        iterable: Iterable[T],
        start: int = 0,
    ) -> None:
        self.iterable = iter(iterable)
        self.start = start - 1

    def __iter__(self) -> Self:
        return self

    def __next__(self) -> tuple[T, int]:
        self.start += 1

        try:
            return (next(self.iterable), self.start)
        except IndexError:
            raise StopIteration
