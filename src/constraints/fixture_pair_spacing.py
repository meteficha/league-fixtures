# pyright: strict, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false
import pycsp3.functions as pycsp3f
from league import League

from .base import CheckResult, Constraint, ConstraintContext
from .utils import cap_reasons, ratio_score


class FixturePairSpacingConstraint(Constraint):
    def __init__(self, strictFixturePairSpacing: int | None = None) -> None:
        self.strictFixturePairSpacing = strictFixturePairSpacing

    def apply(self, ctx: ConstraintContext) -> None:
        if self.strictFixturePairSpacing is None:
            return
        print(f"\t\tFixture pairs played with time between them ({str(self.strictFixturePairSpacing)} weeks)")
        pycsp3f.satisfy(
            pycsp3f.abs(ctx.vars[f1] - ctx.vars[f2]) >= self.strictFixturePairSpacing * 7  # pyright: ignore[reportOperatorIssue]
            for (f1, f2) in ctx.solver.league.fixturePairs
            if not f1.home.relaxed and not f1.away.relaxed
        )

    def check(self, league: League) -> CheckResult:
        if self.strictFixturePairSpacing is None:
            return CheckResult(score=1.0, reasons=[])

        min_days = self.strictFixturePairSpacing * 7
        satisfied = 0
        total = 0
        reasons: list[str] = []

        for pair in league.fixturePairs:
            fixtures = list(pair)
            if len(fixtures) != 2:
                continue
            f1, f2 = fixtures[0], fixtures[1]
            if f1.home.relaxed or f1.away.relaxed:
                continue
            if f1.date is None or f2.date is None:
                continue
            total += 1
            gap = abs((f1.date - f2.date).days)
            if gap >= min_days:
                satisfied += 1
            else:
                reasons.append(f"Pair {f1.name} / {f2.name} gap {gap}d is below {min_days}d")

        score = ratio_score(satisfied, total)
        return CheckResult(score=score, reasons=[] if score == 1.0 else cap_reasons(reasons))
