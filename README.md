# 🏠 Realitný bot

Automatický vyhľadávač bytov na kúpu. Každú hodinu prejde inzertné portály,
nájde nové byty podľa zadaných kritérií a pošle ti ich na e‑mail + zobrazí na stránke.

**Toto je samostatný projekt — s appkou Tower Finance nemá nič spoločné.**

## Čo bot hľadá (predvolené)
- **Lokalita:** Bratislava + okolie 25 km
- **Cena:** do 200 000 €
- **Typy:** garsónka, 1‑izbový, 2‑izbový, dvojgarsónka
- **Stav:** pôvodný stav / na rekonštrukciu (vyhadzuje novostavby a kompletne zrekonštruované)

Kritériá sa menia v súbore [`config.py`](config.py).

## Portály
- **Bazoš** (reality.bazos.sk) — hlavný, najstabilnejší
- **Nehnuteľnosti.sk** — best‑effort
- **TopReality.sk** — best‑effort
- Facebook zatiaľ nie je zapnutý (krehké, rieši sa neskôr).

## Ako to funguje
1. GitHub Actions spustí `scraper.py` každú hodinu (záložka **Actions**).
2. Bot pozbiera inzeráty, odfiltruje duplikáty a už videné.
3. Nové uloží do `data/`, vygeneruje stránku `docs/index.html`.
4. Ak sú nastavené e‑mailové tajomstvá, pošle e‑mail s novými ponukami.

## Nastavenie e‑mailu (voliteľné)
V **Settings → Secrets and variables → Actions** pridaj:
- `SMTP_USER` — tvoja Gmail adresa
- `SMTP_PASS` — Gmail **App Password** (nie bežné heslo)
- `MAIL_TO` — kam posielať (môže byť rovnaká adresa)

## Stránka s výsledkami
Zapni **Settings → Pages → Deploy from a branch → `main` / `docs`**.
Výsledky budú na `https://<tvoj-ucet>.github.io/realitny-bot/`.
