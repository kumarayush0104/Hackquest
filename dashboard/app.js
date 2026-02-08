const stateUrl = "/shared/state.json";
const reportButton = document.getElementById("download-report");

const history = {
  welfareAlpha: [],
  welfareBeta: [],
  welfareGamma: [],
};
let lastTimestamp = "";
let staleTicks = 0;

function byId(id) {
  return document.getElementById(id);
}

function renderTimeline(items) {
  const el = byId("timeline");
  el.innerHTML = "";
  if (!items || items.length === 0) {
    const li = document.createElement("li");
    li.textContent = "Awaiting first policy updates...";
    el.appendChild(li);
    return;
  }
  items.slice().reverse().forEach((item) => {
    const li = document.createElement("li");
    li.innerHTML = `
      <div class="timestamp">${item.timestamp}</div>
      <div>${item.label}</div>
    `;
    el.appendChild(li);
  });
}

function renderFeed(events) {
  const el = byId("feed");
  el.innerHTML = "";
  if (!events || events.length === 0) {
    const li = document.createElement("li");
    li.textContent = "No agent activity yet.";
    el.appendChild(li);
    return;
  }
  events.slice().reverse().forEach((event) => {
    const li = document.createElement("li");
    li.innerHTML = `
      <div class="timestamp">${event.timestamp} | ${event.source}</div>
      <div><strong>${event.title}</strong></div>
      <div>${event.memo}</div>
    `;
    el.appendChild(li);
  });
}

function renderMessages(events) {
  const el = byId("messages");
  el.innerHTML = "";
  if (!events || events.length === 0) {
    const li = document.createElement("li");
    li.textContent = "No inter-agent messages yet.";
    el.appendChild(li);
    return;
  }
  events
    .filter((event) => ["policy", "strategy", "negotiation", "market"].includes(event.topic))
    .slice()
    .reverse()
    .slice(0, 12)
    .forEach((event) => {
      const li = document.createElement("li");
      li.innerHTML = `
        <div class="timestamp">${event.timestamp} | ${event.source}</div>
        <div><strong>${event.title}</strong></div>
        <div>${event.memo}</div>
      `;
      el.appendChild(li);
    });
}

function renderCountryMetrics(targetId, data) {
  const el = byId(targetId);
  if (!data || data.gdp === undefined) {
    el.textContent = "No data available.";
    return;
  }
  const formatNumber = (value) =>
    typeof value === "number" ? value.toFixed(2) : value;
  const table = (obj) =>
    Object.entries(obj || {})
      .map(
        ([k, v]) =>
          `<div class="row"><span>${k}</span><span>${formatNumber(v)}</span></div>`
      )
      .join("");
  el.innerHTML = `
    <div class="country-card">
      <div class="country-kpis">
        <div class="kpi">
          <div class="kpi-label">GDP</div>
          <div class="kpi-value">${formatNumber(data.gdp)}</div>
        </div>
        <div class="kpi">
          <div class="kpi-label">Welfare</div>
          <div class="kpi-value">${formatNumber(data.welfare)}</div>
        </div>
        <div class="kpi">
          <div class="kpi-label">Political pressure</div>
          <div class="kpi-value">${formatNumber(data.political_pressure)}</div>
        </div>
      </div>
      <div class="country-sections">
        <div class="section">
          <div class="section-title">Exports</div>
          <div class="metric-table">${table(data.exports)}</div>
        </div>
        <div class="section">
          <div class="section-title">Imports</div>
          <div class="metric-table">${table(data.imports)}</div>
        </div>
        <div class="section">
          <div class="section-title">Tariffs</div>
          <div class="metric-table">${table(data.tariffs || {})}</div>
        </div>
      </div>
    </div>
  `;
}

function drawTradeFlow(canvas, tradeFlow) {
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const keys = Object.keys(tradeFlow);
  const values = keys.map((k) => tradeFlow[k]);
  const max = Math.max(...values, 1);
  const barWidth = (canvas.width - 40) / keys.length;

  keys.forEach((key, idx) => {
    const height = (values[idx] / max) * (canvas.height - 40);
    const x = 20 + idx * barWidth;
    const y = canvas.height - 20 - height;
    ctx.fillStyle = "#5aa2ff";
    ctx.fillRect(x, y, barWidth * 0.6, height);
    ctx.save();
    ctx.translate(x, canvas.height - 6);
    ctx.rotate(-0.5);
    ctx.fillStyle = "#9aa4ad";
    ctx.font = "10px IBM Plex Mono";
    ctx.fillText(key, 0, 0);
    ctx.restore();
    ctx.fillStyle = "#e6e8ea";
    ctx.fillText(values[idx], x, y - 6);
  });
}

function drawWelfare(canvas) {
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const padding = 30;
  const maxPoints = Math.max(history.welfareAlpha.length, 2);
  const xStep = (canvas.width - padding * 2) / (maxPoints - 1);
  const allValues = [
    ...history.welfareAlpha,
    ...history.welfareBeta,
    ...history.welfareGamma,
  ].filter((v) => typeof v === "number");
  const minValue = Math.min(...allValues, 80);
  const maxValue = Math.max(...allValues, 100);
  const range = Math.max(1, maxValue - minValue);

  function drawLine(values, color) {
    ctx.beginPath();
    values.forEach((value, idx) => {
      const x = padding + idx * xStep;
      const normalized = (value - minValue) / range;
      const y = canvas.height - padding - normalized * (canvas.height - padding * 2);
      if (idx === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.stroke();
  }

  drawLine(history.welfareAlpha, "#5aa2ff");
  drawLine(history.welfareBeta, "#ffb15a");
  drawLine(history.welfareGamma, "#8bd17c");

  ctx.fillStyle = "#9aa4ad";
  ctx.font = "11px IBM Plex Mono";
  ctx.fillText("Alpha", canvas.width - 90, 22);
  ctx.fillStyle = "#5aa2ff";
  ctx.fillRect(canvas.width - 110, 14, 14, 4);
  ctx.fillStyle = "#9aa4ad";
  ctx.fillText("Beta", canvas.width - 90, 38);
  ctx.fillStyle = "#ffb15a";
  ctx.fillRect(canvas.width - 110, 30, 14, 4);
  ctx.fillStyle = "#9aa4ad";
  ctx.fillText("Gamma", canvas.width - 90, 54);
  ctx.fillStyle = "#8bd17c";
  ctx.fillRect(canvas.width - 110, 46, 14, 4);

  ctx.fillStyle = "#9aa4ad";
  ctx.font = "10px IBM Plex Mono";
  ctx.fillText(`Min: ${minValue.toFixed(2)}`, padding, 16);
  ctx.fillText(`Max: ${maxValue.toFixed(2)}`, padding, 30);
}

function renderHeatmap(tradeFlow) {
  const el = byId("heatmap");
  el.innerHTML = "";
  const values = Object.values(tradeFlow || {});
  const max = Math.max(...values, 1);
  Object.entries(tradeFlow || {}).forEach(([sector, value]) => {
    const intensity = Math.min(0.85, 0.2 + value / max);
    const cell = document.createElement("div");
    cell.className = "heatmap-cell";
    cell.style.background = `rgba(90, 162, 255, ${intensity})`;
    cell.innerHTML = `<span>${sector}</span><span>${value}</span>`;
    el.appendChild(cell);
  });
}

async function refresh() {
  try {
    const response = await fetch(`${stateUrl}?t=${Date.now()}`);
    if (!response.ok) return;
    let data;
    try {
      data = await response.json();
    } catch (err) {
      return;
    }
    byId("round").textContent = data.round;
    byId("phase").textContent = data.phase;
    byId("timestamp").textContent = data.timestamp;
    if (data.timestamp === lastTimestamp) {
      staleTicks += 1;
    } else {
      staleTicks = 0;
      lastTimestamp = data.timestamp;
    }
    byId("classification").textContent = data.classification;
    byId("classification-memo").textContent =
      "Scenario classified; see policy notes for strategic guidance.";
    const strategyEvent = (data.events || [])
      .slice()
      .reverse()
      .find((event) => event.topic === "strategy");
    if (strategyEvent && strategyEvent.payload) {
      const payoff = strategyEvent.payload.payoff_matrix || {};
      byId("payoff").textContent = `Payoff matrix: ${JSON.stringify(payoff)}`;
    } else {
      byId("payoff").textContent = "Payoff matrix awaiting update.";
    }

    byId("alpha-aggression").textContent = data.learning.alpha_aggression;
    byId("effectiveness-score").textContent = data.learning.effectiveness_score;
    byId("learning-note").textContent = data.learning.note;

    renderTimeline(data.policy_timeline || []);
    renderFeed(data.events || []);
    renderMessages(data.events || []);
    if (data.countries) {
      const alpha = data.countries["Country Alpha"] || data.countries.alpha;
      const beta = data.countries["Country Beta"] || data.countries.beta;
      const gamma = data.countries["Country Gamma"] || data.countries.gamma;
      if (alpha) renderCountryMetrics("alpha-metrics", alpha);
      if (beta) renderCountryMetrics("beta-metrics", beta);
      if (gamma) renderCountryMetrics("gamma-metrics", gamma);
    }

    if (data.system_health) {
      byId("system-health").textContent = `State backend: ${data.system_health.backend}`;
    }

    if (data.agent_status) {
      const statusEl = byId("agent-status");
      statusEl.innerHTML = "";
      Object.entries(data.agent_status).forEach(([agent, status]) => {
        const li = document.createElement("li");
        li.textContent = `${agent}: ${status}`;
        statusEl.appendChild(li);
      });
    }

    if (data.welfare_impact) {
      history.welfareAlpha.push(data.welfare_impact["Country Alpha"]);
      history.welfareBeta.push(data.welfare_impact["Country Beta"]);
      history.welfareGamma.push(data.welfare_impact["Country Gamma"]);
      if (history.welfareAlpha.length > 20) {
        history.welfareAlpha.shift();
        history.welfareBeta.shift();
        history.welfareGamma.shift();
      }
    }

    drawTradeFlow(byId("trade-flow"), data.trade_flow || {});
    renderHeatmap(data.trade_flow || {});
    drawWelfare(byId("welfare"));
    if (staleTicks >= 6) {
      location.reload();
    }
  } catch (err) {
    console.error(err);
  }
}

async function downloadReport() {
  try {
    const response = await fetch(`${stateUrl}?t=${Date.now()}`);
    if (!response.ok) return;
    const data = await response.json();
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `trade-conflict-round-${data.round}.json`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  } catch (err) {
    console.error(err);
  }
}

if (reportButton) {
  reportButton.addEventListener("click", downloadReport);
}

refresh();
setInterval(refresh, 1200);
