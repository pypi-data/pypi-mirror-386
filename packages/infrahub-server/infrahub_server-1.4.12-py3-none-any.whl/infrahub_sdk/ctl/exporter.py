from asyncio import run as aiorun
from datetime import datetime, timezone
from pathlib import Path

import typer
from rich.console import Console

from ..ctl.client import initialize_client
from ..transfer.exceptions import TransferError
from ..transfer.exporter.json import LineDelimitedJSONExporter
from .parameters import CONFIG_PARAM


def directory_name_with_timestamp() -> str:
    right_now = datetime.now(timezone.utc).astimezone()
    timestamp = right_now.strftime("%Y%m%d-%H%M%S")
    return f"infrahubexport-{timestamp}"


def dump(
    namespace: list[str] = typer.Option([], help="Namespace(s) to export"),
    directory: Path = typer.Option(directory_name_with_timestamp, help="Directory path to store export"),
    quiet: bool = typer.Option(False, help="No console output"),
    _: str = CONFIG_PARAM,
    branch: str = typer.Option(None, help="Branch from which to export"),
    concurrent: int = typer.Option(
        4,
        help="Maximum number of requests to execute at the same time.",
        envvar="INFRAHUB_MAX_CONCURRENT_EXECUTION",
    ),
    timeout: int = typer.Option(60, help="Timeout in sec", envvar="INFRAHUB_TIMEOUT"),
    exclude: list[str] = typer.Option(
        ["CoreAccount"],
        help="Prevent node kind(s) from being exported, CoreAccount is excluded by default",
    ),
) -> None:
    """Export nodes and their relationships out of the database."""
    console = Console()

    client = initialize_client(
        branch=branch, timeout=timeout, max_concurrent_execution=concurrent, retry_on_failure=True
    )

    exporter = LineDelimitedJSONExporter(client, console=Console() if not quiet else None)
    try:
        aiorun(exporter.export(export_directory=directory, namespaces=namespace, branch=branch, exclude=exclude))
    except TransferError as exc:
        console.print(f"[red]{exc}")
        raise typer.Exit(1)
