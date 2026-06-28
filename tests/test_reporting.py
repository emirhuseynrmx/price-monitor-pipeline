from __future__ import annotations

from pathlib import Path

from price_monitor_pipeline.monitor import evaluate_alerts
from price_monitor_pipeline.reporting import (
    _sample_snapshots,
    build_report,
    generate_sample_report,
    render_typst,
)


def test_build_report_summarizes_alert_value(tmp_path: Path) -> None:
    snapshots = _sample_snapshots()
    alerts = evaluate_alerts(snapshots)

    report = build_report(
        snapshots,
        alerts,
        title="Price Report",
        snapshot_csv=tmp_path / "snapshot.csv",
        alerts_csv=tmp_path / "alerts.csv",
    )

    assert report.checked_count == 4
    assert report.alert_count == 3
    assert report.total_delta > 0


def test_render_typst_contains_report_sections() -> None:
    snapshots = _sample_snapshots()
    report = build_report(
        snapshots,
        evaluate_alerts(snapshots),
        title="Price Report",
        snapshot_csv=Path("snapshot.csv"),
        alerts_csv=Path("alerts.csv"),
    )
    typst = render_typst(report)

    assert "= Price Report" in typst
    assert "Alert Queue" in typst
    assert "Full Snapshot" in typst


def test_generate_sample_report_writes_typst_without_pdf(tmp_path: Path) -> None:
    typ_path, pdf_path = generate_sample_report(tmp_path / "out", compile_pdf=False)

    assert typ_path.exists()
    assert pdf_path is None
    assert (tmp_path / "out" / "snapshot.csv").exists()
    assert (tmp_path / "out" / "alerts.csv").exists()
