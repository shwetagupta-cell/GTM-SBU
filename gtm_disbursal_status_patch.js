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

  function statusClass(status) {
    const clean = STATUS_VALUES.has(status) ? status : "Pending";
    return clean.toLowerCase().replace(/\s+/g, "-");
  }

  function badge(status) {
    const clean = STATUS_VALUES.has(status) ? status : "Pending";
    return `<span class="status-badge status-badge--${statusClass(clean)}">${escapeHtml(clean)}</span>`;
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
      .status-badge--pending,
      .project-pill--pending #projectDisbursalStatus {
        background: #fdeaea;
        color: #a43b3b;
        border-color: rgba(164, 59, 59, 0.18);
      }
      .status-badge--in-process,
      .project-pill--in-process #projectDisbursalStatus {
        background: #fff6d8;
        color: #8a6100;
        border-color: rgba(138, 97, 0, 0.18);
      }
      .status-badge--disbursed,
      .project-pill--disbursed #projectDisbursalStatus {
        background: #e7f6ee;
        color: #24724d;
        border-color: rgba(36, 114, 77, 0.18);
      }
      #projectDisbursalStatus {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: fit-content;
        min-height: 36px;
        margin-top: 10px;
        padding: 0 14px;
        border: 1px solid transparent;
        border-radius: 999px;
        font-size: 15px;
        font-weight: 800;
        line-height: 1;
      }
      #projectDisbursalStatusCard {
        align-content: center;
      }
      .monthly-status-bar span[data-status="Pending"].is-current,
      .monthly-status-bar span[data-status="Pending"].is-complete {
        background: #fdeaea;
        color: #a43b3b;
        box-shadow: inset 0 0 0 1px rgba(164, 59, 59, 0.2);
      }
      .monthly-status-bar span[data-status="In Process"].is-current,
      .monthly-status-bar span[data-status="In Process"].is-complete {
        background: #fff6d8;
        color: #8a6100;
        box-shadow: inset 0 0 0 1px rgba(138, 97, 0, 0.2);
      }
      .monthly-status-bar span[data-status="Disbursed"].is-current,
      .monthly-status-bar span[data-status="Disbursed"].is-complete {
        background: #e7f6ee;
        color: #24724d;
        box-shadow: inset 0 0 0 1px rgba(36, 114, 77, 0.2);
      }
      #submitMonthlyStatusBtn {
        box-shadow: none;
      }
      #submitMonthlyStatusBtn[data-status="Pending"] {
        background: #fdeaea;
        color: #a43b3b;
        border-color: rgba(164, 59, 59, 0.2);
      }
      #submitMonthlyStatusBtn[data-status="In Process"] {
        background: #fff6d8;
        color: #8a6100;
        border-color: rgba(138, 97, 0, 0.2);
      }
      #submitMonthlyStatusBtn[data-status="Disbursed"] {
        background: #e7f6ee;
        color: #24724d;
        border-color: rgba(36, 114, 77, 0.2);
      }
      .project-disbursal-status-cell { text-align: left !important; white-space: nowrap; }
    `;
    document.head.appendChild(style);
  }

  function colorMonthlySubmitButton(status) {
    const button = document.getElementById("submitMonthlyStatusBtn");
    if (button) button.dataset.status = STATUS_VALUES.has(status) ? status : "Pending";
  }

  function ensureStatusCard(status) {
    const stats = document.querySelector("#projectPanel .project-stats");
    if (!stats) return;
    const clean = STATUS_VALUES.has(status) ? status : "Pending";
    let card = document.getElementById("projectDisbursalStatusCard");
    if (!card) {
      card = document.createElement("article");
      card.className = "project-pill";
      card.id = "projectDisbursalStatusCard";
      card.innerHTML = '<span>Disbursal Status</span><strong id="projectDisbursalStatus">Pending</strong>';
      stats.appendChild(card);
    }
    card.classList.remove("project-pill--pending", "project-pill--in-process", "project-pill--disbursed");
    card.classList.add(`project-pill--${statusClass(clean)}`);
    const value = document.getElementById("projectDisbursalStatus");
    if (value) value.textContent = clean;
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
    colorMonthlySubmitButton(document.getElementById("monthlyStatusInput")?.value || status);
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
    document.getElementById("monthlyStatusInput")?.addEventListener("change", (event) => {
      colorMonthlySubmitButton(event.target.value);
      scheduleRefresh(150);
    });

    const tableBody = document.getElementById("projectTableBody");
    if (tableBody) {
      new MutationObserver(() => scheduleRefresh()).observe(tableBody, { childList: true });
    }
  });
})();
