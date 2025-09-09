import time
import numpy as np
import paho.mqtt.client as mqtt
import tensorflow as tf
import json
import os
import threading
from flask import Flask, render_template

# -------------------- MQTT + AI CONFIG --------------------
BROKER = "192.168.169.139"
PORT = 1883
KEEPALIVE = 60

# Model path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "..", "model", "time_model.h5")

time_model = tf.keras.models.load_model(MODEL_PATH, compile=False)

# Traffic state from sensors
traffic_state = [0, 0, 0, 0]

# Keep track of current lane (rotates 1→4)
current_lane = 0

# MQTT setup
def on_message(client, userdata, msg):
    global traffic_state
    topic = msg.topic
    value = int(msg.payload.decode())

    if topic == "traffic/ir1": traffic_state[0] = value
    if topic == "traffic/ir2": traffic_state[1] = value
    if topic == "traffic/ir3": traffic_state[2] = value
    if topic == "traffic/ir4": traffic_state[3] = value

client = mqtt.Client()
client.on_message = on_message
client.connect(BROKER, PORT, KEEPALIVE)

# Subscribe to IR sensors
for t in ["traffic/ir1", "traffic/ir2", "traffic/ir3", "traffic/ir4"]:
    client.subscribe(t)

client.loop_start()

# -------------------- SIGNAL LOGIC --------------------
def publish_signal(lane, green_time):
    # Announce active lane
    client.publish("signal/current", f"Lane{lane}")
    client.publish(f"signal/lane{lane}", "GREEN")
    client.publish("signal/timer", str(green_time))

    print(f"🚦 Lane{lane} → GREEN for {green_time}s (AI adaptive timing)")

    # Publish decision details for dashboard
    decision = {
        "lane": f"Lane{lane}",
        "green_time": green_time,
        "ir": traffic_state.copy(),
        "reason": "Fixed sequence (1→4), AI adaptive green time"
    }
    client.publish("decision/signal", json.dumps(decision))

    # Countdown — FIXED for this cycle
    for sec in range(green_time, 0, -1):
        client.publish("signal/timer", str(sec))
        time.sleep(1)

    # End of green → turn RED
    client.publish(f"signal/lane{lane}", "RED")

def traffic_loop():
    global current_lane
    while True:
        # Rotate lanes in fixed sequence
        current_lane = (current_lane % 4) + 1

        # Take a snapshot of the traffic state
        state = np.array(traffic_state).reshape(1, -1)

        # Predict green time ONCE per lane cycle
        time_pred = time_model.predict(state, verbose=0)
        green_time = int(time_pred[0][0])

        # Apply safety bounds
        green_time = max(5, min(30, green_time))

        # Publish and run fixed timer
        publish_signal(current_lane, green_time)

# -------------------- FLASK WEB SERVER --------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "..", "dashboard", "templates")
STATIC_DIR = os.path.join(BASE_DIR, "..", "dashboard", "static")

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)

@app.route('/')
def homepage():
    return render_template('homepage.html')

@app.route('/dashboard.html')
def dashboard_html():
    return render_template("dashboard.html")

if __name__ == "__main__":
    print("✅ Starting system...")

    # Run traffic optimizer in background thread
    threading.Thread(target=traffic_loop, daemon=True).start()

    # Run Flask web server
    app.run(host="0.0.0.0", port=5000, debug=False)
