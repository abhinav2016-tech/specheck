from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from . import __version__
from .engine import has_errors, run
from .parser import parse_spl
from .report import to_html, to_json
from .rules import load_spec

app = typer.Typer(add_completion=False, help="Verify pharma documentation against a spec.")


@app.command()
def check(
    document: Annotated[Path, typer.Argument(exists=True, help="SPL XML file")],
    spec: Annotated[Path, typer.Option("--spec", "-s", exists=True, help="YAML spec")],
    out: Annotated[
        Path | None, typer.Option("--out", "-o", help="Write report (.html or .json)")
    ] = None,
):
    """Check DOCUMENT against SPEC. Exit code 1 if any error-severity rule fails."""
    sp, label = load_spec(spec), parse_spl(document)
    findings = run(sp, label)
    for f in findings:
        mark = "PASS" if f.status == "pass" else f"FAIL[{f.severity}]"
        typer.echo(f"{mark:14} {f.rule_id:10} {f.message}")
    if out:
        out.write_text(
            to_html(sp, label, findings) if out.suffix == ".html" else to_json(sp, label, findings)
        )
        typer.echo(f"report written to {out}")
    raise typer.Exit(1 if has_errors(findings) else 0)


@app.command()
def version():
    """Print version."""
    typer.echo(__version__)


if __name__ == "__main__":
    app()
