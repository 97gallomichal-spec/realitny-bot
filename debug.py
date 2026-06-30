# -*- coding: utf-8 -*-
"""Cielený prieskum #2 — presná štruktúra reality.sk, nehnutelnosti.sk, topreality.sk."""
import re
import json
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"),
    "Accept-Language": "sk,cs;q=0.9,en;q=0.8",
}


def get(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        return r
    except Exception as e:
        print("  CHYBA:", e)
        return None


def dump_ldjson(soup, label):
    print(f"\n--- {label}: ld+json typy ---")
    sample_done = False
    for s in soup.find_all("script", type="application/ld+json"):
        if not s.string:
            continue
        try:
            d = json.loads(s.string, strict=False)
        except Exception as e:
            print("   nečitateľné:", e)
            continue
        items = d if isinstance(d, list) else [d]
        for it in items:
            if not isinstance(it, dict):
                continue
            t = it.get("@type")
            print("   @type =", t, "| kľúče:", list(it)[:10])
            if not sample_done and t not in ("WebSite", "Organization", "BreadcrumbList"):
                print("   VZORKA:", json.dumps(it, ensure_ascii=False)[:700])
                sample_done = True


print("=" * 70, "\nREALITY.SK")
r = get("https://www.reality.sk/byty/bratislava/predaj/")
if r:
    print("HTTP", r.status_code, "| dĺžka", len(r.text), "| URL", r.url)
    soup = BeautifulSoup(r.text, "html.parser")
    dump_ldjson(soup, "reality.sk")

print("\n" + "=" * 70, "\nNEHNUTELNOSTI.SK — kde je cena")
r = get("https://www.nehnutelnosti.sk/vysledky/byty/bratislava/predaj")
if r:
    soup = BeautifulSoup(r.text, "html.parser")
    seen = set()
    n = 0
    for a in soup.find_all("a", href=True):
        m = re.search(r"/detail/([A-Za-z0-9_\-]+)/([a-z0-9\-]+)", a["href"])
        if not m or m.group(1) in seen:
            continue
        seen.add(m.group(1))
        # vystup okolo karty
        p = a
        for _ in range(5):
            p = p.parent
            if p is None:
                break
        txt = re.sub(r"\s+", " ", p.get_text(" ", strip=True))[:260] if p else ""
        print(f"  [{m.group(2)[:40]}] -> {txt}")
        n += 1
        if n >= 4:
            break

print("\n" + "=" * 70, "\nTOPREALITY.SK — hľadám správne URL")
for u in [
    "https://www.topreality.sk/predaj/byty/bratislava/",
    "https://www.topreality.sk/nehnutelnosti-predaj/byty/bratislava/",
    "https://www.topreality.sk/vyhladavanie-1-1--0-0-0-0-0--0-0-1-0-0-0-0--0-0--0-0-1-0----.html",
    "https://www.topreality.sk/byty/predaj/?lokalita=Bratislava",
    "https://www.topreality.sk/",
]:
    r = get(u)
    if not r:
        continue
    soup = BeautifulSoup(r.text, "html.parser")
    hrefs = [a["href"] for a in soup.find_all("a", href=True)
             if re.search(r"/(detail|inzerat|nehnutelnost|byt-)", a["href"], re.I)]
    uniq = list(dict.fromkeys(hrefs))
    print(f"  {r.status_code} | {len(r.text):>7} | odkazy:{len(uniq):>3} | {u}")
    for h in uniq[:4]:
        print("        ", h)

print("\n=== KONIEC ===")
