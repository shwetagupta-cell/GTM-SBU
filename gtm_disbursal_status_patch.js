(() => {
  const STATUS_VALUES = new Set(["Pending", "In Process", "Disbursed"]);
  let refreshTimer = null;

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function badge(status) {
    const clean = STATUS_VALUES.has(status) ? status : "Pending";
    const className = clean.toLowerCase().replace(/\s+/g, "-");
    return `<span class="status-badge status-badge--${className}">${escapeHtml(clean)}</span>`;
  }

  function selectedPeriod() {
    return document.getElementById("projectMonthSelect")?.value || document.getElementById("periodSelect")?.value || "";
  }

  function selectedEmployeeId() {
    const value = document.getElementById("employeePickerInput")?.value || "";
    const match = value.match(/\(([^()]+)\)\s*$/);
    return match ? match[1].trim() : "";
  }

  async function loadStatus() {
    const query = new URLSearchParams();
    const employeeId = selectedEmployeeId();
    const period = selectedPeriod();
    if (employeeId) query.set("employeeId", employeeId);
    if (period) query.set("period", period);
    const response = await fetch(`/api/me?${query.toString()}`, { credentials: "same-origin" });
    if (!response.ok) return "Pending";
    const payload = await response.json();
    const employee = payload.viewedEmployee || {};
    const summary = (period && employee.periods && employee.periods[period]) || employee.latestSummary || {};
    return summary.disbursalStatus || payload.admin?.monthlyDisbursalStatus || "Pending";
  }

  function ensureStyles() {
    if (document.getElementById("disbursalStatusPatchStyles")) return;
    const style = document.createElement("style");
    style.id = "disbursalStatusPatchStyles";
    style.textContent = `
      .status-badge--pending { background: #fff3df; color: #9a5a00; }
      .status-badge--in-process { background: #e8f0ff; color: #2459b6; }
      .status-badge--disbursed { background: #e6f6ed; color: #137047; }
      .project-disbursal-status-cell { text-align: left !important; white-space: nowrap; }
      #projectDisbursalStatus { font-size: clamp(17px, 1.4vw, 22px); }
    `;
    document.head.appendChild(style);
  }

  function ensureStatusCard(status) {
    const stats = document.querySelector("#projectPanel .project-stats");
    if (!stats) return;
    let card = document.getElementById("projectDisbursalStatusCard");
    if (!card) {
      card = document.createElement("article");
      card.className = "project-pill";
      card.id = "projectDisbursalStatusCard";
      card.innerHTML = '<span>Disbursal Status</span><strong id="projectDisbursalStatus">Pending</strong>';
      stats.appendChild(card);
    }
    const value = document.getElementById("projectDisbursalStatus");
    if (value) value.textContent = status || "Pending";
  }

  function ensureStatusHeader() {
    const headerRow = document.querySelector("#projectPanel thead tr");
    if (!headerRow) return;
    const existing = [...headerRow.children].some((cell) => cell.dataset.disbursalStatus === "true");
    if (existing) return;
    const th = document.createElement("th");
    th.dataset.disbursalStatus = "true";
    th.textContent = "Disbursal Status";
    headerRow.insertBefore(th, headerRow.lastElementChild);
  }

  function applyStatusRows(status) {
    const rows = document.querySelectorAll("#projectTableBody tr");
    rows.forEach((row) => {
      const emptyCell = row.querySelector("td[colspan]");
      if (emptyCell && row.children.length === 1) {
        emptyCell.colSpan = Math.max(Number(emptyCell.colSpan || 0), 15);
        return;
      }
      let cell = row.querySelector(".project-disbursal-status-cell");
      if (!cell) {
        cell = document.createElement("td");
        cell.className = "project-disbursal-status-cell";
        row.insertBefore(cell, row.lastElementChild);
      }
      cell.innerHTML = badge(status);
    });
  }

  async function refreshDisbursalStatus() {
    ensureStyles();
    ensureStatusHeader();
    const status = await loadStatus().catch(() => "Pending");
    ensureStatusCard(status);
    ensureStatusHeader();
    applyStatusRows(status);
  }

  function scheduleRefresh(delay = 120) {
    clearTimeout(refreshTimer);
    refreshTimer = setTimeout(refreshDisbursalStatus, delay);
  }

  document.addEventListener("DOMContentLoaded", () => {
    scheduleRefresh(250);
    document.getElementById("projectMonthSelect")?.addEventListener("change", () => scheduleRefresh(700));
    document.getElementById("periodSelect")?.addEventListener("change", () => scheduleRefresh(700));
    document.getElementById("employeePickerInput")?.addEventListener("change", () => scheduleRefresh(700));
    document.getElementById("applyFiltersBtn")?.addEventListener("click", () => scheduleRefresh(900));
    document.getElementById("submitMonthlyStatusBtn")?.addEventListener("click", () => scheduleRefresh(900));

    const tableBody = document.getElementById("projectTableBody");
    if (tableBody) {
      new MutationObserver(() => scheduleRefresh()).observe(tableBody, { childList: true });
    }
  });
})();
