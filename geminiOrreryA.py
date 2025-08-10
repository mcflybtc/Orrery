#!/usr/bin/env python3
# orrery_pro_v3.py
# Versão final com calendário de aspectos, busca de eclipses, ápsides planetários e correções de bugs.

import math
import sys
from datetime import timedelta
from zoneinfo import ZoneInfo

# Importações específicas e novas funcionalidades
import astronomy
from astronomy import (
    Body, Observer, Time, Direction, Refraction, ApsisKind, EclipseKind,
    Equator, Horizon, GeoVector, Ecliptic, Illumination, Constellation,
    JupiterMoons, Libration, PairLongitude,
    SearchRiseSet, SearchHourAngle, SearchLunarApsis, NextLunarApsis,
    SearchPlanetApsis, NextPlanetApsis, SearchLunarEclipse, NextLunarEclipse,
    SearchGlobalSolarEclipse, NextGlobalSolarEclipse, SearchLocalSolarEclipse, NextLocalSolarEclipse,
    Search
)

# --- Configurações Globais ---
CITIES = {
    "São Paulo, Brazil": ((-23.5505, -46.6333), "America/Sao_Paulo"),
    "Rio de Janeiro, Brazil": ((-22.9068, -43.1729), "America/Sao_Paulo"),
    "Fortaleza, Brazil": ((-3.71722, -38.5434), "America/Fortaleza"),
    "Lisbon, Portugal": ((38.7223, -9.1393), "Europe/Lisbon"),
    "New York, USA": ((40.7128, -74.0060), "America/New_York"),
    "London, UK": ((51.5074, -0.1278), "Europe/London"),
    "Tokyo, Japan": ((35.6895, 139.6917), "Asia/Tokyo"),
}

BODIES = {
    "Sun": Body.Sun, "Moon": Body.Moon, "Mercury": Body.Mercury,
    "Venus": Body.Venus, "Mars": Body.Mars, "Jupiter": Body.Jupiter,
    "Saturn": Body.Saturn, "Uranus": Body.Uranus, "Neptune": Body.Neptune,
    "Pluto": Body.Pluto
}

SIGNS = ["Áries", "Touro", "Gêmeos", "Câncer", "Leão", "Virgem", "Libra", "Escorpião", "Sagitário", "Capricórnio", "Aquário", "Peixes"]
ASPECTS = {"Conjunção": (0.0, 8.0), "Oposição": (180.0, 8.0), "Quadratura": (90.0, 6.0), "Trígono": (120.0, 6.0), "Sextil": (60.0, 4.0)}
PLANETS_FOR_ASPECTS = ["Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]

# --- Funções Auxiliares ---
def fmt_num(x, nd=2):
    """Formata um número para exibição, tratando casos nulos."""
    if x is None: return "—"
    if isinstance(x, float): return f"{x:.{nd}f}"
    return str(x)

def to_local(t, tz_name):
    """Converte um objeto astronomy.Time para um datetime local com fuso horário (versão robusta)."""
    if t is None or tz_name is None:
        return None
    try:
        utc_dt = t.Utc()
        return utc_dt.astimezone(ZoneInfo(tz_name))
    except Exception:
        # Em caso de qualquer erro, retorna None para ser tratado de forma consistente.
        return None

def fmt_dt(dt):
    """Formata um objeto datetime para uma string legível."""
    if dt is None: return "—"
    return dt.strftime("%Y-%m-%d %H:%M:%S %Z")

def signo_tropical(lon):
    """Calcula o signo tropical e o grau dentro dele."""
    if lon is None: return ("—", "—")
    idx = int((lon % 360) // 30)
    deg_into = (lon % 30)
    return SIGNS[idx], deg_into

# --- Classe da Aplicação ---
class AstroCLI:
    def __init__(self):
        self.current_city_name = None
        self.observer = None
        self.tz_name = None

    def _ensure_location(self):
        """Verifica se uma localização foi selecionada."""
        if not self.observer:
            print("\nPor favor, selecione uma cidade primeiro (opção 1).")
            return False
        return True

    def _compute_body_info(self, body, time):
        info = {}
        try:
            geo_vec = GeoVector(body, time, True)
            ecl = Ecliptic(geo_vec)
            info['Longitude'] = ecl.elon % 360.0
            info['Signo Tropical'] = signo_tropical(info['Longitude'])

            eq = Equator(body, time, self.observer, True, True)
            info['RA'] = eq.ra
            info['Dec'] = eq.dec
            
            const_info = Constellation(eq.ra, eq.dec)
            info['Constelação'] = f"{const_info.name} ({const_info.symbol})"

            hor = Horizon(time, self.observer, eq.ra, eq.dec, Refraction.Normal)
            info['Azimute'] = hor.azimuth
            info['Altitude'] = hor.altitude

            illum = Illumination(body, time)
            info['Magnitude'] = illum.mag
            info['Fase (%)'] = illum.phase_fraction * 100
            if body == Body.Saturn and illum.ring_tilt is not None:
                info['Inclinação Anéis (°)'] = illum.ring_tilt

            search_limit = 1.2
            info['Rise'] = SearchRiseSet(body, self.observer, Direction.Rise, time, search_limit)
            info['Set'] = SearchRiseSet(body, self.observer, Direction.Set, time, search_limit)
            transit_event = SearchHourAngle(body, self.observer, 0.0, time, +1)
            info['Transit'] = transit_event.time if transit_event else None
            info['TransitAlt'] = transit_event.hor.altitude if transit_event else None

        except Exception as e:
            print(f"Aviso: Não foi possível calcular todos os dados para {body.name}. Erro: {e}", file=sys.stderr)
            keys_to_null = ['Longitude', 'Signo Tropical', 'RA', 'Dec', 'Constelação', 'Azimute', 'Altitude',
                            'Magnitude', 'Fase (%)', 'Inclinação Anéis (°)', 'Rise', 'Set', 'Transit', 'TransitAlt']
            for k in keys_to_null:
                if k not in info: info[k] = None
        
        return info

    def _display_results(self, chosen_bodies, body_infos):
        print("\n--- Resumo dos Corpos Celestes ---")
        headers = ["Corpo", "Altitude", "Azimute", "Magnitude", "Constelação", "Signo Tropical", "Longitude"]
        rows = []
        for name in chosen_bodies:
            info = body_infos[name]
            signo, deg = info.get('Signo Tropical', ('—', '—'))
            rows.append([
                name,
                f"{fmt_num(info.get('Altitude'), 2)}°",
                f"{fmt_num(info.get('Azimute'), 2)}°",
                fmt_num(info.get('Magnitude'), 2),
                info.get('Constelação', '—'),
                f"{signo} {fmt_num(deg, 2)}°",
                f"{fmt_num(info.get('Longitude'), 2)}°",
            ])
        self._print_table(rows, headers)

        print("\n--- Eventos (Horário Local) ---")
        headers = ["Corpo", "Nascer", "Trânsito (Pico)", "Pôr"]
        rows = []
        for name in chosen_bodies:
            info = body_infos[name]
            rows.append([
                name,
                fmt_dt(to_local(info.get('Rise'), self.tz_name)),
                fmt_dt(to_local(info.get('Transit'), self.tz_name)),
                fmt_dt(to_local(info.get('Set'), self.tz_name)),
            ])
        self._print_table(rows, headers)

        self._display_aspects(body_infos)

    def _display_aspects(self, body_infos):
        longitudes = {name: info.get('Longitude') for name, info in body_infos.items()}
        
        aspects_found = []
        names = list(longitudes.keys())
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                name1, name2 = names[i], names[j]
                lon1, lon2 = longitudes[name1], longitudes[name2]
                if lon1 is None or lon2 is None: continue
                
                diff = abs((lon1 - lon2 + 180) % 360 - 180)
                for asp_name, (asp_angle, orb) in ASPECTS.items():
                    if abs(diff - asp_angle) <= orb:
                        aspects_found.append([
                            f"{name1}-{name2}", asp_name, f"{diff:.2f}°", f"{abs(diff - asp_angle):.2f}°"
                        ])
        
        if aspects_found:
            print("\n--- Aspectos Astrológicos (baseado em Longitude Eclíptica) ---")
            headers = ["Par", "Aspecto", "Separação Atual", "Orbe Restante"]
            self._print_table(aspects_found, headers)

    def _print_table(self, rows, headers):
        if not rows: return
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
        city_names = list(CITIES.keys())
        while True:
            print("\nEscolha a cidade (ou 0 para voltar):")
            for i, name in enumerate(city_names, 1): print(f"{i:2d}. {name}")
            
            choice = input("Sua escolha: ").strip()
            if choice == '0': return False

            try:
                idx = int(choice) - 1
                if 0 <= idx < len(city_names):
                    self.current_city_name = city_names[idx]
                    coords, self.tz_name = CITIES[self.current_city_name]
                    self.observer = Observer(coords[0], coords[1], 0.0)
                    print(f"Cidade selecionada: {self.current_city_name}")
                    return True
                else: print("Número inválido.")
            except ValueError: print("Por favor, insira um número.")

    def _run_calculations(self):
        if not self._ensure_location(): return

        body_names = list(BODIES.keys())
        print("\nEscolha os corpos (ex: 1,3,5), 'a' para todos, ou 0 para voltar:")
        for i, name in enumerate(body_names, 1): print(f"{i:2d}. {name}")

        choice = input("Sua escolha: ").strip().lower()
        if choice == '0': return
        
        chosen_bodies = []
        if choice == 'a':
            chosen_bodies = body_names
        else:
            try:
                indices = [int(i.strip()) - 1 for i in choice.split(',')]
                for idx in indices:
                    if 0 <= idx < len(body_names): chosen_bodies.append(body_names[idx])
                    else: print(f"Aviso: número {idx+1} é inválido.")
            except ValueError:
                print("Entrada inválida."); return

        if not chosen_bodies: print("Nenhum corpo selecionado."); return

        print("\nCalculando..."); now = Time.Now()
        body_infos = {name: self._compute_body_info(BODIES[name], now) for name in chosen_bodies}
        self._display_results(chosen_bodies, body_infos)
        
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
            
    def _search_lunar_apsis(self):
        print("\n--- Busca por Apogeu/Perigeu Lunar ---")
        try:
            current_apsis = SearchLunarApsis(Time.Now())
            while True:
                kind_str = "Perigeu (mais próxima)" if current_apsis.kind == ApsisKind.Pericenter else "Apogeu (mais distante)"
                print(f"\nPróximo evento: {kind_str}")
                print(f"  Data (local): {fmt_dt(to_local(current_apsis.time, self.tz_name))}")
                print(f"  Distância   : {fmt_num(current_apsis.dist_km, 0)} km")
                
                choice = input("\nBuscar próximo evento? (s/n): ").strip().lower()
                if choice in ['n', 'nao', 'não']: break
                current_apsis = NextLunarApsis(current_apsis)
        except Exception as e:
            print(f"Ocorreu um erro durante a busca: {e}")

    def _search_planet_apsis(self):
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
                kind_str = "Periélio (mais próximo do Sol)" if current_apsis.kind == ApsisKind.Pericenter else "Afélio (mais distante do Sol)"
                print(f"\nPróximo evento para {planet_name}: {kind_str}")
                print(f"  Data (UTC): {fmt_dt(current_apsis.time.Utc())}")
                print(f"  Distância : {fmt_num(current_apsis.dist_au, 4)} AU")

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

            if choice == '1': self._search_global_solar_eclipse()
            elif choice == '2': self._search_local_solar_eclipse()
            elif choice == '3': self._search_lunar_eclipse()
            elif choice == '0': break
            else: print("Opção inválida.")

    def _search_global_solar_eclipse(self):
        print("\nBuscando próximo eclipse solar global...")
        try:
            eclipse = SearchGlobalSolarEclipse(Time.Now())
            print(f"Tipo: {eclipse.kind.name}")
            print(f"Pico (UTC): {fmt_dt(eclipse.peak.Utc())}")
            if eclipse.kind in [EclipseKind.Total, EclipseKind.Annular]:
                print(f"Obscurecimento: {fmt_num(eclipse.obscuration * 100, 2)}%")
                print(f"Pico de visibilidade em: Latitude {fmt_num(eclipse.latitude, 4)}°, Longitude {fmt_num(eclipse.longitude, 4)}°")
        except Exception as e:
            print(f"Erro ao buscar eclipse: {e}")

    def _search_local_solar_eclipse(self):
        print(f"\nBuscando próximo eclipse solar visível em {self.current_city_name}...")
        try:
            eclipse = SearchLocalSolarEclipse(Time.Now(), self.observer)
            print(f"Tipo para o observador: {eclipse.kind.name}")
            print(f"Obscurecimento máximo: {fmt_num(eclipse.obscuration * 100, 2)}%")
            
            rows = [
                ["Início Parcial", fmt_dt(to_local(eclipse.partial_begin.time, self.tz_name)), f"{fmt_num(eclipse.partial_begin.altitude, 2)}°"],
                ["Pico do Eclipse", fmt_dt(to_local(eclipse.peak.time, self.tz_name)), f"{fmt_num(eclipse.peak.altitude, 2)}°"],
                ["Fim Parcial", fmt_dt(to_local(eclipse.partial_end.time, self.tz_name)), f"{fmt_num(eclipse.partial_end.altitude, 2)}°"],
            ]
            if eclipse.total_begin and eclipse.total_end:
                kind_str = "Total" if eclipse.kind == EclipseKind.Total else "Anular"
                rows.insert(1, [f"Início {kind_str}", fmt_dt(to_local(eclipse.total_begin.time, self.tz_name)), f"{fmt_num(eclipse.total_begin.altitude, 2)}°"])
                rows.insert(3, [f"Fim {kind_str}", fmt_dt(to_local(eclipse.total_end.time, self.tz_name)), f"{fmt_num(eclipse.total_end.altitude, 2)}°"])

            self._print_table(rows, ["Evento", "Horário Local", "Altitude do Sol"])
            print("Nota: Se a altitude do Sol for negativa, o evento ocorre abaixo do horizonte.")
        except Exception as e:
            print(f"Erro ao buscar eclipse local: {e}")

    def _search_lunar_eclipse(self):
        print("\nBuscando próximo eclipse lunar...")
        try:
            eclipse = SearchLunarEclipse(Time.Now())
            print(f"Tipo: {eclipse.kind.name}")
            print(f"Pico (UTC): {fmt_dt(eclipse.peak.Utc())}")
            print(f"Obscurecimento (Umbra): {fmt_num(eclipse.obscuration * 100, 2)}%")
            print("\nDuração das fases (início ao fim):")
            print(f"  Penumbral: {fmt_num(eclipse.sd_penum * 2, 1)} minutos")
            if eclipse.sd_partial > 0: print(f"  Parcial (Umbra): {fmt_num(eclipse.sd_partial * 2, 1)} minutos")
            if eclipse.sd_total > 0: print(f"  Total (Umbra): {fmt_num(eclipse.sd_total * 2, 1)} minutos")
        except Exception as e:
            print(f"Erro ao buscar eclipse: {e}")

    def _generate_aspect_calendar(self):
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
            body1, body2 = BODIES[name1], BODIES[name2]
            synodic_period = 30 # Default step
            try: # Estimate step time based on synodic period relative to Earth
                fast_body = body1 if astronomy.PlanetOrbitalPeriod(body1) < astronomy.PlanetOrbitalPeriod(body2) else body2
                synodic_period = abs(astronomy._SynodicPeriod(fast_body))
            except (astronomy.Error, KeyError): pass

            for aspect_name, (angle, _) in ASPECTS.items():
                if aspect_name == "Oposição" and (name1 in ["Mercury", "Venus"] or name2 in ["Mercury", "Venus"]): continue
                search_time = start_time
                while search_time.ut < end_time.ut:
                    # Search for the next time the relative longitude matches the aspect angle
                    search_window_days = max(2.0, synodic_period / 12)
                    t_next = search_time.AddDays(search_window_days)
                    if t_next.ut > end_time.ut: t_next = end_time
                    
                    context = (name1, name2, angle)
                    event_time = Search(aspect_search_func, context, search_time, t_next, 60) # 60s tolerance
                    
                    if event_time and search_time.ut <= event_time.ut < t_next.ut:
                        events.append((event_time, f"{name1} {aspect_name} {name2}"))
                        search_time = event_time.AddDays(1)
                    else:
                        search_time = t_next
        
        events.sort(key=lambda x: x[0].ut)
        print(f"\n--- Calendário de Aspectos para {year} ---")
        rows = [[fmt_dt(to_local(t, self.tz_name)), desc] for t, desc in events]
        if not rows:
            print("Nenhum aspecto maior encontrado para este ano.")
        else:
            self._print_table(rows, ["Data e Hora (Local)", "Evento"])

    def run(self):
        """Loop principal da aplicação."""
        while True:
            print("\n" + "="*20 + " Orrery Pro v3 " + "="*20)
            if self.current_city_name:
                print(f"Localização: {self.current_city_name} | Horário: {fmt_dt(to_local(Time.Now(), self.tz_name))}")
            else:
                print(f"Localização: Nenhuma selecionada | Horário: {fmt_dt(Time.Now().Utc())}")

            print("\n--- DADOS EM TEMPO REAL ---")
            print("1. Selecionar Cidade")
            print("2. Posições dos Astros")
            print("3. Luas de Júpiter")
            print("4. Libração da Lua")
            print("\n--- BUSCA DE EVENTOS ---")
            print("5. Ápsides Lunares (Apogeu/Perigeu)")
            print("6. Ápsides Planetários (Afélio/Periélio)")
            print("7. Eclipses")
            print("8. Calendário Anual de Aspectos")
            print("\n9. Sair")
            choice = input("Opção: ").strip()

            if choice == '1': self._choose_city()
            elif choice == '2': self._run_calculations()
            elif choice == '3': self._display_jupiter_moons()
            elif choice == '4': self._display_lunar_libration()
            elif choice == '5': self._search_lunar_apsis()
            elif choice == '6': self._search_planet_apsis()
            elif choice == '7': self._search_eclipses()
            elif choice == '8': self._generate_aspect_calendar()
            elif choice == '9':
                print("Obrigado por usar o Orrery Pro! Até a próxima.")
                break
            else:
                print("Opção inválida.")

# --- Ponto de Entrada ---
if __name__ == '__main__':
    cli_app = AstroCLI()
    cli_app.run()