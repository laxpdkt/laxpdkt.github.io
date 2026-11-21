"""Update data/fuel-daily.csv (Chennai petrol and diesel, every day) from PPAC, Government of India.

PPAC (Petroleum Planning & Analysis Cell, Ministry of Petroleum and Natural Gas) posts a PDF "Daily Price of MS & HSD
in Metro cities" on its home page, with every day back to June 2017. This script finds the newest one, reads the
Chennai columns and merges them into data/fuel-daily.csv (days already in the file but not in the PDF are kept).
If PPAC can't be read, the file is not changed. Runs every day on GitHub; see .github/workflows/update-videos.yml.
"""
import csv, io, re, sys, urllib.request, datetime as dt
from pathlib import Path
from pypdf import PdfReader

HOME = "https://ppac.gov.in/"
OUT = Path(__file__).resolve().parent.parent / "data" / "fuel-daily.csv"
UA = {"User-Agent": "sakas.in price updater (daily, once)"}
ROW = re.compile(r"(\d{2}-[A-Z][a-z]{2}-\d{2})\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+\d{2}-[A-Z][a-z]{2}-\d{2}\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)")
# PDF columns: Delhi, Mumbai, Chennai, Kolkata (petrol), then the same four for diesel -> Chennai = groups 4 and 8
PETROL, DIESEL = 4, 8

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
        rows[day] = {"date": day, "petrol_per_litre": m.group(PETROL), "diesel_per_litre": m.group(DIESEL)}
    if len(rows) < 1000:
        sys.exit(f"PPAC: only {len(rows)} days read, expected years of data; nothing changed")
    if OUT.exists():
        with OUT.open(encoding="utf-8") as f:
            for r in csv.DictReader(f):
                rows.setdefault(r["date"], r)       # keep older days the PDF no longer lists
    OUT.parent.mkdir(exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date", "petrol_per_litre", "diesel_per_litre"])
        w.writeheader()
        w.writerows(rows[d] for d in sorted(rows))
    last = max(rows)
    print(f"fuel-daily.csv: {len(rows)} days, {min(rows)} -> {last}; Chennai {last}: petrol {rows[last]['petrol_per_litre']}, diesel {rows[last]['diesel_per_litre']}")

if __name__ == "__main__":
    main()
