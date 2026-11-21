"""Refresh channel.json with saka's corner's YouTube subscriber count (for the subscriber strip on sakas.in).

Runs once a day at 4:30 AM IST on GitHub (.github/workflows/update-subs.yml). Needs the repository secret YT_API_KEY
(a YouTube Data API v3 key). The key is only used here, on GitHub's servers; it is never put in the website.
Without the key, or if YouTube hides the count, the file is left as it is.

Besides the count it keeps one count per day for the last 30 days (the website's "at this pace" forecast),
the time of the last rise (the 3-day thank-you) and how many were gained in the last 7 days.
"""
import json, os, sys, urllib.request, urllib.parse
from datetime import datetime, timezone
from pathlib import Path

CHANNEL_ID = "UCh9xRLefJgg0bUxUQbcUVvg"
OUT = Path(__file__).resolve().parent.parent / "channel.json"

def main():
    key = os.environ.get("YT_API_KEY", "").strip()
    if not key:
        print("No YT_API_KEY secret yet: channel.json not changed."); return
    q = urllib.parse.urlencode({"part": "statistics", "id": CHANNEL_ID, "key": key})
    req = urllib.request.Request("https://www.googleapis.com/youtube/v3/channels?" + q, headers={"User-Agent": "sakas.in channel stats"})
    try:
        data = json.load(urllib.request.urlopen(req, timeout=30))
    except Exception as e:  # never print the URL: it contains the key
        print("YouTube request failed:", type(e).__name__); sys.exit(1)
    items = data.get("items") or []
    if not items:
        print("Channel not found."); sys.exit(1)
    s = items[0].get("statistics", {})
    if s.get("hiddenSubscriberCount"):
        print("Subscriber count is hidden on YouTube: not changed."); return
    subs = int(s.get("subscriberCount", -1))
    if not 0 <= subs < 1_000_000_000:
        print("Odd subscriber count, ignored."); sys.exit(1)

    now = datetime.now(timezone.utc)
    old = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    byday = {h[0]: h[1] for h in old.get("history", []) if isinstance(h, list) and len(h) == 2}
    byday[now.strftime("%Y-%m-%d")] = subs
    hist = [[d, byday[d]] for d in sorted(byday)][-30:]
    week_ago = next((c for d, c in reversed(hist) if (now - datetime.strptime(d, "%Y-%m-%d").replace(tzinfo=timezone.utc)).days >= 7), hist[0][1])
    last_up = old.get("lastIncrease")
    if subs > int(old.get("subscribers", subs)):
        last_up = now.strftime("%Y-%m-%dT%H:%MZ")
    out = {"subscribers": subs, "views": int(s.get("viewCount", 0)), "videos": int(s.get("videoCount", 0)),
           "asOf": now.strftime("%Y-%m-%dT%H:%MZ"), "lastIncrease": last_up, "gainedWeek": max(0, subs - week_ago), "history": hist}
    keys = ("subscribers", "views", "videos", "history", "lastIncrease")
    if {k: old.get(k) for k in keys} == {k: out[k] for k in keys}:
        print("No change:", subs); return
    OUT.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print("Subscribers:", subs)

if __name__ == "__main__":
    main()
