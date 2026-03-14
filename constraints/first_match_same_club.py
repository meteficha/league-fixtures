# pyright: strict, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false
import pycsp3.functions as pycsp3f

from league import Team

from .base import Constraint, ConstraintContext


class FirstMatchSameClubConstraint(Constraint):
    def apply(self, ctx: ConstraintContext) -> None:
        print("\t\tFirst matches of a club's teams in a division are between themselves")
        hasFirstMatchConstraint: set[Team] = set()
        for t in ctx.solver.league.teams:
            if t not in hasFirstMatchConstraint:
                hasFirstMatchConstraint.add(t)
                candidates = [f for f in t.fixtures if f.home == t and f.sameClub()]
                if len(candidates) > 0:
                    best = [f for f in candidates if f.away not in hasFirstMatchConstraint]
                    chosen = best[0] if len(best) > 0 else candidates[0]
                    ctx.firstMatches.add(chosen)
                    pycsp3f.satisfy(
                        ctx.vars[chosen] < ctx.vars[f]  # pyright: ignore[reportOperatorIssue]
                        for u in chosen.teams
                        for f in u.fixtures
                        if f not in ctx.firstMatches
                    )
                    hasFirstMatchConstraint.add(chosen.away)
