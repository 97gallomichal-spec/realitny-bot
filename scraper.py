# -*- coding: utf-8 -*-
"""
Realitný bot — hľadá byty na kúpu v Bratislave podľa kritérií v config.py.
Beží na GitHub Actions každú hodinu. Nové inzeráty pošle e‑mailom a zobrazí
na stránke (docs/index.html). Appky Tower Finance sa NIJAKO netýka.
"""

import os
import re
import json
import html
import smtplib
import datetime
import unicodedata
import urllib.parse
from email.mime.text import MIMEText

import requests
from bs4 import BeautifulSoup

import config

# ── Cesty k súborom ─────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT, "data")
DOCS_DIR = os.path.join(ROOT, "docs")
SEEN_FILE = os.path.join(DATA_DIR, "seen.json")
LISTINGS_FILE = os.path.join(DATA_DIR, "listings.json")
DOCS_HTML = os.path.join(DOCS_DIR, "index.html")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "sk,cs;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
TIMEOUT = 25


# ── Pomocné funkcie ─────────────────────────────────────────────────────────
def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def strip_diacritics(text):
    if not text:
        return ""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def norm(text):
    """Malé písmená bez diakritiky — na hľadanie kľúčových slov."""
    return strip_diacritics(text or "").lower()


def fetch(url):
    """Stiahne stránku. Pri chybe vráti None (bot nespadne)."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if r.status_code == 200:
            return r.text
        print(f"   ⚠ HTTP {r.status_code}: {url}")
    except Exception as e:
        print(f"   ⚠ chyba siete: {e} ({url})")
    return None


def parse_price(text):
    """Z textu '189 000 €' spraví číslo 189000. Vráti (cislo|None, povodny_text)."""
    raw = (text or "").strip()
    digits = re.sub(r"[^\d]", "", raw)
    if digits and len(digits) >= 4:
        return int(digits), raw
    return None, raw


def matches_type(text):
    """Sedí inzerát na hľadané typy bytov?"""
    h = norm(text)
    return any(re.search(pat, h) for pat in config.TYPY_REGEX)


def classify_condition(text):
    """Vráti 'povodny' | 'rekonstruovany' | 'novostavba' | 'neznamy'."""
    h = norm(text)
    for pat in config.STAV_VYLUCIT:
        if re.search(pat, h):
            return "novostavba" if "novostav" in pat else "rekonstruovany"
    for pat in config.STAV_POVODNY:
        if re.search(pat, h):
            return "povodny"
    return "neznamy"


def passes_condition(cond):
    if not config.FILTROVAT_STAV:
        return True
    # Chceme pôvodný stav alebo neznámy (nech nič neujde). Vyhodíme hotové/nové.
    return cond in ("povodny", "neznamy")


def passes_price(price):
    if price is None:
        return True  # cena dohodou — necháme, ale označíme
    if price > config.CENA_MAX:
        return False
    if config.CENA_MIN and price < config.CENA_MIN:
        return False
    return True


def make_listing(portal, lid, title, url, price_text, location, image, desc):
    price, price_raw = parse_price(price_text)
    cond = classify_condition(f"{title} {desc}")
    return {
        "id": f"{portal}:{lid}",
        "portal": portal,
        "title": (title or "").strip(),
        "url": url,
        "price": price,
        "price_text": price_raw or "Cena dohodou",
        "location": (location or "").strip(),
        "image": image or "",
        "condition": cond,
        "desc": (desc or "").strip()[:300],
    }


def keep(listing):
    text = f"{listing['title']} {listing['desc']}"
    return (
        matches_type(text)
        and passes_price(listing["price"])
        and passes_condition(listing["condition"])
    )


# ── Portál: Bazoš ───────────────────────────────────────────────────────────
def scrape_bazos():
    out = []
    q = urllib.parse.urlencode({
        "hlokalita": config.LOKALITA,
        "humkreis": config.OKRUH_KM,
        "cenaod": config.CENA_MIN or "",
        "cenado": config.CENA_MAX,
    })
    for page in range(config.MAX_STRAN):
        offset = page * 20
        base = "https://reality.bazos.sk/predam/byt/"
        url = f"{base}{offset}/?{q}" if offset else f"{base}?{q}"
        htmltext = fetch(url)
        if not htmltext:
            break
        soup = BeautifulSoup(htmltext, "html.parser")
        ads = soup.select("div.inzeraty")
        if not ads:
            break
        for ad in ads:
            a = ad.select_one("div.inzeratynadpis a") or ad.select_one("a")
            if not a or not a.get("href"):
                continue
            href = urllib.parse.urljoin("https://reality.bazos.sk", a["href"])
            title = a.get_text(" ", strip=True)
            price_el = ad.select_one("div.inzeratycena")
            loc_el = ad.select_one("div.inzeratylok")
            desc_el = ad.select_one("div.popis")
            img_el = ad.select_one("img")
            image = ""
            if img_el:
                image = img_el.get("src") or img_el.get("data-src") or ""
                if image.startswith("//"):
                    image = "https:" + image
            m = re.search(r"/inzerat/(\d+)", href)
            lid = m.group(1) if m else href
            out.append(make_listing(
                "bazos", lid, title, href,
                price_el.get_text(" ", strip=True) if price_el else "",
                loc_el.get_text(" ", strip=True) if loc_el else config.LOKALITA,
                image,
                desc_el.get_text(" ", strip=True) if desc_el else "",
            ))
    return out


# ── Portál: Nehnuteľnosti.sk ────────────────────────────────────────────────
def scrape_nehnutelnosti():
    """
    Nehnuteľnosti.sk je moderná appka (Next.js) — dáta sú v JSON bloku
    __NEXT_DATA__ alebo v JSON-LD. Skúšame oboje, defenzívne.
    """
    out = []
    url = (
        "https://www.nehnutelnosti.sk/vysledky/"
        f"?categories=1&transaction=1&priceTo={config.CENA_MAX}"
        f"&query={urllib.parse.quote(config.LOKALITA)}"
    )
    htmltext = fetch(url)
    if not htmltext:
        return out
    soup = BeautifulSoup(htmltext, "html.parser")

    # 1) skús __NEXT_DATA__
    nd = soup.find("script", id="__NEXT_DATA__")
    if nd and nd.string:
        try:
            data = json.loads(nd.string)
            out += _walk_for_listings(data)
        except Exception as e:
            print(f"   ⚠ nehnutelnosti __NEXT_DATA__: {e}")

    # 2) skús JSON-LD (zoznam produktov / RealEstateListing)
    for s in soup.find_all("script", type="application/ld+json"):
        if not s.string:
            continue
        try:
            data = json.loads(s.string)
        except Exception:
            continue
        items = data if isinstance(data, list) else [data]
        for it in items:
            if not isinstance(it, dict):
                continue
            if it.get("@type") in ("Product", "RealEstateListing", "Offer", "Apartment"):
                title = it.get("name", "")
                link = it.get("url", url)
                offers = it.get("offers", {}) or {}
                price = offers.get("price") if isinstance(offers, dict) else None
                img = it.get("image", "")
                if isinstance(img, list):
                    img = img[0] if img else ""
                lid = re.sub(r"\D", "", str(link))[-12:] or title[:30]
                out.append(make_listing(
                    "nehnutelnosti", lid, title, link,
                    str(price or ""), config.LOKALITA, img,
                    it.get("description", ""),
                ))
    return out


def _walk_for_listings(obj, depth=0):
    """Defenzívne prejde JSON a vytiahne, čo vyzerá ako inzeráty (title+url+price)."""
    found = []
    if depth > 8:
        return found
    if isinstance(obj, dict):
        keys = set(obj.keys())
        has_title = bool(keys & {"title", "name", "heading"})
        has_url = bool(keys & {"url", "slug", "link", "uri"})
        if has_title and has_url:
            title = obj.get("title") or obj.get("name") or obj.get("heading") or ""
            link = obj.get("url") or obj.get("link") or obj.get("uri") or obj.get("slug") or ""
            if link and not str(link).startswith("http"):
                link = urllib.parse.urljoin("https://www.nehnutelnosti.sk/", str(link))
            price = obj.get("price") or obj.get("priceValue") or ""
            img = obj.get("image") or obj.get("photo") or obj.get("thumbnail") or ""
            if isinstance(img, list):
                img = img[0] if img else ""
            if isinstance(img, dict):
                img = img.get("url") or img.get("src") or ""
            lid = str(obj.get("id") or re.sub(r"\D", "", str(link))[-12:] or title[:30])
            if title and link:
                found.append(make_listing(
                    "nehnutelnosti", lid, str(title), str(link),
                    str(price), config.LOKALITA, str(img),
                    str(obj.get("description", "")),
                ))
        for v in obj.values():
            found += _walk_for_listings(v, depth + 1)
    elif isinstance(obj, list):
        for v in obj:
            found += _walk_for_listings(v, depth + 1)
    return found


# ── Portál: TopReality.sk ───────────────────────────────────────────────────
def scrape_topreality():
    """Best-effort parser. Po prvom ostrom behu doladíme podľa reálneho HTML."""
    out = []
    url = (
        "https://www.topreality.sk/vyhladavanie?"
        f"form%5Bfulltext%5D={urllib.parse.quote(config.LOKALITA)}"
        f"&form%5Bprice_to%5D={config.CENA_MAX}&form%5Btype%5D=1"
    )
    htmltext = fetch(url)
    if not htmltext:
        return out
    soup = BeautifulSoup(htmltext, "html.parser")
    for s in soup.find_all("script", type="application/ld+json"):
        if not s.string:
            continue
        try:
            data = json.loads(s.string)
        except Exception:
            continue
        items = data if isinstance(data, list) else [data]
        for it in items:
            if isinstance(it, dict) and it.get("@type") in ("Product", "Offer", "RealEstateListing"):
                title = it.get("name", "")
                link = it.get("url", url)
                offers = it.get("offers", {}) or {}
                price = offers.get("price") if isinstance(offers, dict) else None
                img = it.get("image", "")
                if isinstance(img, list):
                    img = img[0] if img else ""
                lid = re.sub(r"\D", "", str(link))[-12:] or title[:30]
                out.append(make_listing(
                    "topreality", lid, title, link,
                    str(price or ""), config.LOKALITA, img,
                    it.get("description", ""),
                ))
    return out


PORTAL_FUNKCIE = {
    "bazos": scrape_bazos,
    "nehnutelnosti": scrape_nehnutelnosti,
    "topreality": scrape_topreality,
}


# ── Stav (čo sme už videli) ─────────────────────────────────────────────────
def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── Generovanie stránky ─────────────────────────────────────────────────────
COND_LABEL = {
    "povodny": ("Pôvodný stav", "#16a34a"),
    "neznamy": ("Stav neuvedený", "#6b7280"),
    "rekonstruovany": ("Zrekonštruovaný", "#9333ea"),
    "novostavba": ("Novostavba", "#2563eb"),
}
PORTAL_LABEL = {
    "bazos": "Bazoš",
    "nehnutelnosti": "Nehnuteľnosti.sk",
    "topreality": "TopReality.sk",
}


def card_html(it, is_new):
    cond_text, cond_color = COND_LABEL.get(it["condition"], COND_LABEL["neznamy"])
    price = f"{it['price']:,} €".replace(",", " ") if it["price"] else it["price_text"]
    badge_new = '<span class="badge new">NOVÉ</span>' if is_new else ""
    img = it["image"] or ""
    img_html = (
        f'<img src="{html.escape(img)}" loading="lazy" alt="">'
        if img else '<div class="noimg">bez fotky</div>'
    )
    return f"""
    <a class="card{' is-new' if is_new else ''}" href="{html.escape(it['url'])}" target="_blank" rel="noopener">
      <div class="thumb">{img_html}{badge_new}</div>
      <div class="body">
        <div class="price">{html.escape(str(price))}</div>
        <div class="title">{html.escape(it['title'])}</div>
        <div class="loc">{html.escape(it['location'])}</div>
        <div class="tags">
          <span class="tag" style="background:{cond_color}">{cond_text}</span>
          <span class="tag portal">{PORTAL_LABEL.get(it['portal'], it['portal'])}</span>
        </div>
      </div>
    </a>"""


def build_html(listings, new_ids, stats):
    cards = "\n".join(card_html(it, it["id"] in new_ids) for it in listings)
    updated = datetime.datetime.now(datetime.timezone.utc).strftime("%d.%m.%Y %H:%M UTC")
    stats_html = " · ".join(
        f"{PORTAL_LABEL.get(k, k)}: {v}" for k, v in stats.items()
    )
    return f"""<!doctype html>
<html lang="sk">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Realitný bot — byty Bratislava do {config.CENA_MAX:,} €</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{ font-family: -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin:0;
         background:#0f172a; color:#e2e8f0; }}
  header {{ padding:20px; background:#1e293b; position:sticky; top:0; z-index:5;
           box-shadow:0 2px 10px rgba(0,0,0,.3); }}
  h1 {{ margin:0 0 4px; font-size:20px; }}
  .meta {{ color:#94a3b8; font-size:13px; }}
  .grid {{ display:grid; gap:14px; padding:18px;
          grid-template-columns:repeat(auto-fill,minmax(260px,1fr)); }}
  .card {{ background:#1e293b; border-radius:14px; overflow:hidden; text-decoration:none;
          color:inherit; border:1px solid #334155; transition:transform .12s, border-color .12s; }}
  .card:hover {{ transform:translateY(-3px); border-color:#64748b; }}
  .card.is-new {{ border-color:#16a34a; box-shadow:0 0 0 1px #16a34a; }}
  .thumb {{ position:relative; aspect-ratio:4/3; background:#0f172a; }}
  .thumb img {{ width:100%; height:100%; object-fit:cover; }}
  .noimg {{ display:flex; align-items:center; justify-content:center; height:100%;
           color:#475569; font-size:13px; }}
  .badge.new {{ position:absolute; top:8px; left:8px; background:#16a34a; color:#fff;
               font-size:11px; font-weight:700; padding:3px 8px; border-radius:20px; }}
  .body {{ padding:12px; }}
  .price {{ font-size:18px; font-weight:800; color:#fff; }}
  .title {{ font-size:14px; margin:4px 0; line-height:1.3; max-height:2.6em; overflow:hidden; }}
  .loc {{ font-size:12px; color:#94a3b8; }}
  .tags {{ display:flex; gap:6px; margin-top:8px; flex-wrap:wrap; }}
  .tag {{ font-size:11px; color:#fff; padding:2px 8px; border-radius:20px; }}
  .tag.portal {{ background:#334155; }}
  .empty {{ padding:40px; text-align:center; color:#94a3b8; }}
</style>
</head>
<body>
<header>
  <h1>🏠 Realitný bot — byty v Bratislave do {config.CENA_MAX:,} €</h1>
  <div class="meta">Aktualizované: {updated} · Nájdených: {len(listings)} · {stats_html}</div>
</header>
{f'<div class="grid">{cards}</div>' if listings else '<div class="empty">Zatiaľ žiadne vyhovujúce inzeráty. Bot kontroluje portály každú hodinu.</div>'}
</body>
</html>"""


# ── E‑mail ──────────────────────────────────────────────────────────────────
def send_email(new_listings):
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASS")
    mail_to = os.environ.get("MAIL_TO") or user
    host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    port = int(os.environ.get("SMTP_PORT", "465"))
    if not (user and password and mail_to):
        print("ℹ E‑mail preskočený (nie sú nastavené SMTP tajomstvá).")
        return
    if not new_listings:
        return
    rows = ""
    for it in new_listings:
        price = f"{it['price']:,} €".replace(",", " ") if it["price"] else it["price_text"]
        cond_text = COND_LABEL.get(it["condition"], COND_LABEL["neznamy"])[0]
        rows += f"""
        <tr>
          <td style="padding:8px;border-bottom:1px solid #eee;font-weight:bold;">{html.escape(str(price))}</td>
          <td style="padding:8px;border-bottom:1px solid #eee;">
            <a href="{html.escape(it['url'])}">{html.escape(it['title'])}</a><br>
            <small style="color:#666;">{html.escape(it['location'])} · {cond_text} · {PORTAL_LABEL.get(it['portal'], it['portal'])}</small>
          </td>
        </tr>"""
    body = f"""<html><body style="font-family:Arial,sans-serif;">
    <h2>🏠 {len(new_listings)} nových bytov v Bratislave</h2>
    <p>Do {config.CENA_MAX:,} € · garsónka / 1‑izbový / 2‑izbový / dvojgarsónka · pôvodný stav</p>
    <table style="border-collapse:collapse;width:100%;">{rows}</table>
    <p style="color:#999;font-size:12px;">Realitný bot · automaticky každú hodinu</p>
    </body></html>"""
    msg = MIMEText(body, "html", "utf-8")
    msg["Subject"] = f"🏠 {len(new_listings)} nových bytov (Bratislava do {config.CENA_MAX//1000}k €)"
    msg["From"] = user
    msg["To"] = mail_to
    try:
        with smtplib.SMTP_SSL(host, port, timeout=30) as s:
            s.login(user, password)
            s.sendmail(user, [mail_to], msg.as_string())
        print(f"✅ E‑mail odoslaný na {mail_to} ({len(new_listings)} nových).")
    except Exception as e:
        print(f"⚠ E‑mail zlyhal: {e}")


# ── Hlavný beh ──────────────────────────────────────────────────────────────
def main():
    print("▶ Realitný bot štartuje…")
    seen = load_json(SEEN_FILE, {})
    all_listings = []
    stats = {}

    for key, enabled in config.PORTALY.items():
        if not enabled:
            continue
        print(f"→ Portál: {key}")
        try:
            found = PORTAL_FUNKCIE[key]()
        except Exception as e:
            print(f"   ⚠ {key} zlyhal: {e}")
            found = []
        kept = [it for it in found if keep(it)]
        stats[key] = len(kept)
        print(f"   nájdených {len(found)}, vyhovuje {len(kept)}")
        all_listings += kept

    # odstráň duplikáty (podľa id)
    uniq = {}
    for it in all_listings:
        uniq[it["id"]] = it
    all_listings = list(uniq.values())

    # ktoré sú nové
    new_ids = [i for i in uniq if i not in seen]
    new_listings = [uniq[i] for i in new_ids]

    # zapíš found_at: nové = teraz, staré = pôvodný čas
    for it in all_listings:
        it["found_at"] = seen.get(it["id"], now_iso())
    # zoradenie: najnovšie hore
    all_listings.sort(key=lambda x: x["found_at"], reverse=True)

    print(f"★ Spolu vyhovuje: {len(all_listings)}, z toho NOVÝCH: {len(new_listings)}")

    # ulož stav
    for i in new_ids:
        seen[i] = now_iso()
    save_json(SEEN_FILE, seen)
    save_json(LISTINGS_FILE, all_listings)

    # stránka
    os.makedirs(DOCS_DIR, exist_ok=True)
    with open(DOCS_HTML, "w", encoding="utf-8") as f:
        f.write(build_html(all_listings, set(new_ids), stats))
    print(f"✅ Stránka zapísaná: {DOCS_HTML}")

    # e‑mail (len ak sú nové)
    send_email(new_listings)
    print("✔ Hotovo.")


if __name__ == "__main__":
    main()
