from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pandas as pd
from bs4 import BeautifulSoup

from price_monitor_pipeline.models import PriceAlert, PriceSnapshot, WatchItem, Watchlist

PRICE_RE = re.compile(r"([0-9]+(?:[,.][0-9]{1,2})?)")


class PriceParseError(ValueError):
    """Raised when a page does not contain the expected price element."""


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
    return pd.DataFrame([snapshot.to_row() for snapshot in snapshots])


def alerts_to_frame(alerts: list[PriceAlert]) -> pd.DataFrame:
    return pd.DataFrame([alert.to_row() for alert in alerts])


def write_csv(frame: pd.DataFrame, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
    return path
