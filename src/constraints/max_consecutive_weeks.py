# pyright: strict, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false
import pycsp3.functions as pycsp3f

from .base import Constraint, ConstraintContext


class MaxConsecutiveWeeksConstraint(Constraint):
    def __init__(self, strictMaxNoWeeksWithMatches: int | None = 2) -> None:
        self.strictMaxNoWeeksWithMatches = strictMaxNoWeeksWithMatches

    def apply(self, ctx: ConstraintContext) -> None:
        if self.strictMaxNoWeeksWithMatches is None:
            return
        print("\t\tTeams can only have " + str(self.strictMaxNoWeeksWithMatches) + " consecutive weeks with matches")
        for t in ctx.solver.league.teams:
            if not t.relaxed:
                pycsp3f.satisfy(
                    pycsp3f.Cumulative(
                        origins=[ctx.vars[f] for f in t.fixtures],
                        lengths=(self.strictMaxNoWeeksWithMatches + 1) * 7,
                        heights=1,
                    )
                    <= self.strictMaxNoWeeksWithMatches
                )
