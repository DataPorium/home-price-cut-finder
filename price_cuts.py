"""Find homes for sale with the biggest price cuts in a ZIP code, city, county or state, and save them to CSV.

    python price_cuts.py --zip 92602,92618
    python price_cuts.py --city Austin --state TX --within-days 7 --price-max 600000
    python price_cuts.py --county Maricopa --state AZ --cut-pct-min 10 --sort recent_cut

Needs a DataPorium API key in the DATAPORIUM_API_KEY environment variable.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from dataporium import DataPorium

# Columns shown first in the CSV when the answer has them; every other field follows.
FIRST = ["address", "street", "city", "state", "zip", "price", "list_price", "beds", "baths", "sqft",
         "price_per_sqft", "last_price_cut", "total_price_cut", "total_price_cut_pct", "listed_date",
         "days_on_market", "true_days_on_market", "relisted", "property_id"]
PAGE = 200


def homes_in(answer) -> list[dict]:
    """The list of homes in an answer: the longest list of records, at the top level or one level down."""
    if isinstance(answer, list):
        return [h for h in answer if isinstance(h, dict)]
    best: list[dict] = []
    candidates = list(answer.values()) if isinstance(answer, dict) else []
    for value in list(candidates):
        if isinstance(value, dict):
            candidates.extend(value.values())
    for value in candidates:
        if isinstance(value, list) and value and all(isinstance(v, dict) for v in value):
            if any("property_id" in v or "price" in v or "list_price" in v for v in value) and len(value) > len(best):
                best = value
    return best


def flatten(home: dict, prefix: str = "") -> dict:
    """Nested records become prefixed columns (price_cut.total -> price_cut_total); lists are joined."""
    flat = {}
    for key, value in home.items():
        name = f"{prefix}{key}"
        if isinstance(value, dict):
            flat.update(flatten(value, f"{name}_"))
        elif isinstance(value, list):
            flat[name] = "; ".join(str(v) for v in value if not isinstance(v, (dict, list)))
        else:
            flat[name] = value
    return flat


def columns_for(rows: list[dict]) -> list[str]:
    seen: list[str] = []
    for row in rows:
        for key in row:
            if key not in seen:
                seen.append(key)
    return [c for c in FIRST if c in seen] + [c for c in seen if c not in FIRST]


def pick(row: dict, *names: str):
    for name in names:
        if row.get(name) not in (None, ""):
            return row[name]
    for name in names:  # a nested field, e.g. price_cut_total for total_price_cut
        for key, value in row.items():
            if name in key and value not in (None, ""):
                return value
    return None


def search(dp: DataPorium, filters: dict, max_homes: int) -> tuple[list[dict], dict]:
    homes: list[dict] = []
    offset = 0
    first: dict = {}
    while len(homes) < max_homes:
        answer = dp.properties(**filters, limit=min(PAGE, max_homes - len(homes)), offset=offset)
        first = first or (answer if isinstance(answer, dict) else {})
        page = homes_in(answer)
        homes.extend(page)
        next_offset = answer.get("next_offset") if isinstance(answer, dict) else None
        if not page or next_offset is None:
            break
        offset = int(next_offset)
    return homes, first


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Find homes with the biggest price cuts and save them to CSV.")
    where = parser.add_argument_group("where (give at least one)")
    where.add_argument("--zip", help="ZIP codes, comma-separated (up to 25)")
    where.add_argument("--city", help="City name; add --state")
    where.add_argument("--county", help="County name; add --state")
    where.add_argument("--state", help="2-letter state code")
    parser.add_argument("--within-days", type=int, help="Latest price cut within this many days, e.g. 7")
    parser.add_argument("--cut-min", type=int, help="Total cut since first listed, at least this many dollars")
    parser.add_argument("--cut-pct-min", type=float, help="Total cut since first listed, at least this percent")
    parser.add_argument("--price-min", type=int)
    parser.add_argument("--price-max", type=int)
    parser.add_argument("--beds-min", type=int)
    parser.add_argument("--style", help="single_family, condos, townhomes, multi_family, ... (comma-separated)")
    parser.add_argument("--sort", default="biggest_cut", choices=["biggest_cut", "recent_cut", "best_value", "price_asc", "dom_desc"])
    parser.add_argument("--max", type=int, default=500, help="Most homes to save (default 500)")
    parser.add_argument("--out", default="price_cuts.csv", help="CSV file to write (default price_cuts.csv)")
    args = parser.parse_args(argv)

    if not (args.zip or args.city or args.county or args.state):
        parser.error("give --zip, --city, --county or --state")

    filters = {"zip": args.zip, "city": args.city, "county": args.county, "state": args.state,
               "status": "for_sale", "price_cut": True, "price_cut_within_days": args.within_days,
               "cut_min": args.cut_min, "cut_pct_min": args.cut_pct_min, "price_min": args.price_min,
               "price_max": args.price_max, "beds_min": args.beds_min, "style": args.style, "sort": args.sort}
    homes, answer = search(DataPorium(), filters, args.max)
    if not homes:
        print("No homes with a price cut match these filters.", file=sys.stderr)
        return 1

    rows = [flatten(h) for h in homes]
    with open(args.out, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns_for(rows), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    total = pick(answer, "total_matches", "total")
    print(f"Saved {len(rows)} homes to {Path(args.out)}" + (f" ({total} match in all)" if total else ""))
    for row in rows[:10]:
        address = pick(row, "address", "street", "full_address") or row.get("property_id")
        price = pick(row, "price", "list_price")
        cut = pick(row, "total_price_cut", "total_cut", "price_cut")
        line = f"  {str(address)[:45]:45}"
        if isinstance(price, (int, float)):
            line += f"  ${price:>12,.0f}"
        if isinstance(cut, (int, float)):
            line += f"  cut ${abs(cut):,.0f}"
        print(line)
    if isinstance(answer, dict) and answer.get("website_link"):
        print(f"See them on the map: {answer['website_link']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
