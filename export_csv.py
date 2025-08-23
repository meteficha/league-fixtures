# pyright: strict
from __future__ import annotations

from league import *
import csv

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from _typeshed import SupportsWrite

def write(output: SupportsWrite[str], league: League):
    writer = csv.writer(output)
    for d in league.divisions:
        for f in sorted(d.fixtures, key=lambda f:(f.date, f.home.name, f.away.name)):
            writer.writerow([d.name, f.home.name, f.away.name, f.date and str(f.date) or "<undefined>"])
