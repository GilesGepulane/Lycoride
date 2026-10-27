import os
import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

#loads the V12 6.6L engine of our Lycoride website, Heart
load_dotenv()
lycoride = Flask(__name__)

#/triggers url, then fetches token on env lesz go
@lycoride.route("/")
def crusaderslowed():
  mapbox_token = os.getenv("MAPBOX_TOKEN")
  return render_template("index.html", mapbox_token=mapbox_token)


@lycoride.route("/api/search-place")
def search_place():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "Missing search text"}), 400
    token = os.getenv("MAPBOX_TOKEN")
    try:
        r = requests.get(
            f"https://api.mapbox.com/geocoding/v5/mapbox.places/{q}.json",
            params={"access_token": token, "limit": 5, "country": "PH"},
            timeout=8,
        )
    except requests.RequestException:
        return jsonify({"error": "Could not reach Mapbox"}), 502
    if r.status_code == 429:
        return jsonify({"error": "Rate limit reached. Try again shortly."}), 429
    if not r.ok:
        return jsonify({"error": "Mapbox error"}), r.status_code 
    places = [{"name": f["place_name"], "lng": f["center"][0], "lat": f["center"][1]}
              for f in r.json()["features"]]
    return jsonify(places)


#post button requests data usapan thingy
@lycoride.route("/api/request-ride", methods=["POST"])
def request_ride():
  user_data = request.json
  pickup_location = user_data.get("pickup", "Home")

  print(f"Processing ride request for pickup at: {pickup_location}")

    #response back to browser
  return jsonify({"status": "success","message": (f"Success! Driver assigned for your pickup at {pickup_location}."),})

@lycoride.route("/api/reverse")
def reverse():
    try:
        lng = float(request.args["lng"]); lat = float(request.args["lat"])
    except (KeyError, ValueError):
        return jsonify({"error": "Missing lng/lat"}), 400
    try:
        r = requests.get(
            f"https://api.mapbox.com/geocoding/v5/mapbox.places/{lng},{lat}.json",
            params={"access_token": os.getenv("MAPBOX_TOKEN"), "limit": 1},
            timeout=8,
        )
    except requests.RequestException:
        return jsonify({"error": "Could not reach Mapbox"}), 502
    feats = r.json().get("features", []) if r.ok else []
    return jsonify({"name": feats[0]["place_name"] if feats else "Dropped pin"})

@lycoride.route("/api/route")
def route():
    try:
        a_lng, a_lat = request.args["from"].split(",")
        b_lng, b_lat = request.args["to"].split(",")
        float(a_lng), float(a_lat), float(b_lng), float(b_lat)
    except (KeyError, ValueError):
        return jsonify({"error": "Use ?from=lng,lat&to=lng,lat"}), 400
    try:
        r = requests.get(
            f"https://router.project-osrm.org/route/v1/driving/{a_lng},{a_lat};{b_lng},{b_lat}",
            params={"overview": "full", "geometries": "geojson"},
            timeout=8,
        )
    except requests.RequestException:
        return jsonify({"error": "Could not reach routing service"}), 502
    data = r.json()
    if not r.ok or not data.get("routes"):
        return jsonify({"error": "No route found"}), 404
    rt = data["routes"][0]
    return jsonify({"km": round(rt["distance"] / 1000, 1),
                    "minutes": round(rt["duration"] / 60),
                    "geometry": rt["geometry"]})

lycoride.run(host="0.0.0.0", port=5000, debug=True)
