#!/usr/bin/env python3
"""UK Keyword Miner - Queries DataForSEO API for high-volume, low-competition UK keywords."""

import csv
import json
import time
import urllib.request
import urllib.error
from collections import defaultdict

API_BASE = "https://api.dataforseo.com/v3"
AUTH_HEADER = "Basic Y29udGF0b0Blc2N1ZG92cG4uY29tOmM5ODFkMTQ0MTVjN2ZkMjk="
COST_LIMIT = 1.50  # Remaining budget safety limit

SEED_KEYWORDS = [
    "council tax", "energy bill", "broadband deals", "skip hire",
    "boiler service", "loft insulation", "car insurance", "debt advice",
    "tax return", "pension calculator", "private dentist", "physiotherapy",
    "CBD oil", "hearing test", "driving lessons", "MOT test",
    "parking permit", "bus timetable", "VPN UK", "cheap phone contract",
    "WiFi booster", "apprenticeship", "CSCS card", "forklift licence",
    "log cabin", "hot tub",
]


def api_post(endpoint, payload):
    url = f"{API_BASE}/{endpoint}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", AUTH_HEADER)
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def api_get(endpoint):
    url = f"{API_BASE}/{endpoint}"
    req = urllib.request.Request(url, method="GET")
    req.add_header("Authorization", AUTH_HEADER)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def check_balance():
    resp = api_get("appendix/user_data")
    if resp.get("tasks") and resp["tasks"][0].get("result"):
        r = resp["tasks"][0]["result"][0]
        money = r.get("money", {})
        print(f"  Balance: ${money.get('balance', 'N/A')}")
        print(f"  Total spent: ${money.get('total', 'N/A')}")
        return money
    else:
        print("  Could not retrieve balance info")
        print(f"  Response: {json.dumps(resp, indent=2)[:500]}")
        return {}


def fetch_keywords(seed):
    payload = [{
        "keyword": seed,
        "location_code": 2826,
        "language_code": "en",
        "include_seed_keyword": True,
        "limit": 350,
    }]
    return api_post("dataforseo_labs/google/keyword_suggestions/live", payload)


def main():
    print("=" * 70)
    print("UK KEYWORD MINER - DataForSEO")
    print("=" * 70)

    # 1. Check balance
    print("\n[1] Checking account balance...")
    check_balance()

    # 2. Mine keywords
    print(f"\n[2] Mining keywords from {len(SEED_KEYWORDS)} seeds...")
    all_keywords = {}  # keyword_str -> record
    seed_stats = {}    # seed -> {keywords: [], volume: 0, cpc_sum: 0}
    total_cost = 0.0

    for i, seed in enumerate(SEED_KEYWORDS):
        print(f"  [{i+1:2d}/{len(SEED_KEYWORDS)}] '{seed}' ... ", end="", flush=True)

        try:
            resp = fetch_keywords(seed)
        except urllib.error.URLError as e:
            print(f"ERROR: {e}")
            time.sleep(0.3)
            continue

        task = resp.get("tasks", [{}])[0]
        cost = task.get("cost", 0) or 0
        total_cost += cost

        result = (task.get("result") or [None])[0]
        items = (result.get("items") if result else None) or []

        count = 0
        seed_stats[seed] = {"count": 0, "volume": 0, "cpc_sum": 0.0, "comp_sum": 0.0}

        for item in items:
            kw_str = item.get("keyword", "")
            ki = item.get("keyword_info", {})
            kp = item.get("keyword_properties", {})

            if not kw_str:
                continue

            vol = ki.get("search_volume") or 0
            cpc = ki.get("cpc") or 0
            comp = ki.get("competition") or 0
            comp_level = ki.get("competition_level") or ""
            difficulty = kp.get("keyword_difficulty")

            # Client-side filtering: volume >= 500, competition LOW or MEDIUM
            if vol < 500:
                continue
            if comp_level not in ("LOW", "MEDIUM"):
                continue

            record = {
                "keyword": kw_str,
                "search_volume": vol,
                "cpc": cpc,
                "competition": comp,
                "competition_level": comp_level,
                "keyword_difficulty": difficulty,
                "seed": seed,
            }

            # Deduplicate: keep the one with higher volume or first seen
            if kw_str not in all_keywords or vol > all_keywords[kw_str]["search_volume"]:
                all_keywords[kw_str] = record

            seed_stats[seed]["count"] += 1
            seed_stats[seed]["volume"] += vol
            seed_stats[seed]["cpc_sum"] += cpc
            seed_stats[seed]["comp_sum"] += comp
            count += 1

        print(f"{count} kws, cost=${cost:.4f}, running=${total_cost:.4f}")

        if total_cost >= COST_LIMIT:
            print(f"\n  *** COST LIMIT ${COST_LIMIT} reached! Stopping. ***")
            break

        time.sleep(0.3)

    # 3. Sort and save CSV
    sorted_kws = sorted(all_keywords.values(), key=lambda x: x["search_volume"], reverse=True)

    csv_path = "uk_keyword_opportunities.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "keyword", "search_volume", "cpc", "competition",
            "competition_level", "keyword_difficulty", "seed"
        ])
        writer.writeheader()
        writer.writerows(sorted_kws)

    print(f"\n[3] Saved {len(sorted_kws)} unique keywords to {csv_path}")

    # 4. Print top 50
    print("\n" + "=" * 90)
    print("TOP 50 KEYWORDS BY SEARCH VOLUME")
    print("=" * 90)
    print(f"{'Keyword':<45} {'Volume':>8} {'CPC':>7} {'Comp Level':<12} {'Difficulty':>10}")
    print("-" * 90)
    for r in sorted_kws[:50]:
        diff = str(r["keyword_difficulty"]) if r["keyword_difficulty"] is not None else "N/A"
        print(f"{r['keyword']:<45} {r['search_volume']:>8,} {r['cpc']:>7.2f} {r['competition_level']:<12} {diff:>10}")

    # 5. Seed breakdown
    print("\n" + "=" * 90)
    print("BREAKDOWN BY SEED KEYWORD")
    print("=" * 90)
    print(f"{'Seed':<25} {'Keywords':>8} {'Total Vol':>12} {'Avg CPC':>9}")
    print("-" * 60)
    for seed in SEED_KEYWORDS:
        s = seed_stats.get(seed)
        if not s:
            continue
        avg_cpc = s["cpc_sum"] / s["count"] if s["count"] > 0 else 0
        print(f"{seed:<25} {s['count']:>8,} {s['volume']:>12,} {avg_cpc:>9.2f}")

    # 6. Summary
    print(f"\n{'=' * 50}")
    print(f"Total unique keywords: {len(sorted_kws):,}")
    print(f"Total API cost:        ${total_cost:.4f}")

    # 7. Final balance check
    print(f"\n[4] Checking final account balance...")
    check_balance()

    # 8. Top 3 niches
    print("\n" + "=" * 70)
    print("TOP 3 MOST PROMISING NICHES")
    print("=" * 70)
    niche_scores = []
    for seed in SEED_KEYWORDS:
        s = seed_stats.get(seed)
        if not s or s["count"] == 0:
            continue
        avg_cpc = s["cpc_sum"] / s["count"]
        avg_comp = s["comp_sum"] / s["count"]
        # Score: high volume, low competition, reasonable CPC (> 0.20)
        if avg_cpc >= 0.20:
            # Higher volume and lower competition = better
            score = s["volume"] * (1 - avg_comp + 0.01)
            niche_scores.append((seed, s["volume"], avg_cpc, avg_comp, s["count"], score))

    niche_scores.sort(key=lambda x: x[5], reverse=True)
    for rank, (seed, vol, cpc, comp, cnt, score) in enumerate(niche_scores[:3], 1):
        print(f"\n  #{rank}: {seed.upper()}")
        print(f"      Keywords: {cnt}, Total Volume: {vol:,}")
        print(f"      Avg CPC: £{cpc:.2f}, Avg Competition: {comp:.3f}")
        print(f"      Score: {score:,.0f}")
        print(f"      → Worth building city-level pages for this niche")

    print()


if __name__ == "__main__":
    main()
