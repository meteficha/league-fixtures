from datetime import date
from enum import Enum
from z3 import z3

class Weekday(Enum):
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6
    SUNDAY = 7

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
        self.ref = z3.BitVec(self.name(), 10)
        home.fixtures.append(self)
        away.fixtures.append(self)
        self.venue().fixtures.append(self)

    def venue(self) -> Venue:
        return self.home.club.venue

    def weekday(self) -> Weekday:
        return self.home.club.weekday

    def name(self) -> str:
        return self.home.name + " x " + self.away.name

    def sameClub(self) -> bool:
        return self.home.club == self.away.club

    def __str__(self) -> str:
        dateStr = str(self.date) if self.date else "????-??-??"
        return f"{dateStr} {self.name()}"

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
        for f in sorted(self.fixtures, key=lambda f: (f.date or date(2000, 1, 1), f.name())):
            r += '    ' + str(f) + '\n'

        return r

class League:
    """A chess league."""
    def __init__(self, name: str, start: date, end: date, divisions: list[Division]):
        assert(end > start)
        self.name = name
        self.start = start
        self.end = end
        self.divisions = divisions

    def __str__(self) -> str:
        r = f'=== {self.name} (from {self.start} until {self.end}) ===\n'
        for d in self.divisions:
            r += '\n' + str(d)
        return r

    def venues(self) -> set[tuple[Venue, Weekday]]:
        return set((t.club.venue, t.club.weekday) for d in self.divisions for t in d.teams)
