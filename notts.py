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
            calendar=Calendar(
                { date(2024, 12, i) for i in range(23, 32) } |
                { date(2025, 1, i) for i in range(1, 6) } |
                { date(2025, 4, 1), date(2025, 5, 5) }
            ))


def season202526() -> League:
    westNottsSchoolHolidays = Calendar(
        { date(2025, 10, i) for i in range(20, 32) } |
        { date(2026, 2, i) for i in range(16, 21) } |
        { date(2026, 5, i) for i in range(25, 32) }
        )
    universityHolidays = Calendar(
        { date(2026, 1, i) for i in range(1, 12) } |
        { date(2026, 3, i) for i in range(28, 32) } |
        { date(2026, 4, i) for i in range(1, 27) }
        )

    bramcote = Venue("Bramcote Memorial Hall", maxMatchesPerDay=3, minimizeEmptyDays=True)
    brownCow = Venue("Brown Cow", calendar=Calendar({date(2025, 12, i) for i in range(1,32)}))
    coronation = Venue("Coronation Social Club", maxMatchesPerDay=2)
    embankment = Venue("The Embankment Pub", maxMatchesPerDay=3)
    gonerby = Venue("Great Gonerby Social Club", maxMatchesPerDay=2)
    legion = Venue("Royal British Legion Club", maxMatchesPerDay=3)
    monica = Venue(
        "Monica Partridge Building",
        maxMatchesPerDay=1,
        calendar=universityHolidays
        )
    poacher = Venue("The Lincolnshire Poacher", maxMatchesPerDay=2) # max 2 "if possible"
    railway = Venue("The Railway Club", maxMatchesPerDay=1, calendar=Calendar({date(2025, 10, i) for i in range(1,7)}))
    wolds = Venue("The Wolds Pub")

    ashfield = Club(
        "Ashfield",
        coronation,
        Weekday.WEDNESDAY,
        lateStart=date(2025, 9, 15)
        )
    westNottingham = Club(
        "West Nottingham",
        bramcote,
        Weekday.TUESDAY,
        lateStart=date(2025, 9, 8)
        )
    beeston = Club(
        "Beeston",
        bramcote,
        Weekday.TUESDAY
        )
    central = Club(
        "Nottingham Central",
        embankment,
        Weekday.TUESDAY,
        lateStart=date(2025, 9, 16),
        calendar=Calendar({date(2025, 12, 9), date(2026, 1, 27)})
        )
    gambit = Club(
        "Gambit",
        poacher,
        Weekday.TUESDAY
        )
    grantham = Club(
        "Grantham",
        gonerby,
        Weekday.WEDNESDAY
        )
    mansfield = Club(
        "Mansfield",
        brownCow,
        Weekday.THURSDAY,
        lateStart=date(2025, 9, 22)
        )
    newark = Club(
        "Newark",
        railway,
        Weekday.MONDAY,
        lateStart=date(2025, 10, 6)
        )
    nomads = Club(
        "Nomads",
        embankment,
        Weekday.MONDAY
        )
    radcliffeBingham = Club(
        "Radcliffe & Bingham",
        legion,
        Weekday.MONDAY,
        lateStart=date(2025, 9, 8),
        calendar=Calendar({date(2026, 4, 6), date(2026, 5, 4), date(2026, 5, 11 )})
        )
    university = Club(
        "University",
        monica,
        Weekday.WEDNESDAY,
        lateStart=date(2025, 9, 27),
        calendar=universityHolidays
        )
    westBridgford = Club(
        "West Bridgford",
        wolds,
        Weekday.MONDAY,
        lateStart=date(2025, 9, 29),
        calendar=Calendar(
            {date(2025, 12, i) for i in range(17, 24)} |
            {date(2026, 2, i) for i in range(2, 6)} |
            {date(2026, 3, i) for i in range(30, 32)} |
            {date(2026, 4, i) for i in range(1, 3)}
            )
        )

    div1 = Division(
        "Division 1",
        [Team(mansfield),
         Team(university),
         Team(gambit),
         Team(grantham),
         Team(westBridgford, calendar=Calendar(
             {date(2025, 10, i) for i in range(20,31)} |
             {date(2026, 2, i) for i in range(16, 21)}
             )),
         Team(newark),
         Team(beeston),
         Team(radcliffeBingham),
         Team(ashfield),
        ])
    div2 = Division(
        "Division 2",
        [Team(gambit),
         Team(nomads),
         Team(westBridgford),
         Team(westNottingham, calendar=westNottsSchoolHolidays),
         Team(grantham),
         Team(gambit),
         Team(radcliffeBingham, calendar=Calendar({date(2025, 9, 8)})),
         Team(ashfield),
         ])
    div3 = Division(
        "Division 3",
        [Team(nomads),
         Team(university),
         Team(gambit),
         Team(newark),
         Team(gambit),
         Team(beeston),
         Team(ashfield),
         Team(grantham),
         ])
    div4 = Division(
        "Division 4",
        [Team(westNottingham),
         Team(central, "Central 1"),
         Team(nomads),
         Team(radcliffeBingham),
         Team(radcliffeBingham),
         Team(gambit),
         Team(ashfield),
         Team(grantham),
         ])
    div5 = Division(
        "Division 5",
        [Team(ashfield),
         Team(beeston),
         Team(radcliffeBingham),
         Team(radcliffeBingham),
         Team(newark),
         Team(gambit),
         Team(central, "Central 2"),
         Team(westNottingham, calendar=westNottsSchoolHolidays),
         ])

    return League(
            name="Notts League 2025/26",
            start=date(2025, 9, 6),
            end=date(2026, 5, 9),
            divisions=[div1, div2, div3, div4, div5],
            onlyWhen={ OnlyWhen(constrained=beeston, reference=westNottingham) },
            calendar=Calendar(
                { date(2025, 12, i) for i in range(21, 32) } | # Christmas
                { date(2026, 1, i) for i in range(1, 5) } | # New Year
                { date(2026, 4, 3), date(2026, 4, 6) } | # Easter
                { date(2026, 5, 4) } | # Early May bank holiday
                { date(2026, 5, 25) } # Spring bank holiday
            ))
