from enum import Enum

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
    def __init__(self, name: str, maxGamesPerDay: int = 2):
        self.name = name
        self.maxGamesPerDay = maxGamesPerDay

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
        club.teams.append(self)

class Division:
    """A division in the chess league."""
    def __init__(self, name: str, teams: list[Team]):
        self.name = name
        self.teams = teams

class League:
    """A chess league."""
    def __init__(self, name: str, divisions: list[Division]):
        self.name = name
        self.divisions = divisions

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

    return League("Notts League 2024/25", [div1, div2, div3, div4, div5])
