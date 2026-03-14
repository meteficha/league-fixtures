# pyright: strict, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false
import pycsp3.functions as pycsp3f

from .base import Constraint, ConstraintContext


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
