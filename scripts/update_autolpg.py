"""Update data/autolpg-daily.csv (Auto-LPG, Trichy) from the KR Fuels website, every day.

K.R Trans Fuels (krfuels.com, Tamil Nadu's largest Auto-LPG network, head office in Tiruchirappalli) shows
"Today · Tiruchirappalli Auto-LPG ₹../litre" at the top of every page. It is the only Auto-LPG price the site
publishes (its Chennai station pages show the same Trichy price), so this is a Trichy price.
One line per day: the price on the day it was read, and when KR Fuels last changed it.
If the site can't be read or the number looks wrong, the file is not changed.
Runs every day on GitHub; see .github/workflows/update-videos.yml.
"""
import csv, re, sys, urllib.request, datetime as dt
from pathlib import Path

URL = "https://www.krfuels.com/"
OUT = Path(__file__).resolve().parent.parent / "data" / "autolpg-daily.csv"
FIELDS = ["date", "autolpg_per_litre", "autolpg_where", "kr_updated"]
WHERE = "KR Fuels Trichy"
# the page carries its data as JSON inside the HTML (quotes may be escaped as \")
PRICE = re.compile(r'\\?"prices\\?"\s*:\s*\{\\?"autoLPG\\?"\s*:\s*([\d.]+)(.*?)\}', re.S)
UPDATED = re.compile(r'\\?"priceUpdatedAt\\?"\s*:\s*\\?"(\d{4}-\d{2}-\d{2})')

def main():
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0 (sakas.in price updater, once a day)"})
    html = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
    m = PRICE.search(html)
    if not m:
        sys.exit("KR Fuels: Auto-LPG price not found on the page; nothing changed")
    price = float(m.group(1))
    if not 20 <= price <= 200:
        sys.exit(f"KR Fuels: Auto-LPG ₹{price} looks wrong; nothing changed")
    u = UPDATED.search(m.group(2))
    updated = u.group(1) if u else ""
    today = dt.datetime.now(dt.timezone(dt.timedelta(hours=5, minutes=30))).date().isoformat()   # India date
    rows = {}
    if OUT.exists():
        with OUT.open(encoding="utf-8") as f:
            rows = {r["date"]: r for r in csv.DictReader(f)}
    rows[today] = {"date": today, "autolpg_per_litre": f"{price:.2f}", "autolpg_where": WHERE, "kr_updated": updated}
    OUT.parent.mkdir(exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, restval="")
        w.writeheader()
        w.writerows(rows[d] for d in sorted(rows))
    print(f"autolpg-daily.csv: {today} Trichy Auto-LPG ₹{price:.2f} (KR Fuels changed it on {updated or '?'})")

if __name__ == "__main__":
    main()
