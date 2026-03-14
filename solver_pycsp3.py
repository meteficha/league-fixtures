# pyright: strict, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false
from datetime import date
from typing import Any, Literal, Sequence

from pycsp3.classes.main.variables import Variable
from pycsp3.tools.curser import ListVar
import pycsp3
import pycsp3.classes.entities as pycsp3ce
import pycsp3.functions as pycsp3f

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

    def dom(self, f: Fixture) -> set[int]:
        # Constraint: respects club late starts.
        start: int = max(self.dateToInt(d) for d in [self.league.start, f.home.club.lateStart, f.away.club.lateStart] if d is not None)

        # Constraint: played within start/end dates.
        # Constraint: played on venue's weekday.
        ret = {d for d in self.possibleDays(f.weekday) if d >= start}

        # Constraint: not played on a holiday.
        ret.difference_update(self.holidaysLeague)
        ret.difference_update(self.holidaysPerVenue[f.venue])
        ret.difference_update(self.holidaysPerClub[f.home.club])
        ret.difference_update(self.holidaysPerClub[f.away.club])
        ret.difference_update(self.holidaysPerTeam[f.home])
        ret.difference_update(self.holidaysPerTeam[f.away])

        # Constraint: matches between teams of the same club must be played by 31 Jan.
        if f.sameClub():
            ret = {d for d in ret if d <= self.dateToInt(date(self.league.end.year, 1, 31))}

        # Allow for fixture dates to be decided manually.
        if f.date is not None:
            ret.intersection_update({self.dateToInt(f.date)})

        return ret

    def __createConstraints(self) -> None:
        if self.constraintsCreated:
            self.vars = {}
            pycsp3ce.clear()
        self.constraintsCreated = True

        ctx = ConstraintContext(solver=self)

        objective_terms: list[Any] = []
        for constraint in self.constraintsPipeline:
            constraint.apply(ctx)
            objective_terms.append(constraint.objective_term(ctx))

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
        r = pycsp3.solve(solver=self.solver, options=self.solverOptions, verbose=0)
        if r is not pycsp3.SAT and r is not pycsp3.OPTIMUM:
            raise UnsatisfiableConstraints(str(r))

        if r is pycsp3.OPTIMUM:
            print("\n\n\tFound the best solution. Wow!")
        print("\n\n\tExtracting solution")
        for f in self.league.fixtures:
            v = pycsp3f.value(self.vars[f])
            if isinstance(v, int):
                f.date = self.intToDate(v)
            else:
                raise Exception(f"pycsp3f.value({self.vars[f]}) is {v}, not an int")


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
