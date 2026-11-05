"""Download real SPL label XML from DailyMed into data/raw/ (git-ignored).

Usage: python scripts/fetch_dailymed.py --drug metformin --n 10
Needs outbound access to dailymed.nlm.nih.gov. UNTESTED against the live API
(the build sandbox blocked that host); check endpoints against
https://dailymed.nlm.nih.gov/dailymed/webservices-help/v2.cfm
"""

import argparse
import json
import pathlib
import urllib.parse
import urllib.request

BASE = "https://dailymed.nlm.nih.gov/dailymed/services/v2"


def get(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=60) as r:
        return r.read()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--drug", required=True)
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--out", default="data/raw")
    a = ap.parse_args()
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    q = urllib.parse.urlencode({"drug_name": a.drug, "pagesize": a.n})
    for item in json.loads(get(f"{BASE}/spls.json?{q}"))["data"]:
        sid = item["setid"]
        (out / f"{sid}.xml").write_bytes(get(f"{BASE}/spls/{sid}.xml"))
        print("saved", sid, item.get("title", "")[:60])


if __name__ == "__main__":
    main()
