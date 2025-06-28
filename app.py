from flask import Flask, request, jsonify, render_template
import requests

app = Flask(__name__)

EVENTBRITE_API_URL = "https://www.eventbriteapi.com/v3/events/search/"
EVENTBRITE_TOKEN = ""  # Optional: Add your token here for more results

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/heatmap")
def heatmap():
    return render_template("osm_heatmap.html")

@app.route("/find_events", methods=["POST"])
def find_events():
    data = request.json
    lat = data["lat"]
    lon = data["lon"]
    keyword = data.get("keyword", "")

    params = {
        "location.latitude": lat,
        "location.longitude": lon,
        "location.within": "50mi",
        "q": keyword,
        "expand": "venue"
    }

    headers = {"Authorization": f"Bearer {EVENTBRITE_TOKEN}"} if EVENTBRITE_TOKEN else {}

    response = requests.get(EVENTBRITE_API_URL, params=params, headers=headers)
    events = response.json().get("events", [])

    results = []
    for event in events:
        venue = event.get("venue", {})
        results.append({
            "name": event.get("name", {}).get("text", "Unnamed Event"),
            "url": event.get("url"),
            "start_time": event.get("start", {}).get("local"),
            "location": venue.get("address", {}).get("localized_address_display", "Unknown Location"),
            "lat": venue.get("latitude"),
            "lon": venue.get("longitude")
        })

    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True)
