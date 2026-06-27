from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from price_monitor_pipeline.monitor import (
    alerts_to_frame,
    evaluate_alerts,
    fetch_snapshots,
    load_watchlist,
    snapshots_to_frame,
    write_csv,
)

app = typer.Typer(help="Track public product prices and write CSV reports.")
console = Console()


@app.command()
def run(
    config: Annotated[Path, typer.Option(help="Watchlist JSON path.")],
    out: Annotated[Path, typer.Option(help="Snapshot CSV path.")] = Path("outputs/snapshot.csv"),
    alerts: Annotated[Path, typer.Option(help="Alerts CSV path.")] = Path("outputs/alerts.csv"),
) -> None:
    watchlist = load_watchlist(config)
    snapshots = asyncio.run(fetch_snapshots(watchlist.items))
    alert_rows = evaluate_alerts(snapshots)

    write_csv(snapshots_to_frame(snapshots), out)
    write_csv(alerts_to_frame(alert_rows), alerts)

    console.print(f"[green]Checked {len(snapshots)} products[/green]")
    console.print(f"[green]Wrote snapshot to {out}[/green]")
    console.print(f"[yellow]Alerts: {len(alert_rows)}[/yellow]")
