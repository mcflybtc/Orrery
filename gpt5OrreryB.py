#!/usr/bin/env python3
# astro_cli_final.py
# Versão final: Fortaleza adicionada, aspectos, tabelas, menu melhorado, 2 casas decimais.

from datetime import timedelta
from zoneinfo import ZoneInfo
import astronomy
from astronomy import *
import math
import sys

# ---------------- Config ----------------
CITIES = {
    "New York, USA": ((40.7128, -74.0060), "America/New_York"),
    "London, UK": ((51.5074, -0.1278), "Europe/London"),
    "Paris, France": ((48.8566, 2.3522), "Europe/Paris"),
    "Tokyo, Japan": ((35.6895, 139.6917), "Asia/Tokyo"),
    "São Paulo, Brazil": ((-23.5505, -46.6333), "America/Sao_Paulo"),
    "Rio de Janeiro, Brazil": ((-22.9068, -43.1729), "America/Sao_Paulo"),
    "Fortaleza, Brazil": ((-3.71722, -38.5434), "America/Fortaleza"),  # ADICIONADA
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

# Aspectos a calcular (nome: (ângulo exato em graus, default_orbe))
ASPECTS = {
    "Conjunção": (0.0, 6.0),
    "Oposição": (180.0, 8.0),
    "Quadratura": (90.0, 6.0),
    "Trígono": (120.0, 6.0),
    "Sextil": (60.0, 4.0)
}

# ---------------- Helpers ----------------

def clamp(x, a=-1.0, b=1.0):
    return max(a, min(b, x))

def angular_sep_deg_from_ra_dec(ra1_h, dec1_deg, ra2_h, dec2_deg):
    """Separação angular (graus). RA em horas."""
    ra1 = math.radians(ra1_h * 15.0)
    ra2 = math.radians(ra2_h * 15.0)
    dec1 = math.radians(dec1_deg)
    dec2 = math.radians(dec2_deg)
    cosval = math.sin(dec1)*math.sin(dec2) + math.cos(dec1)*math.cos(dec2)*math.cos(ra1 - ra2)
    cosval = clamp(cosval, -1.0, 1.0)
    return math.degrees(math.acos(cosval))

def fmt_num(x, nd=2):
    if x is None:
        return "—"
    if isinstance(x, float):
        return f"{x:.{nd}f}"
    return str(x)

def to_local(t, tz):
    """Converte astronomy.Time ou datetime -> datetime local (zoneinfo)."""
    if t is None:
        return None
    if isinstance(t, Time):
        try:
            dt = t.Utc()   # datetime with tzinfo=UTC
        except Exception:
            # fallback to build from Calendar()
            y, m, d, hh, mm, ss = t.Calendar()
            dt = __import__('datetime').datetime(y, m, d, hh, mm, int(ss), tzinfo=__import__('datetime').timezone.utc)
    else:
        dt = t
    try:
        return dt.astimezone(ZoneInfo(tz))
    except Exception:
        return dt

def fmt_dt(dt):
    if dt is None:
        return "—"
    return dt.strftime("%Y-%m-%d %H:%M:%S %Z")

# ---------------- Astrological helpers ----------------

def signo_tropical(lon):
    idx = int((lon % 360) // 30)
    deg_into = (lon % 30)
    return SIGNS[idx], deg_into

def ayanamsha_lahiri(jd):
    t = (jd - 2451545.0) / 36525.0
    return 22.460148 + 1.396042*t + 3.08e-4*t*t

def signo_sideral(lon, jd):
    ayan = ayanamsha_lahiri(jd)
    lon_sid = (lon - ayan) % 360
    idx = int(lon_sid // 30)
    deg_into = lon_sid - idx*30
    return SIGNS[idx], deg_into

# ---------------- Occultation scanning (minute-scan) ----------------

def scan_occultation_between(bodyA, bodyB, obs, step_minutes=1, threshold_deg=0.25):
    events = []
    t0 = Time.Now()
    t = t0
    end_time = t0.AddDays(1.0)
    inside = False
    start_t = None
    min_dist = 999.0
    min_t = None
    step = step_minutes / (24.0 * 60.0)  # days

    while t.ut <= end_time.ut:
        try:
            eqA = Equator(bodyA, t, obs, True, True)
            eqB = Equator(bodyB, t, obs, True, True)
            dist = angular_sep_deg_from_ra_dec(eqA.ra, eqA.dec, eqB.ra, eqB.dec)
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
                dist = angular_sep_deg_from_ra_dec(moon_eq.ra, moon_eq.dec, ra_h, dec_deg)
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
    # longitude eclíptica geocêntrica
    try:
        gv = GeoVector(body, now, True)
        ecl = Ecliptic(gv)
        lon = ecl.elon % 360.0
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
                eclipses['Obscuration'] = getattr(ecl, 'obscuration', None)
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

# ---------------- Aspect calculation ----------------

def angle_diff(a, b):
    """diferença angular mínima entre a e b (graus)"""
    d = abs((a - b + 180) % 360 - 180)
    return d

def find_aspects(longitudes, orb_overrides=None):
    """
    longitudes: dict name->longitude (deg)
    orb_overrides: dict aspect_name->orb (deg) to override defaults
    retorna: lista de (bodyA, bodyB, aspect_name, exact_angle, diff, orb)
    """
    aspects_found = []
    orb_overrides = orb_overrides or {}
    names = list(longitudes.keys())
    for i in range(len(names)):
        for j in range(i+1, len(names)):
            a = names[i]
            b = names[j]
            la = longitudes[a]
            lb = longitudes[b]
            if la is None or lb is None:
                continue
            sep = angle_diff(la, lb)  # 0..180
            for asp_name, (asp_angle, default_orb) in ASPECTS.items():
                orb = orb_overrides.get(asp_name, default_orb)
                # compare sep to asp_angle or to 360-asp_angle (but angle_diff handles symmetrical)
                diff = abs(sep - asp_angle)
                if diff <= orb:
                    aspects_found.append({
                        "A": a, "B": b,
                        "Aspect": asp_name,
                        "ExactAngle": asp_angle,
                        "Separation": sep,
                        "Diff": diff,
                        "Orb": orb
                    })
    return aspects_found

# ---------------- Printing & Menus ----------------

def print_table_lines(rows, headers, colwidths=None):
    if colwidths is None:
        colwidths = [max(len(h), *(len(str(r[i])) for r in rows)) + 2 for i,h in enumerate(headers)]
    # header
    line = " | ".join(h.ljust(colwidths[i]) for i,h in enumerate(headers))
    sep = "-+-".join("-"*colwidths[i] for i in range(len(headers)))
    print(line)
    print(sep)
    for r in rows:
        print(" | ".join(str(r[i]).ljust(colwidths[i]) for i in range(len(headers))))

def print_body_table(name, info, tz):
    # Body summary table (single)
    rows = [
        ["Nome", name],
        ["Longitude (°)", fmt_num(info.get('Longitude'),2)],
        ["Signo (tropical)", f"{info.get('Signo Tropical')[0]} {fmt_num(info.get('Signo Tropical')[1],2)}°" if info.get('Signo Tropical')[0] else "—"],
        ["Signo (sideral)", f"{info.get('Signo Sideral')[0]} {fmt_num(info.get('Signo Sideral')[1],2)}°" if info.get('Signo Sideral')[0] else "—"],
        ["RA (h)", fmt_num(info.get('RA'),3)],
        ["Dec (°)", fmt_num(info.get('Dec'),2)],
        ["Azimute (°)", fmt_num(info.get('Azimute'),2)],
        ["Altitude (°)", fmt_num(info.get('Altitude'),2)],
        ["Visível agora", "Sim" if (info.get('Altitude') is not None and info.get('Altitude')>0) else "Não"],
        ["Nascer (local)", fmt_dt(to_local(info.get('Rise'), tz))],
        ["Trânsito (local)", fmt_dt(to_local(info.get('Transit'), tz)),],
        ["Alt no trânsito (°)", fmt_num(info.get('TransitAlt'),2)],
        ["Pôr (local)", fmt_dt(to_local(info.get('Set'), tz))]
    ]
    colwidths = [18, 40]
    print("\n" + "="*60)
    for r in rows:
        print(f"{r[0].ljust(colwidths[0])} : {r[1]}")
    print("="*60)

    # Eclipses
    if info.get('Eclipse'):
        print("\nEclipse (se aplicável):")
        for k,v in info['Eclipse'].items():
            if isinstance(v, Time):
                print(f"  {k}: {fmt_dt(to_local(v, tz))}")
            else:
                print(f"  {k}: {v}")

    # Occultations
    occ = info.get('Occultations', [])
    if occ:
        print("\nOcultações nas próximas 24h:")
        rows = []
        for ev in occ:
            rows.append([
                ev['tipo'],
                fmt_dt(to_local(ev['start'], tz)),
                fmt_dt(to_local(ev['peak'], tz)),
                fmt_dt(to_local(ev['end'], tz)),
                f"{ev.get('min_dist_deg', 0):.3f}°"
            ])
        headers = ["Evento","Início","Pico","Fim","Distância"]
        print_table_lines(rows, headers)

def print_aspect_table(aspects):
    if not aspects:
        print("\nNenhum aspecto significativo encontrado entre os astros selecionados (dentro dos orbes).")
        return
    rows = []
    for a in aspects:
        rows.append([
            f"{a['A']} — {a['B']}",
            a['Aspect'],
            f"{a['Separation']:.2f}°",
            f"{a['Diff']:.2f}°",
            f"{a['Orb']:.2f}°"
        ])
    headers = ["Par", "Aspecto", "Separação", "Diferença", "Orbe"]
    print("\nAspectos encontrados:")
    print_table_lines(rows, headers)

# ---------------- Menus ----------------

def choose_city_menu():
    keys = list(CITIES.keys())
    while True:
        print("\nEscolha a cidade (número) ou 0 para menu principal:")
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
    current_city = None
    current_ctx = None
    while True:
        print("\n=== ASTRONOMY CLI — MENU PRINCIPAL ===")
        print("1) Selecionar cidade")
        print("2) Selecionar astros e calcular")
        print("3) Mostrar cidade atual")
        print("4) Sair")
        opt = input("Opção: ").strip()
        if opt == '1':
            city, ctx = choose_city_menu()
            if city is None:
                continue
            current_city = city
            current_ctx = ctx
            print(f"Selecionada: {current_city}")
        elif opt == '2':
            if current_city is None:
                print("Primeiro selecione uma cidade (opção 1).")
                continue
            obs, tz = current_ctx
            chosen = choose_bodies_menu()
            if chosen is None:
                continue
            # compute info for each chosen
            longitudes = {}
            infos = {}
            print("\nCalculando... isso pode demorar um pouco se houver varredura de ocultações.")
            for name in chosen:
                try:
                    info = compute_body_info(BODIES[name], obs, tz)
                    infos[name] = info
                    longitudes[name] = info.get('Longitude')
                except Exception as e:
                    print(f"Erro ao calcular {name}: {e}")
                    infos[name] = {}
                    longitudes[name] = None
            # print per-body tables
            for name in chosen:
                print_body_table(name, infos[name], tz)
            # aspects between chosen
            aspects = find_aspects(longitudes)
            print_aspect_table(aspects)
            # after showing, menu choices
            while True:
                print("\nO que quer fazer agora?")
                print("1) Voltar ao menu principal")
                print("2) Selecionar outra cidade")
                print("3) Selecionar outros astros (mesma cidade)")
                print("4) Sair")
                cmd = input("Opção: ").strip()
                if cmd == '1':
                    break  # volta ao menu principal
                elif cmd == '2':
                    # troca cidade e retorna ao menu principal para escolher astros
                    city, ctx = choose_city_menu()
                    if city:
                        current_city = city
                        current_ctx = ctx
                        print(f"Troquei para: {current_city}")
                        break
                    else:
                        continue
                elif cmd == '3':
                    # vai direto para escolher astros novamente (mesma cidade)
                    break_flag = False
                    chosen = choose_bodies_menu()
                    if chosen is None:
                        continue
                    longitudes = {}
                    infos = {}
                    print("\nCalculando (segunda rodada)...")
                    for name in chosen:
                        try:
                            info = compute_body_info(BODIES[name], obs, tz)
                            infos[name] = info
                            longitudes[name] = info.get('Longitude')
                        except Exception as e:
                            print(f"Erro ao calcular {name}: {e}")
                            infos[name] = {}
                            longitudes[name] = None
                    for name in chosen:
                        print_body_table(name, infos[name], tz)
                    aspects = find_aspects(longitudes)
                    print_aspect_table(aspects)
                    continue  # ainda no submenu pós-cálculo
                elif cmd == '4':
                    print("Saindo...")
                    sys.exit(0)
                else:
                    print("Opção inválida.")
        elif opt == '3':
            if current_city:
                print(f"Cidade atual: {current_city}")
            else:
                print("Nenhuma cidade selecionada.")
        elif opt == '4':
            print("Tchau — fechando.")
            break
        else:
            print("Opção inválida. Escolha 1,2,3 ou 4.")

if __name__ == '__main__':
    main_menu()
