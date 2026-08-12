#!/usr/bin/env python3
import html
import json
import os
import re
import time
from datetime import datetime, timezone
from urllib.parse import quote
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

CHANNEL = os.environ.get("TELEGRAM_CHANNEL", "lht_hn")
PAGES = int(os.environ.get("TELEGRAM_PAGES", "10"))
LIMIT = min(int(os.environ.get("TELEGRAM_LIMIT", "100")), 100)
OUT = Path = __import__("pathlib").Path("docs/lht.xml")
BASE = "https://tg.i-c-a.su"

def fetch_json(page):
    if page == 1:
        url = f"{BASE}/json/{CHANNEL}?limit={LIMIT}"
    else:
        url = f"{BASE}/json/{CHANNEL}/{page}?limit={LIMIT}"
    req = Request(url, headers={"User-Agent": "LHT-ClearWave-RSS/1.0"})
    with urlopen(req, timeout=30) as r:
        return json.load(r)

def pick_messages(data):
    if isinstance(data, list):
        return data
    for k in ("messages", "items", "posts", "result", "data"):
        v = data.get(k) if isinstance(data, dict) else None
        if isinstance(v, list):
            return v
    return []

def get_text(m):
    for k in ("text", "caption", "message"):
        v = m.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""

def get_id(m):
    return m.get("id") or m.get("message_id") or m.get("post_id")

def get_date(m):
    v = m.get("date") or m.get("published_at") or m.get("timestamp")
    if isinstance(v, (int, float)):
        return datetime.fromtimestamp(v, timezone.utc)
    if isinstance(v, str):
        try:
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        except Exception:
            pass
    return datetime.now(timezone.utc)

def media_url(msg_id):
    return f"{BASE}/media/{CHANNEL}/{msg_id}"

def looks_audio(m):
    candidates = []
    for k in ("mime_type", "content_type", "type", "media_type"):
        if isinstance(m.get(k), str):
            candidates.append(m[k].lower())
    for k in ("file_name", "filename", "name"):
        if isinstance(m.get(k), str):
            candidates.append(m[k].lower())
    s = " ".join(candidates)
    return ("audio" in s or any(x in s for x in (".mp3", ".m4a", ".aac", ".ogg", ".wav", ".flac")))

def duration(m):
    for k in ("duration", "duration_seconds"):
        v = m.get(k)
        if isinstance(v, (int, float)) and v > 0:
            return int(v)
    return None

def main():
    all_msgs = []
    for page in range(1, PAGES + 1):
        try:
            data = fetch_json(page)
            msgs = pick_messages(data)
            if not msgs:
                break
            all_msgs.extend(msgs)
            time.sleep(4.2)
        except Exception as e:
            print(f"Page {page} failed: {e}")
            break

    seen = set()
    items = []
    for m in all_msgs:
        mid = get_id(m)
        if not mid or mid in seen or not looks_audio(m):
            continue
        seen.add(mid)
        title = get_text(m).splitlines()[0][:300] or f"LHT Telegram #{mid}"
        dt = get_date(m)
        enc = media_url(mid)
        item = {
            "id": str(mid),
            "title": title,
            "date": dt,
            "url": enc,
            "description": get_text(m),
            "duration": duration(m),
        }
        items.append(item)

    items.sort(key=lambda x: x["date"], reverse=True)
    items = items[:500]

    rss = ET.Element("rss", {"version": "2.0", "xmlns:itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd"})
    ch = ET.SubElement(rss, "channel")
    ET.SubElement(ch, "title").text = "La Hora del Té - Telegram"
    ET.SubElement(ch, "link").text = f"https://t.me/{CHANNEL}"
    ET.SubElement(ch, "description").text = "Archivos de audio publicados en el canal de Telegram de La Hora del Té."
    ET.SubElement(ch, "language").text = "es"
    ET.SubElement(ch, "generator").text = "LHT Telegram RSS bridge"

    for x in items:
        it = ET.SubElement(ch, "item")
        ET.SubElement(it, "title").text = x["title"]
        ET.SubElement(it, "guid", {"isPermaLink": "false"}).text = f"telegram-{CHANNEL}-{x['id']}"
        ET.SubElement(it, "pubDate").text = x["date"].strftime("%a, %d %b %Y %H:%M:%S GMT")
        ET.SubElement(it, "description").text = x["description"]
        ET.SubElement(it, "link").text = f"https://t.me/{CHANNEL}/{x['id']}"
        enc = ET.SubElement(it, "enclosure", {"url": x["url"], "type": "audio/mpeg"})
        if x["duration"]:
            ET.SubElement(it, "{http://www.itunes.com/dtds/podcast-1.0.dtd}duration").text = str(x["duration"])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(rss).write(OUT, encoding="utf-8", xml_declaration=True)
    print(f"Wrote {len(items)} audio items to {OUT}")

if __name__ == "__main__":
    main()
