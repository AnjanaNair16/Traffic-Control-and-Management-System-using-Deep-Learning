import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import tensorflow as tf
from tensorflow.keras import Sequential
from tensorflow.keras.layers import Dense, Dropout

# ======= Load dataset =======
DATA_PATH = "data/signal_decisions.csv"
MODEL_PATH = "model/traffic_model.h5"

os.makedirs("model", exist_ok=True)

print("📂 Loading dataset...")
df = pd.read_csv(DATA_PATH)

print("✅ Data loaded:", df.shape)
print(df.head())

# ======= Prepare features & labels =======
X = df[["ir1", "ir2", "ir3", "ir4"]].values
y_lane = df["active_lane"].values
y_time = df["green_time"].values

# Encode lane labels
lane_encoder = LabelEncoder()
y_lane_enc = lane_encoder.fit_transform(y_lane)

# Split train/test
X_train, X_test, y_lane_train, y_lane_test, y_time_train, y_time_test = train_test_split(
    X, y_lane_enc, y_time, test_size=0.2, random_state=42
)

# ======= Build model =======
model = Sequential([
    Dense(32, activation="relu", input_shape=(4,)),
    Dropout(0.2),
    Dense(32, activation="relu"),

    # Two outputs: Lane classification + time regression
    Dense(len(lane_encoder.classes_), activation="softmax", name="lane_output"),
])

# Compile for classification
model.compile(
    optimizer="adam",
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"]
)

# ======= Train lane classifier =======
print("\n🚦 Training lane classifier...")
history = model.fit(X_train, y_lane_train, epochs=30, batch_size=16, validation_split=0.2, verbose=1)

# Evaluate
loss, acc = model.evaluate(X_test, y_lane_test, verbose=0)
print(f"✅ Lane classification accuracy: {acc*100:.2f}%")

# Save model & encoder
model.save(MODEL_PATH)
np.save("model/lane_classes.npy", lane_encoder.classes_)

print(f"💾 Model saved at {MODEL_PATH}")

# ======= Train separate regressor for green_time =======
print("\n⏱ Training green_time regressor...")
time_model = Sequential([
    Dense(32, activation="relu", input_shape=(4,)),
    Dense(16, activation="relu"),
    Dense(1, activation="linear")
])
time_model.compile(optimizer="adam", loss="mse")

time_model.fit(X_train, y_time_train, epochs=30, batch_size=16, validation_split=0.2, verbose=1)

mse = time_model.evaluate(X_test, y_time_test, verbose=0)
print(f"✅ Green time prediction MSE: {mse:.2f}")

time_model.save("model/time_model.h5")
print("💾 Time model saved at model/time_model.h5")
