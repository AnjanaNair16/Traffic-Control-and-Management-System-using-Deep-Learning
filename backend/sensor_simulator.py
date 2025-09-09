import time
import random
import paho.mqtt.client as mqtt

BROKER = "192.168.169.139"
PORT = 1883
KEEPALIVE = 60

client = mqtt.Client()
client.connect(BROKER, PORT, KEEPALIVE)
client.loop_start()

print("🧪 Sensor simulator running. Ctrl+C to stop.")

try:
    t = 0
    while True:
        # randomly toggle presence with some persistence
        ir = [0,0,0,0]
        for i in range(4):
            if random.random() < 0.6:
                ir[i] = 1 if random.random() < 0.5 else 0

        # occasional rush build-up on lanes 1 & 2
        if 0 <= (t % 60) <= 15:
            ir[0] = 1
        if 30 <= (t % 60) <= 45:
            ir[1] = 1

        for i, val in enumerate(ir, start=1):
            client.publish(f"traffic/ir{i}", str(val))

        # rare emergency
        if random.random() < 0.02:
            lane = f"Lane{random.randint(1,4)}"
            print(f"🚑 EMERGENCY {lane} for 6s")
            client.publish("traffic/emergency", lane)
            time.sleep(6)
            client.publish("traffic/emergency", "off")

        t += 1
        time.sleep(0.5)
except KeyboardInterrupt:
    pass
finally:
    client.loop_stop()
    client.disconnect()
    print("\n🛑 Simulator stopped.")
