from flask import Flask, jsonify, g, request
from flask_cors import CORS
import Adafruit_DHT
from threading import Thread
import time
import sqlite3
import requests

DATABASE = './temp.db'

def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], value)
                for idx, value in enumerate(row))

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    db.row_factory = make_dicts
    return db
request
def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def kelvin_to_celsius(k): 
    return round(k - 273.15)

def ms_to_kmh(ms):
    return round(ms * 3.6)

app = Flask(__name__)

cors = CORS(app)

data = {"humidity": "Waiting...", "temperature": "Waiting..."}
data_outside = {"humidity": "Waiting...", "temperature": "Waiting...", "wind": "Waiting..."}

def data_thread():
    print("Data thread started")
    while True:
        humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, 17)
        data["humidity"] = humidity
        data["temperature"] = temperature
        timestamp = time.time()
        print("Sensor data captured")
        with app.app_context():
            db = get_db()
            query_db(f"INSERT INTO tempdata(temperature, humidity, timestamp) VALUES ({temperature}, {humidity}, {timestamp});")
            db.commit()
        print("Sensor data commit: success")
        params = {"q": "Rotterdam", "appid": "api_key"}
        r = requests.get("http://api.openweathermap.org/data/2.5/weather", params=params).json()
        data_outside["temperature"] = kelvin_to_celsius(r["main"]["temp"])
        data_outside["humidity"] = r["main"]["humidity"]
        data_outside["wind"] = ms_to_kmh(r["wind"]["speed"])
        print("Outside data fetched")
        with app.app_context():
            db = get_db()
            query_db(f"INSERT INTO tempdata_outside(temperature, humidity, wind, timestamp) VALUES ({data_outside['temperature']}, {data_outside['humidity']}, {data_outside['wind']}, {timestamp});")
            db.commit()
        print("Outside data commit: success")
        time.sleep(15 * 60)
 
 
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()
        
@app.route('/')
def get_data():
    return jsonify({"success": True, "data": data})

@app.route('/outside')
def get_outside():
    return jsonify({"success": True, "data": data_outside})

@app.route('/history')
def get_history():
    amount = 30
    if request.args.get("amount"):
        amount = int(request.args.get("amount"))
    history_data = query_db(f"""SELECT * FROM (
        SELECT * FROM tempdata ORDER BY timestamp DESC LIMIT {amount}
        ) sub
        ORDER BY timestamp ASC""")
    return jsonify({"success": True, "data": history_data})

@app.route('/history_outside')
def get_history_outside():
    amount = 30
    if request.args.get("amount"):
        amount = int(request.args.get("amount"))
    history_data = query_db(f"""SELECT * FROM (
        SELECT * FROM tempdata_outside ORDER BY timestamp DESC LIMIT {amount}
        ) sub
        ORDER BY timestamp ASC""")
    return jsonify({"success": True, "data": history_data})

Thread(target=data_thread).start()
app.run(host='0.0.0.0', port='8080')
