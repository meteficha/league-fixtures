'''Generate league fixtures for the Nottingham Chess League.

Constraints:

    - League rules constraints: <https://www.nottinghamshirechess.org/league-rules/>

        - (B1) League runs from 1 Sep to 15 May

        - (B4) If two or more teams from the same club play in the same division,
          the first match(es) of the club's teams in that division shall be between them(selves).
          Matches between teams from the same club must be played by 31st January.

    - Venues can only host 2 games per day by default.

Desirable properties:

    - Last fixture should be scheduled at least 5 weeks away from league end.

    - Teams alternate between playing at home and away.
'''

import click
import json
from typing import Literal

from league import League
from report import Report
import export_csv

@click.group()
def cli():
    pass

@cli.command()
@click.option('--example', default='notts_season202526', help='The example league to save')
@click.argument('output')
def save(example: str, output: str) -> None:
    '''Save a hardcoded league example as a JSON file.'''
    league = None
    match example:
        case 'notts_season202425':
            import notts
            league = notts.season202425()
        case 'notts_season202526':
            import notts
            league = notts.season202526()
        case _:
            raise Exception("Unknown example " + example)
    print('Saving example league file')
    with open(output, "w") as f:
        json.dump(league.to_json(), f, sort_keys=True, indent=4, separators=(',', ': '))

@cli.command()
@click.option('--output', help='Output to a different file, instead of overwriting input')
@click.option('--solver', default='ACE', help='Which solver to use (ACE or CHOCO)')
@click.option('--options', help='Options to pass to the solver (e.g., "-rr" for ACE to use ACE-mix or "-p 6" for CHOCO to use 6 threads)')
@click.argument('input')
def solve(input: str, output: str | None, solver: Literal['ACE', 'CHOCO'], options: str | None) -> None:
    '''Solve any fixtures without dates from the input file.'''
    output = input if output is None else output
    if options is None:
        options = '-rr' if solver == 'ACE' else ''

    print('Loading data')
    league = None
    with open(input, "r") as f:
        league = League.from_json(json.load(f))

    print(f'Creating solver ({solver} {options})')
    from solver_pycsp3 import Solver
    s = Solver(league, solver, options)

    print('Solving')
    s.solve()

    print('Saving solved league file')
    with open(output, "w") as f:
        json.dump(league.to_json(), f, sort_keys=True, indent=4, separators=(',', ': '))

@cli.command()
@click.option('--output', help='Output to a different file, instead of just adding an .html suffix')
@click.argument('input')
def report(input: str, output: str | None) -> None:
    '''Generate an HTML report from a league file.'''
    output = input + '.html' if output is None else output

    print('Loading data')
    league = None
    with open(input, "r") as f:
        league = League.from_json(json.load(f))

    print('Saving report')
    Report(league).saveTo(output)

@cli.command()
@click.option('--output', help='Output to a different file, instead of just adding an .csv suffix')
@click.argument('input')
def csv(input: str, output: str | None) -> None:
    '''Generate a CSV report from a league file. Can be used with the ECF LMS importer.'''
    output = input + '.csv' if output is None else output

    print('Loading data')
    league = None
    with open(input, "r") as f:
        league = League.from_json(json.load(f))

    print('Saving CSV')
    with open(output, "w") as f:
        export_csv.write(f, league)

if __name__ == '__main__':
    cli()
