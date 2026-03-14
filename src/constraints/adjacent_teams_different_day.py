# pyright: strict, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false
from itertools import pairwise

import pycsp3.functions as pycsp3f

from .base import Constraint, ConstraintContext


class AdjacentTeamsDifferentDayConstraint(Constraint):
    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled

    def apply(self, ctx: ConstraintContext) -> None:
        if not self.enabled:
            return
        print("\t\tAdjacent teams of a club shouldn't play on the same day")
        pycsp3f.satisfy(
            pycsp3f.AllDifferent(ctx.vars[f] for t in [t1, t2] for f in t.fixtures if not f.teams == frozenset([t1, t2]))
            for c in ctx.solver.league.clubs
            if not c.relaxed
            for (t1, t2) in pairwise(c.teams)
        )
