from flask import Flask, render_template
from flask_mqtt import Mqtt

app = Flask(__name__)

# MQTT Config
app.config['MQTT_BROKER_URL'] = '192.168.169.139'  # 👈 broker ka IP (your PC IP)
app.config['MQTT_BROKER_PORT'] = 9001          # WebSockets port
app.config['MQTT_KEEPALIVE'] = 60
app.config['MQTT_TLS_ENABLED'] = False

mqtt = Mqtt(app)

# Global state for signals
traffic_state = {
    "lane1": {"status": "RED", "time": 0},
    "lane2": {"status": "RED", "time": 0},
    "lane3": {"status": "RED", "time": 0},
    "lane4": {"status": "RED", "time": 0},
}

@app.route('/')
def index():
    return render_template('index.html', state=traffic_state)

# MQTT Message Listener
@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    topic = message.topic
    payload = message.payload.decode()

    if topic.startswith("traffic/signal/"):
        lane = topic.split("/")[-1]
        if lane in traffic_state:
            traffic_state[lane]["status"] = payload
            traffic_state[lane]["time"] = 15 if payload == "GREEN" else 0

if __name__ == '__main__':
    mqtt.subscribe("traffic/signal/#")
    app.run(host="0.0.0.0", port=5000, debug=True)
