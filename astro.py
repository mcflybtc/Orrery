#!/usr/bin/env python3
"""
Sky-Events CLI – menus numéricos para cidade e corpo celeste
"""

import datetime
import astronomy as astr

# ----------------------------------------------------------
CITIES = {
    1:  ("New York",      40.7128,  -74.0060,  10),
    2:  ("London",        51.5074,   -0.1278,  11),
    3:  ("Paris",         48.8566,    2.3522,  35),
    4:  ("Tokyo",         35.6762,  139.6503,  40),
    5:  ("Los Angeles",   34.0522, -118.2437,  93),
    6:  ("Beijing",       39.9042,  116.4074,  44),
    7:  ("Sydney",       -33.8688,  151.2093,   3),
    8:  ("Moscow",        55.7558,   37.6173, 156),
    9:  ("Berlin",        52.5200,   13.4050,  34),
    10: ("Rome",          41.9028,   12.4964,  21),
    11: ("Mumbai",        19.0760,   72.8777,  14),
    12: ("São Paulo",    -23.5505,  -46.6333, 800),
    13: ("Mexico City",   19.4326,  -99.1332, 2240),
    14: ("Cairo",         30.0444,   31.2357,  23),
    15: ("Bangkok",       13.7563,  100.5018,   2),
    16: ("Seoul",         37.5665,  126.9780,  38),
    17: ("Istanbul",      41.0082,   28.9784,  39),
    18: ("Toronto",       43.6532,  -79.3832,  76),
    19: ("Dubai",         25.2048,   55.2708,   5),
    20: ("Singapore",      1.3521,  103.8198,  15),
}

BODIES = {
    1: ("Sol",           astr.Body.Sun),
    2: ("Lua",           astr.Body.Moon),
    3: ("Mercúrio",      astr.Body.Mercury),
    4: ("Vênus",         astr.Body.Venus),
    5: ("Marte",         astr.Body.Mars),
    6: ("Júpiter",       astr.Body.Jupiter),
    7: ("Saturno",       astr.Body.Saturn),
    8: ("Urano",         astr.Body.Uranus),
    9: ("Netuno",        astr.Body.Neptune),
}
# ----------------------------------------------------------

def local_to_utc(dt_local):
    return astr.Time(dt_local.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))

def utc_to_local(dt_utc):
    return dt_utc.astimezone()

def escolha(dicionario, titulo):
    print(f"\n{titulo}")
    for k, (nome, *_) in dicionario.items():
        print(f"{k:2d} – {nome}")
    while True:
        try:
            n = int(input("  Escolha: "))
            if n in dicionario:
                return dicionario[n]
        except ValueError:
            pass
        print("  Opção inválida!")

def eventos_do_dia(body, observer, date_local):
    start = local_to_utc(datetime.datetime(date_local.year, date_local.month, date_local.day,
                                           0, 0, 0, tzinfo=date_local.tzinfo))

    lon = astr.EclipticLongitude(body, start)
    print(f"\nLongitude eclíptica atual: {lon:.2f}°")

    rise   = astr.SearchHourAngle(body, observer, 0.0, start, +1)
    transit= astr.SearchHourAngle(body, observer, 12.0, start, +1)
    set_   = astr.SearchHourAngle(body, observer, 0.0, start.AddDays(1), -1)

    eventos = [("Nascer", rise), ("Meio do céu", transit), ("Pôr", set_)]

    # Verificar ocultação total
    if transit is None or transit.hor.altitude < 0:
        eventos.append(("Oculto o dia todo", None))

    print("\nEventos (hora civil local):")
    for label, evt in eventos:
        if evt is None:
            print(f"  {label:18s} – não ocorre")
        else:
            lt = utc_to_local(evt.time.Utc())
            print(f"  {label:18s} – {lt.strftime('%H:%M:%S')}")

def main():
    nome, lat, lon, alt = escolha(CITIES, "===== CIDADES =====")
    body_nome, body = escolha(BODIES, "===== CORPOS CELESTES =====")

    today = datetime.datetime.now().astimezone().date()
    date_local = datetime.datetime(today.year, today.month, today.day,
                                   tzinfo=datetime.datetime.now().astimezone().tzinfo)

    observer = astr.Observer(lat, lon, alt)
    print(f"\nObservador: {nome}  ({lat:.3f}°, {lon:.3f}°, {alt} m)")
    print(f"Data local : {date_local.strftime('%Y-%m-%d')}")
    print(f"Corpo      : {body_nome}")

    eventos_do_dia(body, observer, date_local)

if __name__ == "__main__":
    main()