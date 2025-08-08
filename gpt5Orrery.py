#!/usr/bin/env python3
# astro_cli_fixed.py
# Conserto e menu numérico + ocultações Linha-a-linha (minute-scan)

from datetime import timedelta
from zoneinfo import ZoneInfo
import astronomy
from astronomy import *
import math
import csv

# ---------------- Config ----------------
CITIES = {
    "New York, USA": ((40.7128, -74.0060), "America/New_York"),
    "London, UK": ((51.5074, -0.1278), "Europe/London"),
    "Paris, France": ((48.8566, 2.3522), "Europe/Paris"),
    "Tokyo, Japan": ((35.6895, 139.6917), "Asia/Tokyo"),
    "São Paulo, Brazil": ((-23.5505, -46.6333), "America/Sao_Paulo"),
    "Rio de Janeiro, Brazil": ((-22.9068, -43.1729), "America/Sao_Paulo"),
    "Beijing, China": ((39.9042, 116.4074), "Asia/Shanghai"),
    "Moscow, Russia": ((55.7558, 37.6176), "Europe/Moscow"),
    "Los Angeles, USA": ((34.0522, -118.2437), "America/Los_Angeles"),
    "Mexico City, Mexico": ((19.4326, -99.1332), "America/Mexico_City"),
    "Cairo, Egypt": ((30.0444, 31.2357), "Africa/Cairo"),
    "Istanbul, Turkey": ((41.0082, 28.9784), "Europe/Istanbul"),
    "Mumbai, India": ((19.0760, 72.8777), "Asia/Kolkata"),
    "Delhi, India": ((28.7041, 77.1025), "Asia/Kolkata"),
    "Berlin, Germany": ((52.5200, 13.4050), "Europe/Berlin"),
    "Rome, Italy": ((41.9028, 12.4964), "Europe/Rome"),
    "Dubai, UAE": ((25.2048, 55.2708), "Asia/Dubai"),
    "Singapore": ((1.3521, 103.8198), "Asia/Singapore"),
    "Sydney, Australia": ((-33.8688, 151.2093), "Australia/Sydney"),
    "Auckland, NZ": ((-36.8485, 174.7633), "Pacific/Auckland"),
    "Cape Town, South Africa": ((-33.9249, 18.4241), "Africa/Johannesburg"),
    "Lagos, Nigeria": ((6.5244, 3.3792), "Africa/Lagos"),
    "Buenos Aires, Argentina": ((-34.6037, -58.3816), "America/Argentina/Buenos_Aires"),
    "Toronto, Canada": ((43.6532, -79.3832), "America/Toronto"),
    "Seoul, South Korea": ((37.5665, 126.9780), "Asia/Seoul"),
    "Bangkok, Thailand": ((13.7563, 100.5018), "Asia/Bangkok"),
    "Hong Kong": ((22.3193, 114.1694), "Asia/Hong_Kong"),
    "Amsterdam, Netherlands": ((52.3676, 4.9041), "Europe/Amsterdam"),
    "Lisbon, Portugal": ((38.7223, -9.1393), "Europe/Lisbon")
}

BODIES = {
    "Sun": Body.Sun,
    "Moon": Body.Moon,
    "Mercury": Body.Mercury,
    "Venus": Body.Venus,
    "Mars": Body.Mars,
    "Jupiter": Body.Jupiter,
    "Saturn": Body.Saturn,
    "Uranus": Body.Uranus,
    "Neptune": Body.Neptune,
    "Pluto": Body.Pluto
}

SIGNS = [
    "Áries", "Touro", "Gêmeos", "Câncer", "Leão", "Virgem",
    "Libra", "Escorpião", "Sagitário", "Capricórnio", "Aquário", "Peixes"
]

# 20 estrelas mais brilhantes (nome, RA_h, Dec_deg)
STARS = [
    ("Sirius", 6.7525, -16.7161),
    ("Canopus", 6.3992, -52.6957),
    ("Rigil Kentaurus", 14.6601, -60.8356),
    ("Arcturus", 14.2610, 19.1825),
    ("Vega", 18.6156, 38.7837),
    ("Capella", 5.2782, 45.9980),
    ("Rigel", 5.2423, -8.2016),
    ("Procyon", 7.6550, 5.2250),
    ("Achernar", 1.6286, -57.2368),
    ("Betelgeuse", 5.9195, 7.4070),
    ("Hadar", 14.0637, -60.3730),
    ("Altair", 19.8464, 8.8683),
    ("Acrux", 12.4433, -63.0991),
    ("Aldebaran", 4.5987, 16.5093),
    ("Antares", 16.4901, -26.4319),
    ("Spica", 13.4199, -11.1613),
    ("Pollux", 7.7553, 28.0262),
    ("Fomalhaut", 22.9608, -29.6222),
    ("Deneb", 20.6905, 45.2803),
    ("Regulus", 10.1395, 11.9672)
]

# ---------------- Helpers ----------------

def to_local(t, tz):
    """Converte Time -> datetime local (zoneinfo)."""
    if t is None:
        return None
    if isinstance(t, Time):
        try:
            dt = t.Utc()   # astronomy.Time -> datetime with tzinfo=UTC
        except Exception:
            y, m, d, hh, mm, ss = t.Calendar()
            dt = __import__('datetime').datetime(y, m, d, hh, mm, int(ss), tzinfo=__import__('datetime').timezone.utc)
    else:
        dt = t
    try:
        return dt.astimezone(ZoneInfo(tz))
    except Exception:
        return dt

def fmt(dt):
    if dt is None:
        return "—"
    return dt.strftime("%Y-%m-%d %H:%M:%S %Z")

def clamp(x, a=-1.0, b=1.0):
    return max(a, min(b, x))

def angular_sep_deg(ra1_h, dec1_deg, ra2_h, dec2_deg):
    """Separação angular (graus). RA em horas."""
    ra1 = math.radians(ra1_h * 15.0)
    ra2 = math.radians(ra2_h * 15.0)
    dec1 = math.radians(dec1_deg)
    dec2 = math.radians(dec2_deg)
    cosval = math.sin(dec1)*math.sin(dec2) + math.cos(dec1)*math.cos(dec2)*math.cos(ra1 - ra2)
    cosval = clamp(cosval, -1.0, 1.0)
    return math.degrees(math.acos(cosval))

def signo_tropical(lon):
    idx = int((lon % 360) // 30)
    return SIGNS[idx], (lon % 30)

def ayanamsha_lahiri(jd):
    t = (jd - 2451545.0) / 36525.0
    return 22.460148 + 1.396042*t + 3.08e-4*t*t

def signo_sideral(lon, jd):
    ayan = ayanamsha_lahiri(jd)
    lon_sid = (lon - ayan) % 360
    idx = int(lon_sid // 30)
    return SIGNS[idx], lon_sid - idx*30

# ---------------- Occultation scanning (minute-scan) ----------------

def scan_occultation_between(bodyA, bodyB, obs, step_minutes=1, threshold_deg=0.25):
    """Procura nas próximas 24h por intervalos onde separação <= threshold_deg."""
    events = []
    t0 = Time.Now()
    t = t0
    end_time = t0.AddDays(1.0)
    inside = False
    start_t = None
    min_dist = 999.0
    min_t = None
    step = step_minutes / (24.0 * 60.0)  # dias

    while t.ut <= end_time.ut:
        try:
            eqA = Equator(bodyA, t, obs, True, True)
            eqB = Equator(bodyB, t, obs, True, True)
            dist = angular_sep_deg(eqA.ra, eqA.dec, eqB.ra, eqB.dec)
        except Exception:
            t = t.AddDays(step)
            continue

        if dist <= threshold_deg:
            if not inside:
                inside = True
                start_t = t
                min_dist = dist
                min_t = t
            else:
                if dist < min_dist:
                    min_dist = dist
                    min_t = t
        else:
            if inside:
                end_t = t.AddDays(-step)
                events.append({"start": start_t, "peak": min_t, "end": end_t, "min_dist_deg": min_dist})
                inside = False
                start_t = None
                min_dist = 999.0
                min_t = None
        t = t.AddDays(step)

    if inside and start_t is not None:
        events.append({"start": start_t, "peak": min_t, "end": end_time, "min_dist_deg": min_dist})
    return events

def scan_moon_star_occultations(obs, tz, step_minutes=1, threshold_deg=0.25):
    events = []
    t0 = Time.Now()
    end_time = t0.AddDays(1.0)
    step = step_minutes / (24.0*60.0)
    for star_name, ra_h, dec_deg in STARS:
        t = t0
        inside = False
        start_t = None
        min_dist = 999.0
        min_t = None
        while t.ut <= end_time.ut:
            try:
                moon_eq = Equator(Body.Moon, t, obs, True, True)
                dist = angular_sep_deg(moon_eq.ra, moon_eq.dec, ra_h, dec_deg)
            except Exception:
                t = t.AddDays(step)
                continue
            if dist <= threshold_deg:
                if not inside:
                    inside = True
                    start_t = t
                    min_dist = dist
                    min_t = t
                else:
                    if dist < min_dist:
                        min_dist = dist
                        min_t = t
            else:
                if inside:
                    end_t = t.AddDays(-step)
                    events.append({"star": star_name, "start": start_t, "peak": min_t, "end": end_t, "min_dist_deg": min_dist})
                    inside = False
                    start_t = None
                    min_dist = 999.0
                    min_t = None
            t = t.AddDays(step)
        if inside and start_t is not None:
            events.append({"star": star_name, "start": start_t, "peak": min_t, "end": end_time, "min_dist_deg": min_dist})
    return events

# ---------------- Compute main info ----------------

def compute_body_info(body, obs, tz):
    now = Time.Now()
    info = {}
    try:
        gv = GeoVector(body, now, True)
        ecl = Ecliptic(gv)
        lon = ecl.elon
        info['Longitude'] = lon
    except Exception:
        info['Longitude'] = None

    try:
        jd = now.tt
    except Exception:
        jd = None

    if info['Longitude'] is not None and jd is not None:
        info['Signo Tropical'] = signo_tropical(info['Longitude'])
        info['Signo Sideral'] = signo_sideral(info['Longitude'], jd)
    else:
        info['Signo Tropical'] = (None, None)
        info['Signo Sideral'] = (None, None)

    try:
        eq = Equator(body, now, obs, True, True)
        info['RA'] = eq.ra
        info['Dec'] = eq.dec
    except Exception:
        info['RA'] = info['Dec'] = None

    try:
        hor = Horizon(now, obs, info['RA'], info['Dec'], Refraction.Normal)
        info['Azimute'] = hor.azimuth
        info['Altitude'] = hor.altitude
    except Exception:
        info['Azimute'] = info['Altitude'] = None

    # rise / set / transit
    try:
        rise = SearchRiseSet(body, obs, Direction.Rise, now, 1.0)
    except Exception:
        rise = None
    try:
        sett = SearchRiseSet(body, obs, Direction.Set, now, 1.0)
    except Exception:
        sett = None
    try:
        ha_event = SearchHourAngle(body, obs, 0.0, now, +1)
    except Exception:
        ha_event = None

    info['Rise'] = rise
    info['Set'] = sett
    info['Transit'] = ha_event.time if ha_event else None
    info['TransitAlt'] = ha_event.hor.altitude if ha_event else None

    # eclipses
    eclipses = {}
    if body == Body.Sun:
        try:
            ecl = SearchLocalSolarEclipse(now, obs)
            if ecl:
                eclipses['Kind'] = ecl.kind
                eclipses['PartialBegin'] = ecl.partial_begin.time
                eclipses['Peak'] = ecl.peak.time
                eclipses['PartialEnd'] = ecl.partial_end.time
                eclipses['Obscuration'] = ecl.obscuration
        except Exception:
            pass
    if body == Body.Moon:
        try:
            le = SearchLunarEclipse(now)
            if le:
                eclipses['Kind'] = le.kind
                eclipses['Peak'] = le.peak
        except Exception:
            pass
    info['Eclipse'] = eclipses

    # occultations (scan)
    occ = []
    try:
        if body == Body.Moon:
            for target_name, target_body in [('Mercury', Body.Mercury), ('Venus', Body.Venus),
                                             ('Mars', Body.Mars), ('Jupiter', Body.Jupiter), ('Saturn', Body.Saturn)]:
                events = scan_occultation_between(Body.Moon, target_body, obs)
                for ev in events:
                    occ.append({'tipo': f'Lua oculta {target_name}', 'start': ev['start'], 'peak': ev['peak'], 'end': ev['end'], 'min_dist_deg': ev['min_dist_deg']})
            star_events = scan_moon_star_occultations(obs, tz)
            for ev in star_events:
                occ.append({'tipo': f'Lua oculta estrela {ev["star"]}', 'start': ev['start'], 'peak': ev['peak'], 'end': ev['end'], 'min_dist_deg': ev['min_dist_deg']})
        else:
            events = scan_occultation_between(Body.Moon, body, obs)
            for ev in events:
                # find name of body (safe fallback)
                body_name = None
                for k, v in BODIES.items():
                    if v == body:
                        body_name = k
                        break
                body_name = body_name or str(body)
                occ.append({'tipo': f'{body_name} ocultado pela Lua', 'start': ev['start'], 'peak': ev['peak'], 'end': ev['end'], 'min_dist_deg': ev['min_dist_deg']})
    except Exception:
        pass

    info['Occultations'] = occ
    return info

# ---------------- Printing & Menu ----------------

def print_body(name, info, tz):
    print(f"\n--- {name} ---")
    print(f"Longitude eclíptica: {info.get('Longitude')}")
    st = info.get('Signo Tropical', (None,None))
    ss = info.get('Signo Sideral', (None,None))
    print(f"Signo tropical: {st[0]} {st[1]:.2f}°" if st[0] else "Signo tropical: —")
    print(f"Signo sideral: {ss[0]} {ss[1]:.2f}°" if ss[0] else "Signo sideral: —")
    print(f"RA: {info.get('RA')} h | Dec: {info.get('Dec')}°")
    print(f"Azimute: {info.get('Azimute')}° | Altitude: {info.get('Altitude')}°")
    print(f"Visível agora? {'Sim' if (info.get('Altitude') is not None and info.get('Altitude')>0) else 'Não'}")
    print(f"Nascer: {fmt(to_local(info.get('Rise'), tz))}")
    print(f"Trânsito: {fmt(to_local(info.get('Transit'), tz))} (Alt: {info.get('TransitAlt')})")
    print(f"Pôr: {fmt(to_local(info.get('Set'), tz))}")
    if info.get('Eclipse'):
        print("Eclipse:")
        for k,v in info['Eclipse'].items():
            if isinstance(v, Time):
                print(f"  {k}: {fmt(to_local(v, tz))}")
            else:
                print(f"  {k}: {v}")
    if info.get('Occultations'):
        print("Ocultações nas próximas 24h:")
        for ev in info['Occultations']:
            print(f"  {ev['tipo']}:")
            print(f"    Início: {fmt(to_local(ev['start'], tz))}")
            print(f"    Pico:   {fmt(to_local(ev['peak'], tz))} (dist {ev['min_dist_deg']:.3f}°)")
            print(f"    Fim:    {fmt(to_local(ev['end'], tz))}")

def choose_city_menu():
    keys = list(CITIES.keys())
    while True:
        print("\nEscolha a cidade (número) ou 0 para voltar/ sair:")
        for i, cname in enumerate(keys, start=1):
            print(f"{i:2d}. {cname}")
        s = input("Cidade nº: ").strip()
        if s == '0' or s == '':
            return None, None
        if not s.isdigit():
            print("Entrada inválida. Tente de novo.")
            continue
        idx = int(s)-1
        if idx <0 or idx >= len(keys):
            print("Número inválido.")
            continue
        city = keys[idx]
        coords, tz = CITIES[city]
        obs = Observer(coords[0], coords[1], 0.0)
        return city, (obs, tz)

def choose_bodies_menu():
    keys = list(BODIES.keys())
    while True:
        print("\nEscolha astros (números separados por vírgula), 'a'=all, ou 0 para voltar:")
        for i, b in enumerate(keys, start=1):
            print(f"{i:2d}. {b}")
        s = input("Escolha: ").strip().lower()
        if s == '0' or s == '':
            return None
        if s == 'a' or s == 'all':
            return list(BODIES.keys())
        parts = [p.strip() for p in s.split(',') if p.strip()]
        chosen = []
        ok = True
        for p in parts:
            if not p.isdigit():
                ok = False
                break
            ii = int(p)-1
            if ii <0 or ii >= len(keys):
                ok = False
                break
            chosen.append(keys[ii])
        if not ok:
            print("Entrada inválida. Use números separados por vírgula.")
            continue
        return chosen

def main_menu():
    print("Astronomy CLI — menu principal")
    while True:
        print("\n1) Escolher cidade e consultar astros")
        print("2) Listar cidades")
        print("3) Sair")
        cmd = input("Opção: ").strip()
        if cmd == '1':
            city, ctx = choose_city_menu()
            if city is None:
                continue
            obs, tz = ctx
            while True:
                chosen = choose_bodies_menu()
                if chosen is None:
                    break
                for name in chosen:
                    print(f"\nCalculando {name} para {city} — aguarde...")
                    try:
                        info = compute_body_info(BODIES[name], obs, tz)
                        print_body(name, info, tz)
                    except Exception as e:
                        print("Erro calculando:", e)
                input("\nTecle Enter para continuar no menu da cidade...")
        elif cmd == '2':
            print("\nCidades disponíveis:")
            for k in CITIES.keys():
                print(" -", k)
        elif cmd == '3':
            print("Tchau — fechando.")
            break
        else:
            print("Opção inválida. Escolha 1, 2 ou 3.")

if __name__ == '__main__':
    main_menu()
