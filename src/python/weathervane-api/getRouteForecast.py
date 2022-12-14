#!/usr/bin/env python3

import os
import logging
import requests
import datetime
import usaddress
import googlemaps
import dateutil.parser

API_KEY = os.getenv('WEATHER_API_KEY')
logging.basicConfig(level=logging.INFO)

"""
- getRouteForecast -
Outputs the series of different forecasts to be experienced along the drive.
the route parameter is taken from the getDirections function dictionary result

Weather Vane Application
Course: CMSC495
Group 1
"""
#       State to abbreviation dictionary
us_state_to_abbrev = {
        "Alabama": "AL",
        "Alaska": "AK",
        "Arizona": "AZ",
        "Arkansas": "AR",
        "California": "CA",
        "Colorado": "CO",
        "Connecticut": "CT",
        "Delaware": "DE",
        "Florida": "FL",
        "Georgia": "GA",
        "Hawaii": "HI",
        "Idaho": "ID",
        "Illinois": "IL",
        "Indiana": "IN",
        "Iowa": "IA",
        "Kansas": "KS",
        "Kentucky": "KY",
        "Louisiana": "LA",
        "Maine": "ME",
        "Maryland": "MD",
        "Massachusetts": "MA",
        "Michigan": "MI",
        "Minnesota": "MN",
        "Mississippi": "MS",
        "Missouri": "MO",
        "Montana": "MT",
        "Nebraska": "NE",
        "Nevada": "NV",
        "New Hampshire": "NH",
        "New Jersey": "NJ",
        "New Mexico": "NM",
        "New York": "NY",
        "North Carolina": "NC",
        "North Dakota": "ND",
        "Ohio": "OH",
        "Oklahoma": "OK",
        "Oregon": "OR",
        "Pennsylvania": "PA",
        "Rhode Island": "RI",
        "South Carolina": "SC",
        "South Dakota": "SD",
        "Tennessee": "TN",
        "Texas": "TX",
        "Utah": "UT",
        "Vermont": "VT",
        "Virginia": "VA",
        "Washington": "WA",
        "West Virginia": "WV",
        "Wisconsin": "WI",
        "Wyoming": "WY",
        "District of Columbia": "DC",
        "American Samoa": "AS",
        "Guam": "GU",
        "Northern Mariana Islands": "MP",
        "Puerto Rico": "PR",
        "United States Minor Outlying Islands": "UM",
        "U.S. Virgin Islands": "VI",
}

def kelvinToFahrenheit(k):
    """
    Converts Kelvin to Fahrenheit

    k: temperature in Kelvin
    """
    return k * 1.8 - 459.67

def getNearestDate(weatherData, date):
    """
    Get weather conditions of time closest to date

    weatherData: dictionary containing weather data of interest
    date: date used to find beginning of data

    Returns dictionary of weather data for approximate date
    """
    temp = {}
    temp_time_diff = datetime.timedelta(days=1)
    for item in weatherData['list']:
        timestamp = item['dt']
        date_compare = datetime.datetime.fromtimestamp(timestamp)
        
        if date_compare > date and date_compare - date < temp_time_diff:
            temp = item
            temp_time_diff = date_compare - date_compare
        if date >= date_compare and date - date_compare < temp_time_diff:
            temp = item
            temp_time_diff = date - date_compare
    
    return temp

def parseLatLong(lat, long):
    """
    Converts latitude and longitude into approximate city

    lat:
    long:
    """
    url = 'http://api.openweathermap.org/geo/1.0/reverse?lat={lat}&lon={lon}&limit={limit}&appid={API}'
    url = url.format(lat=lat, lon=long, limit = 5, API=API_KEY)
    response = requests.get(url)
    json_data = response.json()
    logging.debug(f"Possible locations to parse: {json_data}")
    if json_data:
        city = json_data[0]['name']
        state = json_data[0]['state']
        return f"{city}, {us_state_to_abbrev.get(state)}"
    else:
        return ""

def parseWeather(weather, spec):
    """
    weather:
    spec:
    """
    if weather == 'Thunderstorm':
        if spec == 'thunderstorm with light rain' or spec == 'light thunderstorm' or spec == 'ragged thunderstorm' or spec == 'thunderstorm with light drizzle':
            return 'Thunderstorm', 'Light'
        elif spec == 'thunderstorm with rain' or spec == 'thunderstorm' or spec == 'thunderstorm with drizzle':
            return 'Thunderstorm', 'Normal'
        elif spec == 'thunderstorm with heavy rain' or spec == 'heavy thunderstorm' or spec == 'thunderstorm with heavy drizzle':
            return 'Thunderstorm', 'Heavy'
    
    if weather == 'Drizzle':
        if spec == 'light intensity drizzle' or spec == 'light intensity drizzle rain' or spec == 'shower drizzle':
            return 'Drizzle', 'Light'
        elif spec == 'drizzle' or spec == 'drizzle rain' or spec == 'shower rain and drizzle':
            return 'Drizzle', 'Normal'
        elif spec == 'heavy intensity drizzle' or spec == 'heavy intensity drizzle rain' or spec == 'heavy shower rain and drizzle':
            return 'Drizzle', 'Heavy'
    
    if weather == 'Rain':
        if spec == 'light rain' or spec == 'light intensity shower rain' or spec == 'ragged shower rain':
            return 'Rain', 'Light'
        elif spec == 'moderate rain' or spec == 'shower rain':
            return 'Rain', 'Moderate'
        elif spec == 'heavy intensity rain' or spec == 'heavy intensity shower rain':
            return 'Rain', 'Heavy'
        elif spec == 'very heavy rain' or spec == 'extreme rain':
            return 'Rain', 'Extreme'
        elif spec == 'freezing rain':
            return 'Rain', 'Freezing'
    
    if weather == 'Snow':
        if spec == 'light snow' or spec == 'light shower snow':
            return 'Snow', 'Light'
        elif spec == 'snow' or spec == 'shower snow':
            return 'Snow', 'Normal'
        elif spec == 'heavy snow' or spec == 'heavy shower snow':
            return 'Snow', 'Heavy'
        elif spec == 'light shower sleet' or spec == 'light rain and snow':
            return 'Sleet', 'Light'
        elif spec == 'shower sleet' or spec == 'rain and snow':
            return 'Sleet', 'Normal'
    
    if weather == 'Clear' or weather == 'Clouds':
        return 'Clear or Cloudy', ''
    
    if weather == 'Atmosphere' and spec == 'Tornado':
        return 'Tornado', 'Extreme'
    else:
        return 'Atmospheric Conditions', 'Light'
        

def getTravelcast(route):
    """
    Gets aggregated weather conditions upon route (aggregated by weather)
    Using 3-hour forecast until API access is approved
    
    route:
    """
    results = []
    temp_weather_cond = ''
    temp_weather_name = ''
    temp_lat_lon = [0,0]
    temp_temperature = 0
    start = route[0][0]
    for i in route:
        url = 'https://pro.openweathermap.org/data/2.5/forecast/hourly?lat={lat}&lon={lon}&appid={API}'
        url = url.format(lat=i[1], lon=i[2], API=API_KEY)
        response = requests.get(url)
        json_data = response.json()
        weather = getNearestDate(json_data, i[0])
        weather_name = weather['weather'][0]['main']
        weather_cond = weather['weather'][0]['description']
        weather_temperature = round(kelvinToFahrenheit(weather['main']['feels_like']), 2)
        pw_name, pw_sev = parseWeather(weather_name, weather_cond)
        if temp_weather_name == '':
            temp_weather_cond = pw_sev
            temp_weather_name = pw_name
            temp_temperature = weather_temperature
            temp_lat_lon = [i[1], i[2]]
        if temp_temperature > weather_temperature:
            temp_temperature = weather_temperature
        if temp_weather_cond != pw_sev:
            results.append({
                    'Leg': parseLatLong(temp_lat_lon[0], temp_lat_lon[1]) + ' to ' + parseLatLong(i[1], i[2]),
                    'Date': start.strftime('%-d-%b'),
                    'Time': start.strftime('%I:%M %p') + ' - ' + i[0].strftime('%I:%M %p'),
                    'Temp': str(temp_temperature) + '\N{DEGREE SIGN}',
                    'Forecast': temp_weather_cond + ' ' + temp_weather_name
            })
            start = i[0]
            temp_weather_cond = pw_sev
            temp_weather_name = pw_name
            temp_temperature = weather_temperature
            temp_lat_lon = [i[1], i[2]]
    
    results.append({
        'Leg': parseLatLong(temp_lat_lon[0], temp_lat_lon[1]) + ' to ' + parseLatLong(i[1], i[2]),
        'Date': start.strftime('%-d-%b'),
        'Time': start.strftime('%I:%M %p') + ' - ' + i[0].strftime('%I:%M %p'),
        'Temp': str(temp_temperature) + '\N{DEGREE SIGN}',
        'Forecast': pw_sev + ' ' + pw_name
    })
    
    return results

def getForecast(address, start_date):
    """
    Will return daily forecast for the next 7 days

    address:
    start_date:
    """
    results = []
    retag_mapping = { "PlaceName": "city", "StateName": "state", "LandmarkName": "altCity" }
    try:
        parsed_address = usaddress.tag(address, retag_mapping)
    except usaddress.RepeatedLabelError as e:
        logging.error(f"Unable to parse {address}: {e}")
        raise

    logging.debug(f"Parsed address: {parsed_address}")

    city = parsed_address[0].get('city')
    state = parsed_address[0].get('state').split()[0].rstrip(',')
 
    #multi-word cities are miss-identified as Landmarks, and the state as the city
    if city in us_state_to_abbrev.values():
        state = city
        city = parsed_address[0].get('altCity')

    url = 'http://api.openweathermap.org/geo/1.0/direct?q={city},{state},{country}&limit={limit}&appid={API}'
    url = url.format(city=city, state=state, country='US', limit=1, API=API_KEY)
    response = requests.get(url)
    json_data = response.json()
    lat = json_data[0]['lat']
    long = json_data[0]['lon']
    count = 0
    logging.info(f"Date: {start_date}")
    if start_date is None:
        url = 'http://api.openweathermap.org/data/2.5/forecast/daily?lat={lat}&lon={lon}&cnt={cnt}&appid={API}'
        url = url.format(lat=lat, lon=long, cnt = 16, API=API_KEY)
        response = requests.get(url)
        json_data = response.json()
        flag = False
        for i in json_data['list']:
            if count < 8:
                temp_low = round(kelvinToFahrenheit(i['temp']['min']), 2)
                temp_high = round(kelvinToFahrenheit(i['temp']['max']), 2)
                weather, specific = parseWeather(i['weather'][0]['main'], i['weather'][0]['description'])
                
                d = datetime.datetime.fromtimestamp(i['dt']).strftime('%-d-%b')
                
                if not flag:
                        results.append({
                                'Location': city + ', ' + state,
                                'Date':d,
                                'Temps': str(temp_high) + '\N{DEGREE SIGN}/' + str(temp_low) +'\N{DEGREE SIGN}',
                                'Forecast': specific + ' ' + weather
                        })
                        flag = True
                else:
                        results.append({
                                'Date':d,
                                'Temps': str(temp_high) + '\N{DEGREE SIGN}/' + str(temp_low) +'\N{DEGREE SIGN}',
                                'Forecast': specific + ' ' + weather
                        })
                count += 1
    else:
        url = 'https://pro.openweathermap.org/data/2.5/forecast/hourly?lat={lat}&lon={lon}&appid={API}'
        url = url.format(lat=lat, lon=long, API=API_KEY)
        response = requests.get(url)
        json_data = response.json()
        start_date = dateutil.parser.parse(start_date)
        weather = getNearestDate(json_data, start_date)
        date = start_date.strftime('%-d-%b')
        time = start_date.strftime('%I:%M %p')
        temp = round(kelvinToFahrenheit(weather['main']['temp']), 2)
        weather, specific = parseWeather(weather['weather'][0]['main'], weather['weather'][0]['description'])
        results.append({
            'Location': f"{city}, {state}",
            'Date': date,
            'Time': time,
            'Temps': str(temp) + '\N{DEGREE SIGN}',
            'Forecast': specific + ' ' + weather
        })
    
    return results
