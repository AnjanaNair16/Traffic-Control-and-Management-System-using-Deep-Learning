import os, time, csv, signal, sys
import paho.mqtt.client as mqtt
from datetime import datetime

# ==== CONFIG ==== #
BROKER = "192.168.169.139"   # your PC IP (or "127.0.0.1" if same machine)
PORT   = 1883
DATA_DIR = "data"
CSV_PATH = os.path.join(DATA_DIR, "signal_decisions.csv")
# ================ #

os.makedirs(DATA_DIR, exist_ok=True)

sensors = {"ir1": 0, "ir2": 0, "ir3": 0, "ir4": 0}

current_lane = None         # "Lane1"... "Lane4"
cycle_start_ts = None       # epoch seconds
start_snapshot = sensors.copy()

csv_fp = open(CSV_PATH, "a", newline="", encoding="utf-8")
writer = csv.DictWriter(csv_fp, fieldnames=[
    "timestamp", "ir1", "ir2", "ir3", "ir4", "active_lane", "green_time"
])
if csv_fp.tell() == 0:
    writer.writeheader()

def flush_row(end_ts=None):
    global cycle_start_ts, start_snapshot, current_lane
    if current_lane is None or cycle_start_ts is None:
        return
    if end_ts is None:
        end_ts = time.time()
    green_time = max(1, int(round(end_ts - cycle_start_ts)))
    row = {
        "timestamp": datetime.fromtimestamp(cycle_start_ts).isoformat(sep=" ", timespec="seconds"),
        "ir1": int(start_snapshot["ir1"]),
        "ir2": int(start_snapshot["ir2"]),
        "ir3": int(start_snapshot["ir3"]),
        "ir4": int(start_snapshot["ir4"]),
        "active_lane": current_lane,
        "green_time": green_time
    }
    writer.writerow(row)
    csv_fp.flush()

def on_connect(client, userdata, flags, reason_code, properties=None):
    print("📡 Recorder connected:", reason_code)
    client.subscribe("traffic/ir1")
    client.subscribe("traffic/ir2")
    client.subscribe("traffic/ir3")
    client.subscribe("traffic/ir4")
    client.subscribe("signal/current")  # published by your optimizer

def on_message(client, userdata, msg):
    global current_lane, cycle_start_ts, start_snapshot
    topic = msg.topic
    payload = msg.payload.decode().strip()

    if topic.startswith("traffic/ir"):
        key = topic.split("/")[-1]
        try:
            sensors[key] = int(payload)
        except:
            sensors[key] = 0

    if topic == "signal/current":
        new_lane = payload if payload else None
        now = time.time()
        # first lane -> start a cycle
        if current_lane is None and new_lane is not None and new_lane != "—":
            current_lane = new_lane
            cycle_start_ts = now
            start_snapshot = sensors.copy()
            print(f"▶️  Start {current_lane} @ {datetime.now().strftime('%H:%M:%S')} snapshot={start_snapshot}")
        # lane changed -> close previous row, start new cycle
        elif (new_lane != current_lane) and (new_lane is not None) and (new_lane != "—"):
            if current_lane is not None and cycle_start_ts is not None:
                flush_row(now)
                print(f"⏹  End   {current_lane} -> {int(now - cycle_start_ts)}s")
            current_lane = new_lane
            cycle_start_ts = now
            start_snapshot = sensors.copy()
            print(f"▶️  Start {current_lane} @ {datetime.now().strftime('%H:%M:%S')} snapshot={start_snapshot}")

def shutdown(*_):
    print("\nSaving last partial cycle (if any)…")
    flush_row()
    csv_fp.close()
    try:
        client.disconnect()
    except:
        pass
    sys.exit(0)

signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, PORT, 60)
print(f"📝 Recording to {CSV_PATH}")
client.loop_forever()
