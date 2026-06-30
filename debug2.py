# -*- coding: utf-8 -*-
"""Cielená diagnostika karty na Nehnutelnosti.sk - hladame spravnu hranicu karty."""
import re
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"),
           "Accept-Language": "sk,cs;q=0.9"}

r = requests.get("https://www.nehnutelnosti.sk/vysledky/byty/bratislava/predaj",
                  headers=HEADERS, timeout=30)
print("HTTP", r.status_code, "dlzka", len(r.text))
soup = BeautifulSoup(r.text, "html.parser")

seen = set()
n = 0
for a in soup.find_all("a", href=True):
    m = re.search(r"/detail/([A-Za-z0-9_\-]+)/([a-z0-9\-]+)", a["href"])
    if not m or m.group(1) in seen:
        continue
    seen.add(m.group(1))
    n += 1
    print("\n" + "=" * 70)
    print("DETAIL:", a["href"])
    # vypis retazec rodicov s class a textom (kratky) a obrazkami
    p = a
    for depth in range(8):
        p = p.parent
        if p is None or p.name is None:
            break
        cls = ".".join(p.get("class", []) or [])
        txt = re.sub(r"\s+", " ", p.get_text(" ", strip=True))[:90]
        imgs = p.find_all("img")
        img_srcs = [(im.get("src") or im.get("data-src") or "")[:60] for im in imgs[:3]]
        has_eur = "€" in p.get_text()
        print(f"  d{depth} <{p.name} class='{cls[:60]}'> imgs={len(imgs)}{img_srcs} eur={has_eur}")
        print(f"      txt: {txt}")
    if n >= 3:
        break
print("\n=== KONIEC ===")
