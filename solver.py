from datetime import date
from z3 import z3

from league import *

class Solver:
    """Update every fixture of the given league with dates that
    fit the necessary constraints."""
    def __init__(self, league: League):
        self.league = league
        self.solver = z3.Solver()
        self.__createConstraints()

    def dateToInt(self, x: date) -> int:
        return x.toordinal() - self.league.start.toordinal()

    def intToDate(self, x: int) -> date:
        return date.fromordinal(x + self.league.start.toordinal())

    def weekdayToInt(self, x: Weekday) -> int:
        """dateToInt(x) % 7 == weekdayToInt(Weekday(x.isoweekday()))"""
        offset = self.league.start.isoweekday()
        return (x.value - offset) % 7

    def possibleDays(self, x: Weekday) -> range:
        return range(self.weekdayToInt(x), self.dateToInt(self.league.end) - 1, 7)

    def __createConstraints(self) -> None:
        # Constraints on single fixtures
        for d in self.league.divisions:
            for f in d.fixtures:
                # Allow for fixture dates to be decided manually.
                if f.date is not None:
                    self.solver.add(f.ref == self.dateToInt(f.date))

                # Constraint: played within start/end dates.
                self.solver.add(f.ref >= self.dateToInt(self.league.start), f.ref <= self.dateToInt(self.league.end))

                # Constraint: played on venue's weekday.
                self.solver.add(f.ref % 7 == self.weekdayToInt(f.weekday()))

                # Constraint: matches between teams of the same club must be played by 31 Jan.
                if f.sameClub():
                    self.solver.add(f.ref <= self.dateToInt(date(self.league.end.year, 1, 31)))

        # Constraint: teams can only play one fixture per day.
        for d in self.league.divisions:
            for t in d.teams:
                self.solver.add(z3.Distinct(*[f.date for f in t.fixtures]))

        # Constraint: venues have a maximum number of matches per day.
        for (v, wd) in self.league.venues():
            for d in self.possibleDays(wd):
                self.solver.add(z3.PbLe([(f.ref == d, 1) for f in v.fixtures], v.maxMatchesPerDay))

        # Constraint: first matches of a club's teams in a division are between themselves.
        hasFirstMatchConstraint = set()
        for d in self.league.divisions:
            for t in d.teams:
                if t not in hasFirstMatchConstraint:
                    hasFirstMatchConstraint.add(t)
                    candidates = [f for f in t.fixtures if f.home == t and f.sameClub()]
                    if len(candidates) > 0:
                        best = [f for f in candidates if f.away not in hasFirstMatchConstraint]
                        chosen = best[0] if len(best) > 0 else candidates[0]
                        self.solver.add([chosen.ref < f.ref for f in t.fixtures if chosen != f])
                        hasFirstMatchConstraint.add(chosen.away)
