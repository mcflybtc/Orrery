import sys
from datetime import datetime
from astronomy import *

def display_planet_position(body: Body, time: Time):
    """Display the position of a planet at a given time."""
    vec = HelioVector(body, time)
    dist = vec.Length()
    print(f"\nPosition of {body.name} at {time}")
    print(f"Heliocentric coordinates (AU):")
    print(f"  X = {vec.x:+.8f}")
    print(f"  Y = {vec.y:+.8f}")
    print(f"  Z = {vec.z:+.8f}")
    print(f"Distance from Sun: {dist:.8f} AU")

def display_moon_phase(time: Time):
    """Display the current moon phase."""
    phase = MoonPhase(time)
    index = int((phase / 360 * 28) + 0.5) % 28
    phase_name = [
        "New Moon", "Waxing Crescent", "First Quarter", "Waxing Gibbous",
        "Full Moon", "Waning Gibbous", "Last Quarter", "Waning Crescent"
    ][int(phase / 45) % 8]
    
    print(f"\nMoon Phase at {time}")
    print(f"Phase angle: {phase:.2f}°")
    print(f"Phase name: {phase_name}")
    print("Appearance: " + ("🌑🌒🌓🌔🌕🌖🌗🌘"[int(phase / 45) % 8]))

def display_sun_moon_info(time: Time, observer: Observer):
    """Display sun and moon information for an observer."""
    # Sun rise/set times
    sunrise = SearchRiseSet(Body.Sun, observer, +1, time, 300.0)
    sunset = SearchRiseSet(Body.Sun, observer, -1, time, 300.0)
    
    # Moon rise/set times
    moonrise = SearchRiseSet(Body.Moon, observer, +1, time, 300.0)
    moonset = SearchRiseSet(Body.Moon, observer, -1, time, 300.0)
    
    print(f"\nSun and Moon Information for Observer at {observer}")
    print(f"Sunrise: {sunrise if sunrise else 'No sunrise today'}")
    print(f"Sunset:  {sunset if sunset else 'No sunset today'}")
    print(f"Moonrise: {moonrise if moonrise else 'No moonrise today'}")
    print(f"Moonset:  {moonset if moonset else 'No moonset today'}")
    
    # Current altitude/azimuth
    eq_sun = Equator(Body.Sun, time, observer, True, True)
    hor_sun = Horizon(time, observer, eq_sun.ra, eq_sun.dec)
    
    eq_moon = Equator(Body.Moon, time, observer, True, True)
    hor_moon = Horizon(time, observer, eq_moon.ra, eq_moon.dec)
    
    print("\nCurrent positions:")
    print(f"Sun:  Altitude={hor_sun.altitude:6.2f}°, Azimuth={hor_sun.azimuth:6.2f}°")
    print(f"Moon: Altitude={hor_moon.altitude:6.2f}°, Azimuth={hor_moon.azimuth:6.2f}°")

def display_planet_info():
    """Display information about all planets."""
    print("\nPlanetary Information:")
    print("Body       Mass (GM au³/day²)  Orbital Period (days)  Synodic Period (days)")
    print("--------  -------------------  ---------------------  ---------------------")
    
    for body in [Body.Mercury, Body.Venus, Body.Earth, Body.Mars, 
                 Body.Jupiter, Body.Saturn, Body.Uranus, Body.Neptune]:
        gm = MassProduct(body)
        period = PlanetOrbitalPeriod(body)
        synodic = _SynodicPeriod(body) if body != Body.Earth else float('nan')
        print(f"{body.name:8}  {gm:19.6e}  {period:21.2f}  {synodic:20.2f}")

def main():
    print("Astronomy Calculator")
    print("-------------------")
    
    # Get current time or user-specified time
    now = Time.Now()
    time_str = input(f"Enter date/time [YYYY-MM-DDThh:mm:ssZ] or blank for now ({now}): ").strip()
    
    if time_str:
        try:
            time = Time.Parse(time_str)
        except DateTimeFormatError:
            print("Invalid date/time format. Using current time.")
            time = now
    else:
        time = now
    
    # Get observer location (optional)
    use_observer = input("Use specific observer location? [y/N]: ").lower() == 'y'
    observer = None
    
    if use_observer:
        try:
            lat = float(input("Enter latitude (degrees): "))
            lon = float(input("Enter longitude (degrees): "))
            height = float(input("Enter height above sea level (meters) [0]: ") or "0")
            observer = Observer(lat, lon, height)
        except ValueError:
            print("Invalid number format. Using default observer.")
            observer = Observer(0, 0, 0)
    
    while True:
        print("\nMain Menu:")
        print("1. Planet Positions")
        print("2. Moon Phase")
        print("3. Sun/Moon Info for Observer")
        print("4. Planetary Data")
        print("5. Change Time")
        print("6. Change Observer")
        print("0. Exit")
        
        choice = input("Select option: ").strip()
        
        if choice == '0':
            print("Goodbye!")
            break
            
        elif choice == '1':
            print("\nSelect Planet:")
            for i, body in enumerate([Body.Mercury, Body.Venus, Body.Mars, 
                                     Body.Jupiter, Body.Saturn, Body.Uranus, Body.Neptune], 1):
                print(f"{i}. {body.name}")
            print("8. Earth")
            print("9. Pluto")
            
            planet_choice = input("Select planet (1-9): ").strip()
            try:
                index = int(planet_choice) - 1
                if 0 <= index < 7:
                    body = [Body.Mercury, Body.Venus, Body.Mars, 
                            Body.Jupiter, Body.Saturn, Body.Uranus, Body.Neptune][index]
                elif index == 7:
                    body = Body.Earth
                elif index == 8:
                    body = Body.Pluto
                else:
                    raise ValueError
                display_planet_position(body, time)
            except (ValueError, IndexError):
                print("Invalid selection")
                
        elif choice == '2':
            display_moon_phase(time)
            
        elif choice == '3':
            if observer is None:
                print("No observer location set. Using default (0,0,0).")
                observer = Observer(0, 0, 0)
            display_sun_moon_info(time, observer)
            
        elif choice == '4':
            display_planet_info()
            
        elif choice == '5':
            time_str = input(f"Enter new date/time [YYYY-MM-DDThh:mm:ssZ] ({time}): ").strip()
            if time_str:
                try:
                    time = Time.Parse(time_str)
                except DateTimeFormatError:
                    print("Invalid date/time format. Keeping current time.")
                    
        elif choice == '6':
            if observer is None:
                observer = Observer(0, 0, 0)
            try:
                lat = float(input(f"Enter latitude (degrees) [{observer.latitude}]: ") or str(observer.latitude))
                lon = float(input(f"Enter longitude (degrees) [{observer.longitude}]: ") or str(observer.longitude))
                height = float(input(f"Enter height (meters) [{observer.height}]: ") or str(observer.height))
                observer = Observer(lat, lon, height)
            except ValueError:
                print("Invalid number format. Keeping current observer.")
                
        else:
            print("Invalid option. Please try again.")

if __name__ == "__main__":
    main()