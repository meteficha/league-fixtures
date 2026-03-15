# pyright: strict, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false
from itertools import pairwise

import pycsp3.functions as pycsp3f
from league import League

from .base import CheckResult, Constraint, ConstraintContext
from .utils import cap_reasons, ratio_score


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

    def check(self, league: League) -> CheckResult:
        if not self.enabled:
            return CheckResult(score=1.0, reasons=[])

        satisfied = 0
        total = 0
        reasons: list[str] = []
        for c in league.clubs:
            if c.relaxed:
                continue
            for (t1, t2) in pairwise(c.teams):
                fixtures = [f for t in [t1, t2] for f in t.fixtures if f.teams != frozenset([t1, t2])]
                fixtures = [f for f in fixtures if f.date is not None]
                for i in range(len(fixtures)):
                    for j in range(i + 1, len(fixtures)):
                        total += 1
                        if fixtures[i].date != fixtures[j].date:
                            satisfied += 1
                        else:
                            reasons.append(
                                f"{c.name}: adjacent teams {t1.name}/{t2.name} both play on {fixtures[i].date}"
                            )

        score = ratio_score(satisfied, total)
        return CheckResult(score=score, reasons=[] if score == 1.0 else cap_reasons(reasons))
