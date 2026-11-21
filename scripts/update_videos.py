"""Refresh videos.json from saka's corner's public YouTube feed.

Runs every day on GitHub (see .github/workflows/update-videos.yml), so new uploads appear on sakas.in without
anyone's computer being on. The feed only lists the 15 newest videos, so older ones already in videos.json are kept.
Each video is put on a shelf by simple keyword rules (edit SHELVES below to change them).
"""
import json, re, urllib.request, xml.etree.ElementTree as ET
from pathlib import Path

CHANNEL_ID = "UCh9xRLefJgg0bUxUQbcUVvg"
FEED = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"
OUT = Path(__file__).resolve().parent.parent / "videos.json"

# first matching shelf wins
SHELVES = [
    ("money", r"fuel|petrol|diesel|cng|lpg|inflation|salary|price|taxi|cab|wallet|profit|rupee|₹"),
    ("riddles", r"riddle|brain|outsmart|puzzle|quiz|guess"),
    ("learn", r"for kids|kids|learn|opposite|helpers|animals|cleaning|shapes|transport|fruits|vegetables|tamil"),
    ("discover", r"flag|history|digestive|evolution|science|body|india"),
    ("stories", r"\bmoms?\b|mother|mahabharata|choices|\bstor(y|ies)\b|tribute|song"),
]

def shelf_for(title):
    t = title.lower()
    for name, pat in SHELVES:
        if re.search(pat, t):
            return name
    return "more"

def main():
    ns = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015", "media": "http://search.yahoo.com/mrss/"}
    req = urllib.request.Request(FEED, headers={"User-Agent": "sakas.in video list updater"})
    root = ET.fromstring(urllib.request.urlopen(req, timeout=30).read())
    fresh = {}
    for e in root.findall("a:entry", ns):
        vid = e.find("yt:videoId", ns).text
        title = e.find("a:title", ns).text
        stats = e.find("media:group/media:community/media:statistics", ns)
        fresh[vid] = {"id": vid, "title": title, "published": e.find("a:published", ns).text[:10],
                      "views": int(stats.get("views")) if stats is not None else None, "shelf": shelf_for(title)}
    old = {}
    if OUT.exists():
        old = {v["id"]: v for v in json.loads(OUT.read_text(encoding="utf-8")).get("videos", [])}
    old.update(fresh)                      # new info wins; older videos stay
    videos = sorted(old.values(), key=lambda v: v["published"], reverse=True)
    data = {"channel": "saka's corner", "handle": "@sakascorner", "channelId": CHANNEL_ID, "videos": videos}
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(videos)} videos ({len(fresh)} from the feed)")

if __name__ == "__main__":
    main()
