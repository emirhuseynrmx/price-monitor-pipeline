from __future__ import annotations

from datetime import datetime, timezone

from typer.testing import CliRunner

import price_monitor_pipeline.cli as cli
from price_monitor_pipeline.models import PriceSnapshot


def test_cli_run_command(monkeypatch, tmp_path) -> None:
    async def fake_fetch_snapshots(_items):
        return [
            PriceSnapshot(
                name="Demo Laptop",
                url="https://example.com/laptop",
                title="Demo Laptop 14",
                price=849.99,
                target_price=900,
                checked_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            )
        ]

    monkeypatch.setattr(cli, "fetch_snapshots", fake_fetch_snapshots)
    snapshot_path = tmp_path / "snapshot.csv"
    alerts_path = tmp_path / "alerts.csv"
    summary_path = tmp_path / "summary.md"

    result = CliRunner().invoke(
        cli.app,
        [
            "--config",
            "examples/watchlist.json",
            "--out",
            str(snapshot_path),
            "--alerts",
            str(alerts_path),
            "--summary",
            str(summary_path),
        ],
    )

    assert result.exit_code == 0
    assert "Checked 1 products" in result.output
    assert snapshot_path.exists()
    assert alerts_path.exists()
    assert summary_path.exists()
