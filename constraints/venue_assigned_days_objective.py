# pyright: strict, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false
import pycsp3.functions as pycsp3f

from .base import Constraint, ConstraintContext


class VenueAssignedDaysObjectiveConstraint(Constraint):
    def objective_term(self, ctx: ConstraintContext):
        print("\t\tVenues have matches assigned to most of their days")
        return pycsp3f.Sum(
            pycsp3f.NValues(ctx.vars[f] for f in v.fixtures)
            for v in ctx.solver.league.venues
            if not v.minimizeEmptyDays
        )
