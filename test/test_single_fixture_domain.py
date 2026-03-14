from __future__ import annotations

from datetime import date

from constraints import SingleFixtureDomainConstraint, TeamNoOverlapAndSpacingConstraint

from .helpers import assert_sat, assert_unsat, mk_club, mk_fixture, mk_league, mk_team, mk_venue


def test_single_fixture_domain_sat() -> None:
    v1 = mk_venue("V1")
    v2 = mk_venue("V2")
    c1 = mk_club("C1", v1)
    c2 = mk_club("C2", v2)
    t1 = mk_team(c1, "C1_1")
    t2 = mk_team(c2, "C2_1")

    f1 = mk_fixture(t1, t2, date(2025, 9, 1))
    f2 = mk_fixture(t2, t1, date(2025, 9, 8))
    league = mk_league(teams=[t1, t2], fixtures=[f1, f2])

    assert_sat(league, [SingleFixtureDomainConstraint(), TeamNoOverlapAndSpacingConstraint(strictMatchSpaceOut=1)])


def test_single_fixture_domain_unsat_empty_domain() -> None:
    blocked_day = date(2025, 9, 1)
    v1 = mk_venue("V1")
    v2 = mk_venue("V2")
    c1 = mk_club("C1", v1)
    c2 = mk_club("C2", v2)
    t1 = mk_team(c1, "C1_1")
    t2 = mk_team(c2, "C2_1")
    t1.calendar = t1.calendar.__class__([blocked_day])

    f1 = mk_fixture(t1, t2, blocked_day)
    f2 = mk_fixture(t2, t1, date(2025, 9, 8))
    league = mk_league(teams=[t1, t2], fixtures=[f1, f2])

    assert_unsat(league, [SingleFixtureDomainConstraint()])
