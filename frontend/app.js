const API = "http://127.0.0.1:8000";

const fileEl = document.getElementById("file");
const pairsEl = document.getElementById("pairs");
const historyEl = document.getElementById("history");
const toastEl = document.getElementById("toast");

document.getElementById("addPair").addEventListener("click", () => addPair("", ""));
document.getElementById("submit").addEventListener("click", submit);
document.getElementById("refresh").addEventListener("click", loadHistory);

function toast(msg) {
  toastEl.textContent = msg;
  toastEl.classList.remove("hidden");
  setTimeout(() => toastEl.classList.add("hidden"), 3000);
}

function addPair(from, to) {
  const row = document.createElement("div");
  row.className = "pair";
  row.innerHTML = `
    <input placeholder="Find (exact text)" value="${escapeHtml(from)}" />
    <input placeholder="Replace with" value="${escapeHtml(to)}" />
    <button title="Remove">✕</button>
  `;
  row.querySelector("button").onclick = () => row.remove();
  pairsEl.appendChild(row);
}

function getPairs() {
  const rows = [...pairsEl.querySelectorAll(".pair")];
  const replacements = {};
  for (const r of rows) {
    const [a,b] = r.querySelectorAll("input");
    const from = a.value.trim();
    const to = b.value.trim();
    if (from) replacements[from] = to;
  }
  return replacements;
}

async function submit() {
  const f = fileEl.files[0];
  if (!f) return toast("Please choose a PDF first.");

  const replacements = getPairs();
  if (Object.keys(replacements).length === 0) {
    return toast("Add at least one replacement.");
  }

  const fd = new FormData();
  fd.append("file", f);
  fd.append("replacements_json", JSON.stringify(replacements));

  toast("Uploading + processing...");
  const res = await fetch(`${API}/api/submissions`, { method: "POST", body: fd });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    return toast(`Failed: ${err.detail || res.statusText}`);
  }

  const created = await res.json();
  toast(`Queued: ${created.id}`);
  await loadHistory();
}

async function loadHistory() {
  historyEl.innerHTML = `<div class="small">Loading...</div>`;
  const res = await fetch(`${API}/api/submissions?limit=50&offset=0`);
  const list = await res.json();

  if (!Array.isArray(list) || list.length === 0) {
    historyEl.innerHTML = `<div class="small">No submissions yet.</div>`;
    return;
  }

  historyEl.innerHTML = "";
  for (const s of list) {
    const badge = badgeClass(s.status);
    const item = document.createElement("div");
    item.className = "item";

    const dl = s.output_url
      ? `<a class="btn secondary" href="${API}${s.output_url}" target="_blank">⬇ Download</a>`
      : "";

    item.innerHTML = `
      <div class="meta">
        <div>
          <div><strong>${escapeHtml(s.filename)}</strong></div>
          <div class="small">id: ${escapeHtml(s.id)} • ${escapeHtml(s.created_at)}</div>
        </div>
        <div class="badge ${badge}">${escapeHtml(s.status)}</div>
      </div>

      ${s.error ? `<div class="small" style="margin-top:8px;color:#ffb4b4">Error: ${escapeHtml(s.error)}</div>` : ""}

      <div class="row" style="margin-top:10px; justify-content:space-between; flex-wrap:wrap;">
        <div class="row">
          ${dl}
          <button class="btn ghost" data-rate="1">😡</button>
          <button class="btn ghost" data-rate="3">😐</button>
          <button class="btn ghost" data-rate="5">😍</button>
        </div>
        <div class="small">rating: ${s.rating ?? "-"}</div>
      </div>
    `;

    item.querySelectorAll("button[data-rate]").forEach(btn => {
      btn.addEventListener("click", () => rate(s.id, Number(btn.dataset.rate)));
    });

    historyEl.appendChild(item);
  }
}

async function rate(id, rating) {
  const res = await fetch(`${API}/api/submissions/${id}/rate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ rating, note: "" })
  });

  if (!res.ok) return toast("Rating failed");
  toast("Rated ✅");
  await loadHistory();
}

function badgeClass(s) {
  if (s === "done") return "done";
  if (s === "failed") return "failed";
  return "processing";
}

function escapeHtml(str) {
  return String(str ?? "").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;");
}

// init
addPair("John Doe", "Client A");
addPair("0241234567", "PHONE_REDACTED");
loadHistory();
setInterval(loadHistory, 5000); // simple PoC polling
