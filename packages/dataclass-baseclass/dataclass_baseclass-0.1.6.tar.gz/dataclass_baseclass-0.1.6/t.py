from dataclasses import dataclass
from typing import Protocol


class A:
    s: str


@dataclass
class P(Protocol):
    s: str


@dataclass
class B(P):
    i: int


b = B(1)
