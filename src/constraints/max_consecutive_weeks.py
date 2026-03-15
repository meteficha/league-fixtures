# pyright: strict, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false
import pycsp3.functions as pycsp3f
from league import League

from .base import CheckResult, Constraint, ConstraintContext
from .utils import cap_reasons, ratio_score


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

    def check(self, league: League) -> CheckResult:
        if self.strictMaxNoWeeksWithMatches is None:
            return CheckResult(score=1.0, reasons=[])

        span = self.strictMaxNoWeeksWithMatches + 1
        satisfied = 0
        total = 0
        reasons: list[str] = []

        for t in league.teams:
            if t.relaxed:
                continue
            dates = [f.date for f in t.fixtures if f.date is not None]
            if len(dates) == 0:
                continue
            first = min(dates)
            weeks = {(d - first).days // 7 for d in dates}
            if len(weeks) < span:
                continue
            max_week = max(weeks)
            for w in range(0, max_week - span + 2):
                total += 1
                count = sum(1 for wk in weeks if w <= wk < w + span)
                if count <= self.strictMaxNoWeeksWithMatches:
                    satisfied += 1
                else:
                    reasons.append(
                        f"Team {t.name} has {count} active weeks in window [{w}, {w + span - 1}]"
                    )

        score = ratio_score(satisfied, total)
        return CheckResult(score=score, reasons=[] if score == 1.0 else cap_reasons(reasons))
