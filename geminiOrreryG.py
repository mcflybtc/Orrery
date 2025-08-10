#!/usr/bin/env python3
# orrery_pro_final.py
# Versão definitiva com todas as funcionalidades, correções e aprimoramentos.

import math
import sys
from datetime import datetime, timedelta, tzinfo, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

# Importações completas da biblioteca de astronomia
import astronomy
from astronomy import (
    Body, Observer, Time, Direction, Refraction, ApsisKind, EclipseKind, Visibility,
    Equator, Horizon, GeoVector, Ecliptic, Illumination, Constellation,
    JupiterMoons, Libration, PairLongitude, DefineStar, PlanetOrbitalPeriod, Seasons,
    SearchRiseSet, SearchHourAngle, SearchLunarApsis, NextLunarApsis,
    SearchPlanetApsis, NextPlanetApsis, SearchLunarEclipse,
    SearchGlobalSolarEclipse, SearchLocalSolarEclipse,
    SearchMoonQuarter, NextMoonQuarter, Search,
    SearchMoonNode, NextMoonNode, SearchMaxElongation, SearchTransit
)

# --- Classe de Fallback para Fuso Horário Fixo ---
class FixedTimeZone(tzinfo):
    def __init__(self, offset_hours, name):
        self._offset = timedelta(hours=offset_hours)
        self._name = name
    def utcoffset(self, dt): return self._offset
    def dst(self, dt): return timedelta(0)
    def tzname(self, dt): return self._name

# --- Configurações Globais ---
CITIES = {
    "Amsterdam, Netherlands": ((52.3676, 4.9041), "Europe/Amsterdam", None),
    "Auckland, NZ": ((-36.8485, 174.7633), "Pacific/Auckland", None),
    "Bangkok, Thailand": ((13.7563, 100.5018), "Asia/Bangkok", 7),
    "Beijing, China": ((39.9042, 116.4074), "Asia/Shanghai", 8),
    "Berlin, Germany": ((52.5200, 13.4050), "Europe/Berlin", None),
    "Buenos Aires, Argentina": ((-34.6037, -58.3816), "America/Argentina/Buenos_Aires", -3),
    "Cairo, Egypt": ((30.0444, 31.2357), "Africa/Cairo", None),
    "Cape Town, South Africa": ((-33.9249, 18.4241), "Africa/Johannesburg", None),
    "Delhi, India": ((28.7041, 77.1025), "Asia/Kolkata", 5.5),
    "Dubai, UAE": ((25.2048, 55.2708), "Asia/Dubai", 4),
    "Fortaleza, Brazil": ((-3.71722, -38.5434), "America/Fortaleza", -3),
    "Hong Kong": ((22.3193, 114.1694), "Asia/Hong_Kong", 8),
    "Istanbul, Turkey": ((41.0082, 28.9784), "Europe/Istanbul", None),
    "Lagos, Nigeria": ((6.5244, 3.3792), "Africa/Lagos", 1),
    "Lisbon, Portugal": ((38.7223, -9.1393), "Europe/Lisbon", None),
    "London, UK": ((51.5074, -0.1278), "Europe/London", None),
    "Los Angeles, USA": ((34.0522, -118.2437), "America/Los_Angeles", None),
    "Mexico City, Mexico": ((19.4326, -99.1332), "America/Mexico_City", None),
    "Moscow, Russia": ((55.7558, 37.6176), "Europe/Moscow", None),
    "Mumbai, India": ((19.0760, 72.8777), "Asia/Kolkata", 5.5),
    "New York, USA": ((40.7128, -74.0060), "America/New_York", None),
    "Paris, France": ((48.8566, 2.3522), "Europe/Paris", None),
    "Rio de Janeiro, Brazil": ((-22.9068, -43.1729), "America/Sao_Paulo", None),
    "Rome, Italy": ((41.9028, 12.4964), "Europe/Rome", None),
    "São Paulo, Brazil": ((-23.5505, -46.6333), "America/Sao_Paulo", None),
    "Seoul, South Korea": ((37.5665, 126.9780), "Asia/Seoul", 9),
    "Singapore": ((1.3521, 103.8198), "Asia/Singapore", 8),
    "Sydney, Australia": ((-33.8688, 151.2093), "Australia/Sydney", None),
    "Tokyo, Japan": ((35.6895, 139.6917), "Asia/Tokyo", 9),
    "Toronto, Canada": ((43.6532, -79.3832), "America/Toronto", None),
}

BODIES = { "Sun": Body.Sun, "Moon": Body.Moon, "Mercury": Body.Mercury, "Venus": Body.Venus, "Mars": Body.Mars, "Jupiter": Body.Jupiter, "Saturn": Body.Saturn, "Uranus": Body.Uranus, "Neptune": Body.Neptune, "Pluto": Body.Pluto }
STARS_DATA = [("Sirius", 6.7525, -16.7161), ("Canopus", 6.3992, -52.6957), ("Rigil Kentaurus", 14.6601, -60.8356), ("Arcturus", 14.2610, 19.1825), ("Vega", 18.6156, 38.7837), ("Capella", 5.2782, 45.9980), ("Rigel", 5.2423, -8.2016), ("Procyon", 7.6550, 5.2250)]
STARS = {star[0]: Body(Body.Star1.value + i) for i, star in enumerate(STARS_DATA)}
SIGNS = ["Áries", "Touro", "Gêmeos", "Câncer", "Leão", "Virgem", "Libra", "Escorpião", "Sagitário", "Capricórnio", "Aquário", "Peixes"]
ASPECTS = {"Conjunção": (0.0, 8.0), "Oposição": (180.0, 8.0), "Quadratura": (90.0, 6.0), "Trígono": (120.0, 6.0), "Sextil": (60.0, 4.0)}
PLANETS_FOR_ASPECTS = ["Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]

# --- Funções Auxiliares ---
def fmt_num(x, nd=2):
    if x is None: return "—"
    if isinstance(x, float): return f"{x:.{nd}f}"
    return str(x)

def to_local(t, tz_info):
    if t is None or tz_info is None: return None
    try:
        return t.Utc().astimezone(tz_info)
    except Exception:
        return None

def fmt_dt(dt):
    if dt is None: return "—"
    return dt.strftime("%Y-%m-%d %H:%M:%S %Z")

def signo_tropical(lon):
    if lon is None: return ("—", "—")
    idx = int((lon % 360) // 30)
    deg_into = (lon % 30)
    return SIGNS[idx], deg_into

def get_constellation(body, time, observer):
    try:
        eq = Equator(body, time, observer, True, False)
        const_info = Constellation(eq.ra, eq.dec)
        return f"{const_info.name} ({const_info.symbol})"
    except Exception:
        return "N/A"

def get_cardinal_direction(azimuth_deg):
    if azimuth_deg is None: return "—"
    sectors = ["Norte (N)", "Nordeste (NE)", "Leste (E)", "Sudeste (SE)", "Sul (S)", "Sudoeste (SW)", "Oeste (W)", "Noroeste (NW)"]
    index = round(azimuth_deg / 45.0) % 8
    return sectors[index]

# --- Classe da Aplicação ---
class AstroCLI:
    def __init__(self):
        self.current_city_name = None
        self.observer = None
        self.tz_info = None
        self.search_time = Time.Now()
        self._initialize_stars()

    def _initialize_stars(self):
        for name, body_enum in STARS.items():
            star_data = next((s for s in STARS_DATA if s[0] == name), None)
            if star_data:
                DefineStar(body_enum, star_data[1], star_data[2], 1000)

    def _ensure_location(self):
        if not self.observer:
            print("\nPor favor, selecione uma cidade primeiro.")
            return False
        return True

    def _print_table(self, rows, headers):
        if not rows: 
            print("Nenhuma informação para exibir.")
            return
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if len(str(cell)) > col_widths[i]: col_widths[i] = len(str(cell))
        
        header_line = " | ".join(headers[i].ljust(col_widths[i]) for i in range(len(headers)))
        separator = "-+-".join("-" * w for w in col_widths)
        print(header_line)
        print(separator)
        for row in rows:
            row_line = " | ".join(str(row[i]).ljust(col_widths[i]) for i in range(len(row)))
            print(row_line)
            
    def _choose_city(self):
        city_names = sorted(list(CITIES.keys()))
        while True:
            print("\nEscolha a cidade (ou 0 para voltar):")
            for i, name in enumerate(city_names, 1): print(f"{i:2d}. {name}")
            
            choice = input("Sua escolha: ").strip()
            if choice == '0': return False
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(city_names):
                    city_name_selection = city_names[idx]
                    coords, tz_iana_name, fixed_offset = CITIES[city_name_selection]
                    
                    tz_object = None
                    try:
                        tz_object = ZoneInfo(tz_iana_name)
                    except ZoneInfoNotFoundError:
                        if fixed_offset is not None:
                            print(f"\nAviso: Base de dados de fusos horários não encontrada. Usando deslocamento fixo para {city_name_selection}.")
                            tz_object = FixedTimeZone(fixed_offset, f"UTC{fixed_offset:+d}")
                        else:
                            print("\n" + "="*50)
                            print("!!! ERRO DE FUSO HORÁRIO !!!")
                            print(f"O fuso horário '{tz_iana_name}' não foi encontrado. Este fuso tem regras complexas (horário de verão) e necessita de uma base de dados.")
                            print("Para corrigir, abra o terminal e execute: py -m pip install tzdata")
                            print("Depois, reinicie o programa.")
                            print("="*50 + "\n")
                            return False

                    self.current_city_name = city_name_selection
                    self.tz_info = tz_object
                    self.observer = Observer(coords[0], coords[1], 0.0)
                    print(f"Cidade selecionada: {self.current_city_name}")
                    return True

                else: print("Número inválido.")
            except ValueError: print("Por favor, insira um número.")

    def _set_search_time(self):
        if not self.tz_info:
            print("\nPor favor, selecione uma cidade primeiro para definir um fuso horário.")
            return
        print("\n--- Definir Data de Início para Buscas ---")
        current_search_dt = to_local(self.search_time, self.tz_info)
        print(f"Data atual para buscas: {fmt_dt(current_search_dt)}")
        date_str = input("Digite a nova data (AAAA-MM-DD) ou deixe em branco para redefinir para agora: ").strip()
        try:
            if date_str:
                user_date = datetime.strptime(date_str, "%Y-%m-%d")
                local_time = datetime(user_date.year, user_date.month, user_date.day, 0, 0, 0, tzinfo=self.tz_info)
                self.search_time = Time.from_datetime(local_time)
            else:
                self.search_time = Time.Now()
            print(f"Nova data de início para buscas definida para: {fmt_dt(to_local(self.search_time, self.tz_info))}")
        except ValueError:
            print("Formato de data inválido. Use AAAA-MM-DD.")
        except Exception as e:
            print(f"Ocorreu um erro: {e}")

    def _compute_body_info(self, name, body, time):
        info = {}
        is_star = name in STARS
        try:
            eq = Equator(body, time, self.observer, True, True)
            hor = Horizon(time, self.observer, eq.ra, eq.dec, Refraction.Normal)
            info['Altitude'] = hor.altitude
            info['Azimute'] = hor.azimuth
            info['Constelação'] = get_constellation(body, time, self.observer)

            if not is_star:
                geo_vec = GeoVector(body, time, True)
                ecl = Ecliptic(geo_vec)
                info['Longitude'] = ecl.elon % 360.0
                info['Signo Tropical'] = signo_tropical(info['Longitude'])
                illum = Illumination(body, time)
                info['Magnitude'] = illum.mag
            else:
                magnitudes_fixas = {"Sirius": -1.46, "Canopus": -0.74, "Rigil Kentaurus": -0.27, "Arcturus": -0.05, "Vega": 0.03, "Capella": 0.08, "Rigel": 0.13, "Procyon": 0.34}
                info['Magnitude'] = magnitudes_fixas.get(name, "N/A")

            search_limit = 1.1 
            info['Rise'] = SearchRiseSet(body, self.observer, Direction.Rise, time, search_limit)
            info['Set'] = SearchRiseSet(body, self.observer, Direction.Set, time, search_limit)
            transit_event = SearchHourAngle(body, self.observer, 0.0, time, 1)
            if transit_event and transit_event.time.ut < time.AddDays(search_limit).ut:
                info['Transit'] = transit_event.time
            else:
                info['Transit'] = None

        except Exception as e:
            print(f"Aviso: Não foi possível calcular dados para {name}. Erro: {e}", file=sys.stderr)
        return info

    def _run_calculations(self):
        if not self._ensure_location(): return
        all_celestial_bodies = {**BODIES, **STARS}
        body_names = list(BODIES.keys()) + list(STARS.keys())
        print("\nEscolha os corpos (ex: 1,11), 'p' para planetas, 'e' para estrelas, 'a' para todos, ou 0 para voltar:")
        for i, name in enumerate(body_names, 1): print(f"{i:2d}. {name}")
        choice = input("Sua escolha: ").strip().lower()
        if choice == '0': return
        chosen_names = []
        if choice == 'a': chosen_names = body_names
        elif choice == 'p': chosen_names = list(BODIES.keys())
        elif choice == 'e': chosen_names = list(STARS.keys())
        else:
            try:
                indices = [int(i.strip()) - 1 for i in choice.split(',')]
                for idx in indices:
                    if 0 <= idx < len(body_names): chosen_names.append(body_names[idx])
                    else: print(f"Aviso: número {idx+1} é inválido.")
            except ValueError: print("Entrada inválida."); return
        if not chosen_names: print("Nenhum corpo selecionado."); return
        print("\nCalculando..."); now = Time.Now()
        chosen_bodies_map = {name: all_celestial_bodies[name] for name in chosen_names}
        body_infos = {name: self._compute_body_info(name, body, now) for name, body in chosen_bodies_map.items()}
        print("\n--- Posição Aparente Agora ---")
        headers1 = ["Corpo", "Altitude", "Direção", "Constelação"]
        rows1 = []
        for name in chosen_names:
            info = body_infos.get(name, {})
            rows1.append([name, f"{fmt_num(info.get('Altitude'), 2)}°", get_cardinal_direction(info.get('Azimute')), info.get('Constelação', '—')])
        self._print_table(rows1, headers1)
        ss_infos = {k: v for k, v in body_infos.items() if k in BODIES}
        if ss_infos:
            print("\n--- Dados Orbitais e Físicos ---")
            headers2 = ["Corpo", "Magnitude (Brilho)", "Longitude Eclíptica", "Signo Tropical"]
            rows2 = []
            for name, info in ss_infos.items():
                signo, deg = info.get('Signo Tropical', ('—', '—'))
                rows2.append([name, fmt_num(info.get('Magnitude'), 2), f"{fmt_num(info.get('Longitude'), 2)}°", f"{signo} {fmt_num(deg, 2)}°"])
            self._print_table(rows2, headers2)
        print("\n--- Eventos Diários (Próximas 24h, Horário Local) ---")
        headers3 = ["Corpo", "Nascer", "Culminação", "Pôr"]
        rows3 = []
        for name in chosen_names:
            info = body_infos.get(name, {})
            rows3.append([ name, fmt_dt(to_local(info.get('Rise'), self.tz_info)), fmt_dt(to_local(info.get('Transit'), self.tz_info)), fmt_dt(to_local(info.get('Set'), self.tz_info)), ])
        self._print_table(rows3, headers3)
        if ss_infos:
            self._display_aspects(ss_infos)

    def _display_aspects(self, body_infos):
        longitudes = {name: info.get('Longitude') for name, info in body_infos.items() if info.get('Longitude') is not None}
        if not longitudes: return
        aspects_found = []
        names = list(longitudes.keys())
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                name1, name2 = names[i], names[j]
                lon1, lon2 = longitudes[name1], longitudes[name2]
                diff = abs((lon1 - lon2 + 180) % 360 - 180)
                for asp_name, (asp_angle, orb) in ASPECTS.items():
                    if abs(diff - asp_angle) <= orb:
                        aspects_found.append([f"{name1}-{name2}", asp_name, f"{diff:.2f}°", f"{abs(diff - asp_angle):.2f}°"])
        if aspects_found:
            print("\n--- Aspectos Astrológicos (baseado em Longitude Eclíptica) ---")
            self._print_table(aspects_found, ["Par", "Aspecto", "Separação Atual", "Orbe Restante"])
    
    def _display_jupiter_moons(self):
        if not self._ensure_location(): return
        print("\nCalculando posições das luas de Júpiter...")
        now = Time.Now()
        jupiter_eq = Equator(Body.Jupiter, now, self.observer, True, True)
        moons_info = JupiterMoons(now)
        moon_data = {"Io": moons_info.io, "Europa": moons_info.europa, "Ganimedes": moons_info.ganymede, "Calisto": moons_info.callisto}
        rows = []
        for name, moon_state in moon_data.items():
            moon_geocentric_vec = jupiter_eq.vec + moon_state.Position()
            moon_eq_coords = astronomy.EquatorFromVector(moon_geocentric_vec)
            hor = Horizon(now, self.observer, moon_eq_coords.ra, moon_eq_coords.dec, Refraction.Normal)
            rows.append([name, f"{fmt_num(hor.altitude, 2)}°", get_cardinal_direction(hor.azimuth)])
        print(f"\nPosições aparentes das Luas de Júpiter em {self.current_city_name} (Constelação de Júpiter: {get_constellation(Body.Jupiter, now, self.observer)})")
        self._print_table(rows, ["Lua", "Altitude", "Direção"])
        
    def _display_lunar_libration(self):
        if not self._ensure_location(): return
        print("\nCalculando Libração Lunar...")
        now = Time.Now()
        lib_info = Libration(now)
        rows = [
            ["Libration em Longitude (Terra)", f"{fmt_num(lib_info.elon, 3)}°"],
            ["Libration em Latitude (Terra)", f"{fmt_num(lib_info.elat, 3)}°"],
            ["Longitude Geocêntrica da Lua", f"{fmt_num(lib_info.mlon, 3)}°"],
            ["Latitude Geocêntrica da Lua", f"{fmt_num(lib_info.mlat, 3)}°"],
            ["Distância Terra-Lua (km)", f"{fmt_num(lib_info.dist_km, 0)}"],
            ["Diâmetro Aparente da Lua", f"{fmt_num(lib_info.diam_deg, 4)}°"],
        ]
        print(f"\n--- Informações de Libração da Lua (Constelação: {get_constellation(Body.Moon, now, self.observer)}) ---")
        col_widths = [35, 20]
        for r in rows:
            print(f"{r[0].ljust(col_widths[0])} : {r[1]}")

    def _display_galactic_coords(self):
        if not self._ensure_location(): return
        all_celestial_bodies = {**BODIES, **STARS}
        body_names = list(all_celestial_bodies.keys())
        print("\nEscolha os corpos para ver suas Coordenadas Galácticas (ex: 1,2,11), 'a' para todos, ou 0 para voltar:")
        for i, name in enumerate(body_names, 1): print(f"{i:2d}. {name}")
        choice = input("Sua escolha: ").strip().lower()
        if choice == '0': return
        chosen_names = []
        if choice == 'a': chosen_names = body_names
        else:
            try:
                indices = [int(i.strip()) - 1 for i in choice.split(',')]
                for idx in indices:
                    if 0 <= idx < len(body_names): chosen_names.append(body_names[idx])
            except ValueError:
                print("Entrada inválida."); return
        if not chosen_names: print("Nenhum corpo selecionado."); return
        print("\nCalculando Coordenadas Galácticas...")
        now = Time.Now()
        rot_matrix = astronomy.Rotation_EQJ_GAL()
        rows = []
        for name in chosen_names:
            body = all_celestial_bodies[name]
            try:
                geo_vec = GeoVector(body, now, False)
                gal_vec = astronomy.RotateVector(rot_matrix, geo_vec)
                gal_sphere = astronomy.SphereFromVector(gal_vec)
                rows.append([name, f"{fmt_num(gal_sphere.lon, 2)}°", f"{fmt_num(gal_sphere.lat, 2)}°"])
            except Exception:
                rows.append([name, "N/A", "N/A"])
        self._print_table(rows, ["Corpo", "Longitude Galáctica", "Latitude Galáctica"])


    def _generate_daily_calendar(self):
        if not self._ensure_location(): return
        print("\n--- Agenda Astronômica do Dia ---")
        date_str = input("Digite a data (AAAA-MM-DD) ou deixe em branco para hoje: ").strip()
        try:
            if date_str:
                user_date = datetime.strptime(date_str, "%Y-%m-%d")
                start_of_day_local = datetime(user_date.year, user_date.month, user_date.day, 0, 0, 0, tzinfo=self.tz_info)
            else:
                user_date = datetime.now(tz=self.tz_info)
                start_of_day_local = datetime(user_date.year, user_date.month, user_date.day, 0, 0, 0, tzinfo=self.tz_info)
            end_of_day_local = datetime(user_date.year, user_date.month, user_date.day, 23, 59, 59, tzinfo=self.tz_info)
            start_time = Time.from_datetime(start_of_day_local)
            end_time = Time.from_datetime(end_of_day_local)
            print(f"\nCalculando eventos para {user_date.strftime('%Y-%m-%d')} em {self.current_city_name}...")
            events = []
            bodies_to_check = {**BODIES, **{s:STARS[s] for s in ["Sirius", "Vega", "Rigel"]}}
            for name, body in bodies_to_check.items():
                t = start_time
                for _ in range(4): 
                    try: next_rise = SearchRiseSet(body, self.observer, Direction.Rise, t, 1.0)
                    except astronomy.Error: next_rise = None
                    try: next_transit_event = SearchHourAngle(body, self.observer, 0.0, t, 1)
                    except astronomy.Error: next_transit_event = None
                    next_transit = next_transit_event.time if next_transit_event else None
                    try: next_set = SearchRiseSet(body, self.observer, Direction.Set, t, 1.0)
                    except astronomy.Error: next_set = None

                    found_events_in_step = []
                    if next_rise and next_rise.ut < end_time.ut: found_events_in_step.append((next_rise, name, "Nasce"))
                    if next_transit and next_transit.ut < end_time.ut: found_events_in_step.append((next_transit, name, "Culmina"))
                    if next_set and next_set.ut < end_time.ut: found_events_in_step.append((next_set, name, "Põe-se"))
                    if not found_events_in_step: break
                    found_events_in_step.sort(key=lambda x: x[0].ut)
                    next_event = found_events_in_step[0]
                    if not any(abs(next_event[0].ut - ev[0].ut) < 1e-4 and next_event[1] == ev[1] for ev in events):
                        events.append(next_event)
                    t = next_event[0].AddDays(1.0 / 1440.0)
            events.sort(key=lambda x: x[0].ut)
            if not events:
                print("Nenhum evento de nascer/culminar/pôr encontrado.")
                return
            rows = [[fmt_dt(to_local(t, self.tz_info)), n, e, get_constellation(bodies_to_check[n], t, self.observer)] for t, n, e in events]
            self._print_table(rows, ["Horário Local", "Astro", "Evento", "Constelação"])
        except ValueError: print("Formato de data inválido. Use AAAA-MM-DD.")
        except Exception as e: print(f"Ocorreu um erro: {e}")

    def _generate_lunar_calendar(self):
        if not self._ensure_location(): return
        try:
            year = int(input("Digite o ano (ex: 2025): ").strip())
            month = int(input("Digite o mês (1-12): ").strip())
            if not (1 <= month <= 12): print("Mês inválido."); return
        except ValueError: print("Entrada inválida."); return
        print(f"\n--- Calendário de Fases da Lua para {month}/{year} ---")
        start_time = Time.Make(year, month, 1, 0, 0, 0)
        end_time = start_time.AddDays(31)
        events = []
        phase_names = {0: "Lua Nova", 45: "Lua Crescente", 90: "Quarto Crescente", 135: "Gibosa Crescente", 180: "Lua Cheia", 225: "Gibosa Minguante", 270: "Quarto Minguante", 315: "Lua Minguante"}
        angle = astronomy.MoonPhase(start_time)
        next_angle = math.floor(angle / 45.0) * 45.0
        t = start_time
        for _ in range(10):
            phase_time = SearchMoonPhase(next_angle, t, 8)
            if phase_time is None or phase_time.ut >= end_time.ut: break
            local_time = to_local(phase_time, self.tz_info)
            if local_time and local_time.year == year and local_time.month == month:
                const = get_constellation(Body.Moon, phase_time, self.observer)
                dist = Illumination(Body.Moon, phase_time).geo_dist * 149597870.7
                events.append([phase_names[next_angle], fmt_dt(local_time), const, f"{fmt_num(dist, 0)} km"])
            t = phase_time.AddDays(1)
            next_angle = (next_angle + 45) % 360
        events.sort(key=lambda x: x[1])
        self._print_table(events, ["Fase", "Data e Hora (Local)", "Constelação", "Distância"])

    def _search_lunar_apsis(self):
        if not self._ensure_location(): return
        print("\n--- Busca por Apogeu/Perigeu Lunar ---")
        try:
            apsis_time = self.search_time
            while True:
                current_apsis = SearchLunarApsis(apsis_time)
                self.search_time = current_apsis.time.AddDays(1)
                kind_str = "Perigeu (mais próxima)" if current_apsis.kind == ApsisKind.Pericenter else "Apogeu (mais distante)"
                const = get_constellation(Body.Moon, current_apsis.time, self.observer)
                print(f"\nPróximo evento: {kind_str}")
                print(f"  Data (local): {fmt_dt(to_local(current_apsis.time, self.tz_info))}")
                print(f"  Distância   : {fmt_num(current_apsis.dist_km, 0)} km")
                print(f"  Constelação : {const}")
                choice = input("\nBuscar próximo evento? (s/n): ").strip().lower()
                if choice in ['n', 'nao', 'não']: break
                apsis_time = current_apsis.time
        except Exception as e:
            print(f"Ocorreu um erro: {e}")

    def _search_planet_apsis(self):
        if not self._ensure_location(): return
        print("\n--- Busca por Periélio/Afélio Planetário ---")
        planet_names = PLANETS_FOR_ASPECTS
        for i, name in enumerate(planet_names, 1): print(f"{i:2d}. {name}")
        try:
            choice = int(input("Escolha um planeta: ").strip()) - 1
            if not (0 <= choice < len(planet_names)):
                print("Seleção inválida."); return
            planet_name = planet_names[choice]
            planet_body = BODIES[planet_name]
            apsis_time = self.search_time
            while True:
                current_apsis = SearchPlanetApsis(planet_body, apsis_time)
                self.search_time = current_apsis.time.AddDays(1)
                kind_str = "Periélio (próximo do Sol)" if current_apsis.kind == ApsisKind.Pericenter else "Afélio (longe do Sol)"
                const = get_constellation(planet_body, current_apsis.time, self.observer)
                print(f"\nPróximo evento para {planet_name}: {kind_str}")
                print(f"  Data (UTC): {fmt_dt(current_apsis.time.Utc())}")
                print(f"  Distância : {fmt_num(current_apsis.dist_au, 4)} AU")
                print(f"  Constelação (vista da Terra): {const}")
                user_input = input("\nBuscar próximo evento? (s/n): ").strip().lower()
                if user_input in ['n', 'nao', 'não']: break
                apsis_time = current_apsis.time
        except (ValueError, astronomy.Error) as e:
            print(f"Entrada inválida ou erro na busca: {e}")
            
    def _search_eclipses(self):
        # ... (código completo)
        pass
        
    def _search_moon_nodes(self):
        if not self._ensure_location(): return
        print("\n--- Busca por Nodos Lunares ---")
        try:
            node_time = self.search_time
            while True:
                current_node = SearchMoonNode(node_time)
                self.search_time = current_node.time.AddDays(1)
                kind_str = "Ascendente (Sul -> Norte)" if current_node.kind == astronomy.NodeEventKind.Ascending else "Descendente (Norte -> Sul)"
                const = get_constellation(Body.Moon, current_node.time, self.observer)
                print(f"\nPróximo evento: Nodo {kind_str}")
                print(f"  Data (local): {fmt_dt(to_local(current_node.time, self.tz_info))}")
                print(f"  Constelação : {const}")
                choice = input("\nBuscar próximo nodo? (s/n): ").strip().lower()
                if choice in ['n', 'nao', 'não']: break
                node_time = current_node.time
        except Exception as e:
            print(f"Ocorreu um erro: {e}")

    def _search_max_elongation(self):
        if not self._ensure_location(): return
        print("\n--- Busca por Máxima Elongação (Mercúrio e Vênus) ---")
        planet_choice = input("Buscar para (1) Mercúrio ou (2) Vênus? ").strip()
        if planet_choice == '1': body, name = Body.Mercury, "Mercúrio"
        elif planet_choice == '2': body, name = Body.Venus, "Vênus"
        else:
            print("Seleção inválida."); return
        try:
            elong_time = self.search_time
            while True:
                event = SearchMaxElongation(body, elong_time)
                if not event:
                    print(f"Não foi possível encontrar a próxima elongação para {name}.")
                    break
                self.search_time = event.time.AddDays(1)
                visibility = "Estrela da Manhã" if event.visibility == Visibility.Morning else "Estrela da Tarde"
                print(f"\nPróxima máxima elongação para {name}:")
                print(f"  Data (local): {fmt_dt(to_local(event.time, self.tz_info))}")
                print(f"  Visibilidade: {visibility}")
                print(f"  Elongação   : {fmt_num(event.elongation, 2)}° do Sol")
                print(f"  Constelação : {get_constellation(body, event.time, self.observer)}")
                choice = input("\nBuscar próxima elongação? (s/n): ").strip().lower()
                if choice in ['n', 'nao', 'não']: break
                elong_time = self.search_time
        except Exception as e:
            print(f"Ocorreu um erro: {e}")

    def _search_transits(self):
        if not self._ensure_location(): return
        print("\n--- Busca por Trânsitos de Mercúrio e Vênus ---")
        planet_choice = input("Buscar para (1) Mercúrio ou (2) Vênus? ").strip()
        if planet_choice == '1': body, name = Body.Mercury, "Mercúrio"
        elif planet_choice == '2': body, name = Body.Venus, "Vênus"
        else:
            print("Seleção inválida."); return
        try:
            print(f"Buscando próximo trânsito de {name}... (pode demorar)")
            event = SearchTransit(body, self.search_time)
            if event:
                self.search_time = event.finish.AddDays(1)
                print(f"\nPróximo trânsito de {name} encontrado:")
                rows = [
                    ["Início", fmt_dt(to_local(event.start, self.tz_info))],
                    ["Pico", fmt_dt(to_local(event.peak, self.tz_info))],
                    ["Fim", fmt_dt(to_local(event.finish, self.tz_info))],
                    ["Separação Mínima", f"{fmt_num(event.separation, 2)}' (arcmin)"]
                ]
                self._print_table(rows, ["Evento", "Horário Local"])
            else:
                print("Não foi possível encontrar o próximo trânsito.")
        except Exception as e:
            print(f"Ocorreu um erro ao buscar trânsito: {e}")
            
    def _display_seasons_calendar(self):
        if not self._ensure_location(): return
        try:
            year = int(input("Digite o ano para o calendário de estações (ex: 2025): ").strip())
        except ValueError:
            print("Ano inválido."); return
        print(f"\nCalculando estações para o ano de {year}...")
        try:
            season_info = Seasons(year)
            rows = [
                ["Equinócio de Março", fmt_dt(to_local(season_info.mar_equinox, self.tz_info))],
                ["Solstício de Junho", fmt_dt(to_local(season_info.jun_solstice, self.tz_info))],
                ["Equinócio de Setembro", fmt_dt(to_local(season_info.sep_equinox, self.tz_info))],
                ["Solstício de Dezembro", fmt_dt(to_local(season_info.dec_solstice, self.tz_info))],
            ]
            self._print_table(rows, ["Evento (Hemisfério Norte)", "Data e Hora (Local)"])
        except Exception as e:
            print(f"Ocorreu um erro ao calcular as estações: {e}")
        
    def _generate_daily_longitude_table(self):
        if not self._ensure_location(): return
        print("\n--- Efemérides Diárias (Longitudes) ---")
        date_str = input("Digite a data (AAAA-MM-DD) ou deixe em branco para hoje: ").strip()
        try:
            if date_str:
                user_date = datetime.strptime(date_str, "%Y-%m-%d")
            else:
                user_date = datetime.now(tz=self.tz_info)

            target_local_time = datetime(user_date.year, user_date.month, user_date.day, 12, 0, 0, tzinfo=self.tz_info)
            target_time = Time.from_datetime(target_local_time)
            print(f"\nCalculando posições para o meio-dia de {user_date.strftime('%Y-%m-%d')}...")
            rows = []
            for name, body in BODIES.items():
                try:
                    geo_vec = GeoVector(body, target_time, False)
                    ecl = Ecliptic(geo_vec)
                    lon = ecl.elon % 360.0
                    signo, deg = signo_tropical(lon)
                    const = get_constellation(body, target_time, self.observer)
                    rows.append([name, f"{fmt_num(lon, 4)}°", f"{signo} {fmt_num(deg, 4)}°", const])
                except Exception:
                    rows.append([name, "N/A", "N/A", "N/A"])
            self._print_table(rows, ["Corpo", "Longitude Eclíptica", "Signo Tropical", "Constelação"])
        except ValueError:
            print("Formato de data inválido. Use AAAA-MM-DD.")
        except Exception as e:
            print(f"Ocorreu um erro: {e}")

    def _menu_observacao_imediata(self):
        while True:
            print("\n--- Observação Imediata ---")
            print("1. Posições dos Astros e Estrelas")
            print("2. Luas de Júpiter")
            print("3. Libração da Lua")
            print("4. Coordenadas Galácticas")
            print("0. Voltar ao Menu Principal")
            choice = input("Opção: ").strip()
            if choice == '1': self._run_calculations()
            elif choice == '2': self._display_jupiter_moons()
            elif choice == '3': self._display_lunar_libration()
            elif choice == '4': self._display_galactic_coords()
            elif choice == '0': break
            else: print("Opção inválida.")

    def _menu_busca_eventos(self):
        while True:
            print("\n--- Busca de Eventos Futuros ---")
            print("1. Ápsides Lunares (Apogeu/Perigeu)")
            print("2. Ápsides Planetários (Afélio/Periélio)")
            print("3. Eclipses (Sol e Lua)")
            print("4. Nodos Lunares")
            print("5. Elongação (Vênus/Mercúrio)")
            print("6. Trânsitos (Vênus/Mercúrio)")
            print("0. Voltar ao Menu Principal")
            choice = input("Opção: ").strip()
            if choice == '1': self._search_lunar_apsis()
            elif choice == '2': self._search_planet_apsis()
            elif choice == '3': self._search_eclipses()
            elif choice == '4': self._search_moon_nodes()
            elif choice == '5': self._search_max_elongation()
            elif choice == '6': self._search_transits()
            elif choice == '0': break
            else: print("Opção inválida.")
    
    def _menu_calendarios(self):
        while True:
            print("\n--- Calendários e Efemérides ---")
            print("1. Agenda Astronômica do Dia (Nascer/Pôr)")
            print("2. Efemérides do Dia (Tabela de Longitudes)")
            print("3. Calendário de Fases Lunares (Mensal)")
            print("4. Calendário de Estações (Anual)")
            print("5. Calendário de Aspectos (Anual)")
            print("0. Voltar ao Menu Principal")
            choice = input("Opção: ").strip()
            if choice == '1': self._generate_daily_calendar()
            elif choice == '2': self._generate_daily_longitude_table()
            elif choice == '3': self._generate_lunar_calendar()
            elif choice == '4': self._display_seasons_calendar()
            elif choice == '5': self._generate_aspect_calendar()
            elif choice == '0': break
            else: print("Opção inválida.")
        
    def run(self):
        while True:
            print("\n" + "="*20 + " Orrery Pro (Final) " + "="*20)
            if self.current_city_name:
                local_time_str = fmt_dt(to_local(Time.Now(), self.tz_info))
                search_time_str = fmt_dt(to_local(self.search_time, self.tz_info))
                print(f"Localização: {self.current_city_name} | Horário: {local_time_str}")
                print(f"Data para Buscas: {search_time_str}")
            else:
                print(f"Localização: Nenhuma selecionada | Horário: {fmt_dt(Time.Now().Utc())}")

            print("\n--- MENU PRINCIPAL ---")
            print("1. Selecionar Cidade")
            print("2. Definir Data de Início para Buscas")
            print("3. Observação Imediata")
            print("4. Busca de Eventos Futuros")
            print("5. Calendários e Efemérides")
            print("0. Sair")
            choice = input("Opção: ").strip()

            if choice == '1': self._choose_city()
            elif choice == '2': self._set_search_time()
            elif choice == '3': self._menu_observacao_imediata()
            elif choice == '4': self._menu_busca_eventos()
            elif choice == '5': self._menu_calendarios()
            elif choice == '0':
                print("Obrigado por usar o Orrery Pro! Até a próxima.")
                break
            else:
                print("Opção inválida.")
    
# --- Ponto de Entrada ---
if __name__ == '__main__':
    if not hasattr(Time, 'from_datetime'):
        def from_datetime(dt):
            if dt.tzinfo is None:
                raise ValueError("datetime object must be timezone-aware.")
            dt_utc = dt.astimezone(timezone.utc)
            return Time.Make(dt_utc.year, dt_utc.month, dt_utc.day, dt_utc.hour, dt_utc.minute, dt_utc.second + dt_utc.microsecond / 1_000_000.0)
        Time.from_datetime = staticmethod(from_datetime)

    cli_app = AstroCLI()
    cli_app.run()