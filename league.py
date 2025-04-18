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

class Fixture:
    """A match between two teams."""
    def __init__(self, home: Team, away: Team, date: date | None = None):
        self.home = home
        self.away = away
        self.date = date
        self.ref = z3.Int(self.name())
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

class Division:
    """A division in the chess league."""
    def __init__(self, name: str, teams: list[Team]):
        self.name = name
        self.teams = teams
        self.fixtures = [Fixture(home, away) for home in teams for away in teams if home != away]

class League:
    """A chess league."""
    def __init__(self, name: str, start: date, end: date, divisions: list[Division]):
        assert(end > start)
        self.name = name
        self.start = start
        self.end = end
        self.divisions = divisions

    def venues(self) -> set[tuple[Venue, Weekday]]:
        return set((t.club.venue, t.club.weekday) for d in self.divisions for t in d.teams)

def season202425() -> League:
    bramcote = Venue("Bramcote Memorial Hall")
    brownCow = Venue("Brown Cow")
    coronation = Venue("Coronation Social Club")
    embankment = Venue("The Embankment Pub")
    gonerby = Venue("Great Gonerby Social Club")
    legion = Venue("Royal British Legion Club")
    monica = Venue("Monica Partridge Building")
    poacher = Venue("The Lincolnshire Poacher")
    railway = Venue("The Railway Club")
    wolds = Venue("The Wolds Pub")

    ashfield = Club("Ashfield", coronation, Weekday.WEDNESDAY)
    beeston = Club("Beeston", bramcote, Weekday.TUESDAY)
    central = Club("Nottingham Central", embankment, Weekday.TUESDAY)
    gambit = Club("Gambit", poacher, Weekday.TUESDAY)
    grantham = Club("Grantham", gonerby, Weekday.WEDNESDAY)
    mansfield = Club("Mansfield", brownCow, Weekday.THURSDAY)
    newark = Club("Newark", railway, Weekday.MONDAY)
    nomads = Club("Nomads", embankment, Weekday.MONDAY)
    radcliffeBingham = Club("Radcliffe & Bingham", legion, Weekday.MONDAY)
    university = Club("University", monica, Weekday.WEDNESDAY)
    westBridgford = Club("West Bridgford", wolds, Weekday.MONDAY)
    westNottingham = Club("West Nottingham", bramcote, Weekday.TUESDAY)

    div1 = Division("Division 1", [Team(gambit), Team(gambit), Team(grantham), Team(nomads), Team(mansfield), Team(newark), Team(university), Team(westBridgford)])
    div2 = Division("Division 2", [Team(ashfield), Team(ashfield), Team(beeston), Team(grantham), Team(nomads), Team(radcliffeBingham), Team(westBridgford), Team(westNottingham)])
    div3 = Division("Division 3", [Team(central, "Central 1"), Team(gambit), Team(gambit), Team(gambit), Team(newark), Team(university), Team(radcliffeBingham), Team(westNottingham)])
    div4 = Division("Division 4", [Team(ashfield), Team(ashfield), Team(gambit), Team(grantham), Team(nomads), Team(westBridgford), Team(westNottingham)])
    div5 = Division("Division 5", [Team(radcliffeBingham), Team(radcliffeBingham), Team(newark), Team(grantham), Team(gambit), Team(central, "Central 2"), Team(beeston)])

    return League("Notts League 2024/25", date(2024, 9, 1), date(2025, 5, 15), [div1, div2, div3, div4, div5])
