from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from price_monitor_pipeline.models import WatchItem
from price_monitor_pipeline.monitor import (
    alerts_to_frame,
    evaluate_alerts,
    parse_price,
    parse_product_page,
    snapshots_to_frame,
    write_csv,
)


def test_parse_price() -> None:
    assert parse_price("$849.99") == 849.99
    assert parse_price("EUR 1,25") == 1.25


def test_parse_product_page_extracts_snapshot() -> None:
    html = Path("tests/fixtures/product_page.html").read_text(encoding="utf-8")
    item = WatchItem(
        name="Laptop",
        url="https://example.com/laptop",
        price_selector=".price",
        title_selector="h1",
        target_price=900,
    )
    checked_at = datetime(2026, 1, 1, tzinfo=timezone.utc)

    snapshot = parse_product_page(html, item, checked_at=checked_at)

    assert snapshot.title == "Demo Laptop 14"
    assert snapshot.price == 849.99
    assert snapshot.checked_at == checked_at


def test_evaluate_alerts_returns_below_target_items() -> None:
    html = Path("tests/fixtures/product_page.html").read_text(encoding="utf-8")
    item = WatchItem(
        name="Laptop",
        url="https://example.com/laptop",
        price_selector=".price",
        title_selector="h1",
        target_price=900,
    )
    snapshot = parse_product_page(html, item, checked_at=datetime.now(timezone.utc))

    alerts = evaluate_alerts([snapshot])

    assert len(alerts) == 1
    assert alerts[0].delta == 50.01


def test_frames_and_csv_export(tmp_path: Path) -> None:
    html = Path("tests/fixtures/product_page.html").read_text(encoding="utf-8")
    item = WatchItem(
        name="Laptop",
        url="https://example.com/laptop",
        price_selector=".price",
        title_selector="h1",
        target_price=900,
    )
    snapshot = parse_product_page(html, item, checked_at=datetime.now(timezone.utc))

    snapshot_frame = snapshots_to_frame([snapshot])
    alert_frame = alerts_to_frame(evaluate_alerts([snapshot]))
    output_path = write_csv(snapshot_frame, tmp_path / "snapshot.csv")

    assert list(snapshot_frame.columns) == [
        "name",
        "url",
        "title",
        "price",
        "target_price",
        "checked_at",
    ]
    assert len(alert_frame) == 1
    assert output_path.exists()
