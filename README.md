# Price Monitor Pipeline

[![CI](https://github.com/emirhuseynrmx/price-monitor-pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/emirhuseynrmx/price-monitor-pipeline/actions)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)

Python pipeline for tracking public product prices and generating clean alert reports.

Built for small automation jobs where a business needs repeatable price checks, CSV snapshots, and simple threshold alerts.

## What It Does

- reads product watch rules from JSON
- fetches public product pages
- extracts title and price using CSS selectors
- writes timestamped CSV snapshots
- compares current price against target price
- writes alert reports for products below threshold
- supports fixture-based testing without live network calls

## Demo

```bash
pip install -e ".[dev]"
monitor-prices --config examples/watchlist.json --out outputs/snapshot.csv --alerts outputs/alerts.csv
```

## Watchlist Example

```json
{
  "items": [
    {
      "name": "Demo Laptop",
      "url": "https://example.com/product/demo-laptop",
      "price_selector": ".price",
      "title_selector": "h1",
      "target_price": 900
    }
  ]
}
```

## Run Tests

```bash
ruff check .
pytest
```

## Scope

This project monitors public pages with stable selectors. It does not bypass logins, CAPTCHAs, account restrictions, or terms of service.
