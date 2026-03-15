# pyright: strict, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false
from datetime import date
from typing import Any

import pycsp3.functions as pycsp3f

from .base import Constraint, ConstraintContext


class XmasBreakBalanceConstraint(Constraint):
    def __init__(self, strictXmasBreakDiff: int = 0, strictXmasBreakPercentage: float = 0.8) -> None:
        self.strictXmasBreakDiff = strictXmasBreakDiff
        self.strictXmasBreakPercentage = strictXmasBreakPercentage

    def apply(self, ctx: ConstraintContext) -> Any:
        print("\t\tFixtures should be evenly distributed before/after Xmas break")
        beforeXmasBreakDates = range(ctx.solver.dateToInt(date(ctx.solver.league.end.year, 1, 1)))
        xmasTerms = [
            (len(t.fixtures) // 2, pycsp3f.Count([ctx.vars[f] for f in t.fixtures], values=beforeXmasBreakDates))
            for t in ctx.solver.league.teams
        ]
        xmasArr = pycsp3f.VarArray(size=len(xmasTerms), dom=[0, 1], id="xmasArr")

        if self.strictXmasBreakDiff <= 0:
            pycsp3f.satisfy(xmasArr[i] == (t == u) for (i, (t, u)) in enumerate(xmasTerms))
        else:
            pycsp3f.satisfy(
                xmasArr[i] == (pycsp3f.abs(t - u) <= self.strictXmasBreakDiff)
                for (i, (t, u)) in enumerate(xmasTerms)
            )

        if self.strictXmasBreakPercentage >= 0.99999:
            pycsp3f.satisfy(xmasArr[i] == 1 for i in range(len(xmasTerms)))
            return

        xmasArrCount = pycsp3f.Var(id="xmasArrCount", dom=range(len(xmasTerms) + 1))
        pycsp3f.satisfy(xmasArrCount == pycsp3f.Count(xmasArr, value=1))
        pycsp3f.satisfy(xmasArrCount >= int(len(xmasTerms) * self.strictXmasBreakPercentage))
        return 500 * xmasArrCount
