"""Cube Budget Optimizer CLI entrypoint."""

import typer

from cube_budget.cli.commands.clean import clean
from cube_budget.cli.commands.doctor import doctor
from cube_budget.cli.commands.export import export_cmd
from cube_budget.cli.commands.optimize import optimize
from cube_budget.cli.commands.report import report
from cube_budget.cli.commands.stats import stats
from cube_budget.cli.commands.update_cache import update_cache

app = typer.Typer(
    name="cube-budget",
    help="Cube Budget Optimizer - minimize stores and price for Magic card purchases",
    no_args_is_help=True,
)

app.command(name="optimize")(optimize)
app.command(name="update-cache")(update_cache)
app.command(name="report")(report)
app.command(name="export")(export_cmd)
app.command(name="clean")(clean)
app.command(name="doctor")(doctor)
app.command(name="stats")(stats)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
