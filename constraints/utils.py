# pyright: strict, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false
from itertools import pairwise
from typing import Any, Iterable

from pycsp3.classes.main.variables import Variable
import pycsp3.functions as pycsp3f


def alternate[T](xs: Iterable[T], ys: Iterable[T]) -> Iterable[T]:
    """alternate([a0, ..., ak], [b0, ..., bk]) = [a0, b0, a1, b1, ..., ak, bk]"""
    ai = xs.__iter__()
    bi = ys.__iter__()
    try:
        while True:
            yield next(ai)
            (ai, bi) = (bi, ai)
    except StopIteration:
        return


def domUnion(vs: Iterable[Variable]) -> set[int]:
    return set(x for v in vs for x in v.dom)  # pyright: ignore[reportAttributeAccessIssue]


def build_pair_order_violation_array(as_: list[Any], bs: list[Any], id: str) -> Variable:
    pairs = list(pairwise(alternate(as_, bs)))
    arr = pycsp3f.VarArray(size=len(pairs), dom=[0, 1], id=id)
    pycsp3f.satisfy(
        arr[i] == (a >= b)  # 1 iff the wrong way around
        for (i, (a, b)) in enumerate(pairs)
    )
    return arr
