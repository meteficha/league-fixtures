# pyright: strict, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false
from typing import Any

import pycsp3.functions as pycsp3f
from league import League

from .base import CheckResult, Constraint, ConstraintContext
from .utils import cap_reasons


class DivisionDaySpreadObjectiveConstraint(Constraint):
    def apply(self, ctx: ConstraintContext) -> Any:
        print("\t\tDivision should have matches on as many days as possible")
        return pycsp3f.Sum(
            pycsp3f.NValues(ctx.vars[f] for f in d.fixtures)
            for d in ctx.solver.league.divisions
        )

    def check(self, league: League) -> CheckResult:
        ratios: list[float] = []
        reasons: list[str] = []

        for d in league.divisions:
            fixtures = [f for f in d.fixtures if f.date is not None]
            if len(fixtures) == 0:
                continue
            distinct_days = len({f.date for f in fixtures})
            ratio = distinct_days / len(fixtures)
            ratios.append(ratio)
            if ratio < 1.0:
                reasons.append(
                    f"Division {d.name} uses {distinct_days} distinct days for {len(fixtures)} fixtures"
                )

        score = 1.0 if len(ratios) == 0 else (sum(ratios) / len(ratios))
        return CheckResult(score=score, reasons=[] if score == 1.0 else cap_reasons(reasons))
