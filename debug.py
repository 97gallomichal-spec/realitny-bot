# -*- coding: utf-8 -*-
"""Prieskum #3 — prečo Reality.sk dáva málo. Koľko položiek má url/cenu/typ."""
import re
import json
import requests
from bs4 import BeautifulSoup
import scraper as s

HEADERS = {"User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"),
           "Accept-Language": "sk,cs;q=0.9"}

r = requests.get("https://www.reality.sk/byty/bratislava/predaj/", headers=HEADERS, timeout=30)
print("HTTP", r.status_code, "dĺžka", len(r.text))
soup = BeautifulSoup(r.text, "html.parser")
total = url_ok = price_ok = type_ok = 0
samples = []
for sc in soup.find_all("script", type="application/ld+json"):
    if not sc.string:
        continue
    try:
        d = json.loads(sc.string, strict=False)
    except Exception:
        continue
    for block in (d if isinstance(d, list) else [d]):
        if not isinstance(block, dict):
            continue
        t = block.get("@type"); types = t if isinstance(t, list) else [t]
        if "ItemList" not in types:
            continue
        for el in block.get("itemListElement", []) or []:
            me = el.get("mainEntity") if isinstance(el, dict) and isinstance(el.get("mainEntity"), dict) else (el if isinstance(el, dict) else None)
            if not isinstance(me, dict):
                continue
            total += 1
            name = me.get("name", "")
            link = me.get("url") or me.get("@id") or ""
            offers = me.get("offers") or {}
            if isinstance(offers, list): offers = offers[0] if offers else {}
            price = offers.get("price") if isinstance(offers, dict) else None
            if link: url_ok += 1
            if price: price_ok += 1
            if s.matches_type(name + " " + str(me.get("description", ""))): type_ok += 1
            if len(samples) < 5:
                samples.append((name[:50], "url=" + (link[:45] if link else "CHÝBA"),
                                "cena=" + str(price), "kľúče=" + str(list(me)[:9])))
print(f"itemListElement spolu: {total} | s url: {url_ok} | s cenou: {price_ok} | typ sedí: {type_ok}")
for x in samples:
    print("  ", x)
print("=== KONIEC ===")
