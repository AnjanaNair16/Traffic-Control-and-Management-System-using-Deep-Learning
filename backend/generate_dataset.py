import os, csv, random
from datetime import datetime, timedelta

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
CSV_PATH = os.path.join(DATA_DIR, "signal_decisions.csv")

lanes = ["Lane1", "Lane2", "Lane3", "Lane4"]

def generate_row(ts, period):
    """
    Generate one row of traffic data depending on time period
    """
    # Different probabilities for vehicles based on time period
    if period == "rush":
        probs = [0.7, 0.8, 0.6, 0.75]   # high traffic probability
    elif period == "normal":
        probs = [0.4, 0.5, 0.3, 0.4]   # medium
    else:  # night
        probs = [0.1, 0.2, 0.1, 0.15]  # very low

    # decide vehicles on each lane
    ir = [1 if random.random() < p else 0 for p in probs]

    if sum(ir) == 0:  # no cars, idle
        active_lane = random.choice(lanes)
        green_time = random.randint(5, 8) if period == "night" else random.randint(8, 12)
    else:
        # Pick lane with most cars (weighted random)
        max_lane = ir.index(max(ir)) + 1
        active_lane = f"Lane{max_lane}"

        # Green time proportional to active cars
        base_time = {
            "rush": random.randint(15, 25),
            "normal": random.randint(10, 18),
            "night": random.randint(5, 10)
        }[period]
        green_time = base_time + sum(ir) * 2

    return {
        "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
        "ir1": ir[0],
        "ir2": ir[1],
        "ir3": ir[2],
        "ir4": ir[3],
        "active_lane": active_lane,
        "green_time": green_time
    }

def main():
    with open(CSV_PATH, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["timestamp","ir1","ir2","ir3","ir4","active_lane","green_time"]
        )
        writer.writeheader()

        ts = datetime.now()

        # Simulate 3 traffic periods
        for period, samples in [("rush", 400), ("normal", 350), ("night", 250)]:
            for _ in range(samples):
                row = generate_row(ts, period)
                writer.writerow(row)
                ts += timedelta(seconds=row["green_time"])

    print(f"✅ Realistic dataset generated with rush/normal/night traffic → {CSV_PATH}")

if __name__ == "__main__":
    main()
