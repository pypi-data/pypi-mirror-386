#!/usr/bin/env python3

import typer
from pathlib import Path
from dotenv import load_dotenv
from judgeval.logger import judgeval_logger
from judgeval import JudgmentClient
from judgeval.version import get_version

load_dotenv()

app = typer.Typer(
    no_args_is_help=True,
    rich_markup_mode=None,
    rich_help_panel=None,
    pretty_exceptions_enable=False,
    pretty_exceptions_show_locals=False,
    pretty_exceptions_short=False,
)


@app.command("upload_scorer")
def upload_scorer(
    scorer_file_path: str,
    requirements_file_path: str,
    unique_name: str = typer.Option(
        None, help="Custom name for the scorer (auto-detected if not provided)"
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        "-o",
        help="Overwrite existing scorer if it already exists",
    ),
):
    # Validate file paths
    if not Path(scorer_file_path).exists():
        judgeval_logger.error(f"Scorer file not found: {scorer_file_path}")
        raise typer.Exit(1)

    if not Path(requirements_file_path).exists():
        judgeval_logger.error(f"Requirements file not found: {requirements_file_path}")
        raise typer.Exit(1)

    try:
        client = JudgmentClient()

        result = client.upload_custom_scorer(
            scorer_file_path=scorer_file_path,
            requirements_file_path=requirements_file_path,
            unique_name=unique_name,
            overwrite=overwrite,
        )

        if not result:
            judgeval_logger.error("Failed to upload custom scorer")
            raise typer.Exit(1)

        raise typer.Exit(0)
    except Exception:
        raise


@app.command()
def version():
    """Show version info"""
    judgeval_logger.info(f"Judgeval CLI v{get_version()}")


if __name__ == "__main__":
    app()
