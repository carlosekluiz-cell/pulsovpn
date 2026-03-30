#!/usr/bin/env python3
"""Deep-dive skip hire keyword analysis.
Uses existing mined data + DataForSEO API if balance available."""

import csv
import json
import re
import time
import urllib.request
import urllib.error
from collections import defaultdict

API_BASE = "https://api.dataforseo.com/v3"
AUTH_HEADER = "Basic Y29udGF0b0Blc2N1ZG92cG4uY29tOmM5ODFkMTQ0MTVjN2ZkMjk="
COST_LIMIT = 0.75

SEED_KEYWORDS = [
    "same day skip hire", "cheap skip hire", "skip hire permit",
    "skip sizes", "grab hire", "mini skip", "builders skip",
    "skip hire near me", "skip bag collection", "wait and load skip",
]

UK_CITIES = [
    "aberdeen", "abergavenny", "abingdon", "accrington", "airdrie", "aldershot",
    "alfreton", "altrincham", "amersham", "andover", "arbroath", "ashford",
    "ashton", "aylesbury", "ayr", "banbury", "bangor", "barnsley", "barnstaple",
    "barrow", "barry", "basildon", "basingstoke", "bath", "batley", "bedford",
    "belfast", "bewdley", "bexley", "bicester", "billericay", "birkenhead",
    "birmingham", "bishop auckland", "blackburn", "blackpool", "blandford",
    "blyth", "bodmin", "bognor", "bolton", "bootle", "boston", "bournemouth",
    "bracknell", "bradford", "braintree", "brecon", "brentwood", "bridgend",
    "bridgwater", "bridlington", "brighton", "bristol", "broadstairs",
    "bromley", "bromsgrove", "burnley", "burton", "bury", "bury st edmunds",
    "caerphilly", "camberley", "cambridge", "cannock", "canterbury", "cardiff",
    "carlisle", "carmarthen", "carshalton", "chatham", "chelmsford",
    "cheltenham", "chesham", "chester", "chesterfield", "chichester",
    "chippenham", "chorley", "cirencester", "clacton", "coalville",
    "colchester", "coleraine", "corby", "coventry", "crawley", "crewe",
    "croydon", "cumbernauld", "darlington", "dartford", "daventry", "derby",
    "dereham", "dewsbury", "doncaster", "dorchester", "dover", "droitwich",
    "dudley", "dumfries", "dundee", "dunfermline", "dunmow", "dunstable",
    "durham", "ealing", "eastbourne", "east grinstead", "east kilbride",
    "edinburgh", "elgin", "ely", "enfield", "epsom", "esher", "evesham",
    "exeter", "falkirk", "fareham", "farnborough", "farnham", "felixstowe",
    "fleetwood", "folkestone", "gainsborough", "gateshead", "gillingham",
    "glasgow", "glastonbury", "gloucester", "godalming", "gosport", "grantham",
    "gravesend", "grays", "great yarmouth", "greenock", "grimsby", "guildford",
    "gwynedd", "hailsham", "halifax", "hamilton", "harlow", "harpenden",
    "harrogate", "hartlepool", "harwich", "hastings", "hatfield", "havant",
    "haverfordwest", "haywards heath", "hemel hempstead", "henley", "hereford",
    "hertford", "hexham", "high wycombe", "hinckley", "hitchin", "hoddesdon",
    "horsham", "hove", "huddersfield", "hull", "huntingdon", "hyde", "ilford",
    "ilkeston", "inverness", "ipswich", "irvine", "isle of wight", "keighley",
    "kendal", "kettering", "kidderminster", "kilmarnock", "kings lynn",
    "kingston", "kingswood", "kirkcaldy", "knaresborough", "lancaster",
    "leamington", "leeds", "leicester", "leigh", "letchworth", "lewes",
    "lichfield", "lincoln", "lisburn", "littlehampton", "liverpool",
    "livingston", "llanelli", "london", "loughborough", "louth", "lowestoft",
    "luton", "macclesfield", "maidenhead", "maidstone", "maldon", "malvern",
    "manchester", "mansfield", "margate", "market harborough", "matlock",
    "medway", "melton mowbray", "merthyr", "middlesbrough", "middleton",
    "midlothian", "milton keynes", "minehead", "mitcham", "morecambe",
    "motherwell", "neath", "nelson", "newark", "newbury", "newcastle",
    "newhaven", "newport", "newquay", "newton abbot", "northampton",
    "northwich", "norwich", "nottingham", "nuneaton", "oakham", "oldham",
    "ormskirk", "oswestry", "oxford", "paisley", "peebles", "pembroke",
    "penrith", "penzance", "perth", "peterborough", "petersfield", "pickering",
    "plymouth", "pontefract", "pontypridd", "poole", "portsmouth", "preston",
    "pudsey", "ramsgate", "rayleigh", "reading", "redcar", "redditch",
    "reigate", "retford", "rhyl", "richmond", "ringwood", "ripon", "rochdale",
    "rochester", "romford", "rotherham", "rugby", "rugeley", "runcorn",
    "rushden", "ryde", "salisbury", "scarborough", "scunthorpe", "sheffield",
    "sherborne", "shrewsbury", "sidmouth", "sittingbourne", "skegness",
    "skipton", "sleaford", "slough", "solihull", "southampton", "southend",
    "southport", "south shields", "stafford", "staines", "stamford",
    "stevenage", "stirling", "stockport", "stockton", "stoke", "stourbridge",
    "stowmarket", "stratford", "stroud", "sunderland", "sutton",
    "sutton coldfield", "swansea", "swindon", "tamworth", "taunton", "telford",
    "tenby", "tewkesbury", "thetford", "thirsk", "tilbury", "tiverton",
    "tonbridge", "torquay", "totnes", "trowbridge", "truro", "tunbridge wells",
    "twickenham", "ulverston", "uxbridge", "wakefield", "wallasey", "wallsend",
    "walsall", "walthamstow", "wandsworth", "warminster", "warrington",
    "warwick", "watford", "wednesbury", "wellingborough", "welshpool",
    "welwyn", "weston super mare", "wetherby", "weymouth", "whitby",
    "whitehaven", "whitstable", "widnes", "wigan", "wimbledon", "winchester",
    "windsor", "winsford", "wisbech", "witney", "woking", "wokingham",
    "wolverhampton", "woodbridge", "worcester", "workington", "worksop",
    "worthing", "wrexham", "yeovil", "york", "cheadle", "horwich", "loanhead",
    "walton", "surrey", "weybridge", "bourne", "graveley",
]


def api_get(endpoint):
    url = f"{API_BASE}/{endpoint}"
    req = urllib.request.Request(url, method="GET")
    req.add_header("Authorization", AUTH_HEADER)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def api_post(endpoint, payload):
    url = f"{API_BASE}/{endpoint}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", AUTH_HEADER)
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def check_balance():
    try:
        resp = api_get("appendix/user_data")
        if resp.get("tasks") and resp["tasks"][0].get("result"):
            r = resp["tasks"][0]["result"][0]
            money = r.get("money", {})
            bal = money.get("balance", "N/A")
            print(f"  Balance: ${bal}")
            return money
    except Exception as e:
        print(f"  Balance check failed: {e}")
    return {}


def load_existing_skip_keywords():
    """Load skip-hire related keywords from previous mining run."""
    keywords = {}
    try:
        with open("uk_keyword_opportunities.csv", "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                kw = row["keyword"].lower()
                if any(term in kw for term in ["skip", "grab hire", "grab lorry"]):
                    keywords[row["keyword"]] = {
                        "keyword": row["keyword"],
                        "search_volume": int(row["search_volume"]),
                        "cpc": float(row["cpc"]),
                        "competition": float(row["competition"]),
                        "competition_level": row["competition_level"],
                        "keyword_difficulty": row["keyword_difficulty"] if row["keyword_difficulty"] else None,
                        "seed": row["seed"],
                    }
    except FileNotFoundError:
        pass
    return keywords


def fetch_keywords(seed):
    payload = [{
        "keyword": seed,
        "location_code": 2826,
        "language_code": "en",
        "include_seed_keyword": True,
        "limit": 700,
    }]
    return api_post("dataforseo_labs/google/keyword_suggestions/live", payload)


def classify_keyword(kw):
    kw_lower = kw.lower()

    for city in UK_CITIES:
        pattern = r'\b' + re.escape(city) + r'\b'
        if re.search(pattern, kw_lower):
            return "CITY_PAGE", city

    if "near me" in kw_lower or "close to me" in kw_lower or "nearby" in kw_lower:
        return "NEAR_ME", None

    size_patterns = [
        r'\d+\s*yard', r'\d+\s*cubic', r'\bmini\b', r'\bmidi\b',
        r'\bmaxi\b', r'\blarge skip\b', r'\bsmall skip\b', r'\bbuilders?\s*skip\b',
        r'\bro-?ro\b', r'\broro\b', r'\d+m3', r'\bbag\b',
    ]
    for pat in size_patterns:
        if re.search(pat, kw_lower):
            return "SIZE_SPECIFIC", None

    buy_words = [
        "cheap", "price", "cost", "how much", "quote", "book", "order",
        "hire a", "same day", "next day", "delivery", "collect",
        "affordable", "budget", "deal", "offer", "discount",
        "wait and load", "grab hire", "grab lorry",
    ]
    for w in buy_words:
        if w in kw_lower:
            return "BUYING_INTENT", None

    info_words = [
        "permit", "what can", "what goes", "how to", "rules", "regulation",
        "allowed", "guide", "tip", "weight", "heavy", "recycle", "waste",
        "asbestos", "hazardous", "licence", "license", "council", "law",
        "size", "dimension", "capacity",
    ]
    for w in info_words:
        if w in kw_lower:
            return "INFORMATIONAL", None

    return "BUYING_INTENT", None


def main():
    print("=" * 70)
    print("SKIP HIRE DEEP KEYWORD MINE — DataForSEO")
    print("=" * 70)

    # 1. Check balance
    print("\n[1] Checking account balance...")
    money = check_balance()
    bal = money.get("balance", 0)

    # 2. Load existing skip keywords
    existing = load_existing_skip_keywords()
    print(f"\n[2] Found {len(existing)} existing skip-hire keywords from previous run")

    # 3. Try API mining if balance allows
    all_keywords = dict(existing)  # Start with existing
    total_cost = 0.0
    api_available = isinstance(bal, (int, float)) and bal > 0.10

    if api_available:
        print(f"\n[3] Balance ${bal:.2f} available — mining {len(SEED_KEYWORDS)} seeds...")
        for i, seed in enumerate(SEED_KEYWORDS):
            print(f"  [{i+1:2d}/{len(SEED_KEYWORDS)}] '{seed}' ... ", end="", flush=True)

            try:
                resp = fetch_keywords(seed)
            except urllib.error.HTTPError as e:
                print(f"HTTP {e.code}: {e.reason}")
                if e.code == 402:
                    print("\n  *** PAYMENT REQUIRED — stopping. ***")
                    break
                time.sleep(0.3)
                continue
            except urllib.error.URLError as e:
                print(f"ERROR: {e}")
                time.sleep(0.3)
                continue

            task = resp.get("tasks", [{}])[0]
            if task.get("status_code") != 20000:
                print(f"API error: {task.get('status_message')}")
                time.sleep(0.3)
                continue

            cost = task.get("cost", 0) or 0
            total_cost += cost
            result = (task.get("result") or [None])[0]
            items = (result.get("items") if result else None) or []

            count = 0
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
                if vol < 100 or comp_level not in ("LOW", "MEDIUM"):
                    continue
                count += 1
                if kw_str not in all_keywords or vol > all_keywords[kw_str]["search_volume"]:
                    all_keywords[kw_str] = {
                        "keyword": kw_str, "search_volume": vol, "cpc": cpc,
                        "competition": comp, "competition_level": comp_level,
                        "keyword_difficulty": difficulty, "seed": seed,
                    }

            print(f"{count} matched, cost=${cost:.4f}, total=${total_cost:.4f}")
            if total_cost >= COST_LIMIT:
                print(f"\n  *** COST LIMIT ${COST_LIMIT} reached! Stopping. ***")
                break
            time.sleep(0.3)
    else:
        print(f"\n[3] Balance ${bal} — insufficient for API calls.")
        print("    Analyzing existing skip-hire keywords instead.")

    # 4. Sort and save
    sorted_kws = sorted(all_keywords.values(), key=lambda x: x["search_volume"], reverse=True)

    csv_path = "skip_hire_deep_keywords.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "keyword", "search_volume", "cpc", "competition",
            "competition_level", "keyword_difficulty", "seed"
        ])
        writer.writeheader()
        writer.writerows(sorted_kws)

    print(f"\n[4] Saved {len(sorted_kws)} unique keywords to {csv_path}")

    # 5. Top 50
    print("\n" + "=" * 95)
    print("TOP 50 SKIP HIRE KEYWORDS BY SEARCH VOLUME")
    print("=" * 95)
    print(f"{'Keyword':<50} {'Volume':>8} {'CPC':>7} {'Comp Level':<10} {'Diff':>6}")
    print("-" * 95)
    for r in sorted_kws[:50]:
        diff = str(r["keyword_difficulty"]) if r["keyword_difficulty"] is not None else "N/A"
        print(f"{r['keyword']:<50} {r['search_volume']:>8,} {r['cpc']:>7.2f} {r['competition_level']:<10} {diff:>6}")

    # 6. Summary
    print(f"\n{'=' * 50}")
    print(f"Total unique keywords: {len(sorted_kws):,}")
    print(f"Total API cost this run: ${total_cost:.4f}")

    # 7. Final balance
    print(f"\n[5] Final account balance...")
    check_balance()

    # 8. BUCKET ANALYSIS
    print("\n" + "=" * 70)
    print("KEYWORD BUCKET ANALYSIS")
    print("=" * 70)

    buckets = defaultdict(lambda: {"count": 0, "volume": 0, "keywords": []})
    cities_found = defaultdict(lambda: {"count": 0, "volume": 0, "keywords": []})

    for r in sorted_kws:
        bucket, city = classify_keyword(r["keyword"])
        buckets[bucket]["count"] += 1
        buckets[bucket]["volume"] += r["search_volume"]
        buckets[bucket]["keywords"].append(r)
        if city:
            cities_found[city]["count"] += 1
            cities_found[city]["volume"] += r["search_volume"]
            cities_found[city]["keywords"].append(r["keyword"])

    total_vol = sum(b["volume"] for b in buckets.values()) or 1
    print(f"\n{'Bucket':<20} {'Keywords':>10} {'Total Volume':>14} {'% of Total':>10}")
    print("-" * 60)
    for bucket in ["CITY_PAGE", "BUYING_INTENT", "SIZE_SPECIFIC", "INFORMATIONAL", "NEAR_ME"]:
        b = buckets[bucket]
        pct = b["volume"] / total_vol * 100
        print(f"{bucket:<20} {b['count']:>10,} {b['volume']:>14,} {pct:>9.1f}%")

    # Show top keywords per bucket
    for bucket in ["CITY_PAGE", "BUYING_INTENT", "SIZE_SPECIFIC", "INFORMATIONAL", "NEAR_ME"]:
        b = buckets[bucket]
        if not b["keywords"]:
            continue
        top = sorted(b["keywords"], key=lambda x: x["search_volume"], reverse=True)[:10]
        print(f"\n  Top {bucket} keywords:")
        for kw in top:
            print(f"    {kw['keyword']:<45} vol={kw['search_volume']:>6,}  cpc=£{kw['cpc']:.2f}")

    # 9. City target list
    print("\n" + "=" * 70)
    print("UK CITIES/TOWNS FOUND IN KEYWORDS — PAGE TARGET LIST")
    print("=" * 70)
    sorted_cities = sorted(cities_found.items(), key=lambda x: x[1]["volume"], reverse=True)
    print(f"\n{'City/Town':<25} {'Keywords':>10} {'Total Volume':>14}")
    print("-" * 55)
    for city, data in sorted_cities:
        print(f"{city.title():<25} {data['count']:>10} {data['volume']:>14,}")

    print(f"\nTotal unique cities/towns found: {len(sorted_cities)}")
    print(f"\nCity list for page generation:")
    print(", ".join(c.title() for c, _ in sorted_cities))

    # 10. Page type recommendations
    print("\n" + "=" * 70)
    print("PAGE BUILD RECOMMENDATIONS")
    print("=" * 70)
    print(f"""
Based on keyword analysis:

1. CITY PAGES ({buckets['CITY_PAGE']['count']} keywords, {buckets['CITY_PAGE']['volume']:,} total vol):
   Build individual pages for each city. Target: "skip hire [city]"
   Cities to target: {len(sorted_cities)}

2. BUYING INTENT PAGES ({buckets['BUYING_INTENT']['count']} keywords, {buckets['BUYING_INTENT']['volume']:,} total vol):
   Pricing pages, booking pages, comparison pages

3. SIZE GUIDE PAGES ({buckets['SIZE_SPECIFIC']['count']} keywords, {buckets['SIZE_SPECIFIC']['volume']:,} total vol):
   Individual pages per skip size (mini, midi, builders, etc.)

4. INFO/GUIDE PAGES ({buckets['INFORMATIONAL']['count']} keywords, {buckets['INFORMATIONAL']['volume']:,} total vol):
   Permits guide, waste rules, what goes in a skip, etc.

5. NEAR ME OPTIMIZATION ({buckets['NEAR_ME']['count']} keywords, {buckets['NEAR_ME']['volume']:,} total vol):
   Schema markup + local SEO on all city pages
""")


if __name__ == "__main__":
    main()
