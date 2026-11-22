"""Watch the official minimum-wage pages and tell the owner when something new appears.

Runs every day on GitHub (.github/workflows/check-wages.yml). It NEVER changes a wage figure by itself:
the app shows these wages to drivers, so a new figure is only added after a person has read the official order.

For each state it reads the official page and remembers:
  - every PDF link on that page (a new link = probably a new wage or DA order), and
  - the size / date of a few key files that the state replaces in place (same address, new content).
The remembered state lives in data/wages-watch.json. When something changes, or a page can't be read for
7 days in a row, the workflow opens a GitHub issue (GitHub emails you about it).
When every page with a verified wage was read, "lastChecked" in data/wages.json is set to today.

The first run only records what is there (no alert).
"""
import hashlib, json, re, sys, urllib.request, urllib.parse, datetime as dt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WAGES = ROOT / "data" / "wages.json"
WATCH = ROOT / "data" / "wages-watch.json"
ALERT = ROOT / "wage-alert.md"          # read by the workflow, never committed
UA = {"User-Agent": "Mozilla/5.0 (sakas.in minimum-wage watcher, once a day)"}

SOURCES = {
    "Delhi": {
        "page": "https://labour.delhi.gov.in/labour/current-minimum-wage-rate",
        "links": r"generic_multiple_files/[^\"']+\.pdf",
        "files": ["https://labour.delhi.gov.in/sites/default/files/Labour/generic_multiple_files/minimum_wages_current.pdf"],
    },
    "Tamil Nadu": {
        "page": "https://labour.tn.gov.in/minimum-wages.php",
        "links": r"[^\"']+\.pdf",
        "files": [],
    },
    "Maharashtra": {
        "page": "https://mahakamgar.maharashtra.gov.in/",
        "links": r"[^\"']*(?:[Mm]inimum|[Ww]age|[Aa]llowance|VDA)[^\"']*\.pdf",
        "files": ["https://mahakamgar.maharashtra.gov.in/Site/Upload/Pdf/minimum-wages.pdf"],
    },
    "West Bengal": {
        "page": "https://wblc.gov.in/",
        "links": r"[^\"']*(?:[Mm]inimum|[Ww]age)[^\"']*\.pdf",
        "files": [],
    },
}
DOWN_DAYS = 7

def safe(url):   # spaces and brackets in government file names must be encoded
    return urllib.parse.quote(url, safe=":/%?=&#~+")

def get(url):
    with urllib.request.urlopen(urllib.request.Request(safe(url), headers=UA), timeout=60) as r:
        return r, r.read()

def page_links(src):
    _, body = get(src["page"])
    html = body.decode("utf-8", "replace")
    found = set()
    for m in re.finditer(r"href\s*=\s*[\"']([^\"']+)[\"']", html, re.I):
        href = m.group(1).strip()
        if re.search(src["links"], href):
            found.add(urllib.parse.urljoin(src["page"], href))
    return sorted(found)

def file_stamp(url):
    """A fingerprint of the file's content (size + SHA-256), or None if it could not be downloaded today."""
    try:
        _, body = get(url)
        return f"{len(body)} bytes, sha256 {hashlib.sha256(body).hexdigest()[:16]}"
    except Exception as e:
        print(f"  could not download {url} ({type(e).__name__})")
        return None

def main():
    today = dt.date.today().isoformat()
    wages = json.loads(WAGES.read_text(encoding="utf-8"))
    old = json.loads(WATCH.read_text(encoding="utf-8")) if WATCH.exists() else {}
    new, alerts, all_verified_ok = {}, [], True
    for state, src in SOURCES.items():
        prev = old.get(state, {})
        rec = {"page": src["page"], "links": prev.get("links", []), "files": prev.get("files", {}),
               "lastOk": prev.get("lastOk"), "lastChange": prev.get("lastChange"), "downAlerted": prev.get("downAlerted", False)}
        verified = bool(wages.get("states", {}).get(state, {}).get("verified"))
        official = wages.get("states", {}).get(state, {}).get("officialUrl")
        files = list(src["files"]) + ([official] if official else [])
        try:
            links = page_links(src)
        except Exception as e:
            print(f"{state}: page could not be read ({type(e).__name__})")
            if verified: all_verified_ok = False
            last = rec["lastOk"]
            if last and (dt.date.fromisoformat(today) - dt.date.fromisoformat(last)).days >= DOWN_DAYS and not rec["downAlerted"]:
                alerts.append(f"### {state}\nThe official page has not opened for {DOWN_DAYS}+ days: {src['page']}\nCheck it by hand.")
                rec["downAlerted"] = True
            new[state] = rec; continue
        stamps = {u: file_stamp(u) for u in files}
        if prev.get("links") is not None and prev.get("lastOk"):
            added = [l for l in links if l not in prev.get("links", [])]
            # a file that could not be downloaded today (None) is not a change; keep yesterday's fingerprint
            changed = [u for u, s in stamps.items() if s and prev.get("files", {}).get(u) and prev["files"][u] != s]
            if added or changed:
                lines = [f"### {state}", f"Official page: {src['page']}"]
                lines += [f"- New document: {l}" for l in added]
                lines += [f"- Changed file: {u} (was {prev['files'][u]}, now {stamps[u]})" for u in changed]
                alerts.append("\n".join(lines))
                rec["lastChange"] = today
        stamps = {u: s or prev.get("files", {}).get(u) for u, s in stamps.items()}
        rec.update({"links": links, "files": stamps, "lastOk": today, "downAlerted": False})
        print(f"{state}: {len(links)} documents listed, {len(stamps)} key files checked")
        new[state] = rec
    WATCH.write_text(json.dumps(new, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if all_verified_ok:   # change only the date, keep the file's own layout
        with open(WAGES, encoding="utf-8", newline="") as f: text = f.read()
        with open(WAGES, "w", encoding="utf-8", newline="") as f:
            f.write(re.sub(r'("lastChecked"\s*:\s*")\d{4}-\d{2}-\d{2}(")', rf"\g<1>{today}\g<2>", text, count=1))
    if alerts:
        ALERT.write_text("Something changed on an official minimum-wage page. **The app's wages were NOT changed.**\n\n"
                         + "\n\n".join(alerts)
                         + "\n\nWhat to do: open the new document, check if it changes the driver wage for that state, then update "
                           "`data/wages.json` (amount, `effectiveFrom`, `notification`, `officialUrl`, `petrolAtEffective`) and close this issue. "
                           "Many new documents are for other jobs; if so, just close it.\n", encoding="utf-8")
        print("ALERT written")

if __name__ == "__main__":
    main()
