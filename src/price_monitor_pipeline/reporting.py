from __future__ import annotations

import argparse
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from price_monitor_pipeline.models import PriceAlert, PriceSnapshot
from price_monitor_pipeline.monitor import (
    alerts_to_frame,
    evaluate_alerts,
    snapshots_to_frame,
    write_csv,
)


class PriceReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    title: str
    checked_count: int = Field(ge=0)
    alert_count: int = Field(ge=0)
    total_delta: float = Field(ge=0)
    snapshots: tuple[PriceSnapshot, ...]
    alerts: tuple[PriceAlert, ...]
    snapshot_csv: str
    alerts_csv: str


def build_report(
    snapshots: list[PriceSnapshot],
    alerts: list[PriceAlert],
    *,
    title: str,
    snapshot_csv: Path,
    alerts_csv: Path,
) -> PriceReport:
    return PriceReport(
        title=title,
        checked_count=len(snapshots),
        alert_count=len(alerts),
        total_delta=round(sum(alert.delta for alert in alerts), 2),
        snapshots=tuple(snapshots),
        alerts=tuple(alerts),
        snapshot_csv=snapshot_csv.as_posix(),
        alerts_csv=alerts_csv.as_posix(),
    )


def generate_sample_report(
    output_dir: Path,
    *,
    title: str = "Price Monitoring Alert Report",
    compile_pdf: bool = True,
) -> tuple[Path, Path | None]:
    output_dir.mkdir(parents=True, exist_ok=True)
    snapshots = _sample_snapshots()
    alerts = evaluate_alerts(snapshots)
    snapshot_csv = write_csv(snapshots_to_frame(snapshots), output_dir / "snapshot.csv")
    alerts_csv = write_csv(alerts_to_frame(alerts), output_dir / "alerts.csv")
    report = build_report(
        snapshots,
        alerts,
        title=title,
        snapshot_csv=snapshot_csv,
        alerts_csv=alerts_csv,
    )
    typ_path = output_dir / "price_monitor_report.typ"
    pdf_path = output_dir / "price_monitor_report.pdf"
    typ_path.write_text(render_typst(report), encoding="utf-8")
    if not compile_pdf:
        return typ_path, None
    typst = shutil.which("typst")
    if typst is None:
        return typ_path, None
    subprocess.run(
        [typst, "compile", typ_path.name, pdf_path.name],
        check=True,
        cwd=output_dir,
    )
    return typ_path, pdf_path


def render_typst(report: PriceReport) -> str:
    alert_rows = "\n".join(_alert_row(alert) for alert in report.alerts)
    if not alert_rows:
        alert_rows = "  [No alerts], [No item below target], [-], [-],"
    snapshot_rows = "\n".join(_snapshot_row(snapshot) for snapshot in report.snapshots)
    return f"""#set page(margin: 42pt)
#set text(font: "Arial", size: 10pt)
#set heading(numbering: none)

#let accent = rgb("#1457d9")
#let good = rgb("#11845b")
#let warn = rgb("#b86b00")
#let muted = rgb("#667085")
#let panel = rgb("#f6f8fb")

#let stat(label, value, color: accent) = block[
  #rect(fill: panel, radius: 5pt, inset: 10pt, width: 100%)[
    #text(size: 8pt, fill: muted, weight: "bold")[#upper(label)]
    #linebreak()
    #text(size: 18pt, fill: color, weight: "bold")[#value]
  ]
]

= {_typ_text(report.title)}

#text(fill: muted)[
  Price monitoring summary for public product pages. The report highlights
  which items are below target price and writes CSV files for automation.
]

#grid(columns: (1fr, 1fr, 1fr, 1fr), gutter: 8pt)[
  #stat("Products checked", "{report.checked_count}")
][
  #stat("Alerts", "{report.alert_count}", color: warn)
][
  #stat("Potential savings", "${report.total_delta:,.2f}", color: good)
][
  #stat("Outputs", "CSV + PDF")
]

== Alert Queue

#table(
  columns: (1.2fr, 1.8fr, .8fr, .8fr),
  inset: 5pt,
  stroke: rgb("#d0d5dd"),
  [*Product*], [*Title*], [*Price*], [*Below Target*],
{alert_rows}
)

== Full Snapshot

#table(
  columns: (1.1fr, 1.8fr, .7fr, .7fr),
  inset: 5pt,
  stroke: rgb("#d0d5dd"),
  [*Product*], [*Title*], [*Price*], [*Target*],
{snapshot_rows}
)

== Delivery Notes

- Snapshot CSV: `{_typ_text(report.snapshot_csv)}`
- Alerts CSV: `{_typ_text(report.alerts_csv)}`
- Alerts trigger only when current price is at or below the configured target.
- The pipeline does not bypass logins, CAPTCHAs, account gates, or site restrictions.
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the sample price monitoring report.")
    parser.add_argument("--out", type=Path, default=Path("outputs/sample_report"))
    parser.add_argument("--title", default="Price Monitoring Alert Report")
    parser.add_argument("--no-pdf", action="store_true")
    args = parser.parse_args()
    typ_path, pdf_path = generate_sample_report(
        args.out,
        title=args.title,
        compile_pdf=not args.no_pdf,
    )
    print(f"Wrote {typ_path}")
    if pdf_path is not None:
        print(f"Wrote {pdf_path}")


def _sample_snapshots() -> list[PriceSnapshot]:
    checked_at = datetime(2026, 6, 28, 9, 0, tzinfo=timezone.utc)
    return [
        _snapshot("Demo Laptop", "Demo Laptop 14", 849.99, 900.00, checked_at),
        _snapshot("USB-C Monitor", "27 inch USB-C Monitor", 259.00, 250.00, checked_at),
        _snapshot("Ergonomic Chair", "Ergo Chair Pro", 189.50, 220.00, checked_at),
        _snapshot("Noise Cancelling Headset", "Office ANC Headset", 119.00, 130.00, checked_at),
    ]


def _snapshot(
    name: str,
    title: str,
    price: float,
    target: float,
    checked_at: datetime,
) -> PriceSnapshot:
    slug = name.lower().replace(" ", "-")
    return PriceSnapshot(
        name=name,
        url=HttpUrl(f"https://example.com/products/{slug}"),
        title=title,
        price=price,
        target_price=target,
        checked_at=checked_at,
    )


def _alert_row(alert: PriceAlert) -> str:
    return (
        f"  [{_typ_text(alert.name)}],"
        f" [{_typ_text(alert.title)}],"
        f" [{_typ_text(f'${alert.price:,.2f}')}],"
        f" [{_typ_text(f'${alert.delta:,.2f}')}],"
    )


def _snapshot_row(snapshot: PriceSnapshot) -> str:
    target = "" if snapshot.target_price is None else f"${snapshot.target_price:,.2f}"
    return (
        f"  [{_typ_text(snapshot.name)}],"
        f" [{_typ_text(snapshot.title)}],"
        f" [{_typ_text(f'${snapshot.price:,.2f}')}],"
        f" [{_typ_text(target)}],"
    )


def _typ_text(value: Any) -> str:
    text = "" if value is None else str(value)
    replacements = {
        "\\": "\\\\",
        "[": "\\[",
        "]": "\\]",
        "#": "\\#",
        "$": "\\$",
        "@": "\\@",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text
