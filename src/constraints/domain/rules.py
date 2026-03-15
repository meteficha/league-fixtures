# pyright: strict, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false
from datetime import date

from league import Fixture

from ..base import ConstraintContext, DomainConstraint


class FixtureWeekdayDomainConstraint(DomainConstraint):
    def apply_to_fixture_domain(self, ctx: ConstraintContext, fixture: Fixture, domain: set[int]) -> set[int]:
        return domain.intersection(ctx.solver.possibleDays(fixture.weekday))


class ClubLateStartDomainConstraint(DomainConstraint):
    def apply_to_fixture_domain(self, ctx: ConstraintContext, fixture: Fixture, domain: set[int]) -> set[int]:
        start: int = max(
            ctx.solver.dateToInt(d)
            for d in [ctx.solver.league.start, fixture.home.club.lateStart, fixture.away.club.lateStart]
            if d is not None
        )
        return {d for d in domain if d >= start}


class LeagueHolidayDomainConstraint(DomainConstraint):
    def apply_to_fixture_domain(self, ctx: ConstraintContext, fixture: Fixture, domain: set[int]) -> set[int]:
        del fixture
        ret = set(domain)
        ret.difference_update(ctx.solver.holidaysLeague)
        return ret


class VenueHolidayDomainConstraint(DomainConstraint):
    def apply_to_fixture_domain(self, ctx: ConstraintContext, fixture: Fixture, domain: set[int]) -> set[int]:
        ret = set(domain)
        ret.difference_update(ctx.solver.holidaysPerVenue[fixture.venue])
        return ret


class ClubHolidayDomainConstraint(DomainConstraint):
    def apply_to_fixture_domain(self, ctx: ConstraintContext, fixture: Fixture, domain: set[int]) -> set[int]:
        ret = set(domain)
        ret.difference_update(ctx.solver.holidaysPerClub[fixture.home.club])
        ret.difference_update(ctx.solver.holidaysPerClub[fixture.away.club])
        return ret


class TeamHolidayDomainConstraint(DomainConstraint):
    def apply_to_fixture_domain(self, ctx: ConstraintContext, fixture: Fixture, domain: set[int]) -> set[int]:
        ret = set(domain)
        ret.difference_update(ctx.solver.holidaysPerTeam[fixture.home])
        ret.difference_update(ctx.solver.holidaysPerTeam[fixture.away])
        return ret


class SameClubDeadlineDomainConstraint(DomainConstraint):
    def apply_to_fixture_domain(self, ctx: ConstraintContext, fixture: Fixture, domain: set[int]) -> set[int]:
        if not fixture.sameClub():
            return set(domain)
        deadline = ctx.solver.dateToInt(date(ctx.solver.league.end.year, 1, 31))
        return {d for d in domain if d <= deadline}


class FixedDateDomainConstraint(DomainConstraint):
    def apply_to_fixture_domain(self, ctx: ConstraintContext, fixture: Fixture, domain: set[int]) -> set[int]:
        if fixture.date is None:
            return set(domain)
        return domain.intersection({ctx.solver.dateToInt(fixture.date)})


def create_default_domain_constraints() -> list[DomainConstraint]:
    return [
        FixtureWeekdayDomainConstraint(),
        ClubLateStartDomainConstraint(),
        LeagueHolidayDomainConstraint(),
        VenueHolidayDomainConstraint(),
        ClubHolidayDomainConstraint(),
        TeamHolidayDomainConstraint(),
        SameClubDeadlineDomainConstraint(),
        FixedDateDomainConstraint(),
    ]
