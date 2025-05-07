from league import *

def season202425() -> League:
    bramcote = Venue("Bramcote Memorial Hall", maxMatchesPerDay=3, minimizeEmptyDays=True)
    brownCow = Venue("Brown Cow")
    coronation = Venue("Coronation Social Club")
    embankment = Venue("The Embankment Pub", maxMatchesPerDay=3, calendar=Calendar({date(2025, 1, 14), date(2025, 2, 25)}))
    gonerby = Venue("Great Gonerby Social Club")
    legion = Venue("Royal British Legion Club")
    monica = Venue("Monica Partridge Building")
    poacher = Venue("The Lincolnshire Poacher")
    railway = Venue("The Railway Club", maxMatchesPerDay=3)
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
    university = Club("University", monica, Weekday.WEDNESDAY, lateStart=date(2024, 10, 15), calendar=Calendar({date(2024, 12, i) for i in range(16, 21)}))
    westBridgford = Club("West Bridgford", wolds, Weekday.MONDAY, calendar=Calendar({date(2024, 10, i) for i in range(21, 26)}))
    westNottingham = Club("West Nottingham", bramcote, Weekday.TUESDAY, calendar=Calendar({date(2024, 10, i) for i in range(21, 31)}))

    div1 = Division("Division 1", [Team(gambit), Team(gambit), Team(grantham), Team(nomads), Team(mansfield), Team(newark), Team(university), Team(westBridgford)])
    div2 = Division("Division 2", [Team(ashfield), Team(ashfield), Team(beeston), Team(grantham), Team(nomads), Team(radcliffeBingham), Team(westBridgford), Team(westNottingham)])
    div3 = Division("Division 3", [Team(central, "Central 1"), Team(gambit), Team(gambit), Team(gambit), Team(newark), Team(university), Team(radcliffeBingham), Team(westNottingham)])
    div4 = Division("Division 4", [Team(ashfield), Team(ashfield), Team(gambit), Team(grantham), Team(nomads), Team(westBridgford), Team(westNottingham)])
    div5 = Division("Division 5", [Team(radcliffeBingham), Team(radcliffeBingham), Team(newark), Team(grantham), Team(gambit), Team(central, "Central 2"), Team(beeston)])

    return League(
            "Notts League 2024/25",
            date(2024, 9, 9),
            date(2025, 5, 1),
            [div1, div2, div3, div4, div5],
            Calendar(
                { date(2024, 12, i) for i in range(23, 32) } |
                { date(2025, 1, i) for i in range(1, 6) } |
                { date(2025, 4, 1), date(2025, 5, 5) }
            ))
