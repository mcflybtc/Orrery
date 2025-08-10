#!/usr/bin/env python3
# orrery_pro_v8_final.py
# Versão completa, profissional e robusta com fallback de fuso horário,
# código completo e todas as funcionalidades solicitadas.

import math
import sys
from datetime import datetime, timedelta, tzinfo
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

# Importações da biblioteca de astronomia
import astronomy
from astronomy import (
    Body, Observer, Time, Direction, Refraction, ApsisKind, EclipseKind,
    Equator, Horizon, GeoVector, Ecliptic, Illumination, Constellation,
    JupiterMoons, Libration, PairLongitude, DefineStar, PlanetOrbitalPeriod,
    SearchRiseSet, SearchHourAngle, SearchLunarApsis, NextLunarApsis,
    SearchPlanetApsis, NextPlanetApsis, SearchLunarEclipse,
    SearchGlobalSolarEclipse, SearchLocalSolarEclipse,
    SearchMoonQuarter, NextMoonQuarter, Search
)

# --- Classe de Fallback para Fuso Horário Fixo ---
class FixedTimeZone(tzinfo):
    """Uma classe para representar fusos horários com um deslocamento UTC fixo."""
    def __init__(self, offset_hours, name):
        self._offset = timedelta(hours=offset_hours)
        self._name = name

    def utcoffset(self, dt):
        return self._offset

    def dst(self, dt):
        return timedelta(0)

    def tzname(self, dt):
        return self._name

# --- Configurações Globais ---
# Formato: "Cidade": ((lat, lon), "Nome IANA do Fuso", Deslocamento UTC fixo em horas ou None)
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

BODIES = {
    "Sun": Body.Sun, "Moon": Body.Moon, "Mercury": Body.Mercury,
    "Venus": Body.Venus, "Mars": Body.Mars, "Jupiter": Body.Jupiter,
    "Saturn": Body.Saturn, "Uranus": Body.Uranus, "Neptune": Body.Neptune,
    "Pluto": Body.Pluto
}

STARS_DATA = [
    ("Sirius", 6.7525, -16.7161), ("Canopus", 6.3992, -52.6957),
    ("Rigil Kentaurus", 14.6601, -60.8356), ("Arcturus", 14.2610, 19.1825),
    ("Vega", 18.6156, 38.7837), ("Capella", 5.2782, 45.9980),
    ("Rigel", 5.2423, -8.2016), ("Procyon", 7.6550, 5.2250),
]
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
        utc_dt = t.Utc()
        return utc_dt.astimezone(tz_info)
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

def _calculate_synodic_period(name1, name2):
    try:
        p1 = PlanetOrbitalPeriod(BODIES[name1])
        p2 = PlanetOrbitalPeriod(BODIES[name2])
        return abs(1.0 / (1.0/p1 - 1.0/p2))
    except (astronomy.Error, KeyError):
        return 30

# --- Classe da Aplicação ---
class AstroCLI:
    def __init__(self):
        self.current_city_name = None
        self.observer = None
        self.tz_info = None
        self._initialize_stars()

    def _initialize_stars(self):
        for name, body_enum in STARS.items():
            star_data = next((s for s in STARS_DATA if s[0] == name), None)
            if star_data:
                DefineStar(body_enum, star_data[1], star_data[2], 1000)

    def _ensure_location(self):
        if not self.observer:
            print("\nPor favor, selecione uma cidade primeiro (opção 1).")
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
                info['Fase (%)'] = illum.phase_fraction * 100
                if body == Body.Saturn and illum.ring_tilt is not None:
                    info['Inclinação Anéis (°)'] = illum.ring_tilt
            else:
                info['Magnitude'] = "Fixo"

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
        headers1 = ["Corpo", "Altitude", "Azimute", "Constelação"]
        rows1 = []
        for name in chosen_names:
            info = body_infos.get(name, {})
            rows1.append([name, f"{fmt_num(info.get('Altitude'), 2)}°", f"{fmt_num(info.get('Azimute'), 2)}°", info.get('Constelação', '—')])
        self._print_table(rows1, headers1)

        ss_infos = {k: v for k, v in body_infos.items() if k in BODIES}
        if ss_infos:
            print("\n--- Dados Orbitais e Físicos ---")
            headers2 = ["Corpo", "Magnitude", "Longitude Eclíptica", "Signo Tropical"]
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
            rows3.append([
                name,
                fmt_dt(to_local(info.get('Rise'), self.tz_info)),
                fmt_dt(to_local(info.get('Transit'), self.tz_info)),
                fmt_dt(to_local(info.get('Set'), self.tz_info)),
            ])
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
            rows.append([name, f"{fmt_num(hor.altitude, 2)}°", f"{fmt_num(hor.azimuth, 2)}°"])
            
        print(f"\nPosições aparentes das Luas de Júpiter (relativo a {self.current_city_name})")
        self._print_table(rows, ["Lua", "Altitude", "Azimute"])
        
    def _display_lunar_libration(self):
        print("\nCalculando Libração Lunar...")
        lib_info = Libration(Time.Now())
        
        rows = [
            ["Libration em Longitude (Terra)", f"{fmt_num(lib_info.elon, 3)}°"],
            ["Libration em Latitude (Terra)", f"{fmt_num(lib_info.elat, 3)}°"],
            ["Longitude Geocêntrica da Lua", f"{fmt_num(lib_info.mlon, 3)}°"],
            ["Latitude Geocêntrica da Lua", f"{fmt_num(lib_info.mlat, 3)}°"],
            ["Distância Terra-Lua (km)", f"{fmt_num(lib_info.dist_km, 0)}"],
            ["Diâmetro Aparente da Lua", f"{fmt_num(lib_info.diam_deg, 4)}°"],
        ]
        
        print("\n--- Informações de Libração da Lua ---")
        col_widths = [35, 20]
        for r in rows:
            print(f"{r[0].ljust(col_widths[0])} : {r[1]}")

    def _generate_daily_calendar(self):
        if not self._ensure_location(): return
        
        print("\n--- Agenda Astronômica do Dia ---")
        date_str = input("Digite a data (AAAA-MM-DD) ou deixe em branco para hoje: ").strip()
        
        try:
            if date_str:
                user_date = datetime.strptime(date_str, "%Y-%m-%d")
            else:
                user_date = datetime.now(tz=self.tz_info)

            start_of_day_local = datetime(user_date.year, user_date.month, user_date.day, 0, 0, 0, tzinfo=self.tz_info)
            end_of_day_local = datetime(user_date.year, user_date.month, user_date.day, 23, 59, 59, tzinfo=self.tz_info)

            start_time = Time.from_datetime(start_of_day_local)
            end_time = Time.from_datetime(end_of_day_local)
            
            print(f"\nCalculando eventos para {user_date.strftime('%Y-%m-%d')} em {self.current_city_name}...")

            events = []
            bodies_to_check = {**BODIES, **{s:STARS[s] for s in ["Sirius", "Canopus", "Arcturus", "Vega", "Rigel"]}}

            for name, body in bodies_to_check.items():
                t = start_time
                while t.ut < end_time.ut:
                    # Encontra o próximo evento de qualquer tipo após o tempo 't'
                    next_rise = SearchRiseSet(body, self.observer, Direction.Rise, t, 1.0)
                    next_transit = SearchHourAngle(body, self.observer, 0.0, t, 1).time
                    next_set = SearchRiseSet(body, self.observer, Direction.Set, t, 1.0)
                    
                    found_events = []
                    if next_rise and next_rise.ut < end_time.ut: found_events.append((next_rise, name, "Nasce"))
                    if next_transit and next_transit.ut < end_time.ut: found_events.append((next_transit, name, "Culmina"))
                    if next_set and next_set.ut < end_time.ut: found_events.append((next_set, name, "Põe-se"))

                    if not found_events: break
                    
                    found_events.sort(key=lambda x: x[0].ut)
                    
                    is_new = True
                    for ev in events:
                        if ev[1] == name and abs(ev[0].ut - found_events[0][0].ut) < 1e-4:
                            is_new = False
                            break
                    
                    if is_new:
                        events.append(found_events[0])
                        t = found_events[0][0].AddDays(1.0 / (24 * 60))
                    else:
                        break
            
            events.sort(key=lambda x: x[0].ut)
            
            if not events:
                print("Nenhum evento de nascer/culminar/pôr encontrado para os principais astros nesta data.")
                return

            rows = [[fmt_dt(to_local(t, self.tz_info)), n, e, get_constellation(bodies_to_check[n], t, self.observer)] for t, n, e in events]
            self._print_table(rows, ["Horário Local", "Astro", "Evento", "Constelação"])
            
        except ValueError:
            print("Formato de data inválido. Use AAAA-MM-DD.")
        except Exception as e:
            print(f"Ocorreu um erro: {e}")

    def _generate_lunar_calendar(self):
        if not self._ensure_location(): return
        try:
            year = int(input("Digite o ano (ex: 2025): ").strip())
            month = int(input("Digite o mês (1-12): ").strip())
            if not (1 <= month <= 12):
                print("Mês inválido."); return
        except ValueError:
            print("Entrada inválida."); return
            
        print(f"\n--- Calendário de Fases da Lua para {month}/{year} ---")
        
        start_time = Time.Make(year, month, 1, 0, 0, 0)
        mq = SearchMoonQuarter(start_time.AddDays(-10))
        
        events = []
        phase_names = {0: "Lua Nova", 1: "Quarto Crescente", 2: "Lua Cheia", 3: "Quarto Minguante"}

        for _ in range(5):
            mq = NextMoonQuarter(mq)
            local_time = to_local(mq.time, self.tz_info)
            if local_time and local_time.year == year and local_time.month == month:
                const = get_constellation(Body.Moon, mq.time, self.observer)
                events.append([phase_names[mq.quarter], fmt_dt(local_time), const])
        
        self._print_table(events, ["Fase", "Data e Hora (Local)", "Constelação"])

    def _search_lunar_apsis(self):
        if not self._ensure_location(): return
        print("\n--- Busca por Apogeu/Perigeu Lunar ---")
        try:
            current_apsis = SearchLunarApsis(Time.Now())
            while True:
                kind_str = "Perigeu (mais próxima)" if current_apsis.kind == ApsisKind.Pericenter else "Apogeu (mais distante)"
                const = get_constellation(Body.Moon, current_apsis.time, self.observer)
                
                print(f"\nPróximo evento: {kind_str}")
                print(f"  Data (local): {fmt_dt(to_local(current_apsis.time, self.tz_info))}")
                print(f"  Distância   : {fmt_num(current_apsis.dist_km, 0)} km")
                print(f"  Constelação : {const}")
                
                choice = input("\nBuscar próximo evento? (s/n): ").strip().lower()
                if choice in ['n', 'nao', 'não']: break
                current_apsis = NextLunarApsis(current_apsis)
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
            
            current_apsis = SearchPlanetApsis(planet_body, Time.Now())
            while True:
                kind_str = "Periélio (próximo do Sol)" if current_apsis.kind == ApsisKind.Pericenter else "Afélio (longe do Sol)"
                const = get_constellation(planet_body, current_apsis.time, self.observer)
                
                print(f"\nPróximo evento para {planet_name}: {kind_str}")
                print(f"  Data (UTC): {fmt_dt(current_apsis.time.Utc())}")
                print(f"  Distância : {fmt_num(current_apsis.dist_au, 4)} AU")
                print(f"  Constelação (vista da Terra): {const}")

                user_input = input("\nBuscar próximo evento? (s/n): ").strip().lower()
                if user_input in ['n', 'nao', 'não']: break
                current_apsis = NextPlanetApsis(planet_body, current_apsis)
        except (ValueError, astronomy.Error) as e:
            print(f"Entrada inválida ou erro na busca: {e}")
            
    def _search_eclipses(self):
        if not self._ensure_location(): return
        
        while True:
            print("\n--- Menu de Eclipses ---")
            print("1. Próximo Eclipse Solar (Global)")
            print("2. Próximo Eclipse Solar (Local)")
            print("3. Próximo Eclipse Lunar")
            print("0. Voltar ao menu principal")
            
            choice = input("Sua escolha: ").strip()

            if choice == '1':
                try:
                    print("\nBuscando próximo eclipse solar global...")
                    eclipse = SearchGlobalSolarEclipse(Time.Now())
                    const = get_constellation(Body.Sun, eclipse.peak, self.observer)
                    print(f"Tipo: {eclipse.kind.name} em {const}")
                    print(f"Pico (UTC): {fmt_dt(eclipse.peak.Utc())}")
                    if eclipse.kind in [EclipseKind.Total, EclipseKind.Annular] and eclipse.obscuration is not None:
                        print(f"Obscurecimento: {fmt_num(eclipse.obscuration * 100, 2)}%")
                        print(f"Pico de visibilidade em: Latitude {fmt_num(eclipse.latitude, 4)}°, Longitude {fmt_num(eclipse.longitude, 4)}°")
                except astronomy.Error as e:
                    print(f"Não foi possível encontrar um eclipse: {e}")
            elif choice == '2':
                try:
                    print(f"\nBuscando próximo eclipse solar visível em {self.current_city_name}...")
                    eclipse = SearchLocalSolarEclipse(Time.Now(), self.observer)
                    const = get_constellation(Body.Sun, eclipse.peak.time, self.observer)
                    print(f"Tipo para o observador: {eclipse.kind.name} em {const}")
                    print(f"Obscurecimento máximo: {fmt_num(eclipse.obscuration * 100, 2)}%")
                    
                    rows = [
                        ["Início Parcial", fmt_dt(to_local(eclipse.partial_begin.time, self.tz_info)), f"{fmt_num(eclipse.partial_begin.altitude, 2)}°"],
                        ["Pico do Eclipse", fmt_dt(to_local(eclipse.peak.time, self.tz_info)), f"{fmt_num(eclipse.peak.altitude, 2)}°"],
                        ["Fim Parcial", fmt_dt(to_local(eclipse.partial_end.time, self.tz_info)), f"{fmt_num(eclipse.partial_end.altitude, 2)}°"],
                    ]
                    if eclipse.total_begin and eclipse.total_end:
                        kind_str = "Total" if eclipse.kind == EclipseKind.Total else "Anular"
                        rows.insert(1, [f"Início {kind_str}", fmt_dt(to_local(eclipse.total_begin.time, self.tz_info)), f"{fmt_num(eclipse.total_begin.altitude, 2)}°"])
                        rows.insert(3, [f"Fim {kind_str}", fmt_dt(to_local(eclipse.total_end.time, self.tz_info)), f"{fmt_num(eclipse.total_end.altitude, 2)}°"])

                    self._print_table(rows, ["Evento", "Horário Local", "Altitude do Sol"])
                    print("Nota: Se a altitude do Sol for negativa, o evento ocorre abaixo do horizonte.")

                except astronomy.Error:
                    print(f"Não foi encontrado um eclipse solar visível em {self.current_city_name} no próximo ano.")
            elif choice == '3':
                try:
                    print("\nBuscando próximo eclipse lunar...")
                    eclipse = SearchLunarEclipse(Time.Now())
                    const = get_constellation(Body.Moon, eclipse.peak, self.observer)
                    print(f"Tipo: {eclipse.kind.name} em {const}")
                    print(f"Pico (UTC): {fmt_dt(eclipse.peak.Utc())}")
                    print(f"Obscurecimento (Umbra): {fmt_num(eclipse.obscuration * 100, 2)}%")
                    print("\nDuração das fases (início ao fim):")
                    print(f"  Penumbral: {fmt_num(eclipse.sd_penum * 2, 1)} minutos")
                    if eclipse.sd_partial > 0: print(f"  Parcial (Umbra): {fmt_num(eclipse.sd_partial * 2, 1)} minutos")
                    if eclipse.sd_total > 0: print(f"  Total (Umbra): {fmt_num(eclipse.sd_total * 2, 1)} minutos")
                except astronomy.Error as e:
                    print(f"Não foi possível encontrar um eclipse: {e}")
            elif choice == '0': break
            else: print("Opção inválida.")
    
    def _generate_aspect_calendar(self):
        if not self._ensure_location(): return
        try:
            year = int(input("Digite o ano para o calendário de aspectos (ex: 2025): ").strip())
            if not(1900 < year < 2100):
                print("Por favor, insira um ano entre 1901 e 2099."); return
        except ValueError:
            print("Ano inválido."); return

        print(f"\nCalculando calendário de aspectos para {year}... Isso pode levar alguns segundos.")
        start_time = Time.Make(year, 1, 1, 0, 0, 0)
        end_time = Time.Make(year, 12, 31, 23, 59, 59)
        events = []
        
        pairs = []
        for i in range(len(PLANETS_FOR_ASPECTS)):
            for j in range(i + 1, len(PLANETS_FOR_ASPECTS)):
                pairs.append((PLANETS_FOR_ASPECTS[i], PLANETS_FOR_ASPECTS[j]))

        def aspect_search_func(context, time):
            body1_name, body2_name, target_angle = context
            current_angle = PairLongitude(BODIES[body1_name], BODIES[body2_name], time)
            return astronomy._LongitudeOffset(current_angle - target_angle)

        for name1, name2 in pairs:
            for aspect_name, (angle, _) in ASPECTS.items():
                if aspect_name == "Oposição" and (name1 in ["Mercury", "Venus"] or name2 in ["Mercury", "Venus"]): continue
                
                search_time = start_time
                step_days = _calculate_synodic_period(name1, name2) / 16.0
                step_days = max(1.0, step_days)
                
                while search_time.ut < end_time.ut:
                    t1 = search_time
                    t2 = t1.AddDays(step_days)
                    if t2.ut > end_time.ut: t2 = end_time
                    
                    context = (name1, name2, angle)
                    f1 = aspect_search_func(context, t1)
                    f2 = aspect_search_func(context, t2)

                    if f1 * f2 <= 0.0:
                        event_time = Search(aspect_search_func, context, t1, t2, 60)
                        if event_time:
                            is_duplicate = any(abs(event_time.ut - evt[0].ut) < 0.1 for evt in events if evt[1] == f"{name1} {aspect_name} {name2}")
                            if not is_duplicate:
                                events.append((event_time, f"{name1} {aspect_name} {name2}"))
                    
                    search_time = t2
                    if t2.ut == end_time.ut: break
        
        events.sort(key=lambda x: x[0].ut)
        print(f"\n--- Calendário de Aspectos para {year} ---")
        rows = [[fmt_dt(to_local(t, self.tz_info)), desc] for t, desc in events]
        if not rows:
            print("Nenhum aspecto maior encontrado para este ano.")
        else:
            self._print_table(rows, ["Data e Hora (Local)", "Evento"])

    def run(self):
        """Loop principal da aplicação."""
        while True:
            print("\n" + "="*20 + " Orrery Pro v8 (Robusto) " + "="*20)
            if self.current_city_name:
                print(f"Localização: {self.current_city_name} | Horário: {fmt_dt(to_local(Time.Now(), self.tz_info))}")
            else:
                print(f"Localização: Nenhuma selecionada | Horário: {fmt_dt(Time.Now().Utc())}")

            print("\n--- CÁLCULOS INSTANTÂNEOS ---")
            print("1. Selecionar Cidade")
            print("2. Posições dos Astros e Estrelas")
            print("3. Luas de Júpiter")
            print("4. Libração da Lua")
            print("\n--- CALENDÁRIOS E EVENTOS ---")
            print("5. Agenda Astronômica do Dia")
            print("6. Calendário de Fases Lunares (Mensal)")
            print("7. Calendário de Aspectos (Anual)")
            print("8. Buscar Eclipses")
            print("9. Buscar Ápsides Lunares (Apogeu/Perigeu)")
            print("10. Buscar Ápsides Planetários (Afélio/Periélio)")
            print("\n0. Sair")
            choice = input("Opção: ").strip()

            menu_options = {
                "1": self._choose_city, "2": self._run_calculations,
                "3": self._display_jupiter_moons, "4": self._display_lunar_libration,
                "5": self._generate_daily_calendar, "6": self._generate_lunar_calendar,
                "7": self._generate_aspect_calendar, "8": self._search_eclipses,
                "9": self._search_lunar_apsis, "10": self._search_planet_apsis,
            }
            if choice in menu_options:
                menu_options[choice]()
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
            dt_utc = dt.astimezone(ZoneInfo("UTC"))
            return Time.Make(dt_utc.year, dt_utc.month, dt_utc.day, dt_utc.hour, dt_utc.minute, dt_utc.second + dt_utc.microsecond / 1_000_000.0)
        Time.from_datetime = staticmethod(from_datetime)

    cli_app = AstroCLI()
    cli_app.run()