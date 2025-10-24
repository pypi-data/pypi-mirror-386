
# This is used to make SwiftGUI compatible with python 3.10
def ErrorThrower(text: str, error_type:type = ModuleNotFoundError):
    class ErrorThrower_Class:
        def __init__(self, *_, **__):
            raise error_type(text)

    return ErrorThrower_Class

import sys
from collections.abc import Iterator

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing import TypeVar, Generator

    Self = TypeVar("Self", bound= "Any")

if sys.version_info >= (3, 12):
    from itertools import batched
else:
    # Implement it myself if it's not available...
    def batched(it, n: int) -> Iterator[tuple]:
        collected = list()
        it = list(it)

        num = 0
        for elem in it:
            if num == n:
                num = 0
                yield tuple(collected)
                collected.clear()

            collected.append(elem)
            num += 1

        if collected:
            yield tuple(collected)


