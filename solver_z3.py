# pyright: strict, reportUnknownMemberType=false
from datetime import date
from z3 import z3 # pyright: ignore [reportMissingTypeStubs]

from league import *
from solver_base import SolverBase, UnsatisfiableConstraints

class Solver(SolverBase):
    """Update every fixture of the given league with dates that
    fit the necessary constraints."""
    def __init__(self, league: League):
        super().__init__(league)
        self.solver = z3.Solver()
        self.constraints = False

    def __createConstraints(self) -> None:
        if self.constraints:
            return
        self.constraints = True

        # Constraints on single fixtures
        for d in self.league.divisions:
            for f in d.fixtures:
                # Allow for fixture dates to be decided manually.
                if f.date is not None:
                    self.solver.add(f.z3 == self.dateToInt(f.date))

                # Constraint: played within start/end dates.
                self.solver.add(f.z3 >= self.dateToInt(self.league.start), f.z3 <= self.dateToInt(self.league.end))

                # Constraint: played on venue's weekday.
                self.solver.add(f.z3 % 7 == self.weekdayToInt(f.weekday))

                # Constraint: not played on a holiday.
                self.solver.add([f.z3 != self.dateToInt(holiday) for holiday in self.league.holidays.get(f.weekday, frozenset())])

                # Constraint: matches between teams of the same club must be played by 31 Jan.
                if f.sameClub():
                    self.solver.add(f.z3 <= self.dateToInt(date(self.league.end.year, 1, 31)))

        # Constraint: teams can only play one fixture per day.
        for d in self.league.divisions:
            for t in d.teams:
                self.solver.add(z3.Distinct(*[f.z3 for f in t.fixtures]))

        # Constraint: venues have a maximum number of matches per day.
        for (v, wd) in self.league.venuesWeekdays:
            for d in self.possibleDays(wd):
                self.solver.add(z3.PbLe([(f.z3 == d, 1) for f in v.fixtures], v.maxMatchesPerDay))

        # Constraint: first matches of a club's teams in a division are between themselves.
        hasFirstMatchConstraint: set[Team] = set()
        for d in self.league.divisions:
            for t in d.teams:
                if t not in hasFirstMatchConstraint:
                    hasFirstMatchConstraint.add(t)
                    candidates = [f for f in t.fixtures if f.home == t and f.sameClub()]
                    if len(candidates) > 0:
                        best = [f for f in candidates if f.away not in hasFirstMatchConstraint]
                        chosen = best[0] if len(best) > 0 else candidates[0]
                        self.solver.add([chosen.z3 < f.z3 for f in t.fixtures if chosen != f])
                        hasFirstMatchConstraint.add(chosen.away)

    def solve(self) -> None:
        self.__createConstraints()
        r = self.solver.check()
        if r == z3.unknown:
            raise UnsatisfiableConstraints(self.solver.reason_unknown())
        elif r == z3.unsat:
            raise UnsatisfiableConstraints(str(self.solver.unsat_core()))

        m = self.solver.model()
        for d in self.league.divisions:
            for f in d.fixtures:
                v = m[f.z3] # pyright: ignore[reportUnknownVariableType]
                if isinstance(v, z3.BitVecNumRef):
                    f.date = self.intToDate(v.as_long())
                else:
                    raise Exception(f"{f.z3} is not a BitVecNumRef")
