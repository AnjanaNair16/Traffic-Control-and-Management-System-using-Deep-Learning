let client = null;
let isConnected = false;

// history chart state
let vehicleHistory = { labels: [], ir1: [], ir2: [], ir3: [], ir4: [] };
const HISTORY_WINDOW = 60;
let countdownTimer = null;

// UI refs
const el = {
  connStatus: document.getElementById("connStatus"),
  broker: document.getElementById("broker"),
  wsport: document.getElementById("wsport"),
  btnConnect: document.getElementById("btnConnect"),
  btnDisconnect: document.getElementById("btnDisconnect"),
  ir1: document.getElementById("ir1"),
  ir2: document.getElementById("ir2"),
  ir3: document.getElementById("ir3"),
  ir4: document.getElementById("ir4"),
  lane1: document.querySelector("#lane1 .state"),
  lane2: document.querySelector("#lane2 .state"),
  lane3: document.querySelector("#lane3 .state"),
  lane4: document.querySelector("#lane4 .state"),
  activeLane: document.getElementById("activeLane"),
  countdown: document.getElementById("countdown"),
  tableBody: document.getElementById("decisionTableBody"),
  stCycles: document.getElementById("stCycles"),
  stServed: document.getElementById("stServed"),
  stAvgWait: document.getElementById("stAvgWait"),
};

el.btnConnect.addEventListener("click", connect);
el.btnDisconnect.addEventListener("click", disconnect);

function updateConnStatus() {
  el.connStatus.textContent = "Status: " + (isConnected ? "Connected" : "Disconnected");
  el.connStatus.className = isConnected ? "connected" : "disconnected";
  el.btnConnect.disabled = isConnected;
  el.btnDisconnect.disabled = !isConnected;
}

// MQTT connect
function connect() {
  const host = el.broker.value || "192.168.169.139";
  const port = parseInt(el.wsport.value) || 9001;
  const clientId = "webdash-" + Math.random().toString(16).slice(2, 10);

  client = new Paho.MQTT.Client(host, Number(port), "/mqtt", clientId);

  client.onConnectionLost = () => { isConnected = false; updateConnStatus(); };
  client.onMessageArrived = (message) => handleMessage(message.destinationName, message.payloadString);

  client.connect({
    useSSL: false,
    timeout: 5,
    onSuccess: () => {
      isConnected = true; updateConnStatus();
      [
        "traffic/ir1","traffic/ir2","traffic/ir3","traffic/ir4",
        "signal/lane1","signal/lane2","signal/lane3","signal/lane4",
        "signal/current","signal/timer",
        "decision/signal",
        "stats/cycles","stats/served_total","stats/avg_wait"
      ].forEach(t => client.subscribe(t));
    },
    onFailure: () => { isConnected = false; updateConnStatus(); }
  });

  updateConnStatus();
}

function disconnect() {
  if (client) client.disconnect();
  client = null;
  isConnected = false;
  updateConnStatus();
}

function handleMessage(topic, payload) {
  if (topic === "traffic/ir1") { el.ir1.textContent = payload; pushHistory(0, Number(payload)); }
  if (topic === "traffic/ir2") { el.ir2.textContent = payload; pushHistory(1, Number(payload)); }
  if (topic === "traffic/ir3") { el.ir3.textContent = payload; pushHistory(2, Number(payload)); }
  if (topic === "traffic/ir4") { el.ir4.textContent = payload; pushHistory(3, Number(payload)); }

  if (topic === "signal/lane1") setLaneState("lane1", payload);
  if (topic === "signal/lane2") setLaneState("lane2", payload);
  if (topic === "signal/lane3") setLaneState("lane3", payload);
  if (topic === "signal/lane4") setLaneState("lane4", payload);
  if (topic === "signal/current") el.activeLane.textContent = payload;
  if (topic === "signal/timer") setCountdown(Number(payload));

  if (topic === "decision/signal") {
    try {
      const data = JSON.parse(payload);
      // Overwrite reason text
      data.reason = "Lane order fixed, only green time adaptive";
      updateDashboard(data.lane, data.green_time);
      prependDecisionRow(data);
    } catch (e) {
      console.error("Invalid decision payload:", payload);
    }
  }

  if (topic === "stats/cycles") el.stCycles.textContent = payload;
  if (topic === "stats/served_total") el.stServed.textContent = payload;
  if (topic === "stats/avg_wait") el.stAvgWait.textContent = Number(payload).toFixed(1);
}

// ---- UI helpers ----
function setLaneState(laneId, state) {
  const card = document.getElementById(laneId);
  const stateEl = card.querySelector(".state");
  stateEl.textContent = state;
  if (state === "GREEN") {
    card.classList.add("green", "green-blink");
    card.classList.remove("red");
  } else {
    card.classList.add("red");
    card.classList.remove("green", "green-blink");
  }
}

function updateDashboard(activeLane, greenTime) {
  ["lane1","lane2","lane3","lane4"].forEach(lid => {
    const isActive = ("Lane" + lid.slice(-1)) === activeLane;
    setLaneState(lid, isActive ? "GREEN" : "RED");
  });
  el.activeLane.textContent = activeLane;
  setCountdown(greenTime);
}

function setCountdown(seconds) {
  if (isNaN(seconds)) return;
  if (countdownTimer) clearInterval(countdownTimer);

  let remaining = seconds;
  el.countdown.textContent = `⏱ ${remaining}s`;

  countdownTimer = setInterval(() => {
    remaining--;
    if (remaining <= 0) {
      el.countdown.textContent = "⏱ 0s";
      clearInterval(countdownTimer);
      countdownTimer = null;
    } else {
      el.countdown.textContent = `⏱ ${remaining}s`;
    }
  }, 1000);
}

function prependDecisionRow({ lane, green_time, ir, reason }) {
  const tr = document.createElement("tr");
  const timeStr = new Date().toLocaleTimeString();

  tr.innerHTML = `
    <td>${timeStr}</td>
    <td>${lane}</td>
    <td>${green_time}</td>
    <td>[${ir.join(", ")}]</td>
    <td>${reason}</td>
  `;

  el.tableBody.prepend(tr);
  while (el.tableBody.rows.length > 100) el.tableBody.deleteRow(-1);
}

// ---- Chart ----
const ctx = document.getElementById("historyChart").getContext("2d");
const chart = new Chart(ctx, {
  type: "line",
  data: {
    labels: vehicleHistory.labels,
    datasets: [
      { label: "IR1", data: vehicleHistory.ir1, borderColor: "red", tension: 0.2 },
      { label: "IR2", data: vehicleHistory.ir2, borderColor: "blue", tension: 0.2 },
      { label: "IR3", data: vehicleHistory.ir3, borderColor: "green", tension: 0.2 },
      { label: "IR4", data: vehicleHistory.ir4, borderColor: "orange", tension: 0.2 }
    ]
  },
  options: { animation: false, responsive: true, scales: { y: { min: 0, max: 1 } } }
});

function pushHistory(irIndex, value) {
  const ts = new Date().toLocaleTimeString();
  if (vehicleHistory.labels.length >= HISTORY_WINDOW) {
    vehicleHistory.labels.shift();
    vehicleHistory.ir1.shift();
    vehicleHistory.ir2.shift();
    vehicleHistory.ir3.shift();
    vehicleHistory.ir4.shift();
  }
  vehicleHistory.labels.push(ts);
  [vehicleHistory.ir1,vehicleHistory.ir2,vehicleHistory.ir3,vehicleHistory.ir4][irIndex].push(value);
  chart.update();
}
