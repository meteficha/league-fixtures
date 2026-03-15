# pyright: strict, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false
import pycsp3.functions as pycsp3f
from league import League

from .base import CheckResult, Constraint, ConstraintContext
from .utils import cap_reasons, ratio_score


class OnlyWhenConstraint(Constraint):
    def apply(self, ctx: ConstraintContext) -> None:
        print("\t\tOnly when constraints")
        for ow in ctx.solver.league.onlyWhen:
            print(
                "\t\t\t" + ow.constrained.name + " plays at home only when " + ow.reference.name + " plays at home",
                end="",
                flush=True,
            )
            unconstrainedArray = []
            if ow.unconstrainedDays and len(ow.unconstrainedDays.holidays) > 0:
                unconstrainedDates = [ctx.solver.dateToInt(d) for d in ow.unconstrainedDays.holidays] if ow.unconstrainedDays else []
                unconstrainedArray = pycsp3f.VarArray(
                    size=len(unconstrainedDates),
                    dom=unconstrainedDates,
                    id="unconstrainedArray_" + ow.constrained.sanitized_name + "_" + ow.reference.sanitized_name,
                )
                pycsp3f.satisfy(unconstrainedArray[i] == unconstrainedDates[i] for i in range(len(unconstrainedDates)))
            for t in ow.constrained.teams:
                for f in t.homeFixtures:
                    pycsp3f.satisfy(
                        pycsp3f.Exist([ctx.homeFixtureArrays[t2] for t2 in ow.reference.teams] + [v for v in unconstrainedArray], value=ctx.vars[f])
                    )
            print(".")

    def check(self, league: League) -> CheckResult:
        satisfied = 0
        total = 0
        reasons: list[str] = []

        for ow in league.onlyWhen:
            allowed_dates = {f.date for t in ow.reference.teams for f in t.homeFixtures if f.date is not None}
            if ow.unconstrainedDays is not None:
                allowed_dates.update(ow.unconstrainedDays.holidays)

            for t in ow.constrained.teams:
                for f in t.homeFixtures:
                    if f.date is None:
                        continue
                    total += 1
                    if f.date in allowed_dates:
                        satisfied += 1
                    else:
                        reasons.append(
                            f"OnlyWhen violated: {ow.constrained.name} home fixture {f.name} on {f.date}"
                        )

        score = ratio_score(satisfied, total)
        return CheckResult(score=score, reasons=[] if score == 1.0 else cap_reasons(reasons))
