# -*- coding: utf-8 -*-
"""
Nastavenia vyhľadávania pre realitného bota.
Toto je jediný súbor, ktorý bežne treba upravovať, keď chceš zmeniť kritériá.
"""

# Mesto / lokalita a okruh v km (Bazoš podporuje okruh)
LOKALITA = "Bratislava"
OKRUH_KM = 25

# Cenový strop v eurách (byty drahšie ako toto sa vyhodia)
CENA_MAX = 200000
# Spodná hranica (0 = bez spodnej hranice)
CENA_MIN = 0

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
# kompletne zrekonštruované. Byty bez uvedeného stavu necháme (nech ti nič neujde),
# ale viditeľne ich označíme.
# Ak nastavíš na False, stav sa nefiltruje vôbec (uvidíš všetko).
FILTROVAT_STAV = True

# Frázy, ktoré znamenajú "už hotové / nové" -> takéto byty vyhodíme
STAV_VYLUCIT = [
    r"novostavb",
    r"kompletn[aá]\s+rekon",
    r"kompletne\s+zrekon",
    r"po\s+rekon",
    r"zrekon[sš]truovan",
    r"novy\s+byt",
    r"nov[yý]\s+projekt",
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
    "topreality": True,
}
