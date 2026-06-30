# -*- coding: utf-8 -*-
"""
Prieskum portálov — zistí, ako sú stránky postavené, aby sa dali napísať parsery.
Spúšťa sa cez workflow 'debug.yml' (tlačidlo Run workflow). Výstup je v logu behu.
NEpoužíva sa pri bežnom hľadaní — je to len jednorazový diagnostický nástroj.
"""
import re
import json
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"),
    "Accept-Language": "sk,cs;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

CANDIDATES = [
    ("nehnutelnosti-A", "https://www.nehnutelnosti.sk/vysledky/bratislavsky-kraj/byty/predaj/"),
    ("nehnutelnosti-B", "https://www.nehnutelnosti.sk/byty/bratislava/predaj/"),
    ("topreality-A", "https://www.topreality.sk/byty-bratislava/predaj/"),
    ("topreality-B", "https://www.topreality.sk/vyhladavanie/predaj/byty/bratislava/"),
    ("reality-A", "https://www.reality.sk/byty/bratislava/predaj/"),
    ("reality-B", "https://www.reality.sk/vysledky-hladania/?form%5Bsubtype%5D=1&form%5Bcategory%5D=1&form%5Blocation%5D=Bratislava"),
    ("byty-A", "https://www.byty.sk/bratislava/predaj/"),
    ("bazos-ref", "https://reality.bazos.sk/predam/byt/?hlokalita=Bratislava&humkreis=25&cenado=250000"),
]

LISTING_HREF = re.compile(r"/(detail|inzerat|byt|nehnutelnost|realitne-inzeraty|ponuka)/", re.I)
BLOCK_WORDS = ["captcha", "cloudflare", "attention required", "pristup zamietnut",
               "access denied", "are you a robot", "ddos"]


def probe(name, url):
    print("\n" + "=" * 70)
    print(f"[{name}] {url}")
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
    except Exception as e:
        print(f"  CHYBA: {e}")
        return
    body = r.text or ""
    low = body.lower()
    print(f"  HTTP {r.status_code} | dĺžka {len(body)} | finalna URL: {r.url}")
    blk = [w for w in BLOCK_WORDS if w in low]
    if blk:
        print(f"  ⚠ MOŽNÝ BLOK: {blk}")
    soup = BeautifulSoup(body, "html.parser")
    ldjson = soup.find_all("script", type="application/ld+json")
    print(f"  ld+json blokov: {len(ldjson)}")
    for i, s in enumerate(ldjson[:3]):
        try:
            d = json.loads(s.string or "{}")
            t = d.get("@type") if isinstance(d, dict) else type(d).__name__
            print(f"     ld[{i}] @type={t} kľúče={list(d)[:8] if isinstance(d,dict) else ''}")
        except Exception as e:
            print(f"     ld[{i}] nečitateľné: {e}")
    nd = soup.find("script", id="__NEXT_DATA__")
    if nd and nd.string:
        try:
            d = json.loads(nd.string)
            print(f"  __NEXT_DATA__ NÁJDENÉ, top kľúče: {list(d)}")
            pp = d.get("props", {}).get("pageProps", {})
            print(f"     pageProps kľúče: {list(pp)[:15]}")
        except Exception as e:
            print(f"  __NEXT_DATA__ nečitateľné: {e}")
    # sample odkazov na inzeráty
    hrefs = []
    for a in soup.find_all("a", href=True):
        if LISTING_HREF.search(a["href"]):
            hrefs.append(a["href"])
    uniq = list(dict.fromkeys(hrefs))
    print(f"  odkazy na inzeráty (vzorka): {len(uniq)}")
    for h in uniq[:6]:
        print(f"     {h}")
    # vzorka class názvov kontajnerov okolo prvého odkazu
    if uniq:
        first = soup.find("a", href=lambda x: x and uniq[0] in x)
        if first:
            chain = []
            p = first
            for _ in range(4):
                p = p.parent
                if p is None or p.name is None:
                    break
                chain.append(f"{p.name}.{'.'.join(p.get('class', []) or [])}")
            print(f"     rodičovské tagy: {chain}")


if __name__ == "__main__":
    for name, url in CANDIDATES:
        probe(name, url)
    print("\n=== KONIEC PRIESKUMU ===")
