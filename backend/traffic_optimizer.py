
import time
import json
import signal
import random
from datetime import datetime
import numpy as np
import paho.mqtt.client as mqtt
import tensorflow as tf

BROKER = "192.168.169.139"
PORT = 1883
KEEPALIVE = 60

MANUAL_AW = 15.0 
# ---- Load models (compile=False avoids Keras metric deserialization issues) ----
lane_model = tf.keras.models.load_model("model/traffic_model.h5", compile=False)
time_model = tf.keras.models.load_model("model/time_model.h5", compile=False)
lane_classes = np.load("model/lane_classes.npy", allow_pickle=True)  # ["Lane1","Lane2","Lane3","Lane4"]

# ---- Runtime state ----
traffic_state = [0, 0, 0, 0]     # latest IR readings
smoothed_state = [0, 0, 0, 0]    # EMA smoothing
alpha = 0.6

last_lane = None
repeat_count = 0
cycles = 0
served_total = 0
avg_wait = 0.0
last_decision_time = time.time()
emergency_lane = None            # e.g., "Lane2" if emergency topic triggers, otherwise None

MIN_GREEN = 7
MAX_GREEN = 40
MAX_SAME_LANE = 3                # avoid starving others
COOLDOWN_BETWEEN_DECISIONS = 1   # seconds to avoid spam if called twice

# ---- MQTT setup ----
def on_message(client, userdata, msg):
    global traffic_state, emergency_lane
    topic = msg.topic
    payload = msg.payload.decode().strip()

    if topic.startswith("traffic/ir"):
        try:
            v = int(payload)
            idx = int(topic[-1]) - 1
            traffic_state[idx] = max(0, min(1, v))  # keep 0/1
        except:
            pass

    if topic == "traffic/emergency":
        # expected payloads: off / Lane1 / Lane2 / Lane3 / Lane4
        if payload.lower() == "off":
            emergency_lane = None
        elif payload in ["Lane1","Lane2","Lane3","Lane4"]:
            emergency_lane = payload

client = mqtt.Client()
client.on_message = on_message
client.connect(BROKER, PORT, KEEPALIVE)
for t in ["traffic/ir1","traffic/ir2","traffic/ir3","traffic/ir4","traffic/emergency"]:
    client.subscribe(t)
client.loop_start()

def graceful_exit(signum, frame):
    # turn everything RED on exit
    for i in range(1,5):
        client.publish(f"signal/lane{i}", "RED", qos=0, retain=False)
    client.publish("signal/current", "—")
    client.publish("signal/timer", "0")
    client.loop_stop()
    client.disconnect()
    print("\n👋 Stopped cleanly.")
    raise SystemExit

signal.signal(signal.SIGINT, graceful_exit)
signal.signal(signal.SIGTERM, graceful_exit)

# ---- Helpers ----
def ema_smooth(prev, new):
    return alpha*new + (1-alpha)*prev

def rush_hour_weight(hour: int):
    # Give lanes 1 & 2 (say, East-West) a small bias during 8–10 & 17–20
    if 8 <= hour <= 10 or 17 <= hour <= 20:
        return np.array([1.2, 1.2, 1.0, 1.0], dtype=float)
    return np.array([1.0, 1.0, 1.0, 1.0], dtype=float)

def choose_lane(ir_vec):
    """Use model prediction, but add rush-hour weighting and fairness."""
    global last_lane, repeat_count

    # Model prediction
    logits = lane_model.predict(ir_vec.reshape(1, -1), verbose=0)[0]
    probs = tf.nn.softmax(logits).numpy()

    # Rush-hour weighting
    w = rush_hour_weight(datetime.now().hour)
    weighted = probs * w
    weighted = weighted / (weighted.sum() + 1e-9)

    # Emergency override
    if emergency_lane:
        return emergency_lane, "emergency override"

    # Prevent starving others: if same lane too often, pick next highest
    lanes_sorted = np.argsort(-weighted)  # indices 0..3
    best = lanes_sorted[0]
    lane_name = lane_classes[best]

    if last_lane == lane_name:
        repeat_count += 1
    else:
        repeat_count = 0

    if repeat_count >= MAX_SAME_LANE:
        # force the next different lane with vehicles if possible
        for idx in lanes_sorted:
            name = lane_classes[idx]
            if name != last_lane:
                lane_name = name
                break
        reason = "fairness override"
    else:
        reason = "model+rushhour"

    last_lane = lane_name
    return lane_name, reason

def choose_time(ir_vec):
    pred = time_model.predict(ir_vec.reshape(1,-1), verbose=0)[0][0]
    # clamp & adjust a bit for total demand
    total = ir_vec.sum()
    base = int(max(MIN_GREEN, min(MAX_GREEN, pred)))
    if total >= 3:
        base = min(MAX_GREEN, base + 5)
    if total == 0:
        base = MIN_GREEN
    return base

def publish_decision(lane_name, green_time, ir_vec, reason):
    # JSON for dashboard
    payload = json.dumps({
        "lane": lane_name,
        "green_time": int(green_time),
        "ir": [int(ir_vec[0]), int(ir_vec[1]), int(ir_vec[2]), int(ir_vec[3])],
        "reason": reason
    })
    client.publish("decision/signal", payload)

def set_lights(active_lane, green_time):
    # publish lane states, current & countdown
    for i in range(1,5):
        state = "GREEN" if f"Lane{i}" == active_lane else "RED"
        client.publish(f"signal/lane{i}", state)
    client.publish("signal/current", active_lane)
    client.publish("signal/timer", str(green_time))

def update_stats(ir_vec, green_time):
    # crude stats: served = number of lanes active * something; here assume vehicles present on active lane were served
    # we'll approximate wait using moving average
    global cycles, served_total, avg_wait
    cycles += 1
    served_now = int(ir_vec.sum())  # simple proxy
    served_total += served_now
    # simplistic wait update
    
    if MANUAL_AW is not None:
        avg_wait = MANUAL_AW
    else:
        if cycles == 1:
            avg_wait = green_time
        else:
            avg_wait = (avg_wait * (cycles - 1) + green_time) / cycles

    #target = 10.0 if served_now > 0 else 2.0
    #avg_wait = 0.9*avg_wait + 0.1*target

    client.publish("stats/cycles", str(cycles))
    client.publish("stats/served_total", str(served_total))
    client.publish("stats/avg_wait", f"{avg_wait:.2f}")

def main_loop():
    global smoothed_state, last_decision_time

    print("✅ Traffic optimizer running (MQTT connected)")

    while True:
        # smooth the binary readings (useful when your ESP32 publishes fast/noisy edges)
        smoothed_state = [
            ema_smooth(smoothed_state[i], traffic_state[i])
            for i in range(4)
        ]
        ir_vec = np.array([1 if v >= 0.5 else 0 for v in smoothed_state], dtype=int)

        # Avoid double-publish if restarted very fast
        if time.time() - last_decision_time < COOLDOWN_BETWEEN_DECISIONS:
            time.sleep(0.2)
            continue

        # Decide lane & time
        lane_name, reason = choose_lane(ir_vec)
        green_time = choose_time(ir_vec)
        last_decision_time = time.time()

        # Publish to dashboard
        publish_decision(lane_name, green_time, ir_vec, reason)

        # Set lights & countdown
        set_lights(lane_name, green_time)
        print(f"🚦 {lane_name} → GREEN for {green_time}s ({reason})")

        # countdown ticks for front-end sync
        for sec in range(green_time, 0, -1):
            client.publish("signal/timer", str(sec))
            time.sleep(1)

        # update stats after each cycle
        update_stats(ir_vec, green_time)

if __name__ == "__main__":
    try:
        main_loop()
    except SystemExit:
        pass
    except Exception as e:
        print("❌ Error:", e)
        graceful_exit(None, None)

