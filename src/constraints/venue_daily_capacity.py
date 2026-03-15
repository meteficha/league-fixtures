# pyright: strict, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false
from datetime import date
from collections import defaultdict

import pycsp3.functions as pycsp3f
from league import League

from .base import CheckResult, Constraint, ConstraintContext
from .utils import cap_reasons, ratio_score


class VenueDailyCapacityConstraint(Constraint):
    def apply(self, ctx: ConstraintContext) -> None:
        print("\t\tVenues have a maximum number of matches per day")
        for v in ctx.solver.league.venues:
            dom: set[date] = {d for f in v.fixtures for d in ctx.vars[f].dom}  # pyright: ignore[reportAttributeAccessIssue]
            pycsp3f.satisfy(
                pycsp3f.Cardinality(
                    [ctx.vars[f] for f in v.fixtures],
                    occurrences={d: range(0, v.maxMatchesPerDay + 1) for d in dom},
                )
            )

    def check(self, league: League) -> CheckResult:
        satisfied = 0
        total = 0
        reasons: list[str] = []

        for v in league.venues:
            per_day: dict[date, int] = defaultdict(int)
            for f in v.fixtures:
                if f.date is not None:
                    per_day[f.date] += 1
            for d, n in per_day.items():
                total += 1
                if n <= v.maxMatchesPerDay:
                    satisfied += 1
                else:
                    reasons.append(
                        f"Venue {v.name} has {n} matches on {d}, capacity is {v.maxMatchesPerDay}"
                    )

        score = ratio_score(satisfied, total)
        return CheckResult(score=score, reasons=[] if score == 1.0 else cap_reasons(reasons))
