# pyright: strict, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false
from typing import Any, Literal, Sequence

from pycsp3.classes.main.variables import Variable
from pycsp3.tools.curser import ListVar
import pycsp3
import pycsp3.classes.entities as pycsp3ce
import pycsp3.functions as pycsp3f
import pycsp3.tools.utilities as pycsp3u

from constraints import (
    AdjacentTeamsDifferentDayConstraint,
    Constraint,
    ConstraintContext,
    DivisionDaySpreadObjectiveConstraint,
    FirstMatchSameClubConstraint,
    FixturePairSpacingConstraint,
    HomeAwayAlternationConstraint,
    MaxConsecutiveWeeksConstraint,
    OnlyWhenConstraint,
    SingleFixtureDomainConstraint,
    TeamNoOverlapAndSpacingConstraint,
    VenueAssignedDaysObjectiveConstraint,
    VenueDailyCapacityConstraint,
    VenueMinimizeEmptyDaysObjectiveConstraint,
    XmasBreakBalanceConstraint,
)
from league import *
from solver_base import SolverBase, UnsatisfiableConstraints


class Solver(SolverBase):
    """Update every fixture of the given league with dates that fit the necessary constraints."""

    created = False

    def __init__(self, league: League, constraints: Sequence[Constraint], solver: Literal["ACE", "CHOCO"] = "ACE", solverOptions: str = ""):
        if Solver.created:
            raise Exception("pycsp3 is silly, you can't create two Solvers")
        Solver.created = True
        super().__init__(league)
        self.constraintsCreated = False
        self.constraintsPipeline = list(constraints)

        self.homeFixtureArrays: dict[Team, ListVar] = dict()
        self.homeFixtureDomains: dict[Team, set[int]] = dict()
        self.vars: dict[Fixture, Variable] = dict()
        self.solver = pycsp3.CHOCO if solver == "CHOCO" else pycsp3.ACE
        self.solverOptions = solverOptions

    def __createConstraints(self) -> None:
        if self.constraintsCreated:
            self.vars = {}
            pycsp3ce.clear()
        self.constraintsCreated = True

        ctx = ConstraintContext(solver=self)

        objective_terms: list[Any] = []
        for constraint in self.constraintsPipeline:
            obj_term = constraint.apply(ctx)
            if obj_term is not None:
                objective_terms.append(obj_term)

        if len(objective_terms) > 0:
            objective = 0
            for term in objective_terms:
                objective += term
            pycsp3f.maximize(objective)

        self.vars = ctx.vars
        self.homeFixtureArrays = ctx.homeFixtureArrays
        self.homeFixtureDomains = ctx.homeFixtureDomains

    def solve(self) -> None:
        print("\tCreating constraints...")
        self.__createConstraints()
        print("\tAsking for a solution... (press Ctrl-C to save best solution so far)\n\n\n")
        r = pycsp3.solve(solver=self.solver, options=self.solverOptions, verbose=0, auto_delete=True)
        if r is not pycsp3.SAT and r is not pycsp3.OPTIMUM:
            raise UnsatisfiableConstraints(str(r))

        if r is pycsp3.OPTIMUM:
            print("\n\n\tFound the best solution. Wow!")
        print("\n\n\tExtracting solution")
        for f in self.league.fixtures:
            var = self.vars[f]
            v = pycsp3f.value(var)
            if isinstance(v, int):
                f.date = self.intToDate(v)
            elif isinstance(v, type(pycsp3u.ANY)):
                dom_values = var.dom.all_values() # pyright: ignore[reportAttributeAccessIssue]
                if len(dom_values) == 1 and isinstance(dom_values[0], int):
                    f.date = self.intToDate(dom_values[0])
                else:
                    raise Exception(f"pycsp3f.value({var}) is a star, domain has values {dom_values}, and is not a single int")
            else:
                raise Exception(f"pycsp3f.value({var}) is {v}, not an int")


def create_default_constraints() -> list[Constraint]:
    return [
        SingleFixtureDomainConstraint(),
        TeamNoOverlapAndSpacingConstraint(strictMatchSpaceOut=5),
        MaxConsecutiveWeeksConstraint(strictMaxNoWeeksWithMatches=2),
        VenueDailyCapacityConstraint(),
        FirstMatchSameClubConstraint(),
        AdjacentTeamsDifferentDayConstraint(enabled=True),
        FixturePairSpacingConstraint(strictFixturePairSpacing=None),
        OnlyWhenConstraint(),
        HomeAwayAlternationConstraint(strictHomeAwayConstraint=None),
        XmasBreakBalanceConstraint(strictXmasBreakDiff=0, strictXmasBreakPercentage=0.8),
        VenueAssignedDaysObjectiveConstraint(),
        VenueMinimizeEmptyDaysObjectiveConstraint(),
        DivisionDaySpreadObjectiveConstraint(),
    ]


def create_solver(league: League, solver: Literal["ACE", "CHOCO"] = "ACE", solverOptions: str = "") -> Solver:
    return Solver(league=league, constraints=create_default_constraints(), solver=solver, solverOptions=solverOptions)


__all__ = [
    "Constraint",
    "ConstraintContext",
    "Solver",
    "create_default_constraints",
    "create_solver",
    "SingleFixtureDomainConstraint",
    "TeamNoOverlapAndSpacingConstraint",
    "MaxConsecutiveWeeksConstraint",
    "VenueDailyCapacityConstraint",
    "FirstMatchSameClubConstraint",
    "AdjacentTeamsDifferentDayConstraint",
    "FixturePairSpacingConstraint",
    "OnlyWhenConstraint",
    "HomeAwayAlternationConstraint",
    "XmasBreakBalanceConstraint",
    "VenueAssignedDaysObjectiveConstraint",
    "VenueMinimizeEmptyDaysObjectiveConstraint",
    "DivisionDaySpreadObjectiveConstraint",
]
