# -*- coding: utf-8 -*-
"""
Nastavenia vyhľadávania pre realitného bota.
Toto je jediný súbor, ktorý bežne treba upravovať, keď chceš zmeniť kritériá.
"""

# Mesto / lokalita. OKRUH_KM = 0 znamená LEN Bratislava, žiadne okolité mestá
# (Pezinok, Senec, Modra a pod. sa do výsledkov nedostanú).
LOKALITA = "Bratislava"
OKRUH_KM = 0

# Poistka navyše: lokalita inzerátu musí obsahovať jedno z týchto slov,
# inak sa vyhodí (aj keby ho portál omylom vrátil mimo Bratislavy).
LOKALITA_POVOLENA = ["bratislava"]

# Cenový STROP zberu v eurách (drahšie sa vôbec nesťahuje).
# Dávame trochu navrch (250k), aby mal cenový slider na stránke priestor hore.
CENA_MAX = 250000
# Spodná hranica zberu (0 = bez spodnej hranice)
CENA_MIN = 0

# Cenový slider na stránke — predvolené nastavenie posuvníkov.
SLIDER_MIN = 0
SLIDER_DEFAULT_MAX = 200000

# E‑mail posiela len NOVÉ byty do tejto ceny (aby ti nechodili drahšie).
EMAIL_MAX = 200000

# Aké typy bytov hľadáme. Bot hľadá tieto kľúčové slová v nadpise + popise.
# garsónka, 1-izbový, 2-izbový, dvojgarsónka
TYPY_REGEX = [
    r"garz[oó]nk",          # garsónka / garzónka / garsonka
    r"garson",              # garsonka bez diakritiky
    r"dvojgarz[oó]nk",      # dvojgarsónka
    r"dvojgarson",
    r"1[\s\-]?izb",         # 1-izbový, 1 izbový, 1izb
    r"jednoizb",            # jednoizbový
    r"2[\s\-]?izb",         # 2-izbový
    r"dvojizb",             # dvojizbový
]

# Stav bytu: chceme PÔVODNÝ STAV (na rekonštrukciu), NIE novostavby a NIE
# kompletne zrekonštruované.
# Ak nastavíš na False, stav sa nefiltruje vôbec (uvidíš všetko).
FILTROVAT_STAV = True

# Režim filtrovania stavu:
#   "rozumny" = vyhodí jasné novostavby/rekonštrukcie, zvyšok (neznámy stav) necháva
#   "prisny"  = nechá LEN byty, čo výslovne spomínajú pôvodný stav / na rekonštrukciu
#               (najčistejšie, ale uvidíš menej ponúk)
STAV_MODE = "rozumny"

# Frázy, ktoré znamenajú "už hotové / nové / developerské" -> takéto byty vyhodíme.
# (text sa porovnáva bez diakritiky a malými písmenami)
STAV_VYLUCIT = [
    r"novostavb",
    r"komplet\w*\s+rekon",
    r"komplet\w*\s+zrekon",
    r"po\s+rekon",
    r"po\s+komplet",
    r"(?<!ne)zrekon[sš]truovan",   # zrekonštruovaný (ale NIE „nezrekonštruovaný")
    r"(?<!ne)prerob[ei]",          # prerobený (ale NIE „neprerobený" = pôvodný)
    r"novy\s+byt",
    r"nove\s+byt",
    r"nov[yý]\s+projekt",
    r"nov[yaeý]\s+styl",           # "nový štýlový"
    r"nov[ae]\s+vystavb",
    r"rezidencn",                  # rezidenčný projekt
    r"rezidenci",
    r"developer",
    r"komunitn\w*\s+byvani",       # "komunitné bývanie"
    r"kolaudac",
    r"skolaudovan",
    r"holobyt",                    # holobyt = nový, neobývaný
    r"v\s+cene\s+standard",
]

# Frázy, ktoré potvrdzujú "pôvodný stav" -> takéto byty zvýhodníme/označíme
STAV_POVODNY = [
    r"p[oô]vodn[yý]\s+stav",
    r"pred\s+rekon",
    r"na\s+rekon",
    r"p[oô]vodn[yý]",
]

# Koľko strán z každého portálu prejsť (1 strana = najnovšie inzeráty).
# Pre hodinového bota stačí málo strán — nové pribúdajú navrchu.
MAX_STRAN = 3

# Ktoré portály sú zapnuté
PORTALY = {
    "bazos": True,
    "nehnutelnosti": True,
    "reality": True,
    "topreality": False,   # zatiaľ vypnuté (treba doladiť správnu adresu)
}
