const messagesEl = document.getElementById("messages");
const form = document.getElementById("chatForm");
const input = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const sendSpinner = document.getElementById("sendSpinner");
const btnLabel = sendBtn.querySelector(".btn-label");
const toast = document.getElementById("toast");
const clearBtn = document.getElementById("clearBtn");
const escalateBadge = document.getElementById("escalateBadge");
const statusDot = document.getElementById("statusDot");
const statusLabel = document.getElementById("statusLabel");
const statusMeta = document.getElementById("statusMeta");

const SESSION_KEY = "novamart_support_session";
let sessionId = localStorage.getItem(SESSION_KEY) || null;

function showToast(message, ok = false) {
  toast.textContent = message;
  toast.classList.toggle("ok", ok);
  toast.classList.remove("hidden");
  clearTimeout(showToast._t);
  showToast._t = setTimeout(() => toast.classList.add("hidden"), 4500);
}

function setLoading(loading) {
  sendBtn.disabled = loading;
  sendSpinner.classList.toggle("hidden", !loading);
  btnLabel.classList.toggle("hidden", loading);
}

function renderWelcome() {
  messagesEl.innerHTML = `
    <div class="welcome">
      <h3>How can we help?</h3>
      <p>Ask about shipping, returns, refunds, warranties, or account issues. Complex cases can be escalated to a human agent.</p>
    </div>`;
}

function appendMessage(role, content) {
  const welcome = messagesEl.querySelector(".welcome");
  if (welcome) welcome.remove();
  const div = document.createElement("div");
  div.className = `msg ${role}`;
  div.innerHTML = `<span class="meta">${role === "user" ? "You" : "Support Bot"}</span>${escapeHtml(content)}`;
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function escapeHtml(text) {
  return text
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

async function ensureSession() {
  if (sessionId) return sessionId;
  const res = await fetch("/api/session", { method: "POST" });
  if (!res.ok) throw new Error("Could not create session.");
  const data = await res.json();
  sessionId = data.session_id;
  localStorage.setItem(SESSION_KEY, sessionId);
  return sessionId;
}

async function loadHistory() {
  if (!sessionId) {
    renderWelcome();
    return;
  }
  const res = await fetch(`/api/history/${sessionId}`);
  if (res.status === 404) {
    localStorage.removeItem(SESSION_KEY);
    sessionId = null;
    renderWelcome();
    return;
  }
  if (!res.ok) throw new Error("Could not load history.");
  const data = await res.json();
  messagesEl.innerHTML = "";
  if (!data.history.length) {
    renderWelcome();
    return;
  }
  data.history.forEach((m) => appendMessage(m.role, m.content));
}

async function checkHealth() {
  try {
    const res = await fetch("/api/health");
    const data = await res.json();
    statusDot.classList.toggle("ok", data.llm_configured);
    statusDot.classList.toggle("err", !data.llm_configured);
    statusLabel.textContent = data.llm_configured ? "API ready" : "API key missing";
    statusMeta.textContent = data.llm_configured
      ? `Model: ${data.model}`
      : "Add OPENROUTER_API_KEY to .env";
  } catch {
    statusDot.classList.add("err");
    statusLabel.textContent = "Offline";
    statusMeta.textContent = "Backend unreachable";
  }
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const message = input.value.trim();
  if (!message) return;

  appendMessage("user", message);
  input.value = "";
  setLoading(true);
  escalateBadge.classList.add("hidden");

  try {
    await ensureSession();
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, session_id: sessionId }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || "Chat request failed.");

    sessionId = data.session_id;
    localStorage.setItem(SESSION_KEY, sessionId);
    appendMessage("assistant", data.reply);
    if (data.escalate) escalateBadge.classList.remove("hidden");
  } catch (err) {
    showToast(err.message || "Something went wrong.");
  } finally {
    setLoading(false);
  }
});

clearBtn.addEventListener("click", async () => {
  try {
    if (sessionId) {
      await fetch(`/api/history/${sessionId}`, { method: "DELETE" });
    }
    escalateBadge.classList.add("hidden");
    renderWelcome();
    showToast("Conversation cleared.", true);
  } catch (err) {
    showToast(err.message || "Could not clear conversation.");
  }
});

document.querySelectorAll(".chip").forEach((btn) => {
  btn.addEventListener("click", () => {
    input.value = btn.dataset.prompt;
    input.focus();
  });
});

input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    form.requestSubmit();
  }
});

renderWelcome();
checkHealth();
loadHistory().catch((err) => showToast(err.message));
