# pyright: strict, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false
from typing import Any

import pycsp3.functions as pycsp3f

from .base import Constraint, ConstraintContext


class VenueAssignedDaysObjectiveConstraint(Constraint):
    def apply(self, ctx: ConstraintContext) -> Any:
        print("\t\tVenues have matches assigned to most of their days")
        return pycsp3f.Sum(
            pycsp3f.NValues(ctx.vars[f] for f in v.fixtures)
            for v in ctx.solver.league.venues
            if not v.minimizeEmptyDays
            if len(v.fixtures) >= 2
        )
