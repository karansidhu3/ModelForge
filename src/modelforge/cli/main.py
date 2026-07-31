"""The `modelforge` command-line entrypoint.

Argument parsing and table formatting only — every call delegates to
`experiments.tracker` for the actual work. See DD-005 in
`DESIGN_DECISIONS.md`.
"""

from __future__ import annotations

from pathlib import Path

import typer

from modelforge.experiments.tracker import DEFAULT_RUNS_DIR, ExperimentRecord, load_experiments

app = typer.Typer(
    help="ModelForge: an engineering framework for translating quantitative "
    "research into tested, reproducible software."
)
experiments_app = typer.Typer(help="Inspect tracked experiment runs.")
app.add_typer(experiments_app, name="experiments")


@experiments_app.command("list")
def list_experiments(
    runs_dir: Path = typer.Option(  # noqa: B008 — Typer's supported pattern for options
        DEFAULT_RUNS_DIR, help="Directory containing recorded run JSON files."
    ),
) -> None:
    """Summarize tracked experiment runs as a table, oldest first."""
    records = load_experiments(runs_dir)

    if not records:
        typer.echo(f"No tracked experiments found under {runs_dir}.")
        return

    for line in _format_table(records):
        typer.echo(line)


def _format_table(records: list[ExperimentRecord]) -> list[str]:
    columns = ("run_id", "timestamp", "model", "params", "runtime_ms", "passed")
    rows = [
        (
            record.run_id[:8],
            record.timestamp,
            record.model_name,
            str(record.params),
            f"{record.runtime_seconds * 1000:.2f}",
            str(record.validation_passed),
        )
        for record in records
    ]

    widths = [max(len(columns[i]), *(len(row[i]) for row in rows)) for i in range(len(columns))]
    header = "  ".join(col.ljust(width) for col, width in zip(columns, widths, strict=True))
    separator = "  ".join("-" * width for width in widths)
    body = [
        "  ".join(cell.ljust(width) for cell, width in zip(row, widths, strict=True))
        for row in rows
    ]

    return [header, separator, *body]


if __name__ == "__main__":
    app()
