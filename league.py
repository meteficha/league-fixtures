from datetime import date
from enum import Enum
from functools import cached_property
from pycsp3.classes.main.variables import Variable
from typing import Iterable, Self
from z3 import z3

class Weekday(Enum):
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6
    SUNDAY = 7

    @classmethod
    def fromDate(cls: type[Self], d: date) -> Self:
        return cls(d.isoweekday())

class Venue:
    """A venue is a place that clubs use to schedule their matches.

    Multiple clubs may play on the same venue.
    """
    def __init__(self, name: str, maxMatchesPerDay: int = 2):
        self.name = name
        self.maxMatchesPerDay = maxMatchesPerDay
        self.fixtures: list[Fixture] = []

class Club:
    """A chess club."""
    def __init__(self, name: str, venue: Venue, weekday: Weekday):
        self.name = name
        self.venue = venue
        self.weekday = weekday
        self.teams: list[Team] = []

class Team:
    """A team from a chess club."""
    def __init__(self, club: Club, name: str | None = None):
        self.club = club
        self.name = club.name + " " + str(len(club.teams) + 1) if name is None else name
        self.fixtures: list[Fixture] = []
        club.teams.append(self)

    def __str__(self) -> str:
        return self.name

class Fixture:
    """A match between two teams."""
    def __init__(self, home: Team, away: Team, date: date | None = None):
        self.home = home
        self.away = away
        self.date = date
        self.pycsp3: Variable | None = None
        self.z3 = z3.BitVec(self.name, 10)
        home.fixtures.append(self)
        away.fixtures.append(self)
        self.venue.fixtures.append(self)

    @property
    def venue(self) -> Venue:
        return self.home.club.venue

    @property
    def weekday(self) -> Weekday:
        return self.home.club.weekday

    @cached_property
    def name(self) -> str:
        return self.home.name + " x " + self.away.name

    @cached_property
    def sanitized_name(self) -> str:
        return self.name.replace(" ", "_").replace("&", "_")

    @cached_property
    def teams(self) -> frozenset[Team]:
        return frozenset([self.home, self.away])

    def sameClub(self) -> bool:
        return self.home.club == self.away.club

    def __str__(self) -> str:
        dateStr = str(self.date) if self.date else "????-??-??"
        return f"{dateStr} {self.name}"

class Division:
    """A division in the chess league."""
    def __init__(self, name: str, teams: list[Team]):
        self.name = name
        self.teams = teams
        self.fixtures = [Fixture(home, away) for home in teams for away in teams if home != away]

    def __str__(self) -> str:
        r = f'= {self.name} =\nTeams:\n'
        for ts in sorted(map(str, self.teams)):
            r += '    ' + ts + '\n'

        r += '\nFixtures:\n'
        for f in sorted(self.fixtures, key=lambda f: (f.date or date(2000, 1, 1), f.name)):
            r += '    ' + str(f) + '\n'

        return r

    @cached_property
    def fixturePairs(self) -> frozenset[frozenset[Fixture]]:
        """All fixtures in the division, paired so that T1 v T2 and T2 v T1 are together.
        All inner sets have two Fixtures in them."""
        toAdd = self.fixtures.copy()
        ret = set()
        while toAdd:
            f1 = toAdd.pop()
            f2 = next(f for f in toAdd if f.teams == f1.teams)
            toAdd.remove(f2)
            ret.add(frozenset({f1, f2}))
        return frozenset(ret)

class Calendar:
    """A set of holidays."""
    def __init__(self, holidays: Iterable[date]):
        self.holidays = frozenset(holidays)

    @classmethod
    def empty(cls: type[Self]) -> Self:
        return cls([])

class League:
    """A chess league."""
    def __init__(self, name: str, start: date, end: date, divisions: list[Division], calendar: Calendar = Calendar.empty()):
        assert(end > start)
        self.name = name
        self.start = start
        self.end = end
        self.divisions = divisions
        self.calendar = calendar

    def __str__(self) -> str:
        r = f'=== {self.name} (from {self.start} until {self.end}) ===\n'
        for d in self.divisions:
            r += '\n' + str(d)
        return r

    @cached_property
    def venues(self) -> frozenset[tuple[Venue, Weekday]]:
        return frozenset((t.club.venue, t.club.weekday) for d in self.divisions for t in d.teams)

    @cached_property
    def holidays(self) -> dict[Weekday, frozenset[date]]:
        r: dict[Weekday, set[date]] = dict()
        for d in self.calendar.holidays:
            if self.start <= d <= self.end:
                r.setdefault(Weekday.fromDate(d), set()).add(d)
        return {k: frozenset(v) for (k, v) in r.items()}

    @cached_property
    def clubs(self) -> frozenset[Club]:
        return frozenset(t.club for d in self.divisions for t in d.teams)
