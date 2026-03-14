from __future__ import annotations

from datetime import date

from constraints import OnlyWhenConstraint, SingleFixtureDomainConstraint
from league import OnlyWhen

from .helpers import assert_sat, assert_unsat, mk_club, mk_fixture, mk_league, mk_team, mk_venue


def _league_for_only_when(constrained_date: date, reference_date: date):
    vc = mk_venue("VC")
    vr = mk_venue("VR")
    vo = mk_venue("VO")

    constrained = mk_club("Constrained", vc)
    reference = mk_club("Reference", vr)
    opp = mk_club("Opp", vo)

    tc = mk_team(constrained, "C1")
    tr = mk_team(reference, "R1")
    to = mk_team(opp, "O1")

    f_constrained = mk_fixture(tc, to, constrained_date)
    f_reference = mk_fixture(tr, to, reference_date)
    f_balanced = mk_fixture(to, tc, date(2025, 10, 6))
    ow = OnlyWhen(constrained=constrained, reference=reference)

    return mk_league(teams=[tc, tr, to], fixtures=[f_constrained, f_reference, f_balanced], only_when=[ow])


def test_only_when_sat() -> None:
    league = _league_for_only_when(date(2025, 9, 1), date(2025, 9, 1))
    constraints = [SingleFixtureDomainConstraint(), OnlyWhenConstraint()]
    assert_sat(league, constraints)


def test_only_when_unsat() -> None:
    league = _league_for_only_when(date(2025, 9, 8), date(2025, 9, 1))
    constraints = [SingleFixtureDomainConstraint(), OnlyWhenConstraint()]
    assert_unsat(league, constraints)
