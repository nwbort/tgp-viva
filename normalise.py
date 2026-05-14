#!/usr/bin/env python3
"""Normalise the Viva Energy TGP history CSV into the standard schema.

Reads tgp-viva-history.csv and writes:
  - tgp-viva-normalised.csv  (date,state,location,fuel_type,price_cpl)
  - tgp_data.json            (records as array-of-arrays for the site)
"""

import csv
import datetime as dt
import json
import sys
from pathlib import Path

HISTORY_FILE = Path("tgp-viva-history.csv")
NORMALISED_CSV = Path("tgp-viva-normalised.csv")
JSON_FILE = Path("tgp_data.json")
PROVIDER = "viva"

STATE_MAP = {
    "NEW SOUTH WALES": "NSW",
    "VICTORIA": "VIC",
    "QUEENSLAND": "QLD",
    "SOUTH AUSTRALIA": "SA",
    "WESTERN AUSTRALIA": "WA",
    "NORTHERN TERRITORY": "NT",
    "TASMANIA": "TAS",
    "AUSTRALIAN CAPITAL TERRITORY": "ACT",
}

FUEL_COLUMNS = {
    "UnleadedPetrol": "ulp91",
    "PremiumUnleadedPetrol": "p95",
    "UnleadedPetrol E10": "e10",
    "UnleadedPetrol 98": "p98",
    "Diesel": "diesel",
    "BiodieselB5": "b5",
}

FIELDS = ["date", "state", "location", "fuel_type", "price_cpl"]


def normalise_state(raw: str) -> str:
    key = raw.strip().upper()
    return STATE_MAP.get(key, key)


def normalise_location(raw: str) -> str:
    parts = raw.strip().split()
    return " ".join(p.capitalize() for p in parts)


def parse_price(raw: str):
    raw = raw.strip()
    if not raw or raw.upper() == "N/A":
        return None
    try:
        return round(float(raw), 1)
    except ValueError:
        return None


def load_records():
    with HISTORY_FILE.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            date = row.get("Date", "").strip()
            if not date:
                continue
            state = normalise_state(row.get("State", ""))
            location = normalise_location(row.get("City", ""))
            for source_col, fuel_type in FUEL_COLUMNS.items():
                price = parse_price(row.get(source_col, ""))
                if price is None:
                    continue
                yield [date, state, location, fuel_type, price]


def main() -> int:
    if not HISTORY_FILE.exists():
        print(f"Error: {HISTORY_FILE} not found", file=sys.stderr)
        return 1

    records = list(load_records())
    records.sort(key=lambda r: (r[0], r[1], r[2], r[3]))

    with NORMALISED_CSV.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(FIELDS)
        for row in records:
            writer.writerow([row[0], row[1], row[2], row[3], f"{row[4]:.1f}"])

    payload = {
        "provider": PROVIDER,
        "updated": dt.date.today().isoformat(),
        "fields": FIELDS,
        "records": records,
    }
    with JSON_FILE.open("w") as f:
        json.dump(payload, f, separators=(",", ":"))
        f.write("\n")

    print(f"Wrote {NORMALISED_CSV} ({len(records)} rows) and {JSON_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
