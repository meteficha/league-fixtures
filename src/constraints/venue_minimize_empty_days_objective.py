# pyright: strict, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false
from typing import Any

import pycsp3.functions as pycsp3f

from .base import Constraint, ConstraintContext


class VenueMinimizeEmptyDaysObjectiveConstraint(Constraint):
    def apply(self, _ctx: ConstraintContext) -> None:
        return None

    def objective_term(self, ctx: ConstraintContext) -> Any:
        print("\t\tVenues can choose to minimize empty days")
        return -1 * pycsp3f.Sum(
            pycsp3f.NValues(ctx.vars[f] for f in v.fixtures)
            for v in ctx.solver.league.venues
            if v.minimizeEmptyDays
        )
