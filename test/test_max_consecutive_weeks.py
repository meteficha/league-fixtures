from __future__ import annotations

from datetime import date

from constraints import MaxConsecutiveWeeksConstraint, SingleFixtureDomainConstraint

from .helpers import assert_sat, assert_unsat, mk_club, mk_fixture, mk_league, mk_team, mk_venue


def _league_for_consecutive_weeks(dates: tuple[date, date, date]):
    va = mk_venue("VA")
    vb = mk_venue("VB")
    vc = mk_venue("VC")
    vd = mk_venue("VD")
    ca = mk_club("A", va)
    cb = mk_club("B", vb)
    cc = mk_club("C", vc)
    cd = mk_club("D", vd)

    ta = mk_team(ca, "A1")
    tb = mk_team(cb, "B1")
    tc = mk_team(cc, "C1")
    td = mk_team(cd, "D1")

    f1 = mk_fixture(ta, tb, dates[0])
    f2 = mk_fixture(tc, ta, dates[1])
    f3 = mk_fixture(ta, td, dates[2])
    f4 = mk_fixture(tb, tc, date(2025, 10, 6))
    f5 = mk_fixture(td, tb, date(2025, 10, 13))
    return mk_league(teams=[ta, tb, tc, td], fixtures=[f1, f2, f3, f4, f5])


def test_max_consecutive_weeks_sat() -> None:
    league = _league_for_consecutive_weeks((date(2025, 9, 1), date(2025, 9, 8), date(2025, 9, 22)))
    constraints = [SingleFixtureDomainConstraint(), MaxConsecutiveWeeksConstraint(strictMaxNoWeeksWithMatches=2)]
    assert_sat(league, constraints)


def test_max_consecutive_weeks_unsat() -> None:
    league = _league_for_consecutive_weeks((date(2025, 9, 1), date(2025, 9, 8), date(2025, 9, 15)))
    constraints = [SingleFixtureDomainConstraint(), MaxConsecutiveWeeksConstraint(strictMaxNoWeeksWithMatches=2)]
    assert_unsat(league, constraints)
