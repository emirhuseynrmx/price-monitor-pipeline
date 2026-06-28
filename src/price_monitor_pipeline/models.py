from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class WatchItem(BaseModel):
    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    name: str
    url: HttpUrl
    price_selector: str
    title_selector: str = "title"
    target_price: float | None = Field(default=None, gt=0)


class Watchlist(BaseModel):
    model_config = ConfigDict(frozen=True)

    items: list[WatchItem]


class PriceSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    url: HttpUrl
    title: str
    price: float
    target_price: float | None
    checked_at: datetime

    def to_row(self) -> dict[str, object]:
        data = self.model_dump(mode="python")
        data["url"] = str(self.url)
        return data


class PriceAlert(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    url: HttpUrl
    title: str
    price: float
    target_price: float
    delta: float
    checked_at: datetime

    def to_row(self) -> dict[str, object]:
        data = self.model_dump(mode="python")
        data["url"] = str(self.url)
        return data


class RunManifest(BaseModel):
    model_config = ConfigDict(frozen=True)

    run_id: str
    generated_at: datetime
    products_checked: int = Field(ge=0)
    alerts_triggered: int = Field(ge=0)
    total_alert_delta: float = Field(ge=0)
    schema_fingerprint: str
    sources: list[str]
    files: dict[str, str]
    notes: list[str] = Field(default_factory=list)
