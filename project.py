import requests

# ============================================================================
# PROGRAM FUNCTION:
# Asks user for their geographical location and in which directions
# are their windows situated in their home. The program then gives suggestion on combinations
# window openings for optimum airflow
#
#
# CORE IDEA: DEGREES -> SECTORS
# The wind API reports wind direction as a number from 0-360 degrees. The program
# doesn't need that precision - it chops the compass circle into 8 sectors of
# 45 degrees each (N, NE, E, ...) according to cardinal directions. Every window
# and every wind direction is then just an index 0-7 into this list.
# All logic runs on those small integers. Results are eventually displayed in a more readable format.
# ============================================================================

sectors = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
full_names = {
    "N": "NORTH",
    "NE": "NORTHEAST",
    "E": "EAST",
    "SE": "SOUTHEAST",
    "S": "SOUTH",
    "SW": "SOUTHWEST",
    "W": "WEST",
    "NW": "NORTHWEST",
}


# -----------------------------------------------------------------------------------------------------
# The Home class contains the instance of the user's home in which contains the cardinal directions of
# the user's home. Then it converts those cardinal direction to sectors from 0-7.
# The class rejects bad inputs.
# -----------------------------------------------------------------------------------------------------
class Home:
    def __init__(self, windows):
        self.windows = set(windows)
        if not self.windows <= set(sectors):
            raise ValueError("Invalid direction")
        if not self.windows:
            raise ValueError("Need at least one window")
        self.windows_idx = {sectors.index(w) for w in self.windows}


def main():
    lat, long = get_location()                                      # STEP 1: get user location - either input or geocoded
    city_name = get_city_name(lat, long)
    wind_direction, wind_speed = get_wind_direction(lat, long)      # STEP 2: Open-Meteo API returns wind direction in degrees
    wind_i = get_sector_index(wind_direction)                       # STEP 3: Retrieves the sector index of the wind direction
    sides = get_windows()                                           # STEP 4: Setup the user's home windows
                                                                    # STEP 5: Print the results
    print("+--------------------------------------------------------------------------------------------------------------+")
    print(f"                            --- City / Locality: {city_name} ---")
    print(f"Wind Direction: {wind_direction} Degrees. The winds are coming in from the {full_names[sectors[wind_i]]} at {wind_speed} km/h.")
    print(recommend_window(wind_i, sides))
    print("+--------------------------------------------------------------------------------------------------------------+")


# ----------------------------------------------------------------------------------------------------------
# Step 1a and 1b:
# Getting location based on 2 methods.
# First method is user's manual coordinate inputs. Inputs are checked to make sure they are within limits.
# Second method is the coordinates are generated from the geocoding API based on the user's city search.
# The function is repeated in a loop until valid inputs are registered.
# ----------------------------------------------------------------------------------------------------------
def get_location():
    while True:
        selection = input("Select '1' to input coordinates, '2' to search by city \nSelection: ")
        if selection == "1":
            print("Input the coordinates in decimal degrees format.")
            try:
                lat = float(input("Latitude: "))
                long = float(input("Longitude: "))
                if not (-90 <= lat <= 90 and -180 <= long <= 180):
                    raise ValueError("Invalid coordinates.")
                break
            except ValueError as e:
                print(e)
        elif selection == "2":
            try:
                lat, long = get_coordinates(input("City: "))
                break
            except ValueError as e:
                print(e)
        else:
            print("Please choose 1 or 2.")
    return lat, long


# --------------------------------------------------------------------------------------------------------
# Step 1b:
# Uses the user's search and tries to match with a city. If a city is matched, coordinates are returned.
# If no matches were found, user receives an error message stating the city could not be found
# is looped back to Step 1.
# --------------------------------------------------------------------------------------------------------
def get_coordinates(search):
    geo = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search", params={"name": search}, timeout=10
    )
    geos = geo.json()
    if not geos.get("results"):
        raise ValueError(f"City {search} not found.")
    count = len(geos["results"])
    if count > 1:
        for s in range(count):
            print(
                f'{s+1} for {geos["results"][s]["name"]}, {geos["results"][s]["admin1"]}, {geos["results"][s]["country"]}'
            )
        while True:
            try:
                user = int(input("Selection: "))
                if not 1 <= user <= count:
                    raise ValueError
                results = geos["results"][user - 1]
                break
            except ValueError:
                print(f"Please enter a number from 1 to {count}.")
    else:
        results = geos["results"][0]

    get_latitude = results["latitude"]
    get_longitude = results["longitude"]
    return get_latitude, get_longitude


# ----------------------------------------------------------------------------------------------------------
# Step 1c:
# Uses BIGDATACLOUD's API service to return the location of the city or locality name.
# Function uses lat/long  variables from the previous step.
# ----------------------------------------------------------------------------------------------------------
def get_city_name(lat, long):
    r = requests.get(
        "https://api.bigdatacloud.net/data/reverse-geocode-client",
        params={"latitude": lat, "longitude": long, "localityLanguage": "en"},
        timeout=10,
    )
    city = r.json().get("city") or r.json().get("locality")
    return city


# ---------------------------------------------------------------------------------------------------------
# Step 2:
# Given the coordinates of latitude and longitude, this function sends a request to Open-Meteo's API call.
# It returns the CURRENT wind direction at an elevation of 10 meters above surface and wind speed.
# ---------------------------------------------------------------------------------------------------------
def get_wind_direction(latitude, longitude):
    current = ["wind_direction_10m", "wind_speed_10m"]
    response = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={"latitude": latitude, "longitude": longitude, "current": current},
        timeout=20,
    )
    content = response.json()
    wind_direction = content["current"]["wind_direction_10m"]
    wind_speed = content["current"]["wind_speed_10m"]
    return wind_direction, wind_speed


# --------------------------------------------------------------------------------------------------------------------
# Step 3:
# Returns a number representing cardinal direction from 0 to 7 for N, NE, E, SE, S, SW, W, NW respectively.
# The function takes the wind direction as input, then is divided by 45 to represent the one of 8 cardinal positions.
# The modulo operator became very useful here as it helps with cycles. For example, a wind direction of 360 degrees
# gives a sector of 8. The % 8 snaps it back to 0 which equals North.
# --------------------------------------------------------------------------------------------------------------------
def get_sector_index(wind):
    return round(wind / 45) % 8


# -------------------------------------------------------------------------------------------------------
# Step 4:
# Creates an instance of the user's home. User specifies for which of the 8 cardinal directions they have
# a window available. User's input can be from the example printed on the screen.
# If errors occur, prompts the user the same question again.
# ---------------------------------------------------------------------------------------------------------
def get_windows():
    while True:
        try:
            windows = input(
                "Which directions do your windows face? \nType all that apply from (N, NE, E, SE, S, SW, W, NW) separated by commas.\nWindows: "
            )
            sides = {s.strip().upper() for s in windows.split(",")}
            return Home(sides)
        except ValueError:
            print("Invalid window(s). Try again.\n")

# ---------------------------------------------------------------------------------------------------------
# Step 5:
# Given all the data inputs, this function returns the recommended combinations of windows to open based
# on the current wind direction for optimum natural air flow through the home.
# The ratings dictionary is used to rate each available window by its circular distance from the wind.
# The more the window is facing the wind, the better. Distance 0 = faces the wind head on, distance 4 is
# complete opposite. In each for loop, two distances are measured and the lowest is grouped by distances.
# ----------------------------------------------------------------------------------------------------------
def recommend_window(wind, sides):
    ratings = {}
    for s in sides.windows_idx:
        match = min((wind - s) % 8, (s - wind) % 8)
        ratings.setdefault(match, []).append(sectors[s])

    # ---------------------------------------------------------------------------------------------------------
    # Step 6:
    # Based on the distances, windows at distances 0-1, where air pushes in, are assigned the inlets variable.
    # Windows at distances 3-4 are assigned outlets variable as they are used for exhausting the air.
    # Windows at distance 2 are unassigned as they are perpendicular to the wind direction and therefore offer
    # little effect on airflow.
    # ---------------------------------------------------------------------------------------------------------
    inlets = ratings.get(0, []) + ratings.get(1, [])
    outlets = ratings.get(3, []) + ratings.get(4, [])

    # ---------------------------------------------------------------------------------------------------------
    # Step 7:
    # The final piece of the program returns strings to be printed. There are four conditionals based on the
    # layout of the windows and the airflow. The optimum airflow is when inlets and outlets are available in line
    # with wind direction. If suboptimal conditions are present, the program advises the user of the suboptimal
    # conditions at the present time. Indicating to try at a later time.
    # ----------------------------------------------------------------------------------------------------------
    if inlets and outlets:
        return f"Open the {convert(inlets)} facing window(s) to let air in, and open the {convert(outlets)} window(s) for the air to flow out."
    elif inlets:
        return f"Open the {convert(inlets)} facing windows - air will come in, but with no opposite window, airflow will be weak."
    elif outlets:
        return f"Windows on the {convert(outlets)} are sheltered from wind direction. Expect little airflow currently."
    else:
        return "All windows sit perpendicular to the wind - minimal natural ventilation right now"

# -----------------------------------------------------------------------------------------------------
# Step 7a:
# Output helper to make the final notes more legible.
# Converts ["N", "NW"] to "NORTH and NORTHWEST"
# -----------------------------------------------------------------------------------------------------
def convert(windows):
    return " and ".join(full_names[w] for w in windows)


if __name__ == "__main__":
    main()
