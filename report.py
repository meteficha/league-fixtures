# pyright: strict, reportCallIssue=false, reportGeneralTypeIssues=false
from airium import Airium # pyright: ignore[reportMissingTypeStubs]
from datetime import timedelta
from itertools import chain, groupby

from league import *

class WeekSection:
    def __init__(self, league: League, extraCalendars: Iterable[Calendar] = []):
        self.league = league
        self.extraCalendars = extraCalendars

    @cached_property
    def start(self) -> date:
        """Last Monday on or before league start"""
        return self.league.start - timedelta(days=self.league.start.weekday())

    @cached_property
    def end(self) -> date:
        """First Sunday on or after league end"""
        return self.league.end + timedelta(days=6 - self.league.end.weekday())

    @cached_property
    def weekCount(self) -> int:
        """Number of weeks in heatmap"""
        return ((self.end - self.start).days + 1) // 7

    def weekOf(self, x: date | Fixture) -> int:
        '''
            x.weekOf(start) == 0
            x.weekOf(end) == x.weekCount - 1
        '''
        if isinstance(x, Fixture):
            if x.date is None:
                return -1
            x = x.date
        return (x - self.start).days // 7

    def isHoliday(self, date: date) -> bool:
        return any(c.isHoliday(date) for c in chain([self.league.calendar], self.extraCalendars))

class Heatmap(WeekSection):
    def __init__(self, league: League, extraCalendars: Iterable[Calendar] = []):
        super().__init__(league, extraCalendars)
        self.points: dict[date, int] = dict()

    def add(self, point: Fixture | date) -> None:
        if isinstance(point, Fixture):
            if point.date is None:
                return
            point = point.date
        self.points[point] = self.points.get(point, 0) + 1

    def addAll(self, points: Iterable[Fixture | date]) -> None:
        for p in points:
            self.add(p)

    def table(self) -> list[list[tuple[date, int]]]: # weekdays, weeks, actual date + fixture count
        ret: list[list[tuple[date, int]]] = []
        for i in range(7):
            cur: list[tuple[date, int]] = []
            d = self.start + timedelta(days=i)
            for _ in range(self.weekCount):
                cur.append((d, self.points.get(d, 0)))
                d += timedelta(days=7)
            ret.append(cur)
        return ret

    def render(self, a: Airium) -> None:
        with a.table(klass='heatmap'):
            with a.tbody():
                for row in self.table():
                    with a.tr():
                        for (date, count) in row:
                            holiday = ' heat-holiday' if self.isHoliday(date) else ''
                            a.td(klass='heat-' + str(max(0, min(4, count))) + holiday + ' heat-day-' + str(date))

class BaseSummary(WeekSection):
    @cached_property
    def teams(self) -> Iterable[Team]:
        return [t for c in sorted(self.league.clubs, key=lambda c: c.name) for t in c.teams]

    @cached_property
    def divisionOf(self) -> dict[Team, int]:
        return { t: i+1 for (i, d) in enumerate(self.league.divisions) for t in d.teams }

    def renderTeam(self, a: Airium, t: Team):
        a.abbr(_t=t.acronym, title=t.name)

class TeamSummary(BaseSummary):
    def table(self) -> list[tuple[date, list[list[Fixture]]]]: # weeks, home team, fixture list for that week
        fixturesByWeek: dict[int, dict[Team, list[Fixture]]] = dict()
        for f in self.league.fixtures:
            weekDict = fixturesByWeek.setdefault(self.weekOf(f), dict())
            weekDict.setdefault(f.home, []).append(f)
            weekDict.setdefault(f.away, []).append(f)
        return [(self.start + timedelta(days=7*wk), [fixturesByWeek.get(wk, dict()).get(t, []) for t in self.teams]) for wk in range(self.weekCount)]

    def render(self, a: Airium) -> None:
        with a.table(klass='team_summary'):
            with a.thead():
                with a.tr():
                    a.th(colspan='2')
                    for (c, ts) in groupby(self.teams, key=lambda t: t.club):
                        a.th(_t=c.name, klass='club', colspan=str(len(list(ts))))
                with a.tr():
                    a.th(_t='Week commencing', klass='week', colspan='2')
                    for t in self.teams:
                        with a.th(klass='team division_' + str(self.divisionOf[t])):
                            self.renderTeam(a, t)
            with a.tbody():
                for (i, (date, row)) in enumerate(self.table()):
                    with a.tr():
                        a.td(_t=str(i+1), klass='week')
                        a.td(_t=str(date), klass='week')
                        for (team, fixtures) in zip(self.teams, row):
                            if not fixtures:
                                a.td(klass='team empty')
                            else:
                                atHome = fixtures[0].home == team
                                homeAway = 'home' if atHome else 'away'
                                division = 'division_' + str(self.divisionOf[fixtures[0].away])
                                with a.td(klass='team full ' + division + ' ' + homeAway):
                                    for (i, f) in enumerate(sorted(fixtures, key=lambda f: f.date or -1)):
                                        if i > 0:
                                            # We don't expect two fixtures in the same week.
                                            # But this code path supports it anyway.
                                            a(" | ")
                                        self.renderTeam(a, atHome and f.away or f.home)

class DivisionSummary(BaseSummary):
    def table(self) -> list[dict[date, list[list[Fixture]]]]: # weeks, fixture date, division, fixtures list for that day/division
        ret: list[dict[date, list[list[Fixture]]]] = [dict() for _ in range(self.weekCount)]
        for f in self.league.fixtures:
            if f.date:
                ret[self.weekOf(f)].setdefault(f.date, [[] for _ in self.league.divisions])[self.divisionOf[f.home]-1].append(f)
        return ret

    def render(self, a: Airium) -> None:
        with a.table(klass='division_summary'):
            with a.thead():
                with a.tr():
                    a.th(_t='Week', klass='week', rowspan='2')
                    a.th(_t='Date', klass='date', rowspan='2', colspan='2')
                    for d in self.league.divisions:
                        a.th(_t=d.name, colspan='2')
                with a.tr():
                    for _ in self.league.divisions:
                        a.th(_t='Home', klass='home')
                        a.th(_t='Away', klass='away')
            with a.tbody():
                odd = True
                for (i, weekDict) in enumerate(self.table()):
                    weekNoStr = str(i+1)
                    weekRowCount = sum(max(len(fixtures) for fixtures in day) for day in weekDict.values())
                    for (date, divisions) in sorted(weekDict.items()):
                        dateRowCount = max(len(fixtures) for fixtures in divisions)
                        for dateRow in range(dateRowCount):
                            with a.tr(klass=odd and 'odd' or 'even'):
                                if weekNoStr:
                                    a.td(_t=str(i+1), klass='week', rowspan=str(weekRowCount))
                                    weekNoStr = None
                                if date:
                                    a.td(_t=str(date), klass='date', rowspan=str(dateRowCount))
                                    a.td(_t=Weekday.fromDate(date).name.capitalize()[:3], klass='date', rowspan=str(dateRowCount))
                                    date = None
                                for division in divisions:
                                    if dateRow < len(division):
                                        fixture = division[dateRow]
                                        with a.td(klass='home empty'):
                                            self.renderTeam(a, fixture.home)
                                        with a.td(klass='away empty'):
                                            self.renderTeam(a, fixture.away)
                                    else:
                                        a.td(klass='home empty')
                                        a.td(klass='away empty')
                    if weekRowCount >= 1:
                        odd = not odd

class Report:
    def __init__(self, league: League):
        self.league = league

    def saveTo(self, fp: str) -> None:
        a = Airium()
        a('<!DOCTYPE html>')
        with a.html(lang='en'):
            with a.head():
                a.meta(charset='utf-8')
                a.title(_t=self.league.name)
                self.style(a)
            with a.body():
                self.render(a)
        with open(file=fp, mode='w') as f:
            f.write(str(a))

    def render(self, a: Airium) -> None:
        a.h1(_t=self.league.name)
        self.renderHeatmap(a, self.league.fixtures)
        self.renderTeamSummary(a)
        self.renderDivisionSummary(a)
        self.renderByDivision(a)
        self.renderByTeam(a)
        self.renderByVenue(a)

    def renderTeamSummary(self, a: Airium) -> None:
        a.h2(_t='Team summary')
        TeamSummary(self.league).render(a)

    def renderDivisionSummary(self, a: Airium) -> None:
        a.h2(_t='Division summary')
        DivisionSummary(self.league).render(a)

    def renderByDivision(self, a: Airium) -> None:
        a.h2(_t='Fixtures by division')
        for d in self.league.divisions:
            a.h3(_t=d.name)
            self.renderFixtureTable(a, d.fixtures)

    def renderByVenue(self, a: Airium) -> None:
        a.h2(_t='Fixtures by venue')
        for (v, wd) in sorted(self.league.venuesWeekdays, key=lambda t: (t[0].name, t[1])):
            a.h3(_t=v.name + ' on a ' + wd.name.capitalize())
            self.renderFixtureTable(a, byDate(f for f in v.fixtures if f.weekday == wd), [v.calendar])

    def renderByTeam(self, a: Airium) -> None:
        a.h2(_t='Fixtures by team')
        for c in sorted(self.league.clubs, key=lambda c: c.name):
            a.h3(_t=c.name)
            for t in c.teams:
                a.h4(_t=t.name)
                self.renderFixtureTable(a, byDate(t.fixtures), [c.calendar, t.calendar])

    def renderFixtureTable(self, a: Airium, fixtures: Iterable[Fixture], extraCalendars: Iterable[Calendar] = []) -> None:
        self.renderHeatmap(a, fixtures, extraCalendars)

        with a.table(klass='fixture'):
            with a.thead():
                with a.tr():
                    a.th(_t='Date', klass='date')
                    a.th(_t='Home', klass='home')
                    a.th(_t='Away', klass='away')
                    a.th(_t='Venue', klass='venue')
                    a.th(_t='Weekday', klass='weekday')
            with a.tbody():
                for f in byDate(fixtures):
                    with a.tr():
                        a.td(_t=str(f.date), klass='date')
                        a.td(_t=f.home.name, klass='home')
                        a.td(_t=f.away.name, klass='away')
                        a.td(_t=f.venue.name, klass='venue')
                        a.td(_t=f.weekday.name.capitalize(), klass='weekday')

    def renderHeatmap(self, a: Airium, fixtures: Iterable[Fixture], extraCalendars: Iterable[Calendar] = []) -> None:
        h = Heatmap(self.league, extraCalendars)
        h.addAll(fixtures)
        h.render(a)

    @cached_property
    def weekCount(self) -> int:
        return self.league.end.isocalendar().week - self.league.start.isocalendar().week + 1

    def style(self, a: Airium) -> None:
        a.link(rel='preconnect', href='https://fonts.googleapis.com')
        a.link(rel='preconnect', href='https://fonts.gstatic.com', crossorigin='true')
        a.link(href='https://fonts.googleapis.com/css2?family=Lato:ital,wght@0,100;0,300;0,400;0,700;0,900;1,100;1,300;1,400;1,700;1,900&display=swap', rel='stylesheet')
        a.style(_t='''
            body {
                font-family: "Lato", sans-serif;
                font-weight: 400;
                font-style: normal;
                font-size: 14pt;
                margin: 2em;
            }

            h2 {
                padding-top: 2em;
            }

            .fixture {
                border-spacing: 0;
            }

            .fixture td, .fixture th{
                padding: 0.25em 0.75em;
            }

            .fixture th {
                border-bottom: solid 1pt black;
                text-align: center;
            }

            .fixture .home {
                text-align: right;
                padding-right: 0.4em;
            }

            .fixture .away {
                text-align: left;
                padding-left: 0.4em;
            }

            .heatmap {
                border: solid 1pt black;
                margin: 0.75em;
            }

            .heatmap td {
                padding: 0.5em;
                border: 1px solid transparent;
            }

            .heatmap .heat-0 {
                background: rgb(243, 243, 243);
            }

            .heatmap .heat-1 {
                background: rgb(172, 238, 187);
            }

            .heatmap .heat-2 {
                background: rgb(74, 194, 107);
            }

            .heatmap .heat-3 {
                background: rgb(45, 164, 78);
            }

            .heatmap .heat-4 {
                background: rgb(17, 99, 41);
            }

            .heatmap .heat-holiday {
                border: 1px solid blueviolet;
            }

            .team_summary, .team_summary th, .team_summary td {
                font-size: 10pt;
                border: 1px solid rgb(200, 200, 200);
                border-collapse: collapse;
            }

            .team_summary .team.home.division_1, .team_summary .team.home.division_6 {
                background: rgb(172, 238, 187);
            }

            .team_summary .team.home.division_2, .team_summary .team.home.division_7 {
                background: rgb(238, 172, 187);
            }

            .team_summary .team.home.division_3, .team_summary .team.home.division_8 {
                background: rgb(172, 187, 238);
            }

            .team_summary .team.home.division_4, .team_summary .team.home.division_9 {
                background: rgb(238, 187, 172);
            }

            .team_summary .team.home.division_5, .team_summary .team.home.division_10 {
                background: rgb(187, 172, 238);
            }

            .team_summary .team.away {
                background: rgb(200, 200, 200);
            }

            .division_summary, .division_summary th, .division_summary td {
                font-size: 12pt;
                border: 1px solid rgb(200, 200, 200);
                border-collapse: collapse;
            }

            .division_summary tr.odd td {
                background: rgb(225, 225, 225);
            }

            .division_summary .home {
                text-align: right;
            }
            ''')
