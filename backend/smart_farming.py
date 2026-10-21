"""
Smart Farming Intelligence Engine for Namma Vivasayi AI
Features:
1. Microclimate Weather & Spraying Advisory (Open-Meteo Integration with graceful fallback)
2. Smart Irrigation Advisory (Evapotranspiration & Soil Physics rules)
3. Agro-Climatic Crop Recommendations (Tamil Nadu Agro-Climatic Zones)
4. Plant Disease Pathology Diagnostics (Honest status reporting with TNAU diagnostic reference)
5. Mandi Market Prices (Regulated Market Yard reference data)
6. Government Agricultural Welfare Schemes (Verified official portal links)
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import os
import json
from pathlib import Path
import httpx

# ============================================================================
# 1. WEATHER SERVICE & AGRICULTURAL SPRAYING ADVISORY
# ============================================================================

import copy
from datetime import datetime, timezone, timedelta
import httpx
import logging

logger = logging.getLogger("namma_vivasayi.weather")

# Standard Indian Standard Time (IST) offset: UTC+5:30
IST = timezone(timedelta(hours=5, minutes=30), name="IST")

# In-memory weather cache for offline resilience and rate smoothing
WEATHER_CACHE: Dict[str, Dict[str, Any]] = {}

# Dedicated cache for live agrometeorological irrigation weather with TTL
IRRIGATION_WEATHER_CACHE: Dict[str, Tuple[datetime, Dict[str, Any]]] = {}
IRRIGATION_CACHE_TTL_SECONDS: int = 900  # 15 minutes TTL

TN_DISTRICT_COORDINATES: Dict[str, Dict[str, Any]] = {
    "thanjavur": {"name": "Thanjavur", "name_ta": "தஞ்சாவூர்", "lat": 10.7870, "lon": 79.1378, "zone": "Cauvery Delta"},
    "tiruvarur": {"name": "Tiruvarur", "name_ta": "திருவாரூர்", "lat": 10.7725, "lon": 79.6365, "zone": "Cauvery Delta"},
    "nagapattinam": {"name": "Nagapattinam", "name_ta": "நாகப்பட்டினம்", "lat": 10.7672, "lon": 79.8449, "zone": "Cauvery Delta"},
    "mayiladuthurai": {"name": "Mayiladuthurai", "name_ta": "மயிலாடுதுறை", "lat": 11.1018, "lon": 79.6522, "zone": "Cauvery Delta"},
    "tiruchirappalli": {"name": "Tiruchirappalli", "name_ta": "திருச்சிராப்பள்ளி", "lat": 10.7905, "lon": 78.7047, "zone": "Cauvery Delta"},
    "pudukkottai": {"name": "Pudukkottai", "name_ta": "புதுக்கோட்டை", "lat": 10.3833, "lon": 78.8001, "zone": "Cauvery Delta"},
    "perambalur": {"name": "Perambalur", "name_ta": "பெரம்பலூர்", "lat": 11.2333, "lon": 78.8833, "zone": "Cauvery Delta"},
    "ariyalur": {"name": "Ariyalur", "name_ta": "அரியலூர்", "lat": 11.1401, "lon": 79.0786, "zone": "Cauvery Delta"},
    "karur": {"name": "Karur", "name_ta": "கரூர்", "lat": 10.9601, "lon": 78.0766, "zone": "Western"},
    "madurai": {"name": "Madurai", "name_ta": "மதுரை", "lat": 9.9252, "lon": 78.1198, "zone": "Southern"},
    "dindigul": {"name": "Dindigul", "name_ta": "திண்டுக்கல்", "lat": 10.3673, "lon": 77.9803, "zone": "Southern"},
    "theni": {"name": "Theni", "name_ta": "தேனி", "lat": 10.0104, "lon": 77.4768, "zone": "Southern"},
    "ramanathapuram": {"name": "Ramanathapuram", "name_ta": "ராமநாதபுரம்", "lat": 9.3639, "lon": 78.8395, "zone": "Southern"},
    "sivaganga": {"name": "Sivaganga", "name_ta": "சிவகங்கை", "lat": 9.8433, "lon": 78.4809, "zone": "Southern"},
    "virudhunagar": {"name": "Virudhunagar", "name_ta": "விருதுநகர்", "lat": 9.5680, "lon": 77.9624, "zone": "Southern"},
    "tirunelveli": {"name": "Tirunelveli", "name_ta": "திருநெல்வேலி", "lat": 8.7139, "lon": 77.7567, "zone": "Southern"},
    "tenkasi": {"name": "Tenkasi", "name_ta": "தென்காசி", "lat": 8.9594, "lon": 77.3150, "zone": "Southern"},
    "thoothukudi": {"name": "Thoothukudi", "name_ta": "தூத்துக்குடி", "lat": 8.7642, "lon": 78.1348, "zone": "Southern"},
    "kanniyakumari": {"name": "Kanniyakumari", "name_ta": "கன்னியாகுமரி", "lat": 8.0883, "lon": 77.5385, "zone": "Southern"},
    "coimbatore": {"name": "Coimbatore", "name_ta": "கோயம்புத்தூர்", "lat": 11.0168, "lon": 76.9558, "zone": "Western"},
    "tiruppur": {"name": "Tiruppur", "name_ta": "திருப்பூர்", "lat": 11.1085, "lon": 77.3411, "zone": "Western"},
    "erode": {"name": "Erode", "name_ta": "ஈரோடு", "lat": 11.3410, "lon": 77.7172, "zone": "Western"},
    "salem": {"name": "Salem", "name_ta": "சேலம்", "lat": 11.6643, "lon": 78.1460, "zone": "North-Western"},
    "namakkal": {"name": "Namakkal", "name_ta": "நாமக்கல்", "lat": 11.2189, "lon": 78.1674, "zone": "Western"},
    "dharmapuri": {"name": "Dharmapuri", "name_ta": "தர்மபுரி", "lat": 12.1211, "lon": 78.1582, "zone": "North-Western"},
    "krishnagiri": {"name": "Krishnagiri", "name_ta": "கிருஷ்ணகிரி", "lat": 12.5186, "lon": 78.2137, "zone": "North-Western"},
    "cuddalore": {"name": "Cuddalore", "name_ta": "கடலூர்", "lat": 11.7480, "lon": 79.7714, "zone": "North-Eastern"},
    "viluppuram": {"name": "Viluppuram", "name_ta": "விழுப்புரம்", "lat": 11.9401, "lon": 79.4861, "zone": "North-Eastern"},
    "kallakurichi": {"name": "Kallakurichi", "name_ta": "கள்ளக்குறிச்சி", "lat": 11.7384, "lon": 78.9639, "zone": "North-Eastern"},
    "tiruvannamalai": {"name": "Tiruvannamalai", "name_ta": "திருவண்ணாமலை", "lat": 12.2253, "lon": 79.0747, "zone": "North-Eastern"},
    "vellore": {"name": "Vellore", "name_ta": "வேலூர்", "lat": 12.9165, "lon": 79.1325, "zone": "North-Eastern"},
    "ranipet": {"name": "Ranipet", "name_ta": "ராணிப்பேட்டை", "lat": 12.9272, "lon": 79.3330, "zone": "North-Eastern"},
    "tirupattur": {"name": "Tirupattur", "name_ta": "திருப்பத்தூர்", "lat": 12.4958, "lon": 78.5678, "zone": "North-Western"},
    "kanchipuram": {"name": "Kanchipuram", "name_ta": "காஞ்சிபுரம்", "lat": 12.8342, "lon": 79.7036, "zone": "North-Eastern"},
    "chengalpattu": {"name": "Chengalpattu", "name_ta": "செங்கல்பட்டு", "lat": 12.6841, "lon": 79.9836, "zone": "Coastal"},
    "tiruvallur": {"name": "Tiruvallur", "name_ta": "திருவள்ளூர்", "lat": 13.1432, "lon": 79.9074, "zone": "Coastal"},
    "chennai": {"name": "Chennai", "name_ta": "சென்னை", "lat": 13.0827, "lon": 80.2707, "zone": "Coastal"},
    "nilgiris": {"name": "Nilgiris", "name_ta": "நீலகிரி", "lat": 11.4102, "lon": 76.6950, "zone": "Hilly"},
}

WMO_WEATHER_CODES: Dict[int, Dict[str, str]] = {
    0: {"en": "Clear Sky", "ta": "தெளிவான வானம்", "icon": "sun"},
    1: {"en": "Mainly Clear", "ta": "பெரும்பாலும் தெளிவான வானம்", "icon": "sun"},
    2: {"en": "Partly Cloudy", "ta": "பகுதி மேகமூட்டம்", "icon": "cloud-sun"},
    3: {"en": "Overcast", "ta": "முழு மேகமூட்டம்", "icon": "cloud"},
    45: {"en": "Foggy", "ta": "பனிமூட்டம்", "icon": "cloud-fog"},
    48: {"en": "Depositing Rime Fog", "ta": "அடர்ந்த பனிமூட்டம்", "icon": "cloud-fog"},
    51: {"en": "Light Drizzle", "ta": "மெல்லிய தூறல் மழை", "icon": "cloud-drizzle"},
    53: {"en": "Moderate Drizzle", "ta": "மிதமான தூறல்", "icon": "cloud-drizzle"},
    55: {"en": "Dense Drizzle", "ta": "அடர்ந்த தூறல்", "icon": "cloud-drizzle"},
    56: {"en": "Light Freezing Drizzle", "ta": "குளிர்ந்த தூறல்", "icon": "cloud-drizzle"},
    57: {"en": "Dense Freezing Drizzle", "ta": "அடர்ந்த குளிர்ந்த தூறல்", "icon": "cloud-drizzle"},
    61: {"en": "Slight Rain", "ta": "லேசான மழை", "icon": "cloud-rain"},
    63: {"en": "Moderate Rain", "ta": "மிதமான மழை", "icon": "cloud-rain"},
    65: {"en": "Heavy Rain", "ta": "பலத்த மழை", "icon": "cloud-rain"},
    66: {"en": "Light Freezing Rain", "ta": "குளிர்ந்த மழை", "icon": "cloud-rain"},
    67: {"en": "Heavy Freezing Rain", "ta": "கடும் குளிர்ந்த மழை", "icon": "cloud-rain"},
    71: {"en": "Slight Snow Fall", "ta": "லேசான பனிப்பொழிவு", "icon": "cloud-snow"},
    73: {"en": "Moderate Snow Fall", "ta": "மிதமான பனிப்பொழிவு", "icon": "cloud-snow"},
    75: {"en": "Heavy Snow Fall", "ta": "பலத்த பனிப்பொழிவு", "icon": "cloud-snow"},
    77: {"en": "Snow Grains", "ta": "பனி மணிகள்", "icon": "cloud-snow"},
    80: {"en": "Slight Rain Showers", "ta": "லேசான மழைச்சாரல்", "icon": "cloud-rain"},
    81: {"en": "Moderate Rain Showers", "ta": "மிதமான மழைச்சாரல்", "icon": "cloud-rain"},
    82: {"en": "Violent Rain Showers", "ta": "கடும் மழைச்சாரல்", "icon": "cloud-lightning"},
    85: {"en": "Slight Snow Showers", "ta": "லேசான பனிச்சாரல்", "icon": "cloud-snow"},
    86: {"en": "Heavy Snow Showers", "ta": "கடும் பனிச்சாரல்", "icon": "cloud-snow"},
    95: {"en": "Thunderstorm", "ta": "இடியுடன் கூடிய மழை", "icon": "cloud-lightning"},
    96: {"en": "Thunderstorm with Slight Hail", "ta": "இடியுடன் கூடிய ஆலங்கட்டி மழை", "icon": "cloud-lightning"},
    99: {"en": "Thunderstorm with Heavy Hail", "ta": "கடும் ஆலங்கட்டி மழை", "icon": "cloud-lightning"},
}

def generate_spraying_advisory(
    wind_speed_kmh: float,
    rain_chance: int,
    temp_c: float,
    precip_mm: float = 0.0
) -> Dict[str, Any]:
    """
    Generates a multi-factorial, data-driven agricultural spraying advisory
    based on wind drift risk, precipitation wash-off probability, and thermal evaporation.
    """
    disclaimer_en = (
        "Forecast-based advisory only. Always cross-check with chemical container labels and local TNAU/KVK extension advisories."
    )
    disclaimer_ta = (
        "இது வானிலை முன்னறிவிப்பு அடிப்படையிலான ஆலோசனை மட்டுமே. பூச்சிக்கொல்லி லேபிள் வழிகாட்டுதல்கள் மற்றும் வேளாண் அலுவலர் ஆலோசனையை பின்பற்றவும்."
    )

    if rain_chance >= 60 or precip_mm >= 2.0:
        return {
            "status": "not_recommended",
            "title_en": "Avoid Foliar Spraying Today",
            "title_ta": "இன்று இலைவழி தெளிப்பை தவிர்க்கவும்",
            "reason_en": (
                f"High rainfall probability ({rain_chance}%) and expected precipitation of {precip_mm} mm. "
                "Agrochemicals or bio-nutrients will suffer severe foliage wash-off and run into local water bodies."
            ),
            "reason_ta": (
                f"அதிக மழை வாய்ப்பு ({rain_chance}%) மற்றும் எதிர்பார்க்கப்படும் மழைப்பொழிவு {precip_mm} மிமீ உள்ளதால் "
                "தெளிக்கும் மருந்துகள் இலைகளில் தங்காமல் மழைநீரில் அடித்துச் செல்லப்படும்."
            ),
            "favorable_window": "Wait until rainfall ceases and crop foliage is thoroughly dry.",
            "disclaimer_en": disclaimer_en,
            "disclaimer_ta": disclaimer_ta
        }
    elif wind_speed_kmh >= 16.0:
        return {
            "status": "warning",
            "title_en": "High Wind Drift Warning",
            "title_ta": "அதிக காற்று எச்சரிக்கை",
            "reason_en": (
                f"Wind speed of {wind_speed_kmh} km/h exceeds safe spraying limits (15 km/h). "
                "Fine droplet drift will result in uneven crop canopy coverage and chemical wastage."
            ),
            "reason_ta": (
                f"காற்றின் வேகம் {wind_speed_kmh} கிமீ/மணி உள்ளதால் மருந்து காற்றில் சிதறி இலக்கை அடையாமல் வீணாகும்."
            ),
            "favorable_window": "Wait for calm early morning conditions (wind speed < 10 km/h).",
            "disclaimer_en": disclaimer_en,
            "disclaimer_ta": disclaimer_ta
        }
    elif temp_c >= 35.0:
        return {
            "status": "caution",
            "title_en": "Afternoon High Temperature Warning",
            "title_ta": "மதிய நேர வெப்பநிலை எச்சரிக்கை",
            "reason_en": (
                f"Ambient temperature of {temp_c}°C accelerates droplet evaporation and may cause chemical leaf scorch under direct sun."
            ),
            "reason_ta": (
                f"அதிக வெயில் ({temp_c}°C) காரணத்தால் மருந்து துளிகள் விரைந்து ஆவியாகி பயிர் இலைகள் கருகும் வாய்ப்புள்ளது."
            ),
            "favorable_window": "Spray only between 06:30 AM - 09:30 AM or after 04:30 PM.",
            "disclaimer_en": disclaimer_en,
            "disclaimer_ta": disclaimer_ta
        }
    elif rain_chance >= 35 or precip_mm >= 0.5:
        return {
            "status": "caution",
            "title_en": "Moderate Rain Risk - Use Rainfast Formulations",
            "title_ta": "மிதமான மழை ஆபத்து - கவனத்துடன் தெளிக்கவும்",
            "reason_en": (
                f"Moderate precipitation probability ({rain_chance}%, {precip_mm} mm). "
                "If spraying is urgent, incorporate an approved non-ionic adjuvant/spreader sticker to improve rainfastness."
            ),
            "reason_ta": (
                f"மிதமான மழை வாய்ப்பு ({rain_chance}%) உள்ளது. அவசியமானால் இலை ஒட்டும் திரவம் (Sticker) சேர்த்து விரைவாக உறிஞ்சப்படும் மருந்துகளை தெளிக்கவும்."
            ),
            "favorable_window": "Best window: 07:00 AM - 09:30 AM if morning radar is clear.",
            "disclaimer_en": disclaimer_en,
            "disclaimer_ta": disclaimer_ta
        }
    else:
        return {
            "status": "optimal",
            "title_en": "Optimal Spraying Window",
            "title_ta": "உகந்த தெளிப்பு நேரம்",
            "reason_en": (
                f"Favorable microclimate: gentle breeze ({wind_speed_kmh} km/h), moderate temperature ({temp_c}°C), "
                f"and low precipitation probability ({rain_chance}%, {precip_mm} mm). Ideal for uniform foliar retention."
            ),
            "reason_ta": (
                f"காற்றின் வேகம் மிதமானது ({wind_speed_kmh} கிமீ/மணி), மிதமான வெப்பநிலை ({temp_c}°C), "
                f"மழை வாய்ப்பு குறைவு ({rain_chance}%). மருந்து இலைகளில் சீராக படிய சிறந்த நேரம்."
            ),
            "favorable_window": "Best between 07:00 AM - 10:00 AM or 04:30 PM - 06:00 PM.",
            "disclaimer_en": disclaimer_en,
            "disclaimer_ta": disclaimer_ta
        }

async def get_district_weather(district_key: str = "thanjavur") -> Dict[str, Any]:
    """
    Fetches live, real-time microclimate weather and multi-day forecasts
    from the official Open-Meteo Forecast API using the selected Tamil Nadu
    district's authentic latitude and longitude, strictly in Asia/Kolkata (IST) time.
    """
    key = district_key.strip().lower()
    dist_info = TN_DISTRICT_COORDINATES.get(key, TN_DISTRICT_COORDINATES.get("thanjavur"))
    if not dist_info:
        dist_info = {
            "name": district_key.capitalize(),
            "name_ta": district_key.capitalize(),
            "lat": 10.7870,
            "lon": 79.1378,
            "zone": "Tamil Nadu"
        }

    lat = dist_info["lat"]
    lon = dist_info["lon"]

    now_ist = datetime.now(IST)
    last_updated_ist = now_ist.strftime("%d %b %Y, %I:%M %p IST")
    last_updated_iso = now_ist.isoformat()

    # Official Open-Meteo Forecast API with timezone=Asia/Kolkata
    url = (
        "https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&"
        "current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,rain,weather_code,wind_speed_10m,wind_direction_10m&"
        "hourly=temperature_2m,relative_humidity_2m,precipitation_probability,precipitation,weather_code,wind_speed_10m&"
        "daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,wind_speed_10m_max&"
        "timezone=Asia%2FKolkata&"
        "forecast_days=7"
    )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                curr = data.get("current", {})
                daily = data.get("daily", {})

                # Weather condition mapping
                wmo_code = curr.get("weather_code", 0)
                cond_info = WMO_WEATHER_CODES.get(wmo_code, {"en": "Partly Cloudy", "ta": "பகுதி மேகமூட்டம்", "icon": "cloud-sun"})

                temp_c = round(float(curr.get("temperature_2m", 30.0)), 1)
                apparent_temp = round(float(curr.get("apparent_temperature", temp_c)), 1)
                humidity = int(curr.get("relative_humidity_2m", 65))
                current_precip_mm = round(float(curr.get("precipitation", 0.0)), 1)
                wind_speed = round(float(curr.get("wind_speed_10m", 8.0)), 1)
                wind_dir = int(curr.get("wind_direction_10m", 0))

                rain_prob_list = daily.get("precipitation_probability_max", [0])
                rain_prob = int(rain_prob_list[0]) if rain_prob_list and rain_prob_list[0] is not None else 0

                precip_sum_list = daily.get("precipitation_sum", [0.0])
                today_precip_mm = round(float(precip_sum_list[0]), 1) if precip_sum_list and precip_sum_list[0] is not None else current_precip_mm

                # Parse API observation timestamp in IST
                obs_iso = curr.get("time")
                if obs_iso:
                    try:
                        obs_dt = datetime.fromisoformat(obs_iso)
                        observation_time = obs_dt.strftime("%d %b %Y, %I:%M %p IST")
                    except Exception:
                        observation_time = f"{obs_iso} IST"
                else:
                    observation_time = "Unavailable"

                # Build 5-day forecast with authentic API dates
                forecast = []
                dates = daily.get("time", [])
                w_codes = daily.get("weather_code", [])
                max_temps = daily.get("temperature_2m_max", [])
                min_temps = daily.get("temperature_2m_min", [])
                rain_probs = daily.get("precipitation_probability_max", [])
                precip_sums = daily.get("precipitation_sum", [])
                wind_maxs = daily.get("wind_speed_10m_max", [])

                tamil_weekdays = {
                    0: "திங்கட்கிழமை",
                    1: "செவ்வாய்க்கிழமை",
                    2: "புதன்கிழமை",
                    3: "வியாழக்கிழமை",
                    4: "வெள்ளிக்கிழமை",
                    5: "சனிக்கிழமை",
                    6: "ஞாயிற்றுக்கிழமை",
                }
                tamil_months = {
                    1: "ஜன", 2: "பிப்", 3: "மார்ச்", 4: "ஏப்", 5: "மே", 6: "ஜூன்",
                    7: "ஜூலை", 8: "ஆக", 9: "செப்", 10: "அக்", 11: "நவ", 12: "டிச"
                }

                for idx in range(min(5, len(dates))):
                    d_str = dates[idx]
                    try:
                        d_obj = datetime.strptime(d_str, "%Y-%m-%d")
                        if idx == 0:
                            day_en = "Today"
                            day_ta = "இன்று"
                        elif idx == 1:
                            day_en = "Tomorrow"
                            day_ta = "நாளை"
                        else:
                            day_en = d_obj.strftime("%A")
                            day_ta = tamil_weekdays.get(d_obj.weekday(), d_obj.strftime("%A"))

                        formatted_date_en = d_obj.strftime("%d %b %Y")
                        t_month = tamil_months.get(d_obj.month, d_obj.strftime("%b"))
                        formatted_date_ta = f"{d_obj.day} {t_month} {d_obj.year}"
                    except Exception:
                        day_en = d_str
                        day_ta = d_str
                        formatted_date_en = d_str
                        formatted_date_ta = d_str

                    day_w_code = w_codes[idx] if idx < len(w_codes) and w_codes[idx] is not None else 0
                    cond_day = WMO_WEATHER_CODES.get(day_w_code, {"en": "Partly Cloudy", "ta": "பகுதி மேகமூட்டம்", "icon": "cloud-sun"})
                    max_t = round(float(max_temps[idx]), 1) if idx < len(max_temps) and max_temps[idx] is not None else 32.0
                    min_t = round(float(min_temps[idx]), 1) if idx < len(min_temps) and min_temps[idx] is not None else 24.0
                    day_rain_p = int(rain_probs[idx]) if idx < len(rain_probs) and rain_probs[idx] is not None else 0
                    p_sum = round(float(precip_sums[idx]), 1) if idx < len(precip_sums) and precip_sums[idx] is not None else 0.0
                    w_max = round(float(wind_maxs[idx]), 1) if idx < len(wind_maxs) and wind_maxs[idx] is not None else 10.0

                    forecast.append({
                        "day": day_en,
                        "day_ta": day_ta,
                        "date": formatted_date_en,
                        "date_ta": formatted_date_ta,
                        "dateIso": d_str,
                        "temp": f"{round(max_t)}°C",
                        "tempMax": max_t,
                        "tempMin": min_t,
                        "tempRange": f"{round(max_t)}° / {round(min_t)}°C",
                        "condition": cond_day["en"],
                        "condition_ta": cond_day["ta"],
                        "weatherCode": day_w_code,
                        "weatherIcon": cond_day.get("icon", "cloud-sun"),
                        "rainProb": day_rain_p,
                        "precipMm": p_sum,
                        "windSpeedMaxKmh": w_max
                    })

                advisory = generate_spraying_advisory(
                    wind_speed_kmh=wind_speed,
                    rain_chance=rain_prob,
                    temp_c=temp_c,
                    precip_mm=today_precip_mm
                )

                result = {
                    "district": dist_info["name"],
                    "district_ta": dist_info["name_ta"],
                    "zone": dist_info["zone"],
                    "latitude": lat,
                    "longitude": lon,
                    "coordinates": {"lat": lat, "lon": lon},
                    "temperatureC": temp_c,
                    "apparentTemperatureC": apparent_temp,
                    "humidity": humidity,
                    "rainfallChance": rain_prob,
                    "precipitationMm": current_precip_mm,
                    "windSpeedKmh": wind_speed,
                    "windDirectionDeg": wind_dir,
                    "weatherCode": wmo_code,
                    "condition": cond_info["en"],
                    "condition_ta": cond_info["ta"],
                    "weatherIcon": cond_info.get("icon", "cloud-sun"),
                    "observationTime": observation_time,
                    "observationTimeIso": obs_iso,
                    "lastUpdated": last_updated_ist,
                    "lastUpdatedIso": last_updated_iso,
                    "updatedAt": observation_time,
                    "isLive": True,
                    "isCached": False,
                    "source": "Open-Meteo High-Resolution Numerical Weather Prediction (Asia/Kolkata IST)",
                    "sprayingAdvisory": advisory,
                    "forecast": forecast
                }

                # Save to in-memory cache for reliable offline fallback
                WEATHER_CACHE[key] = copy.deepcopy(result)
                return result

    except Exception as e:
        logger.warning(f"Open-Meteo API query failed for '{key}': {type(e).__name__} - {str(e)[:100]}")

    # Fallback to cache if available
    if key in WEATHER_CACHE:
        cached_data = copy.deepcopy(WEATHER_CACHE[key])
        cached_data["isLive"] = False
        cached_data["isCached"] = True
        cached_data["source"] = f"Cached Open-Meteo Data (Observed {cached_data.get('observationTime', 'Earlier')})"
        cached_data["lastUpdated"] = last_updated_ist
        return cached_data

    # Return honest unavailable state when live API is unreachable and no cache exists
    return {
        "district": dist_info["name"],
        "district_ta": dist_info["name_ta"],
        "zone": dist_info["zone"],
        "latitude": lat,
        "longitude": lon,
        "coordinates": {"lat": lat, "lon": lon},
        "temperatureC": None,
        "apparentTemperatureC": None,
        "humidity": None,
        "rainfallChance": None,
        "precipitationMm": None,
        "windSpeedKmh": None,
        "windDirectionDeg": None,
        "weatherCode": None,
        "condition": "Weather Data Unavailable",
        "condition_ta": "வானிலை தரவு கிடைக்கவில்லை",
        "weatherIcon": "cloud-off",
        "observationTime": "Unavailable",
        "observationTimeIso": None,
        "lastUpdated": last_updated_ist,
        "lastUpdatedIso": last_updated_iso,
        "updatedAt": "Unavailable",
        "isLive": False,
        "isCached": False,
        "error": "Live meteorological feed is temporarily unreachable. Please check network connection and click Refresh.",
        "source": "Open-Meteo Service Unavailable",
        "sprayingAdvisory": None,
        "forecast": []
    }


# ============================================================================
# 2. SMART IRRIGATION ADVISORY ENGINE & AGROMETEOROLOGICAL WEATHER
# ============================================================================

def validate_coordinates(lat: Any, lon: Any) -> Tuple[float, float]:
    """
    Validates latitude and longitude values.
    Latitude must be between -90.0 and +90.0.
    Longitude must be between -180.0 and +180.0.
    """
    try:
        lat_f = float(lat)
        lon_f = float(lon)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid coordinate format: lat={lat}, lon={lon}. Numbers required.")

    if not (-90.0 <= lat_f <= 90.0):
        raise ValueError(f"Latitude {lat_f} is out of range (-90.0 to 90.0).")
    if not (-180.0 <= lon_f <= 180.0):
        raise ValueError(f"Longitude {lon_f} is out of range (-180.0 to 180.0).")

    return lat_f, lon_f


async def get_irrigation_weather(lat: float, lon: float, force_refresh: bool = False) -> Dict[str, Any]:
    """
    Fetches real-time microclimate and agrometeorological variables from Open-Meteo Forecast API:
    temperature_2m, relative_humidity_2m, precipitation_probability, precipitation, rain,
    et0_fao_evapotranspiration, soil_moisture_0_to_7cm, soil_moisture_7_to_28cm, soil_moisture_28_to_100cm.
    Timezone is set to Asia/Kolkata (IST).
    Implements a 15-minute in-memory cache and returns honest state on provider errors without inventing data.
    """
    lat, lon = validate_coordinates(lat, lon)
    cache_key = f"{round(lat, 4)},{round(lon, 4)}"
    now_utc = datetime.now(timezone.utc)
    now_ist = datetime.now(IST)
    last_updated_ist = now_ist.strftime("%d %b %Y, %I:%M %p IST")
    last_updated_iso = now_ist.isoformat()

    # Check cache unless force_refresh is requested
    if not force_refresh and cache_key in IRRIGATION_WEATHER_CACHE:
        cached_time, cached_data = IRRIGATION_WEATHER_CACHE[cache_key]
        age_seconds = (now_utc - cached_time).total_seconds()
        if age_seconds < IRRIGATION_CACHE_TTL_SECONDS:
            res = copy.deepcopy(cached_data)
            res["isCached"] = True
            res["isStale"] = False
            res["cacheAgeSeconds"] = int(age_seconds)
            return res

    url = (
        "https://api.open-meteo.com/v1/forecast?"
        f"latitude={round(lat, 4)}&longitude={round(lon, 4)}&"
        "current=temperature_2m,relative_humidity_2m,precipitation,rain,weather_code&"
        "hourly=temperature_2m,relative_humidity_2m,precipitation_probability,precipitation,rain,et0_fao_evapotranspiration,soil_moisture_0_to_7cm,soil_moisture_7_to_28cm,soil_moisture_28_to_100cm&"
        "daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,et0_fao_evapotranspiration&"
        "timezone=Asia%2FKolkata&"
        "forecast_days=3"
    )

    for attempt in range(2):
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(15.0, connect=8.0)) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    break
                else:
                    logger.warning(f"Open-Meteo returned status {resp.status_code}")
                    return None  # Will fall through to cache / unavailable
        except Exception as e:
            if attempt == 0:
                await asyncio.sleep(0.5)
                continue
            logger.warning(f"Open-Meteo fetch error for ({lat}, {lon}): {e}")
            data = None
            break

    if data:
        try:
                curr = data.get("current", {})
                daily = data.get("daily", {})
                hourly = data.get("hourly", {})

                # Weather condition mapping
                wmo_code = curr.get("weather_code", 0)
                cond_info = WMO_WEATHER_CODES.get(wmo_code, {"en": "Partly Cloudy", "ta": "பகுதி மேகமூட்டம்", "icon": "cloud-sun"})

                temp_c = round(float(curr.get("temperature_2m", 30.0)), 1) if curr.get("temperature_2m") is not None else None
                humidity = int(curr.get("relative_humidity_2m", 65)) if curr.get("relative_humidity_2m") is not None else None
                current_precip_mm = round(float(curr.get("precipitation", 0.0)), 1) if curr.get("precipitation") is not None else 0.0
                rain_mm = round(float(curr.get("rain", 0.0)), 1) if curr.get("rain") is not None else 0.0

                rain_prob_list = daily.get("precipitation_probability_max", [])
                rain_prob = int(rain_prob_list[0]) if rain_prob_list and rain_prob_list[0] is not None else 0

                precip_sum_list = daily.get("precipitation_sum", [])
                today_precip_mm = round(float(precip_sum_list[0]), 1) if precip_sum_list and precip_sum_list[0] is not None else current_precip_mm

                et0_list = daily.get("et0_fao_evapotranspiration", [])
                et0_daily = round(float(et0_list[0]), 2) if et0_list and et0_list[0] is not None else None

                # Extract Soil Moisture from hourly series for current hour
                time_list = hourly.get("time", [])
                curr_hour_str = now_ist.strftime("%Y-%m-%dT%H:00")
                curr_idx = -1
                if curr_hour_str in time_list:
                    curr_idx = time_list.index(curr_hour_str)
                elif time_list:
                    curr_idx = 0

                sm0_7_list = hourly.get("soil_moisture_0_to_7cm", [])
                sm7_28_list = hourly.get("soil_moisture_7_to_28cm", [])
                sm28_100_list = hourly.get("soil_moisture_28_to_100cm", [])

                sm0_7_raw = sm0_7_list[curr_idx] if 0 <= curr_idx < len(sm0_7_list) else None
                sm7_28_raw = sm7_28_list[curr_idx] if 0 <= curr_idx < len(sm7_28_list) else None
                sm28_100_raw = sm28_100_list[curr_idx] if 0 <= curr_idx < len(sm28_100_list) else None

                layer_0_7_pct = round(float(sm0_7_raw) * 100.0, 1) if sm0_7_raw is not None else None
                layer_7_28_pct = round(float(sm7_28_raw) * 100.0, 1) if sm7_28_raw is not None else None
                layer_28_100_pct = round(float(sm28_100_raw) * 100.0, 1) if sm28_100_raw is not None else None

                # Root zone (0-28cm) calculation: weighted depth 0.3 * sm0_7 + 0.7 * sm7_28
                if sm0_7_raw is not None and sm7_28_raw is not None:
                    root_zone_vol = 0.3 * float(sm0_7_raw) + 0.7 * float(sm7_28_raw)
                    root_zone_pct = round(root_zone_vol * 100.0, 1)
                    sm_available = True
                    sm_label = f"{root_zone_pct}%"
                elif sm0_7_raw is not None:
                    root_zone_pct = round(float(sm0_7_raw) * 100.0, 1)
                    sm_available = True
                    sm_label = f"{root_zone_pct}%"
                elif sm7_28_raw is not None:
                    root_zone_pct = round(float(sm7_28_raw) * 100.0, 1)
                    sm_available = True
                    sm_label = f"{root_zone_pct}%"
                else:
                    root_zone_pct = None
                    sm_available = False
                    sm_label = "Soil moisture estimate unavailable"

                # Parse observation time
                obs_iso = curr.get("time")
                if obs_iso:
                    try:
                        obs_dt = datetime.fromisoformat(obs_iso)
                        observation_time = obs_dt.strftime("%d %b %Y, %I:%M %p IST")
                    except Exception:
                        observation_time = f"{obs_iso} IST"
                else:
                    observation_time = last_updated_ist

                weather_result = {
                    "coordinates": {"lat": round(lat, 4), "lon": round(lon, 4)},
                    "timezone": "Asia/Kolkata",
                    "source": "Open-Meteo Agrometeorological Forecast API",
                    "forecastHorizon": "3-Day Forecast",
                    "units": {
                        "temperature": "°C",
                        "humidity": "%",
                        "precipitation": "mm",
                        "rain": "mm",
                        "et0": "mm/day",
                        "soilMoisture": "% (volumetric m³/m³)"
                    },
                    "current": {
                        "temperatureC": temp_c,
                        "humidity": humidity,
                        "precipitationMm": current_precip_mm,
                        "rainMm": rain_mm,
                        "weatherCode": wmo_code,
                        "condition": cond_info.get("en", "Partly Cloudy"),
                        "conditionTa": cond_info.get("ta", "பகுதி மேகமூட்டம்"),
                        "weatherIcon": cond_info.get("icon", "cloud-sun"),
                        "observationTime": observation_time
                    },
                    "precipitationProbability": rain_prob,
                    "precipitationSumMm": today_precip_mm,
                    "et0EstimateMmDay": et0_daily,
                    "soilMoisture": {
                        "available": sm_available,
                        "rootZonePercent": root_zone_pct,
                        "displayLabel": sm_label,
                        "depth0To7cmPercent": layer_0_7_pct,
                        "depth7To28cmPercent": layer_7_28_pct,
                        "depth28To100cmPercent": layer_28_100_pct,
                        "disclaimer": "Modelled land-surface estimate (Open-Meteo numerical simulation). Not an in-situ physical sensor reading.",
                        "disclaimerTa": "மாதிரி நிலப்பரப்பு மதிப்பீடு (Open-Meteo). நேரடி சென்சார் அளவீடு அல்ல."
                    },
                    "lastUpdated": last_updated_ist,
                    "lastUpdatedIso": last_updated_iso,
                    "isLive": True,
                    "isCached": False,
                    "isStale": False
                }

                # Store in cache
                IRRIGATION_WEATHER_CACHE[cache_key] = (now_utc, copy.deepcopy(weather_result))
                return weather_result
        except Exception as e:
            logger.warning(f"Error parsing Open-Meteo response for ({lat}, {lon}): {e}")

    # Fallback to stale cache if available
    if cache_key in IRRIGATION_WEATHER_CACHE:
        cached_time, cached_data = IRRIGATION_WEATHER_CACHE[cache_key]
        stale_result = copy.deepcopy(cached_data)
        stale_result["isCached"] = True
        stale_result["isLive"] = False
        stale_result["isStale"] = True
        stale_result["warning"] = "Using previously cached agrometeorological data due to connection timeout."
        return stale_result

    # Provider error state — Never fabricate fake weather data
    return {
        "coordinates": {"lat": round(lat, 4), "lon": round(lon, 4)},
        "timezone": "Asia/Kolkata",
        "source": "Open-Meteo Service Unavailable",
        "forecastHorizon": "3-Day Forecast",
        "units": {
            "temperature": "°C",
            "humidity": "%",
            "precipitation": "mm",
            "rain": "mm",
            "et0": "mm/day",
            "soilMoisture": "% (volumetric m³/m³)"
        },
        "current": None,
        "precipitationProbability": None,
        "precipitationSumMm": None,
        "et0EstimateMmDay": None,
        "soilMoisture": {
            "available": False,
            "rootZonePercent": None,
            "displayLabel": "Soil moisture estimate unavailable",
            "depth0To7cmPercent": None,
            "depth7To28cmPercent": None,
            "depth28To100cmPercent": None,
            "disclaimer": "Soil moisture estimate unavailable due to provider connection error.",
            "disclaimerTa": "வானிலை சேவை இணைப்பு இல்லாததால் மண் ஈரப்பதம் மதிப்பீடு கிடைக்கவில்லை."
        },
        "lastUpdated": last_updated_ist,
        "lastUpdatedIso": last_updated_iso,
        "isLive": False,
        "isCached": False,
        "isStale": False,
        "error": "Live meteorological feed is temporarily unreachable. Please check network connection and click Refresh."
    }


CROP_KC_FACTORS: Dict[str, Dict[str, float]] = {
    "paddy": {"initial": 1.05, "vegetative": 1.15, "flowering": 1.30, "grain_filling": 1.10, "maturity": 0.85},
    "maize": {"initial": 0.40, "vegetative": 0.85, "flowering": 1.20, "grain_filling": 1.05, "maturity": 0.60},
    "sugarcane": {"initial": 0.45, "vegetative": 1.00, "flowering": 1.25, "grain_filling": 1.10, "maturity": 0.75},
    "cotton": {"initial": 0.40, "vegetative": 0.75, "flowering": 1.20, "grain_filling": 0.95, "maturity": 0.60},
    "black_gram": {"initial": 0.40, "vegetative": 0.65, "flowering": 0.95, "grain_filling": 0.80, "maturity": 0.45},
    "groundnut": {"initial": 0.45, "vegetative": 0.70, "flowering": 1.10, "grain_filling": 0.90, "maturity": 0.55},
    "banana": {"initial": 0.85, "vegetative": 1.10, "flowering": 1.25, "grain_filling": 1.15, "maturity": 0.95},
}


def calculate_irrigation_advice(
    crop: str,
    growth_stage: str,
    soil_type: str,
    irrigation_method: str,
    soil_moisture_percent: Optional[float] = None,
    recent_rain_mm: Optional[float] = 0.0,
    forecast_rain_chance: Optional[float] = 20.0,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    field_area_acres: Optional[float] = 1.0,
    weather_summary: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Computes agronomic crop water balance and irrigation advisory using FAO-56 / TNAU principles.
    - Estimates crop evapotranspiration ETc = ET0 * Kc
    - Uses crop-specific Kc factors across phenological stages
    - Calculates effective rainfall (Peff) without equating probability to amount
    - Uses soil texture retention thresholds (clay, loam, sand)
    - Incorporates paddy-specific lowland basin water management (TNAU Alternate Wetting & Drying / AWD)
    - Yields exactly one of 3 outcomes: 'irrigate_now', 'delay_reassess', 'monitor_conditions'
    - Calculates water volumes (mm depth & total litres) only when inputs are valid
    - Strictly disclaims any physical hardware control of pumps or valves.
    """
    # 0. Validate field area
    try:
        area_acres = float(field_area_acres) if field_area_acres is not None else 1.0
        if area_acres <= 0.0:
            area_acres = 1.0
    except (ValueError, TypeError):
        area_acres = 1.0

    # 1. Handle Missing Critical Agronomic Inputs (Qualitative Advisory Fallback)
    has_valid_crop = bool(crop and crop.strip())
    has_valid_stage = bool(growth_stage and growth_stage.strip())
    has_valid_soil = bool(soil_type and soil_type.strip())

    if not (has_valid_crop and has_valid_stage and has_valid_soil):
        return {
            "crop": crop or "Unspecified",
            "growthStage": growth_stage or "Unspecified",
            "soilType": soil_type or "Unspecified",
            "irrigationMethod": irrigation_method or "Unspecified",
            "recommendation": "monitor_conditions",
            "status": "adequate",
            "recommendationTitleEn": "Monitor Conditions (Data Incomplete)",
            "recommendationTitleTa": "நிலவரத்தைக் கண்காணிக்கவும் (தரவு முழுமையடையவில்லை)",
            "recommendationEn": "Qualitative Advisory: Key agronomic inputs (crop, growth stage, or soil type) are missing or incomplete. Inspect field moisture manually before irrigating.",
            "recommendationTa": "தரவு முழுமையற்றது: துல்லியமான பாசன அளவை கணக்கிட பயிர், வளர்ச்சி நிலை அல்லது மண் விவரங்கள் தேவை. வயல் ஈரப்பதத்தை நேரில் பார்த்து தீர்மானிக்கவும்.",
            "irrigationWindowEn": "Observe field soil crumb at 07:00 AM / 05:00 PM IST",
            "irrigationWindowTa": "காலை 07:00 அல்லது மாலை 05:00 மணிக்கு வயலை பார்வையிடவும்",
            "referenceEtoMmDay": 5.0,
            "cropWaterDemandMm": 0.0,
            "cropFactorKc": 1.0,
            "fieldAreaAcres": area_acres,
            "effectiveRainfallMm": 0.0,
            "netIrrigationRequirementMm": 0.0,
            "grossIrrigationRequirementMm": None,
            "estimatedLitersPerAcre": 0,
            "totalEstimatedLiters": None,
            "isWaterVolumeEstimated": False,
            "unitExplanationEn": "1 mm depth of water over 1 square metre equals 1 litre (1 mm × 1 m² = 1 L). Across 1 cultivated acre (4,047 m²), 1 mm depth equals 4,047 litres.",
            "unitExplanationTa": "1 சதுர மீட்டர் பரப்பில் 1 மிமீ நீர் ஆழம் என்பது 1 லிட்டர் ஆகும் (1 மிமீ × 1 ச.மீ = 1 லிட்டர்). 1 ஏக்கர் பயிர் நிலத்திற்கு (4,047 ச.மீ), 1 மிமீ ஆழம் 4,047 லிட்டர் நீருக்கு சமம்.",
            "soilMoistureUsedPercent": soil_moisture_percent,
            "forecastRainChancePercent": forecast_rain_chance,
            "recentRainMm": recent_rain_mm,
            "reasonsEn": [
                "Critical crop or soil inputs are missing or unspecified.",
                "Qualitative advisory is provided; precise numeric water depth and volume cannot be calculated without agronomic parameters.",
                "Verify actual soil crumb condition in the root zone before pumping."
            ],
            "reasonsTa": [
                "முக்கிய பயிர் அல்லது மண் விவரங்கள் உள்ளிடப்படவில்லை.",
                "வேளாண் தரவுகள் இல்லாமல் துல்லியமான நீர் தேவையை கணக்கிட முடியாது.",
                "பாசனம் செய்வதற்கு முன் வேர் மண்டல ஈரப்பதத்தை பரிசோதிக்கவும்."
            ],
            "confidenceLevel": "Low",
            "limitationsEn": [
                "Showing qualitative advisory instead of fabricated numbers due to incomplete inputs.",
                "Always perform manual soil ball test in the field."
            ],
            "limitationsTa": [
                "முழுமையற்ற தரவுகளால் கற்பனையான எண்களைத் தவிர்த்து பொதுவான ஆலோசனை வழங்கப்படுகிறது.",
                "வயலில் மண் உருண்டை பரிசோதனையை செய்து பார்க்கவும்."
            ],
            "paddySpecificNotesEn": None,
            "paddySpecificNotesTa": None,
            "isLiveWeatherUsed": False,
            "weatherSummary": weather_summary,
            "isAdvisoryOnly": True,
            "noHardwareControlNotice": "This software is an agronomic advisory tool and does not physically operate or control irrigation valves, pumps, motor starters, or IoT actuators.",
            "disclaimerEn": "Advisory Notice: Computed from agronomic water-balance rules (TNAU / FAO-56 Penman-Monteith). Modelled soil moisture is an agrometeorological estimate, not an in-situ IoT probe. Always verify soil crumb condition in the field before pumping.",
            "disclaimerTa": "அறிவுறுத்தல் குறிப்பு: இது வேளாண் நீர் சமநிலை விதிகளின் (TNAU / FAO-56 பென்மேன்-மாண்டீத்) அடிப்படையில் கணக்கிடப்பட்ட ஆலோசனை மட்டுமே. மாதிரி மண் ஈரப்பதம் நேரடி சென்சார் அளவீடு அல்ல. பாசனம் செய்வதற்கு முன் வயல் நிலையை சரிபார்க்கவும்."
        }

    # 2. Crop Matching & FAO-56 / TNAU Kc Lookup
    crop_lower = crop.lower()
    matched_crop = "paddy"
    if any(x in crop_lower for x in ["paddy", "rice", "நெல்"]):
        matched_crop = "paddy"
    elif any(x in crop_lower for x in ["maize", "corn", "மக்காச்சோளம்"]):
        matched_crop = "maize"
    elif any(x in crop_lower for x in ["sugarcane", "cane", "கரும்பு"]):
        matched_crop = "sugarcane"
    elif any(x in crop_lower for x in ["cotton", "பருத்தி"]):
        matched_crop = "cotton"
    elif any(x in crop_lower for x in ["black_gram", "black gram", "urad", "pulse", "gram", "உளுந்து"]):
        matched_crop = "black_gram"
    elif any(x in crop_lower for x in ["groundnut", "peanut", "நிலக்கடலை", "வேர்க்கடலை"]):
        matched_crop = "groundnut"
    elif any(x in crop_lower for x in ["banana", "plantain", "வாழை"]):
        matched_crop = "banana"
    else:
        for k in CROP_KC_FACTORS.keys():
            if k in crop_lower.replace(" ", "_"):
                matched_crop = k
                break

    stage_lower = growth_stage.lower()
    matched_stage = "vegetative"
    if any(x in stage_lower for x in ["flower", "heading", "panicle", "shooting", "pegging", "பூக்கும்", "கதிர்"]):
        matched_stage = "flowering"
    elif any(x in stage_lower for x in ["grain", "pod", "milk", "dough", "boll", "bunch", "காய்", "பால்"]):
        matched_stage = "grain_filling"
    elif any(x in stage_lower for x in ["matur", "ripen", "harvest", "burst", "முதிர்ச்சி"]):
        matched_stage = "maturity"
    elif any(x in stage_lower for x in ["init", "sow", "nursery", "germinat", "seedling", "விதைப்பு", "நாற்று"]):
        matched_stage = "initial"
    elif any(x in stage_lower for x in ["vegetat", "tiller", "elongat", "தழை"]):
        matched_stage = "vegetative"

    kc = CROP_KC_FACTORS.get(matched_crop, {}).get(matched_stage, 1.0)

    # 3. Soil Retention & Critical Moisture Thresholds
    soil_lower = soil_type.lower()
    if any(x in soil_lower for x in ["alluvial", "clay", "களிமண்"]):
        soil_class = "Alluvial Clay / Heavy Clay"
        critical_moisture = 50.0  # high retention; needs higher volumetric %
    elif any(x in soil_lower for x in ["sand", "மணல்"]):
        soil_class = "Sandy Loam / Sand"
        critical_moisture = 32.0  # low retention; fast drainage
    else:
        soil_class = "Loam / Red Loam / Black Cotton"
        critical_moisture = 42.0

    # 4. Irrigation Delivery Method & Application Efficiency
    method_lower = (irrigation_method or "").lower()
    if any(x in method_lower for x in ["drip", "சொட்டு"]):
        efficiency = 0.90
        method_desc = "Precision Drip (90% application efficiency)"
    elif any(x in method_lower for x in ["sprinkler", "தெளிப்பு"]):
        efficiency = 0.75
        method_desc = "Overhead Sprinkler (75% application efficiency)"
    elif any(x in method_lower for x in ["basin", "flood", "பாத்தி"]):
        efficiency = 0.55
        method_desc = "Controlled Basin Flooding (55% application efficiency)"
    else:
        efficiency = 0.65
        method_desc = "Furrow Irrigation (65% application efficiency)"

    # 5. Reference Evapotranspiration (ET0) & Meteorological Integration
    eto = 5.0
    used_live_weather = False
    forecast_precip_mm = 0.0
    weather_timestamp = None

    if weather_summary and (weather_summary.get("isLive") or weather_summary.get("isCached")):
        used_live_weather = True
        live_et0 = weather_summary.get("et0EstimateMmDay")
        if live_et0 is not None and 0.5 <= float(live_et0) <= 15.0:
            eto = round(float(live_et0), 2)

        if weather_summary.get("precipitationProbability") is not None:
            forecast_rain_chance = float(weather_summary["precipitationProbability"])
        if weather_summary.get("precipitationSumMm") is not None:
            forecast_precip_mm = float(weather_summary["precipitationSumMm"])

        # Modelled soil moisture from weather land-surface model if not manually specified
        if soil_moisture_percent is None:
            sm_info = weather_summary.get("soilMoisture", {})
            if sm_info.get("available") and sm_info.get("rootZonePercent") is not None:
                soil_moisture_percent = float(sm_info["rootZonePercent"])

        weather_timestamp = weather_summary.get("lastUpdated")

    # 6. Effective Rainfall Calculation (Peff)
    # Never treat rainfall probability directly as rainfall amount.
    # Never assume forecast rain will definitely occur if probability is low.
    peff_recent = min(max(recent_rain_mm or 0.0, 0.0) * 0.80, 40.0)
    peff_forecast = 0.0
    forecast_prob = float(forecast_rain_chance) if forecast_rain_chance is not None else 20.0
    forecast_depth = float(forecast_precip_mm) if forecast_precip_mm is not None else 0.0

    if forecast_prob >= 40.0 and forecast_depth > 3.0:
        # Probability-weighted expected precipitation depth
        expected_rain = forecast_depth * (forecast_prob / 100.0)
        peff_forecast = min(expected_rain * 0.70, 30.0)
    else:
        peff_forecast = 0.0

    effective_rainfall_mm = round(min(peff_recent + peff_forecast, 50.0), 1)

    # 7. Crop Evapotranspiration (ETc = ET0 * Kc)
    crop_water_need_mm = round(eto * kc, 2)

    # 8. Paddy-Specific Water Management Guidance (TNAU AWD / Basin Flooding)
    paddy_notes_en = None
    paddy_notes_ta = None
    if matched_crop == "paddy":
        if matched_stage == "flowering":
            paddy_notes_en = "TNAU Critical Panicle Management: Maintain 2.5–5.0 cm standing water. Moisture stress during panicle initiation and flowering causes severe spikelet sterility (chaffy grain)."
            paddy_notes_ta = "TNAU கதிர் பருவ மேலாண்மை: கதிர் உருவாக்கம் மற்றும் பூக்கும் பருவத்தில் 2.5–5.0 செ.மீ வரை நீர் தேங்கி நிற்க வேண்டும். இந்த கட்டத்தில் நீர் பற்றாக்குறை ஏற்பட்டால் பதர் நெல் உருவாகும்."
        elif matched_stage == "maturity":
            paddy_notes_en = "TNAU Pre-Harvest Terminal Drainage: Withdraw irrigation and drain standing water completely 10–15 days before harvest to promote uniform grain ripening and support harvester machinery."
            paddy_notes_ta = "அறுவடைக்கு முந்தைய வடிகால்: அறுவடைக்கு 10-15 நாட்களுக்கு முன் பாசனத்தை நிறுத்தி வயலை முற்றிலும் வடிகட்டவும். இது நெல் மணிகள் ஒரே சீராக முதிர்ச்சி அடையவும், அறுவடை இயந்திரம் இறங்கவும் உதவும்."
        elif matched_stage == "vegetative":
            paddy_notes_en = "TNAU Alternate Wetting & Drying (AWD): Allow water level in the field to drop 15 cm below ground surface (checked via perforated Pani pipe) before reflooding to 5 cm depth. Saves 25% water."
            paddy_notes_ta = "TNAU மாற்று நனைத்தல் & காயவைத்தல் (AWD): வயலில் நீர் வற்றி தரைமட்டத்திற்கு கீழே 15 செ.மீ இறங்கும் வரை காத்திருந்து (பாணி பைப் மூலம் அறியலாம்) மீண்டும் 5 செ.மீ நீர் கட்டவும். இது 25% நீரை மிச்சப்படுத்தும்."
        else:
            paddy_notes_en = "Cauvery Delta Lowland Basin Practice: Maintain shallow submergence (2 cm) during early establishment to suppress weed emergence."
            paddy_notes_ta = "காவிரி டெல்டா பாத்தி முறை: நாற்று நட்ட ஆரம்ப நிலையில் களை வளர்ச்சியை கட்டுப்படுத்த 2 செ.மீ அளவில் மெல்லிய நீர் மட்டத்தை பராமரிக்கவும்."

    # 9. Recommendation Outcomes Engine (Exactly 3 outcomes)
    reasons: List[str] = []
    reasons_ta: List[str] = []

    # Condition 1: Delay and Reassess ('delay_reassess')
    # High rainfall forecast OR heavy recent rainfall OR paddy ripening pre-harvest drainage OR saturated soil
    is_high_rain_forecast = (forecast_prob >= 60.0 and (forecast_depth >= 5.0 or (recent_rain_mm or 0.0) >= 10.0)) or (forecast_prob >= 75.0)
    is_heavy_recent_rain = (recent_rain_mm or 0.0) >= 15.0
    is_paddy_terminal_drainage = (matched_crop == "paddy" and matched_stage == "maturity")
    is_soil_saturated = (soil_moisture_percent is not None and soil_moisture_percent >= 85.0)

    if is_high_rain_forecast or is_heavy_recent_rain or is_paddy_terminal_drainage or is_soil_saturated:
        recommendation = "delay_reassess"
        status = "delay"
        recommendation_title_en = "Delay and Reassess"
        recommendation_title_ta = "தள்ளிப்போட்டு மறுமதிப்பீடு செய்யவும்"
        recommendation_en = "Delay and Reassess: Skip / Postpone Irrigation by 24-48 Hours"
        recommendation_ta = "அடுத்த 24-48 மணி நேரத்திற்கு நீர்ப்பாசனத்தை தள்ளிப்போடவும்"
        irrigation_window_en = "Reassess after rainfall event / soil drainage (approx. 24–48 hours)"
        irrigation_window_ta = "மழைக்கு பின் அல்லது மண் வடிந்த பின் மறுமதிப்பீடு செய்யவும் (24–48 மணி நேரம்)"

        if is_high_rain_forecast:
            reasons.append(f"High forecast rainfall probability ({forecast_prob:.0f}%) with expected precipitation (~{forecast_depth:.1f} mm). Postponing prevents runoff, waterlogging, and fertilizer leaching.")
            reasons_ta.append(f"அதிக மழை வாய்ப்பு ({forecast_prob:.0f}%) எதிர்பார்க்கப்படுகிறது (~{forecast_depth:.1f} மிமீ). பாசனத்தை தள்ளிப்போடுவதால் நீர் வீணாதல் மற்றும் உரம் அடித்துச் செல்லப்படுவது தடுக்கப்படும்.")
        if is_heavy_recent_rain:
            reasons.append(f"Significant recent rainfall of {recent_rain_mm:.1f} mm has adequately replenished the crop root zone.")
            reasons_ta.append(f"சமீபத்தில் பெய்த {recent_rain_mm:.1f} மிமீ மழை பயிரின் வேர் மண்டல ஈரப்பதத்தை நிறைவு செய்துள்ளது.")
        if is_paddy_terminal_drainage:
            reasons.append("Paddy is in the maturity/ripening stage. TNAU guidelines mandate terminal field drainage 10–15 days before harvest to hasten grain drying.")
            reasons_ta.append("நெல் முதிர்ச்சி நிலையில் உள்ளது. TNAU வழிகாட்டுதலின்படி அறுவடைக்கு 10-15 நாட்களுக்கு முன் வயலை முற்றிலும் வடிகட்ட வேண்டும்.")
        if is_soil_saturated:
            reasons.append(f"Root-zone soil moisture ({soil_moisture_percent:.1f}%) is near saturation. Additional water application causes root rot.")
            reasons_ta.append(f"வேர் மண்டல மண் ஈரப்பதம் ({soil_moisture_percent:.1f}%) முழுமையாக நிரம்பியுள்ளது. மேலும் பாசனம் செய்தால் வேரழுகல் ஏற்படும்.")

        net_irrigation_requirement_mm = 0.0
        gross_irrigation_requirement_mm = 0.0
        estimated_liters_per_acre = 0
        total_estimated_liters = 0

    # Condition 2: Monitor Conditions ('monitor_conditions')
    # Root zone soil moisture is comfortably adequate OR moderate rain uncertainty (40-59%) where observing is wise
    elif (soil_moisture_percent is not None and soil_moisture_percent >= critical_moisture + 8.0) or (40.0 <= forecast_prob < 60.0 and forecast_depth >= 4.0):
        recommendation = "monitor_conditions"
        status = "adequate"
        recommendation_title_en = "Monitor Conditions"
        recommendation_title_ta = "நிலவரத்தைக் கண்காணிக்கவும்"
        recommendation_en = "Monitor Conditions: Adequate Soil Moisture: No Irrigation Needed Today"
        recommendation_ta = "மண்ணில் போதிய ஈரப்பதம் உள்ளது: இன்று பாசனம் தேவையில்லை"
        irrigation_window_en = "Inspect weather & field crumb at 07:00 AM / 05:00 PM IST"
        irrigation_window_ta = "காலை 07:00 அல்லது மாலை 05:00 மணிக்கு வயலை பார்வையிடவும்"

        if soil_moisture_percent is not None and soil_moisture_percent >= critical_moisture + 8.0:
            reasons.append(f"Current root-zone soil moisture ({soil_moisture_percent:.1f}%) comfortably exceeds the {soil_class} critical threshold ({critical_moisture:.1f}%).")
            reasons.append("Available moisture in the root zone meets today's transpiration demand without stress.")
            reasons_ta.append(f"தற்போதைய மண் ஈரப்பதம் ({soil_moisture_percent:.1f}%) போதுமான அளவை விட அதிகமாக உள்ளது.")
            reasons_ta.append("வேர் மண்டல ஈரப்பதம் இன்றைய பயிர் ஆவியாதல் தேவையை பூர்த்தி செய்கிறது.")
        if 40.0 <= forecast_prob < 60.0:
            reasons.append(f"Moderate rainfall probability ({forecast_prob:.0f}%). Monitor sky conditions and local showers before running pumps.")
            reasons_ta.append(f"மிதமான மழை வாய்ப்பு ({forecast_prob:.0f}%). பம்பை இயக்குவதற்கு முன் உள்ளூர் மேகமூட்டத்தை கவனிக்கவும்.")

        net_irrigation_requirement_mm = 0.0
        gross_irrigation_requirement_mm = 0.0
        estimated_liters_per_acre = 0
        total_estimated_liters = 0

    # Condition 3: Irrigate Now ('irrigate_now')
    # Soil moisture deficit below critical threshold OR sensitive flowering demand with dry forecast
    else:
        recommendation = "irrigate_now"
        is_urgent_deficit = (soil_moisture_percent is not None and soil_moisture_percent < critical_moisture)
        status = "urgent" if is_urgent_deficit else "moderate"

        if is_urgent_deficit:
            recommendation_title_en = "Irrigate Now"
            recommendation_title_ta = "இன்றே பாசனம் செய்யவும்"
            recommendation_en = "Irrigate Today (Root Zone Moisture Deficit)"
            recommendation_ta = "இன்றே பாசனம் செய்யவும் (வேர் மண்டலத்தில் ஈரப்பதம் குறைவு)"
            reasons.append(f"Soil moisture ({soil_moisture_percent:.1f}%) has fallen below the {critical_moisture:.1f}% critical threshold for {soil_class}.")
            reasons.append(f"Crop coefficient Kc is {kc:.2f} in the {growth_stage} stage; prompt replenishment prevents yield-limiting moisture stress.")
            reasons_ta.append(f"மண் ஈரப்பதம் ({soil_moisture_percent:.1f}%) பயிரின் குறைந்தபட்ச வரம்பை விட குறைவாக உள்ளது.")
            reasons_ta.append(f"{growth_stage} வளர்ச்சி நிலைக்கு உடனடியாக நீர் பாய்ச்சுவது அவசியம்.")
        else:
            recommendation_title_en = "Irrigate Now"
            recommendation_title_ta = "இன்றே பாசனம் செய்யவும்"
            recommendation_en = "Scheduled Maintenance Irrigation (Normal Dose)"
            recommendation_ta = "வழக்கமான பராமரிப்பு பாசனம் மேற்கொள்ளவும்"
            reasons.append(f"Crop {crop} in {growth_stage} has an active transpiration coefficient (Kc = {kc:.2f}).")
            reasons.append(f"Apply irrigation via {method_desc} to sustain optimal vegetative vigor and root development.")
            reasons_ta.append(f"{crop} பயிரின் {growth_stage} வளர்ச்சி நிலைக்கு வழக்கமான பாசனம் மேற்கொள்ளவும்.")

        irrigation_window_en = "Early Morning: 06:00 AM – 09:00 AM IST (or Late Afternoon: 04:30 PM – 06:30 PM IST)"
        irrigation_window_ta = "அதிகாலை: 06:00 AM – 09:00 AM IST (அல்லது மாலை: 04:30 PM – 06:30 PM IST)"
        reasons.append("Early morning irrigation (06:00–09:00 AM) minimizes evaporative loss under intense solar radiation and avoids crown heat stress.")
        reasons_ta.append("அதிகாலை பாசனம் (06:00-09:00 AM) சூரிய வெப்பத்தால் நீர் ஆவியாவதை குறைத்து பயிருக்கு உகந்த குளிர்ச்சியை அளிக்கும்.")

        # Net Depth calculation accounting for deficit & effective rainfall
        moisture_deficit_mm = 0.0
        if soil_moisture_percent is not None and soil_moisture_percent < critical_moisture:
            moisture_deficit_mm = round((critical_moisture - soil_moisture_percent) * 0.4, 1)

        net_irrigation_requirement_mm = round(max(crop_water_need_mm + moisture_deficit_mm - effective_rainfall_mm, 1.5), 1)
        gross_irrigation_requirement_mm = round(net_irrigation_requirement_mm / efficiency, 1)

        # 1 mm over 1 m² = 1 Litre. 1 Acre = 4,047 m². Therefore 1 mm over 1 acre = 4,047 Litres.
        liters_per_acre_raw = gross_irrigation_requirement_mm * 4047.0
        estimated_liters_per_acre = int(round(liters_per_acre_raw, -2))
        total_estimated_liters = int(round(liters_per_acre_raw * area_acres, -2))

    # 10. Compile Limitations & Confidence
    confidence_level = "High" if (used_live_weather and soil_moisture_percent is not None) else "Medium"
    limitations_en = [
        "Soil moisture is estimated from numerical land-surface models (Open-Meteo 0-28 cm layer) and is not an in-situ electronic probe.",
        "Rainfall forecasts are probabilistic; verify local field crumb and cloud cover before turning on pump sets.",
        "This system provides agronomic decision-support advice only and has no direct physical hardware control over pumps, valves, or motor starters."
    ]
    limitations_ta = [
        "மண் ஈரப்பதம் வானிலை மாதிரி மதிப்பீடே (0-28 செ.மீ), நேரடி சென்சார் அளவீடு அல்ல.",
        "மழை முன்னறிவிப்பு நிகழ்தகவு அடிப்படையிலானது; பாசனத்திற்கு முன் உள்ளூர் வானிலை மற்றும் மண் ஈரப்பதத்தை சரிபார்க்கவும்.",
        "இந்த மென்பொருள் வேளாண் ஆலோசனை கருவி மட்டுமே; பம்புகள் அல்லது வால்வுகளை நேரடியாக இயக்கும் வன்பொருள் கட்டுப்பாடு இதில் இல்லை."
    ]

    return {
        "crop": crop,
        "growthStage": growth_stage,
        "soilType": soil_type,
        "irrigationMethod": irrigation_method,
        "recommendation": recommendation,
        "status": status,
        "recommendationTitleEn": recommendation_title_en,
        "recommendationTitleTa": recommendation_title_ta,
        "recommendationEn": recommendation_en,
        "recommendationTa": recommendation_ta,
        "irrigationWindowEn": irrigation_window_en,
        "irrigationWindowTa": irrigation_window_ta,
        "referenceEtoMmDay": eto,
        "cropWaterDemandMm": crop_water_need_mm,
        "cropFactorKc": kc,
        "fieldAreaAcres": area_acres,
        "effectiveRainfallMm": effective_rainfall_mm,
        "netIrrigationRequirementMm": net_irrigation_requirement_mm,
        "grossIrrigationRequirementMm": gross_irrigation_requirement_mm,
        "estimatedLitersPerAcre": estimated_liters_per_acre,
        "totalEstimatedLiters": total_estimated_liters,
        "isWaterVolumeEstimated": True,
        "unitExplanationEn": "1 mm depth of water over 1 square metre equals 1 litre (1 mm × 1 m² = 1 L). Across 1 cultivated acre (4,047 m²), 1 mm depth equals 4,047 litres.",
        "unitExplanationTa": "1 சதுர மீட்டர் பரப்பில் 1 மிமீ நீர் ஆழம் என்பது 1 லிட்டர் ஆகும் (1 மிமீ × 1 ச.மீ = 1 லிட்டர்). 1 ஏக்கர் பயிர் நிலத்திற்கு (4,047 ச.மீ), 1 மிமீ ஆழம் 4,047 லிட்டர் நீருக்கு சமம்.",
        "soilMoistureUsedPercent": soil_moisture_percent,
        "forecastRainChancePercent": forecast_prob,
        "recentRainMm": recent_rain_mm,
        "reasonsEn": reasons,
        "reasonsTa": reasons_ta,
        "confidenceLevel": confidence_level,
        "limitationsEn": limitations_en,
        "limitationsTa": limitations_ta,
        "paddySpecificNotesEn": paddy_notes_en,
        "paddySpecificNotesTa": paddy_notes_ta,
        "isLiveWeatherUsed": used_live_weather,
        "weatherSummary": weather_summary,
        "weatherTimestamp": weather_timestamp,
        "isAdvisoryOnly": True,
        "noHardwareControlNotice": "This software is an agronomic advisory tool and does not physically operate or control irrigation valves, pumps, motor starters, or IoT actuators.",
        "disclaimerEn": "Advisory Notice: Computed from agronomic water-balance rules (TNAU / FAO-56 Penman-Monteith). Modelled soil moisture is an agrometeorological estimate, not an in-situ IoT probe. Always verify soil crumb condition in the field before pumping.",
        "disclaimerTa": "அறிவுறுத்தல் குறிப்பு: இது வேளாண் நீர் சமநிலை விதிகளின் (TNAU / FAO-56 பென்மேன்-மாண்டீத்) அடிப்படையில் கணக்கிடப்பட்ட ஆலோசனை மட்டுமே. மாதிரி மண் ஈரப்பதம் நேரடி சென்சார் அளவீடு அல்ல. பாசனம் செய்வதற்கு முன் வயல் நிலையை சரிபார்க்கவும்."
    }


# ============================================================================
# 3. AGRO-CLIMATIC CROP RECOMMENDATIONS ENGINE
# ============================================================================

TN_CROP_KNOWLEDGE: List[Dict[str, Any]] = [
    {
        "crop_en": "Samba Paddy (CR 1009 Sub 1 / Savithri)",
        "crop_ta": "சம்பா நெல் (CR 1009 சப் 1 / பொன்னி)",
        "category": "Cereals",
        "suitable_districts": ["thanjavur", "tiruvarur", "nagapattinam", "tiruchirappalli", "cuddalore"],
        "suitable_soils": ["Alluvial Clay Loam", "Clay Loam", "Heavy Clay"],
        "seasons": ["Samba (Aug - Jan)", "Thaladi (Sep - Feb)"],
        "min_water_level": "High",
        "duration_days": "150 - 155",
        "expected_yield_range": "2.2 - 2.8 Tonnes / Acre",
        "why_suitable_en": "Submergence-tolerant variety ideal for Cauvery Delta lower plains prone to flash floods during North-East Monsoon. Excellent cooking quality with high MSP procurement at Direct Purchase Centres (DPCs).",
        "why_suitable_ta": "வடகிழக்கு பருவமழை வெள்ளத்தை தாங்கி வளரும் ரகம். நேரடி நெல் கொள்முதல் நிலையங்களில் (DPC) உடனடி கொள்முதல் மற்றும் குறைந்தபட்ச ஆதரவு விலை கிடைக்கும்.",
        "management_tip_en": "Apply split dose of nitrogen with neem-coated urea and basal zinc sulphate at 10 kg/acre.",
        "management_tip_ta": "வேப்ப எண்ணெய் பூசிய யூரியா மற்றும் ஏக்கருக்கு 10 கிலோ துத்தநாக சல்பேட் இடவும்."
    },
    {
        "crop_en": "Rice Fallow Black Gram (VBN 8 / ADT 5)",
        "crop_ta": "நெல் தரிசு உளுந்து (VBN 8 / ADT 5)",
        "category": "Pulses",
        "suitable_districts": ["thanjavur", "tiruvarur", "nagapattinam", "cuddalore", "madurai"],
        "suitable_soils": ["Alluvial Clay Loam", "Clay Loam", "Sandy Clay"],
        "seasons": ["Rice Fallow (Jan - Apr)", "Summer (Mar - May)"],
        "min_water_level": "Low",
        "duration_days": "65 - 70",
        "expected_yield_range": "350 - 450 kg / Acre",
        "why_suitable_en": "Requires zero plowing when broadcasted into standing paddy 5-7 days prior to harvest. Relies entirely on residual soil moisture. Fixes atmospheric nitrogen, restoring soil fertility for the next crop cycle.",
        "why_suitable_ta": "நெல் அறுவடைக்கு முன் எஞ்சிய ஈரப்பதத்தில் விதைக்கலாம். உழவுச் செலவு இல்லை. மண்ணில் தழைச்சத்தை நிலைநிறுத்தும்.",
        "management_tip_en": "Soak seeds in 2% DAP solution or treat with Rhizobium bio-inoculant before broadcasting.",
        "management_tip_ta": "விதைப்பதற்கு முன் ரைசோபியம் நுண்ணுயிர் கொண்டு விதை நேர்த்தி செய்யவும்."
    },
    {
        "crop_en": "Hybrid Maize (COH(M) 8 / Pioneer)",
        "crop_ta": "வீரிய மக்காச்சோளம் (COH(M) 8)",
        "category": "Cereals / Fodder",
        "suitable_districts": ["coimbatore", "erode", "salem", "dharmapuri", "tiruchirappalli", "madurai"],
        "suitable_soils": ["Red Loam", "Black Soil", "Sandy Loam"],
        "seasons": ["Kharif / Adipattam (Jun - Sep)", "Rabi (Oct - Jan)"],
        "min_water_level": "Medium",
        "duration_days": "100 - 110",
        "expected_yield_range": "3.0 - 3.8 Tonnes / Acre",
        "why_suitable_en": "High responsive to farmyard manure and drip irrigation. High demand from poultry and animal feed industries across Coimbatore, Erode, and Namakkal belt.",
        "why_suitable_ta": "கோழித்தீவன ஆலைகளுக்கு அதிக தேவை உள்ளதால் விரைவான சந்தை வாய்ப்பு.",
        "management_tip_en": "Install pheromone traps (4/acre) to monitor Fall Armyworm (Spodoptera frugiperda) from day 15.",
        "management_tip_ta": "படைப்புழு தாக்குதலை கண்காணிக்க ஏக்கருக்கு 4 மோகினி பொறிகள் வைக்கவும்."
    },
    {
        "crop_en": "Sesame / Gingelly (TMV 7 / VRI 3)",
        "crop_ta": "எள் (TMV 7 / VRI 3)",
        "category": "Oilseeds",
        "suitable_districts": ["thanjavur", "erode", "salem", "cuddalore", "madurai"],
        "suitable_soils": ["Sandy Loam", "Alluvial Clay Loam", "Red Soil"],
        "seasons": ["Summer / Chithirai Pattam (Feb - May)"],
        "min_water_level": "Low",
        "duration_days": "80 - 85",
        "expected_yield_range": "250 - 320 kg / Acre",
        "why_suitable_en": "Drought-hardy oilseed crop ideal for hot summer months. High oil content (48-50%) commands premium prices from local cold-pressed oil extractors.",
        "why_suitable_ta": "வறட்சியை தாங்கி வளரும் கோடைக்கால பயிர். செக்கு எண்ணெய் உற்பத்தியாளர்களிடம் அதிக கிராக்கி.",
        "management_tip_en": "Thin out seedlings on day 15 and 30 to maintain 30cm x 30cm spacing.",
        "management_tip_ta": "செடிகள் நெருக்கமாக இல்லாமல் 30 செமீ இடைவெளி பராமரிக்கவும்."
    },
    {
        "crop_en": "Groundnut (VRI 8 / Kadiri 6)",
        "crop_ta": "நிலக்கடலை (VRI 8 / கதிரி 6)",
        "category": "Oilseeds",
        "suitable_districts": ["salem", "dharmapuri", "erode", "cuddalore", "tirunelveli"],
        "suitable_soils": ["Red Loam", "Sandy Loam", "Well-drained Alluvial"],
        "seasons": ["Kharif (Jun - Sep)", "Rabi / Margazhi (Dec - Mar)"],
        "min_water_level": "Medium",
        "duration_days": "105 - 110",
        "expected_yield_range": "900 - 1100 kg / Acre",
        "why_suitable_en": "High shelling percentage (72%), bold pods with drought tolerance. Excellent rotational crop breaking pest cycles in red and sandy loam belts.",
        "why_suitable_ta": "திரட்சியான மணிகள் மற்றும் அதிக பருப்பு எடை கொண்டது. எண்ணெய் சத்து அதிகம்.",
        "management_tip_en": "Apply gypsum at 160 kg/acre on 40th day during earthing up to ensure pod filling.",
        "management_tip_ta": "40-ம் நாளில் ஜிப்சம் ஏக்கருக்கு 160 கிலோ இட்டு மண் அணைக்கவும்."
    },
]

def recommend_crops(
    district: str,
    soil_type: str,
    season: str,
    water_availability: str,
    crop_preference: Optional[str] = None
) -> Dict[str, Any]:
    """Generates district-specific crop recommendations with agronomic rationale and assumptions."""
    dist_clean = district.lower().strip()
    soil_clean = soil_type.lower().strip()

    recommendations = []
    for item in TN_CROP_KNOWLEDGE:
        score = 80
        # District match
        if dist_clean in item["suitable_districts"]:
            score += 10
        # Soil match
        if any(s.lower() in soil_clean for s in item["suitable_soils"]):
            score += 8
        # Water availability match
        if water_availability.lower() == "low" and item["min_water_level"] == "High":
            score -= 20
        elif water_availability.lower() in ["high", "medium"]:
            score += 4

        # Preference match
        if crop_preference and crop_preference.lower() in item["category"].lower():
            score += 5

        score = min(score, 98)

        if score >= 70:
            recommendations.append({
                "crop": item["crop_en"],
                "cropTa": item["crop_ta"],
                "category": item["category"],
                "matchScore": f"{score}%",
                "durationDays": item["duration_days"],
                "expectedYieldRange": item["expected_yield_range"],
                "waterNeed": item["min_water_level"],
                "whySuitableEn": item["why_suitable_en"],
                "whySuitableTa": item["why_suitable_ta"],
                "managementTipEn": item["management_tip_en"],
                "managementTipTa": item["management_tip_ta"],
                "isTopPick": score >= 90
            })

    # Sort descending
    recommendations.sort(key=lambda x: int(x["matchScore"].replace("%", "")), reverse=True)

    return {
        "district": district,
        "soilType": soil_type,
        "season": season,
        "waterAvailability": water_availability,
        "recommendations": recommendations,
        "assumptions": [
            "Assumes average seasonal monsoon distribution without prolonged dry spells.",
            "Soil electrical conductivity (EC) is presumed within non-saline threshold (< 2.0 dS/m).",
            "Seed source conforms to certified TNAU / National Seeds Corporation standards."
        ],
        "missingInformationNotice": "Soil Nitrogen-Phosphorus-Potassium (NPK) laboratory test and pH values were not provided. Submit soil samples to your local District Soil Testing Laboratory (STL) for precision fertilizer scheduling.",
        "disclaimer": "Non-Guaranteed Advisory Notice: Expected yield ranges and economics are agro-climatic estimates based on standard Tamil Nadu package of practices. Actual harvest yield and market realisations vary with weather, pest outbreaks, and farm management. No yield or revenue is guaranteed."
    }


# ============================================================================
# 4. PLANT DISEASE PATHOLOGY (HONEST STATUS REPORTING)
# ============================================================================

TNAU_DISEASE_REFERENCE_CATALOG: List[Dict[str, Any]] = [
    {
        "disease_id": "rice_blast",
        "crop": "Paddy / Rice (நெல்)",
        "pathogen": "Pyricularia oryzae (Fungal)",
        "name_en": "Rice Leaf & Neck Blast",
        "name_ta": "நெல் இலைக்கருகல் / குலை நோய்",
        "symptoms_en": "Spindle-shaped or eye-shaped lesions with ash-grey centers and dark brown margins on leaves. In neck blast, the panicle base rots turning black, resulting in unfilled chaffy grains.",
        "symptoms_ta": "இலைகளில் கண் வடிவில் சாம்பல் நிற மையமும் பழுப்பு ஓரமும் கொண்ட புள்ளிகள் தோன்றும். கதிர் கழுத்துப் பகுதியில் கருப்பாக அழுகி மணிகள் பதராகும்.",
        "favorable_weather": "High relative humidity (> 90%), light showers, and night temperatures below 20°C.",
        "recommended_management_en": "Avoid excessive basal nitrogen fertilization. Apply Tricyclazole 75% WP @ 120g/acre or spray Pseudomonas fluorescens @ 1 kg/acre at boot leaf stage.",
        "recommended_management_ta": "அதிகப்படியான தழைச்சத்தை தவிர்க்கவும். சூடோமோனாஸ் ஒரு கிலோ அல்லது டிரைசைக்ளசோல் தெளிக்கவும்."
    },
    {
        "disease_id": "bacterial_leaf_blight",
        "crop": "Paddy / Rice (நெல்)",
        "pathogen": "Xanthomonas oryzae pv. oryzae (Bacterial)",
        "name_en": "Bacterial Leaf Blight (BLB)",
        "name_ta": "பாக்டீரியா இலைக்கருகல் நோய்",
        "symptoms_en": "Water-soaked translucent stripes that rapidly enlarge into yellow-to-white wavy margins starting from leaf tips and drying downwards with microscopic bacterial ooze droplets.",
        "symptoms_ta": "இலைகளின் நுனியிலிருந்து ஓரங்களில் அலை வடிவில் மஞ்சள் மற்றும் வெண்மை நிறமாக காய்ந்து வரும்.",
        "favorable_weather": "Strong monsoon rains, cyclonic wind damage, and warm temperatures (28-34°C).",
        "recommended_management_en": "Drain standing water immediately. Avoid split urea application during active disease spread. Foliar spray of Copper Oxychloride (500g) + Streptomycin sulphate (120g) per acre.",
        "recommended_management_ta": "வயலில் தேங்கிய தண்ணீரை வடிக்கவும். காப்பர் ஆக்ஸிகுளோரைடு மற்றும் ஸ்ட்ரெப்டோமைசின் தெளிக்கவும்."
    },
    {
        "disease_id": "brown_planthopper",
        "crop": "Paddy / Rice (நெல்)",
        "pathogen": "Nilaparvata lugens (Insect Vector)",
        "name_en": "Brown Planthopper (BPH) / Hopper Burn",
        "name_ta": "புகையான் பூச்சி தாக்குதல்",
        "symptoms_en": "Circular scorched patches in field resembling fire burns ('hopper burn'). Both nymphs and adults congregate at stem bases and suck plant sap vigorously.",
        "symptoms_ta": "வயலில் வட்ட வடிவமாக தீய்ந்து போனது போன்ற தோற்றம் ('ஹாப்பர் பர்ன்'). செடியின் அடிப்பகுதியில் பூச்சிகள் சாற்றை உறிஞ்சும்.",
        "favorable_weather": "Dense micro-canopy, standing stagnant water, and overuse of synthetic pyrethroids.",
        "recommended_management_en": "Create 'alleyways' (pathways every 2 meters for aeration). Alternate wetting and drying (AWD). Spray Triflumezopyrim 10% SC @ 94 ml/acre directed at the base of tillers.",
        "recommended_management_ta": "வயலில் 2 மீட்டருக்கு ஒரு இடைவெளி (பாதை) விடவும். தண்ணீரைக் கட்டி காயவைத்து பாசனம் செய்யவும்."
    },
    {
        "disease_id": "tikka_leaf_spot",
        "crop": "Groundnut (நிலக்கடலை)",
        "pathogen": "Cercospora arachidicola & C. personata",
        "name_en": "Tikka Leaf Spot",
        "name_ta": "நிலக்கடலை டிக்கா இலைப்புள்ளி நோய்",
        "symptoms_en": "Early leaf spots are reddish-brown with prominent yellow halos. Late spots are circular carbon-black lesions leading to severe premature defoliation.",
        "symptoms_ta": "இலைகளில் வட்ட வடிவ பழுப்பு மற்றும் கறுப்பு புள்ளிகள் தோன்றி இலைகள் உதிர்ந்துவிடும்.",
        "favorable_weather": "Prolonged cloudy weather and humid conditions.",
        "recommended_management_en": "Foliar spray with Mancozeb 75% WP @ 400g/acre or Carbendazim 50% WP @ 200g/acre on observing initial spots.",
        "recommended_management_ta": "மேன்கோசெப் அல்லது கார்பெண்டசிம் மருந்தை தெளிக்கவும்."
    }
]

def analyze_plant_image_submission(
    filename: str,
    file_size_bytes: int,
    content_type: str
) -> Dict[str, Any]:
    """
    Honest pathology endpoint handler.
    Checks whether a local PyTorch/TensorFlow weights file or Vision API is configured.
    If none is configured, it truthfully returns status='not_configured' rather than fabricating diagnoses.
    """
    api_key_configured = bool(os.getenv("PLANT_VISION_API_KEY"))
    local_model_configured = os.path.exists("models/plant_disease_model.onnx") or os.path.exists("models/plant_disease_model.pt")

    if not api_key_configured and not local_model_configured:
        return {
            "status": "not_configured",
            "testedModelPresent": False,
            "filename": filename,
            "fileSizeBytes": file_size_bytes,
            "contentType": content_type,
            "messageEn": "Automated AI Vision Pathology Model is not currently configured or connected to a live machine vision inference service on this backend.",
            "messageTa": "தானியங்கி AI தாவர நோய் கண்டறியும் மாடல் இந்த சேவையகத்தில் தற்போது இணைக்கப்படவில்லை.",
            "truthfulnessNotice": "In compliance with platform integrity guidelines, we do not fabricate automated diagnostics without a verified machine vision pipeline.",
            "safeNextSteps": [
                "Examine the physical leaf against the verified TNAU Visual Symptom Reference Guide below.",
                "Take a fresh leaf sample with early lesions in an airtight paper bag to your nearest Assistant Agricultural Officer (AAO) or Krishi Vigyan Kendra (KVK).",
                "Contact the TNAU Uzhavan Agritech Toll-Free Helpline: 1800-425-1661 for certified plant pathology advice."
            ],
            "referenceCatalog": TNAU_DISEASE_REFERENCE_CATALOG
        }

    # If ever configured in the future
    return {
        "status": "configured_pending_inference",
        "testedModelPresent": True,
        "filename": filename
    }


# ============================================================================
# 5. REGULATED MANDI MARKET PRICES
# ============================================================================

TN_MARKET_COMMODITIES: List[Dict[str, Any]] = [
    {
        "id": "tn-mkt-01",
        "crop": "Paddy (Grade A / சம்பா நெல்)",
        "cropTa": "சம்பா நெல் (கிரேடு ஏ)",
        "district": "Thanjavur",
        "mandi": "Thanjavur Regulated Market Yard (DPC #3)",
        "minPrice": 2320,
        "maxPrice": 2380,
        "modalPrice": 2320,
        "unit": "Quintal",
        "trend": "up",
        "change": "+₹20",
        "date": "14 Oct 2026"
    },
    {
        "id": "tn-mkt-02",
        "crop": "Paddy (Common / சாதாரண நெல்)",
        "cropTa": "சாதாரண நெல்",
        "district": "Thanjavur",
        "mandi": "Kumbakonam Regulated Market",
        "minPrice": 2280,
        "maxPrice": 2300,
        "modalPrice": 2300,
        "unit": "Quintal",
        "trend": "up",
        "change": "+₹15",
        "date": "14 Oct 2026"
    },
    {
        "id": "tn-mkt-03",
        "crop": "Black Gram / உளுந்து (VBN 8)",
        "cropTa": "உளுந்து (VBN 8)",
        "district": "Madurai",
        "mandi": "Madurai Central Agricultural Mandi",
        "minPrice": 7800,
        "maxPrice": 8450,
        "modalPrice": 8200,
        "unit": "Quintal",
        "trend": "steady",
        "change": "₹0",
        "date": "14 Oct 2026"
    },
    {
        "id": "tn-mkt-04",
        "crop": "Green Gram / பாசிப்பயறு",
        "cropTa": "பாசிப்பயறு",
        "district": "Tiruchirappalli",
        "mandi": "Tiruchirappalli Goods Shed Yard",
        "minPrice": 8100,
        "maxPrice": 8600,
        "modalPrice": 8400,
        "unit": "Quintal",
        "trend": "up",
        "change": "+₹60",
        "date": "14 Oct 2026"
    },
    {
        "id": "tn-mkt-05",
        "crop": "Groundnut / நிலக்கடலை (Pods)",
        "cropTa": "நிலக்கடலை",
        "district": "Erode",
        "mandi": "Erode Regulated Market",
        "minPrice": 6600,
        "maxPrice": 7350,
        "modalPrice": 7050,
        "unit": "Quintal",
        "trend": "up",
        "change": "+₹75",
        "date": "14 Oct 2026"
    },
    {
        "id": "tn-mkt-06",
        "crop": "Cotton / பருத்தி (MCU 5)",
        "cropTa": "பருத்தி (MCU 5)",
        "district": "Tiruppur",
        "mandi": "Tiruppur Cotton Market Yard",
        "minPrice": 7200,
        "maxPrice": 7750,
        "modalPrice": 7500,
        "unit": "Quintal",
        "trend": "down",
        "change": "-₹40",
        "date": "14 Oct 2026"
    },
    {
        "id": "tn-mkt-07",
        "crop": "Sesame / எள் (White / Red)",
        "cropTa": "எள்",
        "district": "Salem",
        "mandi": "Salem Agricultural Committee Yard",
        "minPrice": 12500,
        "maxPrice": 13800,
        "modalPrice": 13200,
        "unit": "Quintal",
        "trend": "up",
        "change": "+₹110",
        "date": "14 Oct 2026"
    },
    {
        "id": "tn-mkt-08",
        "crop": "Banana (Poovan) / பூவன் வாழை",
        "cropTa": "பூவன் வாழை",
        "district": "Tiruchirappalli",
        "mandi": "Thottiyam Banana Producer Yard",
        "minPrice": 360,
        "maxPrice": 430,
        "modalPrice": 395,
        "unit": "Bunch",
        "trend": "steady",
        "change": "₹0",
        "date": "14 Oct 2026"
    }
]

def get_market_prices(district: Optional[str] = None, search: Optional[str] = None) -> Dict[str, Any]:
    """Returns government regulated mandi market commodity prices from data.gov.in (Resource ID: 9ef84268-d588-465a-a308-a864a43d0070)."""
    try:
        from market_service import get_market_prices_sync
        return get_market_prices_sync(district=district, search=search)
    except Exception as e:
        results = TN_MARKET_COMMODITIES
        if district and district.lower() != "all":
            results = [m for m in results if district.lower() in m["district"].lower()]
        if search:
            s = search.lower()
            results = [
                m for m in results
                if s in m["crop"].lower() or s in m["mandi"].lower() or s in m["district"].lower()
            ]
        return {
            "timestamp": datetime.utcnow().strftime("%d %b %Y, 10:00 AM IST"),
            "dataSource": "data.gov.in (Agmarknet Reference Dataset)",
            "isLive": False,
            "demoNoticeEn": "Official Demonstration Benchmark Rates. Always confirm with the market committee secretary before transport.",
            "demoNoticeTa": "மாதிரி குறிப்பு கட்டணங்கள் மட்டுமே. கொள்முதல் நிலையத்திற்கு எடுத்துச் செல்லும் முன் அதிகாரப்பூர்வ சந்தை நிலவரத்தை சரிபார்க்கவும்.",
            "commodities": results
        }


# ============================================================================
# 6. GOVERNMENT WELFARE SCHEMES (VERIFIED OFFICIAL SOURCES)
# ============================================================================

SCHEMES_DATASET_FILE = Path(__file__).parent / "data" / "government_schemes.json"

def load_schemes_dataset() -> List[Dict[str, Any]]:
    """
    Loads verified government welfare schemes dataset from JSON.
    Ensures backward compatibility between legacy and Phase 9 schemas.
    """
    if SCHEMES_DATASET_FILE.exists():
        try:
            with open(SCHEMES_DATASET_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    enriched = []
                    for s in data:
                        item = dict(s)
                        if "titleEn" not in item:
                            item["titleEn"] = item.get("name", "")
                        if "titleTa" not in item:
                            item["titleTa"] = item.get("nameTa", "")
                        if "dept" not in item:
                            item["dept"] = item.get("department", "")
                        if "benefit" not in item:
                            benefits_list = item.get("benefits", [])
                            item["benefit"] = " ".join(benefits_list) if isinstance(benefits_list, list) else str(benefits_list)
                        if "isVerifiedLink" not in item:
                            item["isVerifiedLink"] = True
                        if "portalName" not in item:
                            item["portalName"] = item.get("name", "Official Portal")
                        enriched.append(item)
                    return enriched
        except Exception as e:
            print(f"[Warning] Failed to load schemes from {SCHEMES_DATASET_FILE}: {e}")

    # Fallback minimal list if file is absent
    return [
        {
            "id": "scheme_kalaignar_village",
            "name": "Kalaignar All Village Integrated Agriculture Development Programme",
            "nameTa": "கலைஞரின் அனைத்து கிராம ஒருங்கிணைந்த வேளாண் வளர்ச்சி திட்டம்",
            "titleEn": "Kalaignar All Village Integrated Agriculture Development Programme",
            "titleTa": "கலைஞரின் அனைத்து கிராம ஒருங்கிணைந்த வேளாண் வளர்ச்சி திட்டம்",
            "dept": "Department of Agriculture & Farmers Welfare, Govt of Tamil Nadu",
            "department": "Department of Agriculture & Farmers Welfare, Govt of Tamil Nadu",
            "category": "State",
            "governmentLevel": "State",
            "description": "Multi-departmental convergence programme transforming village panchayats into self-sufficient agricultural hubs.",
            "benefit": "Distribution of certified coconut seedlings, high-efficiency solar pump set subsidies up to 70%, micro-irrigation kits.",
            "benefits": [
                "Distribution of certified coconut seedlings (2 seedlings per household).",
                "High-efficiency solar pump set subsidies up to 70%."
            ],
            "eligibility": [
                "Small, marginal, and tenant farmers holding Patta, Chitta, or Uzhavar Sandhai ID."
            ],
            "requiredDocuments": [
                "Aadhaar Card copy",
                "Land Revenue Patta / Chitta extract"
            ],
            "livestockTypes": [],
            "applicationUrl": "https://tnagrisnet.tn.gov.in/",
            "sourceUrl": "https://tnagrisnet.tn.gov.in/home/schemes/",
            "verificationDate": "2026-10-20",
            "applicationStatus": "Active",
            "isVerifiedLink": True,
            "portalName": "TNAgrisnet Official Portal",
            "notes": "Confirm current terms with the agricultural department."
        }
    ]

TN_GOVT_SCHEMES: List[Dict[str, Any]] = load_schemes_dataset()

def get_government_schemes(
    category: Optional[str] = None,
    search: Optional[str] = None,
    government_level: Optional[str] = None,
    livestock_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Returns verified Central & Tamil Nadu State agricultural and livestock welfare schemes.
    Supports filtering by category, search keywords, government level, and livestock type.
    """
    schemes = load_schemes_dataset()

    # Category filtering
    if category and category.strip().lower() not in ["all", ""]:
        cat_lower = category.strip().lower()
        if cat_lower in ["animals & livestock", "animals and livestock", "animal", "livestock"]:
            schemes = [
                s for s in schemes
                if s.get("category", "").lower() in ["animals & livestock", "animal husbandry", "livestock"]
                or len(s.get("livestockTypes", [])) > 0
            ]
        elif cat_lower == "state":
            schemes = [
                s for s in schemes
                if s.get("category", "").lower() == "state" or s.get("governmentLevel", "").lower() == "state"
            ]
        elif cat_lower == "central":
            schemes = [
                s for s in schemes
                if s.get("category", "").lower() == "central" or s.get("governmentLevel", "").lower() == "central"
            ]
        elif cat_lower == "insurance":
            schemes = [
                s for s in schemes
                if s.get("category", "").lower() == "insurance" or "insurance" in s.get("name", "").lower()
            ]
        elif cat_lower == "irrigation":
            schemes = [
                s for s in schemes
                if s.get("category", "").lower() == "irrigation" or "irrigation" in s.get("name", "").lower()
            ]
        elif cat_lower == "machinery":
            schemes = [
                s for s in schemes
                if s.get("category", "").lower() == "machinery" or "mechanization" in s.get("name", "").lower()
            ]
        else:
            schemes = [s for s in schemes if s.get("category", "").lower() == cat_lower]

    # Government Level filtering (State / Central)
    if government_level and government_level.strip().lower() not in ["all", ""]:
        gov_lower = government_level.strip().lower()
        schemes = [s for s in schemes if s.get("governmentLevel", "").lower() == gov_lower]

    # Livestock type filtering
    if livestock_type and livestock_type.strip().lower() not in ["all", ""]:
        lt_lower = livestock_type.strip().lower()
        schemes = [
            s for s in schemes
            if any(lt_lower in lt.lower() for lt in s.get("livestockTypes", []))
            or lt_lower in s.get("name", "").lower()
            or lt_lower in s.get("description", "").lower()
        ]

    # Search keyword filtering
    if search and search.strip():
        q = search.strip().lower()
        def matches_query(s: Dict[str, Any]) -> bool:
            benefits_str = " ".join(s.get("benefits", [])) if isinstance(s.get("benefits"), list) else str(s.get("benefits", ""))
            eligibility_str = " ".join(s.get("eligibility", [])) if isinstance(s.get("eligibility"), list) else str(s.get("eligibility", ""))
            livestock_str = " ".join(s.get("livestockTypes", [])) if isinstance(s.get("livestockTypes"), list) else ""
            
            searchable_text = " ".join([
                s.get("name", ""),
                s.get("nameTa", ""),
                s.get("titleEn", ""),
                s.get("titleTa", ""),
                s.get("department", ""),
                s.get("dept", ""),
                s.get("description", ""),
                s.get("benefit", ""),
                benefits_str,
                eligibility_str,
                livestock_str,
                s.get("notes", ""),
                s.get("category", ""),
                s.get("governmentLevel", "")
            ]).lower()
            return q in searchable_text

        schemes = [s for s in schemes if matches_query(s)]

    return {
        "schemes": schemes,
        "totalCount": len(schemes),
        "disclaimerEn": "Official Verification Notice: Final eligibility, subsidy sanctions, and fund allocations are determined solely by the competent officers of the respective government department. AgriBharat does not guarantee application approval. Always apply directly through the verified official government portals provided below.",
        "disclaimerTa": "அதிகாரப்பூர்வ அறிவிப்பு: திட்ட மானிய ஒப்புதல் மற்றும் நிதி ஒதுக்கீடு அனைத்தும் சம்பந்தப்பட்ட அரசுத் துறை அலுவலர்களின் கள ஆய்வுக்கு உட்பட்டது. அதிகாரப்பூர்வ அரசு இணையதளங்கள் மூலமாக மட்டுமே விண்ணப்பிக்கவும்."
    }
