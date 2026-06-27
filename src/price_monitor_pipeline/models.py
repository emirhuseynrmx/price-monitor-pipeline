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
