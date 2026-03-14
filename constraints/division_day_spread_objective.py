# pyright: strict, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false
from typing import Any

import pycsp3.functions as pycsp3f

from .base import Constraint, ConstraintContext


class DivisionDaySpreadObjectiveConstraint(Constraint):
    def objective_term(self, ctx: ConstraintContext) -> Any:
        print("\t\tDivision should have matches on as many days as possible")
        return pycsp3f.Sum(
            pycsp3f.NValues(ctx.vars[f] for f in d.fixtures)
            for d in ctx.solver.league.divisions
        )
