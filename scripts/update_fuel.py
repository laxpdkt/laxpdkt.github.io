"""Update data/fuel-daily.csv (petrol and diesel in the four metros, every day) from PPAC, Government of India.

PPAC (Petroleum Planning & Analysis Cell, Ministry of Petroleum and Natural Gas) posts a PDF "Daily Price of MS & HSD
in Metro cities" on its home page, with every day back to June 2017, for Delhi, Mumbai, Chennai and Kolkata.
This script finds the newest one, reads all four cities and merges them into data/fuel-daily.csv
(days already in the file but not in the PDF are kept). If PPAC can't be read, the file is not changed.
Runs every day on GitHub; see .github/workflows/update-videos.yml.

Columns: petrol_per_litre and diesel_per_litre are Chennai (the site's home city); the other three cities have
their own columns, e.g. delhi_petrol_per_litre.
"""
import csv, io, re, sys, urllib.request, datetime as dt
from pathlib import Path
from pypdf import PdfReader

HOME = "https://ppac.gov.in/"
OUT = Path(__file__).resolve().parent.parent / "data" / "fuel-daily.csv"
UA = {"User-Agent": "sakas.in price updater (daily, once)"}
ROW = re.compile(r"(\d{2}-[A-Z][a-z]{2}-\d{2})\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+\d{2}-[A-Z][a-z]{2}-\d{2}\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)")
# PDF columns: Delhi, Mumbai, Chennai, Kolkata (petrol, groups 2-5), then the same four for diesel (groups 6-9)
CITIES = {"delhi": 0, "mumbai": 1, "chennai": 2, "kolkata": 3}
FIELDS = ["date", "petrol_per_litre", "diesel_per_litre"] + [
    f"{c}_{f}_per_litre" for c in ("delhi", "mumbai", "kolkata") for f in ("petrol", "diesel")]

def col(city, fuel):
    return f"{fuel}_per_litre" if city == "chennai" else f"{city}_{fuel}_per_litre"

def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()

def main():
    html = get(HOME).decode("utf-8", "replace")
    links = re.findall(r'href="([^"]*PP_9_a_DailyPriceMSHSD_Metro[^"]*\.pdf)"', html)
    if not links:
        sys.exit("PPAC: daily metro price PDF not found on the home page; nothing changed")
    url = links[0] if links[0].startswith("http") else HOME + links[0].lstrip("/")
    text = "".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(get(url.replace(" ", "%20")))).pages)
    rows = {}
    for m in ROW.finditer(text):
        day = dt.datetime.strptime(m.group(1), "%d-%b-%y").date().isoformat()
        r = {"date": day}
        for c, i in CITIES.items():
            r[col(c, "petrol")] = m.group(2 + i)
            r[col(c, "diesel")] = m.group(6 + i)
        rows[day] = r
    if len(rows) < 1000:
        sys.exit(f"PPAC: only {len(rows)} days read, expected years of data; nothing changed")
    if OUT.exists():
        with OUT.open(encoding="utf-8") as f:
            for r in csv.DictReader(f):
                old = {k: v for k, v in r.items() if k in FIELDS and v}
                if r["date"] not in rows:
                    rows[r["date"]] = old              # keep older days the PDF no longer lists
                else:
                    for k, v in old.items():           # fill a gap from the file, never overwrite PPAC
                        rows[r["date"]].setdefault(k, v)
    OUT.parent.mkdir(exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, restval="")
        w.writeheader()
        w.writerows(rows[d] for d in sorted(rows))
    last = max(rows)
    print(f"fuel-daily.csv: {len(rows)} days, {min(rows)} -> {last}")
    for c in CITIES:
        print(f"  {c:8} {last}: petrol {rows[last].get(col(c, 'petrol'))}, diesel {rows[last].get(col(c, 'diesel'))}")

if __name__ == "__main__":
    main()
