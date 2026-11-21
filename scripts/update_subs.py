"""Refresh channel.json with saka's corner's YouTube subscriber count (for the odometer on sakas.in).

Runs every 3 hours on GitHub (.github/workflows/update-subs.yml). Needs the repository secret YT_API_KEY
(a YouTube Data API v3 key). The key is only used here, on GitHub's servers; it is never put in the website.
Without the key, or if YouTube hides the count, the file is left as it is.
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
    out = {"subscribers": subs, "views": int(s.get("viewCount", 0)), "videos": int(s.get("videoCount", 0)),
           "asOf": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")}
    old = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    if {k: old.get(k) for k in ("subscribers", "views", "videos")} == {k: out[k] for k in ("subscribers", "views", "videos")}:
        print("No change:", subs); return
    OUT.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print("Subscribers:", subs)

if __name__ == "__main__":
    main()
