# pyright: strict, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false
from datetime import date

import pycsp3.functions as pycsp3f

from .base import Constraint, ConstraintContext


class VenueDailyCapacityConstraint(Constraint):
    def apply(self, ctx: ConstraintContext) -> None:
        print("\t\tVenues have a maximum number of matches per day")
        for v in ctx.solver.league.venues:
            dom: set[date] = {d for f in v.fixtures for d in ctx.vars[f].dom}  # pyright: ignore[reportAttributeAccessIssue]
            pycsp3f.satisfy(
                pycsp3f.Cardinality(
                    [ctx.vars[f] for f in v.fixtures],
                    occurrences={d: range(0, v.maxMatchesPerDay + 1) for d in dom},
                )
            )
