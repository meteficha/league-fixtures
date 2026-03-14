# pyright: strict, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false
from typing import Any

import pycsp3.functions as pycsp3f

from .base import Constraint, ConstraintContext


class TeamNoOverlapAndSpacingConstraint(Constraint):
    def __init__(self, strictMatchSpaceOut: int | None = 5) -> None:
        self.strictMatchSpaceOut = strictMatchSpaceOut
        self._optSpaceTeams: Any = 0

    def apply(self, ctx: ConstraintContext) -> None:
        print("\t\tTeams can only play one fixture per day / Space out the matches of a team")
        self._optSpaceTeams = 0
        spaceNoMoreOpt = pycsp3f.Var(dom=[7 * 3], id="spaceNoMoreOpt")
        for t in ctx.solver.league.teams:
            minimum = self.strictMatchSpaceOut if self.strictMatchSpaceOut is not None and not t.relaxed else 1
            arr = pycsp3f.VarArray(
                size=len(t.fixtures),
                dom=range(minimum, 365),
                id="SpaceOut_NoOverlap_" + t.sanitized_name,
            )
            pycsp3f.satisfy(pycsp3f.NoOverlap(origins=[ctx.vars[f] for f in t.fixtures], lengths=arr))
            self._optSpaceTeams += pycsp3f.Sum(10 * pycsp3f.Minimum(v, spaceNoMoreOpt) for v in arr)

    def objective_term(self, _ctx: ConstraintContext) -> Any:
        return self._optSpaceTeams
