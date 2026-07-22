![Windrose Logo](windrose_logo_dark.png)
# Windrose
### _Ventilation Airflow Advisor_
#### <ins>Video Demo</ins>: https://youtu.be/OluDKioaCnY

Created by: **Omar Fishir**

## Installation
Requires an internet connection as the program calls live weather APIs

```bash
pip install -r requirements.txt
```

## Program Description
Windrose is a program for which its function is to provide the user with advice on which windows to open to achieve
optimum airflow ventilation. The program receives the user's location and cardinal orientation as inputs from the
user and uses that with information received from Open-Meteo's wind information to provide the user with advice
on which windows to use to achieve the most optimum ventilation. An example of the results:
```
+--------------------------------------------------------------------------------------------------------------+
                            --- City / Locality: Makkah ---
Wind Direction: 346 Degrees. The winds are coming in from the NORTH at 10.0 km/h.
Open the NORTH facing window(s) to let air in, and open the SOUTH windows for the air to flow out.
+--------------------------------------------------------------------------------------------------------------+
```

## How it works

### Step 1: Getting the user's location
The user provides the location for which they seek advice on, usually their home.
The user is given an option to either input the latitude and longitude coordinates manually,
```
Select '1' to input coordinates, '2' to search by city
Selection: 1
Input the coordinates in decimal degrees format.
Latitude: 21.422412
Longitude: 39.826026
```
or you can search by entering a city name.
```
Select '1' to input coordinates, '2' to search by city
Selection: 2
City: Springfield
```

If the user chooses to input his own coordinates, then those inputs are stored in variables `lat` and `long`.
If the user chooses to search for the city, their input is fed to a function called `get_coordinates`.
This function takes the user's city search input and feeds it in the parameters in the API call
from Open-Meteo. Open-Meteo is a website that provides extensive weather information. The function
then parses the json file retrieved. If there is only 1 city match, the longitude and latitude coordinates are
returned. However, if there are more than one match, the program will ask the user to specify.

Since there are many cities named springfield, the program will ask you to specify which one.
```
Select '1' to input coordinates, '2' to search by city
Selection: 2
City: Springfield
1 for Springfield, Missouri, United States
2 for Springfield, Illinois, United States
3 for Springfield, Massachusetts, United States
4 for Springfield, Ohio, United States
5 for Springfield, Tennessee, United States
6 for Palmyra, Missouri, United States
7 for Jackson, Minnesota, United States
8 for Springfield, Kentucky, United States
9 for Springfield, Georgia, United States
10 for Springfield, Colorado, United States
Selection:
```
Using the user's selection, the program finds the correct latitude and longitude coordinates and sends them
back to main.

main uses those coordinates to call a function to retrieve the city name
`city_name = get_city_name(lat, long)`

Since Open-Meteo didn't have the option to return a city name based on coordinates, I used BigDataCloud.
This function uses the latitude and longitude coordinates to return a city name. If coordinates are
not within a general vicinity of an area, it'll return the locality of the area.
*Using this function to retrieve the name of city might be redundant after the city search, but I*
*wanted to get the city name for users who input coordinates themselves. Will revise in future version.*

>[!TIP]
>Use exact coordinates of your location for more accurate results.

### Step 2: Getting wind direction
Main calls the function `get_wind_direction` with latitude and longitude coordinates passed.
The function uses another Open-Meteo API to retrieve current wind direction and wind speed
for the location provided via the coordinates.
```python
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
```
`wind_direction` and `wind_speed` are returned back to main.

### Step 3: Retrieves sector index of wind
**CORE IDEA**\
**Degrees -> Sectors**\
Open-Meteo's API request returns a radial direction from 0-360 degrees. The program does
not need that precision. I decided to divide the compass circle into 8 sectors of 45 degrees
each. N, NE, E, SE, S, SW, W, NW according to the cardinal directions. Each direction is then
indexed to a figure between 0-7 where "N" is 0, "NE" is 1, "E" is 2, and so on.

A simple function is used here.

```python
def get_sector_index(wind):
    return round(wind / 45) % 8
```
the function takes in the wind direction, divides the direction by 45 representing the 8 sectors,
then rounds to the nearest whole number so every number snaps to a sector. After that, the modulo 8 operator
is used to snap any results of 8 back to 0 to represent north.
For example, 359 degrees / 45 = 7.97. Rounded would be 8. Modulo 8 snaps it back to 0.
Making only possible inputs of 0-7 to represent 8 cardinal directions.
The function returns an integer that represents the cardinal direction the wind is blowing from.

### Step 4: Build the user's home
Uses the `get_windows` function to retrieve and build an instance of the user's windows layout.
The function prompts the user to input the cardinal direction their windows face. With the user's input,
the function instantiates a home with their specified windows.
```python
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
```

The "Home" class instantiates a user's home windows layout.
```python
class Home:
    def __init__(self, windows):
        self.windows = set(windows)
        if not self.windows <= set(sectors):
            raise ValueError("Invalid direction")
        if not self.windows:
            raise ValueError("Need at least one window")
        self.windows_idx = {sectors.index(w) for w in self.windows}
```
The class verifies the users input against a list of cardinal directions. If there is an error,
the user is reprompted. After, the class assigns sector values to those windows under `self.windows_idx`

### Step 5: The Engine
Given all the data inputs, `recommend_window(wind, sides)` takes the wind sector and the windows sectors
and rates each window based on the radial distance to the wind.

```python
def recommend_window(wind, sides):
    ratings = {}
    for s in sides.windows_idx:
        match = min((wind - s) % 8, (s - wind) % 8)
        ratings.setdefault(match, []).append(sectors[s])
```

This is probably the coolest part of the program and the part I'm most proud of. An ideal window
would be a window directly facing the wind. So wind from the NORTH(Sector 0) and a NORTH(Sector 0)
facing window would achieve optimum airflow intake.

So we take the difference between wind direction and direction of the window.

wind direction (North) 0 minus window direction (North) 0 = Distance 0
wind direction (South) 4 minus window direction (North) 0 = Distance 4

Therefore we can surmise a distance scoring spectrum [0, 1, 2, 3, 4]
where 0 is best for air intake and 4 is the worst. From this as well, we can infer that while 4
would be worst for air inlets, it'd be best for air outlets. So, from this distance spectrum,
we can calculate best windows for air inlets and best windows for air outlets.

*However*,
> 7(NW) wind - 0(N) window = 7 distance
> 0(N) window - 7(NW) wind = -7 distance

A user who has a window situated North (Sector 0) and wind coming in from
the NORTHWEST (Sector 7) would get a distance score of -7. The distance of the user's
window is near the incoming wind but the distance score is far from 0.
This is where I discovered how powerful the modulo % operator can be.

> 0(N) window -7(NW) wind = -7 distance
> -7 % 8 = 1 distance

The modulo operator is so useful in arrays that cycle back to a set point. In order to
get the remainder of a negative number, the modulo 8 has to decrease to become less
than -7. It becomes less than -7 at -8. The remainder is +1, which is the
sector distance difference between NORTH and NORTHWEST. It's such a powerful tool.
I first used modulo in a previous project with 12hr/24hr time format to get 12:00a.m. to
snap back to 00:00. However, even then I didn't realize how powerful and clever it is.
```python
match = min((wind - s) % 8, (s - wind) % 8)
```
Since we are dealing with circular distances, this formula does the equation in both
possibilities and stores the lower number to `match` as the distance score.

### Step 6: Inlets and outlets
```python
    inlets = ratings.get(0, []) + ratings.get(1, [])
    outlets = ratings.get(3, []) + ratings.get(4, [])
```
Based on the distances, windows at distances 0-1, where air pushes in, are assigned the inlets variable.
Windows at distances 3-4 are assigned outlets variable as they are used for exhausting the air.
Windows at distance 2 are unassigned as they are perpendicular to the wind direction and therefore offer
little effect on airflow.

### Step 7: Print the results.
```python
    if inlets and outlets:
        return f"Open the {convert(inlets)} facing window(s) to let air in, and open the {convert(outlets)} windows for the air to flow out."
    elif inlets:
        return f"Open the {convert(inlets)} facing windows - air will come in, but with no opposite window, airflow will be weak."
    elif outlets:
        return f"Windows on the {convert(outlets)} are sheltered from wind direction. Expect little airflow currently."
    else:
        return "All windows sit perpendicular to the wind - minimal natural ventilation right now"
```
The final piece of the program returns strings to be printed. There are four conditionals based on the
layout of the windows and the airflow. The optimum airflow is when inlets and outlets are available in line
with wind direction. If suboptimal conditions are present, the program advises the user of the suboptimal
conditions at the present time. Indicating to try at a later time.

### Design decision for `recommend_window()`
Using API of constantly changing wind data, I only had 3 testable functions.
One of the testable functions was get_coordinates. However, when I discovered the issue when a user searches for a city with a common name,
the user was just given the first result. I had to extract the different
possibilities of selections and prompt the user to select the correct
city. That extra input made the function untestable.
Meanwhile, `recommend_window` was a function inside the Home class. I ended up removing it from there and implementing it outside to satisfy the requirements for tests. I had to do quite a few changes but it
worked out better in the end.

### Guards
Every input path (menu selection, coordinates, city search, window list) validates and re-prompts
on bad input rather than crashing. In addition, all three API calls carry timeouts to avoid hanging requests.

### Files:
- project.py -> the full program: A Home class, a main and 8 other functions as described above.
- test_project.py -> pytest tests for `get_sector_index`, `convert`, `recommend_window` and the `Home` class.
- requirements.txt -> A single third-party dependency, "requests"

### Future Versions
This program has the potential to be much better and more useful. Plans for future development:

**V2:** Once the program makes a recommendation, it creates a PDF with a visual diagram of the user's window selections, wind flow inlets and outlets, and a **ventilation score** based on optimum inlet/outlet and wind speed.

**V3:** Host the program on a website to be more accessible.

**V4:** Animated airflow visualizations against complex floorplans and multiple windows.
