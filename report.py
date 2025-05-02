# pyright: strict, reportCallIssue=false, reportGeneralTypeIssues=false
from airium import Airium # pyright: ignore[reportMissingTypeStubs]
from datetime import timedelta

from league import *

class Heatmap:
    def __init__(self, league: League):
        self.league = league
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

    def table(self) -> list[list[tuple[date, int]]]:
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
                            holiday = ' heat-holiday' if self.league.calendar.isHoliday(date) else ''
                            a.td(klass='heat-' + str(max(0, min(4, count))) + holiday + ' heat-day-' + str(date))

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
        self.renderByDivision(a)
        self.renderByVenue(a)
        self.renderByTeam(a)

    def renderByDivision(self, a: Airium) -> None:
        a.h2(_t='Fixtures by division')
        for d in self.league.divisions:
            a.h3(_t=d.name)
            self.renderFixtureTable(a, d.fixtures)

    def renderByVenue(self, a: Airium) -> None:
        a.h2(_t='Fixtures by venue')
        for (v, wd) in sorted(self.league.venues, key=lambda t: (t[0].name, t[1])):
            a.h3(_t=v.name + ' on a ' + wd.name.capitalize())
            self.renderFixtureTable(a, byDate(f for f in v.fixtures if f.weekday == wd))

    def renderByTeam(self, a: Airium) -> None:
        a.h2(_t='Fixtures by team')
        for c in self.league.clubs:
            a.h3(_t=c.name)
            for t in c.teams:
                a.h4(_t=t.name)
                self.renderFixtureTable(a, byDate(t.fixtures))

    def renderFixtureTable(self, a: Airium, fixtures: Iterable[Fixture]) -> None:
        self.renderHeatmap(a, fixtures)

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

    def renderHeatmap(self, a: Airium, fixtures: Iterable[Fixture]) -> None:
        h = Heatmap(self.league)
        h.addAll(fixtures)
        h.render(a)

    @cached_property
    def weekCount(self) -> int:
        return self.league.end.isocalendar().week - self.league.start.isocalendar().week + 1

    def style(self, a: Airium) -> None:
        a.link(rel='preconnect', href='https://fonts.googleapis.com')
        a.link(rel='preconnect', href='https://fonts.gstatic.com', crossorigin=True)
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
            ''')
