const videoEl = document.getElementById("video");
const statusPill = document.getElementById("connection-status");
const fpsEl = document.getElementById("fps");
const frameCountEl = document.getElementById("frame-count");
const statusTextEl = document.getElementById("status-text");
const lastCommandEl = document.getElementById("last-command");
const logEl = document.getElementById("log");
const commandInput = document.getElementById("command-input");
const sendCommandBtn = document.getElementById("send-command");

const COMMAND_ENDPOINT = "/api/command";
const STATUS_ENDPOINT = "/api/status";
const FRAME_ENDPOINT = "/api/frame.jpg";
const STREAM_ENDPOINT = "/api/stream.mjpg"; // added
let streamStarted = false; // added

function addLog(message, level = "info") {
  const entry = document.createElement("div");
  entry.className = `log-entry${level === "error" ? " error" : ""}`;
  entry.textContent = `${new Date().toLocaleTimeString()} — ${message}`;
  logEl.prepend(entry);
  const children = Array.from(logEl.children);
  if (children.length > 30) {
    children.slice(30).forEach((node) => node.remove());
  }
}

async function sendCommand(command) {
  if (!command) return;
  addLog(`Sending: ${command}`);
  lastCommandEl.textContent = command;

  try {
    const res = await fetch(COMMAND_ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ command }),
    });

    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.error || `Command failed (${res.status})`);
    }
  } catch (err) {
    addLog(err.message, "error");
    statusPill.textContent = "Command failed";
    statusPill.style.borderColor = "rgba(255,95,109,0.7)";
    return;
  }
}

async function pollStatus() {
  try {
    const res = await fetch(STATUS_ENDPOINT);
    if (!res.ok) throw new Error("Status unavailable");
    const data = await res.json();

    const connected = Boolean(data.connected);
    statusPill.textContent = connected ? "Camera linked" : "No camera";
    statusPill.style.borderColor = connected ? "rgba(11,211,211,0.5)" : "rgba(255,255,255,0.12)";
    statusTextEl.textContent = connected ? "Streaming" : "Idle";
    fpsEl.textContent = data.fps ?? 0;
    frameCountEl.textContent = data.frames ?? 0;
  } catch (err) {
    addLog(err.message, "error");
    statusPill.textContent = "Status error";
    statusPill.style.borderColor = "rgba(255,95,109,0.7)";
  }
}

function refreshFrame() {
  if (!streamStarted) { // added
    videoEl.src = STREAM_ENDPOINT; // added
    streamStarted = true; // added
    return; // added
  } // added
  videoEl.src = `${FRAME_ENDPOINT}?t=${Date.now()}`; // added fallback for snapshot
}

function wireControls() {
  document.querySelectorAll("[data-command]").forEach((btn) => {
    btn.addEventListener("click", () => sendCommand(btn.dataset.command));
  });

  sendCommandBtn.addEventListener("click", () => {
    const text = commandInput.value.trim();
    if (!text) return;
    sendCommand(text);
    commandInput.value = "";
  });

  commandInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      sendCommandBtn.click();
    }
  });

  videoEl.addEventListener("error", () => {
    statusPill.textContent = "Waiting for frames…";
  });
}

function boot() {
  wireControls();
  refreshFrame();
  setInterval(refreshFrame, 600);
  pollStatus();
  setInterval(pollStatus, 1400);
  addLog("UI ready. Waiting for camera stream…");
}

boot();
