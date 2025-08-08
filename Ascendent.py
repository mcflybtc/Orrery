from datetime import timedelta
from zoneinfo import ZoneInfo
import astronomy
from astronomy import *

# ===================== CONFIGURAÇÃO =====================

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

# 20 estrelas brilhantes (nome, RA_horas, Dec_graus, magnitude)
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

# ===================== FUNÇÕES =====================

def signo_tropical(lon):
    idx = int(lon // 30)
    return SIGNS[idx], lon - idx*30

def ayanamsha_lahiri(jd):
    t = (jd - 2451545.0) / 36525.0
    return 22.460148 + 1.396042*t + 3.08e-4*t*t

def signo_sideral(lon, jd):
    ayan = ayanamsha_lahiri(jd)
    lon_sid = (lon - ayan) % 360
    idx = int(lon_sid // 30)
    return SIGNS[idx], lon_sid - idx*30

def local_time(t, tz):
    if t is None:
        return None
    return t.ToDatetime().replace(tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo(tz))

def angular_distance(ra1, dec1, ra2, dec2):
    from math import radians, degrees, cos, sin, acos
    ra1r, dec1r, ra2r, dec2r = map(radians, [ra1*15, dec1, ra2*15, dec2])
    return degrees(acos(sin(dec1r)*sin(dec2r) + cos(dec1r)*cos(dec2r)*cos(ra1r - ra2r)))

def ocultacoes_estrelas(obs, tz):
    eventos = []
    t0 = Time.Now()
    step = 1.0/1440.0  # 1 min
    for star_name, ra, dec in STARS:
        t = t0
        while t.ut <= t0.ut + 1.0:  # até 24h
            moon_eq = Equator(Body.Moon, t, obs, True, True)
            dist = angular_distance(moon_eq.ra, moon_eq.dec, ra, dec)
            if dist <= 0.25:
                eventos.append({
                    "Estrela": star_name,
                    "Hora": local_time(t, tz),
                    "Distância°": dist
                })
                break
            t = Time(t.ut + step)
    return eventos

def check_ocultacoes_planetas(body, obs, tz):
    eventos = []
    t0 = Time.Now()
    if body == Body.Moon:
        for target in [Body.Mercury, Body.Venus, Body.Mars, Body.Jupiter, Body.Saturn]:
            trans = SearchTransit(body, target, obs, t0, 1.0)
            if trans:
                eventos.append({
                    "Tipo": f"Lua oculta {target.name}",
                    "Início": local_time(trans.start, tz),
                    "Pico": local_time(trans.peak, tz),
                    "Fim": local_time(trans.finish, tz)
                })
    else:
        trans = SearchTransit(Body.Moon, body, obs, t0, 1.0)
        if trans:
            eventos.append({
                "Tipo": f"{body.name} ocultado pela Lua",
                "Início": local_time(trans.start, tz),
                "Pico": local_time(trans.peak, tz),
                "Fim": local_time(trans.finish, tz)
            })
    return eventos

def compute_body_info(body, obs, tz):
    t0 = Time.Now()
    gv = GeoVector(body, t0, True)
    ecl = Ecliptic(gv)
    lon = ecl.elon
    jd = t0.tt

    sig_trop, deg_trop = signo_tropical(lon)
    sig_sid, deg_sid = signo_sideral(lon, jd)

    eq = Equator(body, t0, obs, True, True)
    hor = Horizon(t0, obs, eq.ra, eq.dec, Refraction.Normal)

    rise = SearchRiseSet(body, obs, Direction.Rise, t0, 1.0)
    sett = SearchRiseSet(body, obs, Direction.Set, t0, 1.0)
    transit = SearchHourAngle(body, obs, 0.0, t0, +1)
    transit_alt = transit.hor.altitude if transit else None

    eclipse_info = {}
    if body == Body.Sun:
        eclp = SearchLocalSolarEclipse(t0, obs)
        if eclp:
            eclipse_info = {
                "Tipo": eclp.kind,
                "Início Parcial": local_time(eclp.partial_begin.time, tz),
                "Pico": local_time(eclp.peak.time, tz),
                "Fim Parcial": local_time(eclp.partial_end.time, tz)
            }
    elif body == Body.Moon:
        eclp = SearchLunarEclipse(t0)
        if eclp:
            eclipse_info = {
                "Tipo": eclp.kind,
                "Pico": local_time(eclp.peak, tz)
            }

    ocultacoes = check_ocultacoes_planetas(body, obs, tz)
    if body == Body.Moon:
        ocultacoes += [{"Tipo": f"Lua oculta {ev['Estrela']}", "Hora": ev["Hora"], "Distância°": ev["Distância°"]} for ev in ocultacoes_estrelas(obs, tz)]

    return {
        "Longitude": lon,
        "Signo Tropical": (sig_trop, deg_trop),
        "Signo Sideral": (sig_sid, deg_sid),
        "RA": eq.ra,
        "Dec": eq.dec,
        "Azimute": hor.azimuth,
        "Altitude": hor.altitude,
        "Visível": hor.altitude > 0,
        "Nascer": local_time(rise, tz),
        "Trânsito": local_time(transit.time, tz) if transit else None,
        "Alt. no Trânsito": transit_alt,
        "Pôr": local_time(sett, tz),
        "Eclipse": eclipse_info,
        "Ocultações": ocultacoes
    }

def print_info(name, info):
    print(f"\n=== {name} ===")
    print(f"Longitude eclíptica: {info['Longitude']:.3f}°")
    print(f"Signo Tropical: {info['Signo Tropical'][0]} {info['Signo Tropical'][1]:.2f}°")
    print(f"Signo Sideral: {info['Signo Sideral'][0]} {info['Signo Sideral'][1]:.2f}°")
    print(f"RA: {info['RA']:.3f} h | Dec: {info['Dec']:.3f}°")
    print(f"Azimute: {info['Azimute']:.2f}° | Altitude: {info['Altitude']:.2f}°")
    print(f"Visível agora? {'Sim' if info['Visível'] else 'Não'}")
    print(f"Nascer: {info['Nascer']}")
    print(f"Trânsito: {info['Trânsito']} (Alt: {info['Alt. no Trânsito']})")
    print(f"Pôr: {info['Pôr']}")
    if info['Eclipse']:
        print("Eclipse detectado:")
        for k,v in info['Eclipse'].items():
            print(f"  {k}: {v}")
    if info['Ocultações']:
        print("Ocultações próximas:")
        for ev in info['Ocultações']:
            detalhes = " | ".join([f"{k}: {v}" for k,v in ev.items()])
            print(f"  {detalhes}")

def menu():
    while True:
        print("\n--- Escolha a cidade ---")
        keys = list(CITIES.keys())
        for i,k in enumerate(keys, 1):
            print(f"{i}. {k}")
        choice = input("Cidade: ")
        if not choice.isdigit():
            break
        city = keys[int(choice)-1]
        coords, tz = CITIES[city]
        obs = Observer(coords[0], coords[1], 0.0)
        bodies = input("Astros (nomes separados por vírgula ou 'all'): ")
        if bodies.lower() == 'all':
            chosen = BODIES.keys()
        else:
            chosen = [b.strip() for b in bodies.split(',') if b.strip() in BODIES]
        for name in chosen:
            info = compute_body_info(BODIES[name], obs, tz)
            print_info(name, info)

if __name__ == "__main__":
    menu()
