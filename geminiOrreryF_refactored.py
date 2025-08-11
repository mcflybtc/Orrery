# geminiOrreryF_refactored.py
import math
import sys
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

# Importações da biblioteca de astronomia
from astronomy import (
    Body, Observer, Time, Direction, Refraction, ApsisKind, EclipseKind, Visibility,
    Equator, Horizon, GeoVector, Ecliptic, Illumination, Constellation,
    JupiterMoons, Libration, PairLongitude, DefineStar, PlanetOrbitalPeriod, Seasons,
    SearchRiseSet, SearchHourAngle, SearchLunarApsis,
    SearchPlanetApsis, SearchLunarEclipse, SearchGlobalSolarEclipse, SearchLocalSolarEclipse,
    SearchMoonQuarter, Search, SearchMoonNode, SearchMaxElongation, SearchTransit, Error as AstronomyError
)

# --- Configurações Globais (mesmas do seu script original) ---
CITIES = {
    "Amsterdam, Netherlands": ((52.3676, 4.9041), "Europe/Amsterdam"),
    # ... (cole aqui o resto do seu dicionário CITIES)
    "Toronto, Canada": ((43.6532, -79.3832), "America/Toronto"),
}

BODIES = { "Sun": Body.Sun, "Moon": Body.Moon, "Mercury": Body.Mercury, "Venus": Body.Venus, "Mars": Body.Mars, "Jupiter": Body.Jupiter, "Saturn": Body.Saturn, "Uranus": Body.Uranus, "Neptune": Body.Neptune, "Pluto": Body.Pluto }
STARS_DATA = [("Sirius", 6.7525, -16.7161), ("Canopus", 6.3992, -52.6957), ("Rigil Kentaurus", 14.6601, -60.8356), ("Arcturus", 14.2610, 19.1825), ("Vega", 18.6156, 38.7837), ("Capella", 5.2782, 45.9980), ("Rigel", 5.2423, -8.2016), ("Procyon", 7.6550, 5.2250)]
STARS = {star[0]: Body(Body.Star1.value + i) for i, star in enumerate(STARS_DATA)}
SIGNS = ["Áries", "Touro", "Gêmeos", "Câncer", "Leão", "Virgem", "Libra", "Escorpião", "Sagitário", "Capricórnio", "Aquário", "Peixes"]
ASPECTS = {"Conjunção": (0.0, 8.0), "Oposição": (180.0, 8.0), "Quadratura": (90.0, 6.0), "Trígono": (120.0, 6.0), "Sextil": (60.0, 4.0)}
PLANETS_FOR_ASPECTS = ["Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]


class AstroCLI:
    """
    Backend de lógica para a aplicação Orrery Pro.
    Contém todos os métodos de cálculo astronômico, refatorados para retornar
    strings ou dados, em vez de interagir com o console.
    """
    def __init__(self):
        self.current_city_name = None
        self.observer = None
        self.tz_info = None
        self.search_time = Time.Now()
        self._initialize_stars()
        
        # Adiciona o método from_datetime à classe Time se ele não existir
        if not hasattr(Time, 'from_datetime'):
            def from_datetime(dt):
                if dt.tzinfo is None:
                    raise ValueError("datetime object must be timezone-aware.")
                dt_utc = dt.astimezone(timezone.utc)
                return Time.Make(dt_utc.year, dt_utc.month, dt_utc.day, dt_utc.hour, dt_utc.minute, dt_utc.second + dt_utc.microsecond / 1_000_000.0)
            Time.from_datetime = staticmethod(from_datetime)

    # --- Funções Auxiliares (mantidas do original) ---
    def _initialize_stars(self):
        for name, body_enum in STARS.items():
            star_data = next((s for s in STARS_DATA if s[0] == name), None)
            if star_data:
                DefineStar(body_enum, star_data[1], star_data[2], 1000)

    def fmt_num(self, x, nd=2):
        if x is None: return "—"
        if isinstance(x, float): return f"{x:.{nd}f}"
        return str(x)

    def to_local(self, t, tz_info):
        if t is None or tz_info is None: return None
        try:
            return t.Utc().astimezone(tz_info)
        except Exception: return None

    def fmt_dt(self, dt):
        if dt is None: return "—"
        return dt.strftime("%Y-%m-%d %H:%M:%S %Z")

    def get_constellation(self, body, time):
        try:
            eq = Equator(body, time, self.observer, True, False)
            const_info = Constellation(eq.ra, eq.dec)
            return f"{const_info.name} ({const_info.symbol})"
        except Exception: return "N/A"
    
    # ... (cole aqui as outras funções auxiliares: signo_tropical, get_cardinal_direction, etc.)

    # --- Métodos Refatorados para a GUI ---

    def set_city(self, city_name):
        """Define a cidade e o observador. Retorna (sucesso, mensagem)."""
        try:
            coords, tz_iana_name = CITIES[city_name]
            tz_object = ZoneInfo(tz_iana_name)
            self.current_city_name = city_name
            self.tz_info = tz_object
            self.observer = Observer(coords[0], coords[1], 0.0)
            return (True, f"Cidade '{city_name}' selecionada com sucesso.")
        except ZoneInfoNotFoundError:
            msg = f"O fuso horário '{tz_iana_name}' não foi encontrado. Instale o 'tzdata' com: pip install tzdata"
            return (False, msg)
        except Exception as e:
            return (False, f"Erro inesperado: {e}")

    def get_search_time_str(self):
        """Retorna a data de busca atual como uma string formatada."""
        if not self.tz_info: return "Nenhum fuso horário definido"
        local_dt = self.to_local(self.search_time, self.tz_info)
        return self.fmt_dt(local_dt)

    def set_search_time_from_str(self, date_str):
        """Define a data de busca a partir de uma string. Retorna (sucesso, mensagem)."""
        if not self.tz_info:
            return (False, "Selecione uma cidade primeiro.")
        try:
            if date_str:
                user_date = datetime.strptime(date_str, "%Y-%m-%d")
                local_time = datetime(user_date.year, user_date.month, user_date.day, 0, 0, 0, tzinfo=self.tz_info)
                self.search_time = Time.from_datetime(local_time)
            else:
                self.search_time = Time.Now()
            return (True, f"Nova data de busca definida para: {self.get_search_time_str()}")
        except ValueError:
            return (False, "Formato de data inválido. Use AAAA-MM-DD.")
        except Exception as e:
            return (False, f"Ocorreu um erro: {e}")
    
    def _print_table(self, rows, headers):
        """Formata uma lista de listas em uma tabela de texto. Retorna uma string."""
        if not rows:
            return "Nenhuma informação para exibir."
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(cell)))
        
        header_line = " | ".join(headers[i].ljust(col_widths[i]) for i in range(len(headers)))
        separator = "-+-".join("-" * w for w in col_widths)
        
        lines = [header_line, separator]
        for row in rows:
            row_line = " | ".join(str(row[i]).ljust(col_widths[i]) for i in range(len(row)))
            lines.append(row_line)
        return "\n".join(lines)

    def calculate_positions_string(self, choice_str):
        """Lógica de _run_calculations, mas retorna uma string e um erro (se houver)."""
        try:
            # Lógica de seleção de corpos (adaptada do original)
            all_bodies = {**BODIES, **STARS}
            body_names = list(BODIES.keys()) + list(STARS.keys())
            chosen_names = []
            choice = choice_str.lower().strip()
            
            if choice == 'a': chosen_names = body_names
            elif choice == 'p': chosen_names = list(BODIES.keys())
            elif choice == 'e': chosen_names = list(STARS.keys())
            else:
                indices = [int(i.strip()) - 1 for i in choice.split(',')]
                for idx in indices:
                    if 0 <= idx < len(body_names): chosen_names.append(body_names[idx])
            
            if not chosen_names: return "Nenhum corpo válido selecionado.", None

            # Lógica de cálculo (adaptada do original)
            now = Time.Now()
            body_infos = {name: self._compute_body_info(name, all_bodies[name], now) for name in chosen_names}
            
            # Construção da string de saída
            output = ""
            output += "--- Posição Aparente Agora ---\n"
            # ... (Continue a lógica de _run_calculations, usando self._print_table e concatenando em 'output')
            # Exemplo para a primeira tabela:
            headers1 = ["Corpo", "Altitude", "Direção", "Constelação"]
            rows1 = []
            for name in chosen_names:
                info = body_infos.get(name, {})
                rows1.append([name, f"{self.fmt_num(info.get('Altitude'), 2)}°", "N/A", self.get_constellation(all_bodies[name], now)])
            output += self._print_table(rows1, headers1) + "\n\n"
            
            # ... adicione as outras tabelas da mesma forma ...

            return output, None
        except Exception as e:
            return "", f"Erro no cálculo: {e}"

    def _compute_body_info(self, name, body, time):
        # Este método auxiliar é chamado por outros, mantê-lo como está
        info = {}
        # ... (cole o corpo do seu método _compute_body_info original aqui) ...
        try:
            eq = Equator(body, time, self.observer, True, True)
            hor = Horizon(time, self.observer, eq.ra, eq.dec, Refraction.Normal)
            info['Altitude'] = hor.altitude
            info['Azimute'] = hor.azimuth
        except AstronomyError:
            info['Altitude'] = None
            info['Azimute'] = None
        return info


    def get_jupiter_moons_string(self):
        """Retorna uma string formatada com as posições das luas de Júpiter."""
        try:
            now = Time.Now()
            jupiter_eq = Equator(Body.Jupiter, now, self.observer, True, True)
            moons_info = JupiterMoons(now)
            moon_data = {"Io": moons_info.io, "Europa": moons_info.europa, "Ganimedes": moons_info.ganymede, "Calisto": moons_info.callisto}
            rows = []
            for name, moon_state in moon_data.items():
                moon_geocentric_vec = jupiter_eq.vec + moon_state.Position()
                moon_eq_coords = Equator.from_vector(moon_geocentric_vec)
                hor = Horizon(now, self.observer, moon_eq_coords.ra, moon_eq_coords.dec, Refraction.Normal)
                rows.append([name, f"{self.fmt_num(hor.altitude, 2)}°", "N/A"]) # Direção omitida para simplicidade
            
            header = f"Posições das Luas de Júpiter em {self.current_city_name}\n"
            table = self._print_table(rows, ["Lua", "Altitude", "Direção"])
            return header + table, None
        except Exception as e:
            return "", str(e)

    def find_next_lunar_apsis(self):
        """Encontra e formata o próximo apogeu/perigeu."""
        try:
            current_apsis = SearchLunarApsis(self.search_time)
            kind_str = "Perigeu (mais próxima)" if current_apsis.kind == ApsisKind.Pericenter else "Apogeu (mais distante)"
            const = self.get_constellation(Body.Moon, current_apsis.time)
            
            output = (
                f"Próximo evento: {kind_str}\n"
                f"  Data (local): {self.fmt_dt(self.to_local(current_apsis.time, self.tz_info))}\n"
                f"  Distância   : {self.fmt_num(current_apsis.dist_km, 0)} km\n"
                f"  Constelação : {const}"
            )
            # Atualiza o tempo de busca para o próximo evento
            self.search_time = current_apsis.time.AddDays(1)
            return output, None
        except Exception as e:
            return "", str(e)

    def find_next_eclipse(self, mode):
        """Encontra o próximo eclipse baseado no modo ('solar_global', 'solar_local', 'lunar')."""
        try:
            output = ""
            if mode == "solar_global":
                eclipse = SearchGlobalSolarEclipse(self.search_time)
                self.search_time = eclipse.peak.AddDays(1)
                const = self.get_constellation(Body.Sun, eclipse.peak)
                output = f"Eclipse Solar Global: {eclipse.kind.name} em {const}\nPico (UTC): {self.fmt_dt(eclipse.peak.Utc())}"
            elif mode == "solar_local":
                eclipse = SearchLocalSolarEclipse(self.search_time, self.observer)
                self.search_time = eclipse.peak.time.AddDays(1)
                const = self.get_constellation(Body.Sun, eclipse.peak.time)
                output = f"Eclipse Solar em {self.current_city_name}: {eclipse.kind.name} em {const}\nObscurecimento: {self.fmt_num(eclipse.obscuration * 100, 2)}%\nPico (local): {self.fmt_dt(self.to_local(eclipse.peak.time, self.tz_info))}"
            elif mode == "lunar":
                eclipse = SearchLunarEclipse(self.search_time)
                self.search_time = eclipse.peak.AddDays(1)
                const = self.get_constellation(Body.Moon, eclipse.peak)
                output = f"Eclipse Lunar: {eclipse.kind.name} em {const}\nPico (UTC): {self.fmt_dt(eclipse.peak.Utc())}"

            return output, None
        except AstronomyError:
            return f"Não foi possível encontrar o próximo eclipse ({mode}) a partir da data de busca.", None
        except Exception as e:
            return "", str(e)

# ... continue a refatoração para as outras funções da mesma maneira ...