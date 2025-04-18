from datetime import date
from z3 import z3

from league import *

def arrangeFixtures(league: League) -> None:
    """Update every fixture of the given league with dates that
    fit the necessary constraints."""

    def dateToInt(x: date) -> int:
        return x.toordinal() - league.start.toordinal()

    def intToDate(x: int) -> date:
        return date.fromordinal(x + league.start.toordinal())

    def weekdayToInt(x: Weekday) -> int:
        """dateToInt(x) % 7 == weekdayToInt(Weekday(x.isoweekday()))"""
        offset = league.start.isoweekday()
        return (x.value - offset) % 7

    def possibleDays(x: Weekday) -> range:
        return range(weekdayToInt(x), dateToInt(league.end) - 1, 7)

    s = z3.Solver()

    # Constraints on single fixtures
    for d in league.divisions:
        for f in d.fixtures:
            # Allow for fixture dates to be decided manually.
            if f.date is not None:
                s.add(f.ref == dateToInt(f.date))

            # Constraint: played within start/end dates.
            s.add(f.ref >= dateToInt(league.start), f.ref <= dateToInt(league.end))

            # Constraint: played on venue's weekday.
            s.add(f.ref % 7 == weekdayToInt(f.weekday()))

            # Constraint: matches between teams of the same club must be played by 31 Jan.
            if f.sameClub():
                s.add(f.ref <= dateToInt(date(league.end.year, 1, 31)))

    # Constraint: teams can only play one fixture per day.
    for d in league.divisions:
        for t in d.teams:
            s.add(z3.Distinct(*[f.date for f in t.fixtures]))

    # Constraint: venues have a maximum number of matches per day.
    for (v, wd) in league.venues():
        for d in possibleDays(wd):
            s.add(z3.PbLe([(f.ref == d, 1) for f in v.fixtures], v.maxMatchesPerDay))

    # Constraint: first matches of a club's teams in a division are between themselves.
    hasFirstMatchConstraint = set()
    for d in league.divisions:
        for t in d.teams:
            if t not in hasFirstMatchConstraint:
                hasFirstMatchConstraint.add(t)
                candidates = [f for f in t.fixtures if f.home == t and f.sameClub()]
                if len(candidates) > 0:
                    best = [f for f in candidates if f.away not in hasFirstMatchConstraint]
                    chosen = best[0] if len(best) > 0 else candidates[0]
                    s.add([chosen.ref < f.ref for f in t.fixtures if chosen != f])
                    hasFirstMatchConstraint.add(chosen.away)

    return
