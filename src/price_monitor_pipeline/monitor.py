from __future__ import annotations

import re
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

import httpx
import pandas as pd
import pandera.pandas as pa
from bs4 import BeautifulSoup

from price_monitor_pipeline.models import (
    PriceAlert,
    PriceSnapshot,
    RunManifest,
    WatchItem,
    Watchlist,
)

PRICE_RE = re.compile(r"([0-9]+(?:[,.][0-9]{1,2})?)")


class PriceParseError(ValueError):
    """Raised when a page does not contain the expected price element."""


SNAPSHOT_SCHEMA = pa.DataFrameSchema(
    {
        "name": pa.Column(str, nullable=False),
        "url": pa.Column(str, nullable=False),
        "title": pa.Column(str, nullable=False),
        "price": pa.Column(float, checks=pa.Check.ge(0), nullable=False),
        "target_price": pa.Column(float, checks=pa.Check.gt(0), nullable=True),
        "checked_at": pa.Column(pa.DateTime, nullable=False),
    },
    coerce=True,
    strict=True,
)

ALERT_SCHEMA = pa.DataFrameSchema(
    {
        "name": pa.Column(str, nullable=False),
        "url": pa.Column(str, nullable=False),
        "title": pa.Column(str, nullable=False),
        "price": pa.Column(float, checks=pa.Check.ge(0), nullable=False),
        "target_price": pa.Column(float, checks=pa.Check.gt(0), nullable=False),
        "delta": pa.Column(float, checks=pa.Check.ge(0), nullable=False),
        "checked_at": pa.Column(pa.DateTime, nullable=False),
    },
    coerce=True,
    strict=True,
)


def parse_price(raw_value: str) -> float:
    normalized = raw_value.replace(",", ".")
    match = PRICE_RE.search(normalized)
    if match is None:
        raise PriceParseError(f"Could not parse price from {raw_value!r}")
    return float(match.group(1))


def load_watchlist(path: Path) -> Watchlist:
    return Watchlist.model_validate_json(path.read_text(encoding="utf-8"))


def parse_product_page(html: str, item: WatchItem, *, checked_at: datetime) -> PriceSnapshot:
    soup = BeautifulSoup(html, "html.parser")
    price_node = soup.select_one(item.price_selector)
    title_node = soup.select_one(item.title_selector)
    if price_node is None:
        raise PriceParseError(f"Missing price selector: {item.price_selector}")

    title = title_node.get_text(strip=True) if title_node else item.name
    price = parse_price(price_node.get_text(strip=True))
    return PriceSnapshot(
        name=item.name,
        url=item.url,
        title=title,
        price=price,
        target_price=item.target_price,
        checked_at=checked_at,
    )


async def fetch_snapshots(items: list[WatchItem]) -> list[PriceSnapshot]:
    checked_at = datetime.now(timezone.utc)
    snapshots: list[PriceSnapshot] = []
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        for item in items:
            response = await client.get(str(item.url))
            response.raise_for_status()
            snapshots.append(parse_product_page(response.text, item, checked_at=checked_at))
    return snapshots


def evaluate_alerts(snapshots: list[PriceSnapshot]) -> list[PriceAlert]:
    alerts: list[PriceAlert] = []
    for snapshot in snapshots:
        if snapshot.target_price is None or snapshot.price > snapshot.target_price:
            continue
        alerts.append(
            PriceAlert(
                name=snapshot.name,
                url=snapshot.url,
                title=snapshot.title,
                price=snapshot.price,
                target_price=snapshot.target_price,
                delta=round(snapshot.target_price - snapshot.price, 2),
                checked_at=snapshot.checked_at,
            )
        )
    return alerts


def snapshots_to_frame(snapshots: list[PriceSnapshot]) -> pd.DataFrame:
    frame = pd.DataFrame([snapshot.to_row() for snapshot in snapshots])
    return SNAPSHOT_SCHEMA.validate(frame)


def alerts_to_frame(alerts: list[PriceAlert]) -> pd.DataFrame:
    frame = pd.DataFrame([alert.to_row() for alert in alerts])
    if frame.empty:
        frame = pd.DataFrame(
            columns=["name", "url", "title", "price", "target_price", "delta", "checked_at"]
        )
    return ALERT_SCHEMA.validate(frame)


def write_csv(frame: pd.DataFrame, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
    return path


def write_summary(snapshots: list[PriceSnapshot], alerts: list[PriceAlert], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Price Monitor Summary",
        "",
        f"- Products checked: `{len(snapshots)}`",
        f"- Alerts triggered: `{len(alerts)}`",
        "",
        "## Alerts",
        "",
    ]
    if alerts:
        for alert in alerts:
            lines.append(
                f"- `{alert.name}` is `{alert.price}` against target `{alert.target_price}` "
                f"(`{alert.delta}` below target)"
            )
    else:
        lines.append("- No alerts triggered.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def build_run_manifest(
    *,
    snapshots: list[PriceSnapshot],
    alerts: list[PriceAlert],
    files: dict[str, Path],
) -> RunManifest:
    return RunManifest(
        run_id=uuid4().hex,
        generated_at=datetime.now(timezone.utc),
        products_checked=len(snapshots),
        alerts_triggered=len(alerts),
        total_alert_delta=round(sum(alert.delta for alert in alerts), 2),
        schema_fingerprint=_schema_fingerprint(),
        sources=sorted({str(snapshot.url) for snapshot in snapshots}),
        files={key: value.as_posix() for key, value in files.items()},
        notes=[
            "Alerts are generated from public product pages only.",
            "Selectors and thresholds come from the watchlist config.",
            "The run does not bypass authentication, captchas, or protected pages.",
        ],
    )


def write_manifest(manifest: RunManifest, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    return path


def _schema_fingerprint() -> str:
    schema_text = "|".join(
        [
            "snapshot:name,url,title,price,target_price,checked_at",
            "alerts:name,url,title,price,target_price,delta,checked_at",
        ]
    )
    return sha256(schema_text.encode("utf-8")).hexdigest()[:16]
