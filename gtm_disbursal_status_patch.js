(() => {
  const STATUS_VALUES = new Set(["Pending", "In Process", "Disbursed"]);
  const REPORT_LINK_IDS = ["downloadReportLink", "downloadCompleteReportLink", "downloadEmployeeReportLink"];
  let refreshTimer = null;
  let lastTableSignature = "";
  let statusCache = { key: "", value: "Pending", updatedAt: 0 };

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
    const employeeId = selectedEmployeeId();
    const period = selectedPeriod();
    const cacheKey = `${employeeId}|${period}`;
    if (statusCache.key === cacheKey && Date.now() - statusCache.updatedAt < 30000) {
      return statusCache.value;
    }
    const query = new URLSearchParams();
    if (employeeId) query.set("employeeId", employeeId);
    if (period) query.set("period", period);
    const response = await fetch(`/api/me?${query.toString()}`, { credentials: "same-origin" });
    if (!response.ok) return statusCache.value || "Pending";
    const payload = await response.json();
    const employee = payload.viewedEmployee || {};
    const summary = (period && employee.periods && employee.periods[period]) || employee.latestSummary || {};
    const status = summary.disbursalStatus || payload.admin?.monthlyDisbursalStatus || "Pending";
    statusCache = { key: cacheKey, value: status, updatedAt: Date.now() };
    return status;
  }

  function ensureStyles() {
    if (document.getElementById("disbursalStatusPatchStyles")) return;
    const style = document.createElement("style");
    style.id = "disbursalStatusPatchStyles";
    style.textContent = `
      #projectPanel .panel-head .eyebrow { display: none !important; }
      #kpiPanel .kpi-live-stats article:nth-child(2),
      #kpiPanel th:nth-child(9),
      #kpiPanel td:nth-child(9) { display: none !important; }
      #kpiPanel .table-wrap table { min-width: 1120px; }
      #kpiPanel .kpi-live-stats { grid-template-columns: minmax(0, 1fr) !important; }
      .status-badge--pending,
      .project-pill--pending #projectDisbursalStatus { background: #fdeaea; color: #a43b3b; border-color: rgba(164,59,59,.18); }
      .status-badge--in-process,
      .project-pill--in-process #projectDisbursalStatus { background: #fff6d8; color: #8a6100; border-color: rgba(138,97,0,.18); }
      .status-badge--disbursed,
      .project-pill--disbursed #projectDisbursalStatus { background: #e7f6ee; color: #24724d; border-color: rgba(36,114,77,.18); }
      #projectDisbursalStatus { display: inline-flex; align-items: center; justify-content: center; width: fit-content; min-height: 36px; margin-top: 10px; padding: 0 14px; border: 1px solid transparent; border-radius: 999px; font-size: 15px; font-weight: 800; line-height: 1; }
      #projectDisbursalStatusCard { align-content: center; }
      .monthly-status-bar span[data-status="Pending"].is-current,
      .monthly-status-bar span[data-status="Pending"].is-complete { background: #fdeaea; color: #a43b3b; box-shadow: inset 0 0 0 1px rgba(164,59,59,.2); }
      .monthly-status-bar span[data-status="In Process"].is-current,
      .monthly-status-bar span[data-status="In Process"].is-complete { background: #fff6d8; color: #8a6100; box-shadow: inset 0 0 0 1px rgba(138,97,0,.2); }
      .monthly-status-bar span[data-status="Disbursed"].is-current,
      .monthly-status-bar span[data-status="Disbursed"].is-complete { background: #e7f6ee; color: #24724d; box-shadow: inset 0 0 0 1px rgba(36,114,77,.2); }
      #submitMonthlyStatusBtn { box-shadow: none; }
      #submitMonthlyStatusBtn[data-status="Pending"] { background: #fdeaea; color: #a43b3b; border-color: rgba(164,59,59,.2); }
      #submitMonthlyStatusBtn[data-status="In Process"] { background: #fff6d8; color: #8a6100; border-color: rgba(138,97,0,.2); }
      #submitMonthlyStatusBtn[data-status="Disbursed"] { background: #e7f6ee; color: #24724d; border-color: rgba(36,114,77,.2); }
      .project-disbursal-status-cell { text-align: left !important; white-space: nowrap; }
      .is-loading-action { opacity: .72; pointer-events: none; }
      .pdf-report-link { margin-top: 8px; }
    `;
    document.head.appendChild(style);
  }

  function patchKpiScorecard() {
    const scoreCard = document.querySelector("#kpiPanel .kpi-live-stats article:first-child span");
    if (scoreCard) scoreCard.textContent = "Final KPI Score";
    document.querySelectorAll("#kpiPanel th").forEach((header) => {
      const text = header.textContent.trim().toLowerCase();
      if (text === "score") header.textContent = "Score / Points";
      if (text === "weighted score") header.textContent = "Final KPI Score";
    });
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
    document.querySelectorAll("#projectTableBody tr").forEach((row) => {
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

  function reportPdfHref(csvHref) {
    try {
      const url = new URL(csvHref, window.location.origin);
      url.pathname = url.pathname.replace(/report\.csv$/, "report.pdf");
      return `${url.pathname}${url.search}`;
    } catch {
      return "/api/report.pdf";
    }
  }

  function ensurePdfReportLinks() {
    REPORT_LINK_IDS.forEach((id) => {
      const csvLink = document.getElementById(id);
      if (!csvLink) return;
      const pdfId = `${id}Pdf`;
      let pdfLink = document.getElementById(pdfId);
      if (!pdfLink) {
        pdfLink = document.createElement("a");
        pdfLink.id = pdfId;
        pdfLink.className = `${csvLink.className || "ghost-btn full-btn"} pdf-report-link`;
        pdfLink.textContent = csvLink.textContent.toLowerCase().includes("complete") ? "Download Complete PDF" : "Download PDF Report";
        csvLink.insertAdjacentElement("afterend", pdfLink);
      }
      pdfLink.href = reportPdfHref(csvLink.getAttribute("href") || "/api/report.csv");
    });
  }

  async function refreshDisbursalStatus(force = false) {
    ensureStyles();
    patchKpiScorecard();
    ensurePdfReportLinks();
    ensureStatusHeader();
    const period = selectedPeriod();
    const employeeId = selectedEmployeeId();
    const rowCount = document.querySelectorAll("#projectTableBody tr").length;
    const signature = `${employeeId}|${period}|${rowCount}`;
    const status = await loadStatus().catch(() => "Pending");
    ensureStatusCard(status);
    colorMonthlySubmitButton(document.getElementById("monthlyStatusInput")?.value || status);
    if (force || signature !== lastTableSignature) {
      ensureStatusHeader();
      applyStatusRows(status);
      lastTableSignature = signature;
    }
  }

  function scheduleRefresh(delay = 120, force = false) {
    clearTimeout(refreshTimer);
    refreshTimer = setTimeout(() => refreshDisbursalStatus(force), delay);
  }

  function syncMonthSelects(sourceId) {
    const source = document.getElementById(sourceId);
    const targetId = sourceId === "periodSelect" ? "projectMonthSelect" : "periodSelect";
    const target = document.getElementById(targetId);
    if (source && target && target.value !== source.value) target.value = source.value;
    statusCache.updatedAt = 0;
    lastTableSignature = "";
  }

  function markTemporaryLoading(element, text) {
    if (!element) return;
    const previousText = element.textContent;
    element.classList.add("is-loading-action");
    element.textContent = text;
    setTimeout(() => {
      element.classList.remove("is-loading-action");
      if (element.textContent === text) element.textContent = previousText;
    }, 8000);
  }

  document.addEventListener("DOMContentLoaded", () => {
    scheduleRefresh(250, true);
    document.getElementById("projectMonthSelect")?.addEventListener("change", () => {
      syncMonthSelects("projectMonthSelect");
      scheduleRefresh(500, true);
    });
    document.getElementById("periodSelect")?.addEventListener("change", () => {
      syncMonthSelects("periodSelect");
      scheduleRefresh(500, true);
    });
    document.getElementById("employeePickerInput")?.addEventListener("change", () => {
      statusCache.updatedAt = 0;
      lastTableSignature = "";
      scheduleRefresh(500, true);
    });
    document.getElementById("applyFiltersBtn")?.addEventListener("click", () => {
      statusCache.updatedAt = 0;
      lastTableSignature = "";
      scheduleRefresh(700, true);
    });
    document.body.addEventListener("click", (event) => {
      const target = event.target.closest("a, button");
      if (!target) return;
      if (REPORT_LINK_IDS.includes(target.id) || target.classList.contains("pdf-report-link")) {
        markTemporaryLoading(target, "Preparing...");
      }
      if (target.classList.contains("upload-trigger")) markTemporaryLoading(target, "Uploading...");
      if (target.classList.contains("delete-upload-btn")) markTemporaryLoading(target, "Deleting...");
      if (target.id === "submitMonthlyStatusBtn") {
        statusCache.updatedAt = 0;
        lastTableSignature = "";
        scheduleRefresh(700, true);
      }
    });
    document.getElementById("monthlyStatusInput")?.addEventListener("change", (event) => {
      colorMonthlySubmitButton(event.target.value);
      scheduleRefresh(120, true);
    });
    const tableBody = document.getElementById("projectTableBody");
    if (tableBody) new MutationObserver(() => scheduleRefresh(80, true)).observe(tableBody, { childList: true });
    const kpiBody = document.getElementById("kpiTableBody");
    if (kpiBody) new MutationObserver(() => patchKpiScorecard()).observe(kpiBody, { childList: true });
    const reportPanel = document.querySelector("#adminPanel") || document.body;
    new MutationObserver(() => ensurePdfReportLinks()).observe(reportPanel, { childList: true, subtree: true, attributes: true, attributeFilter: ["href"] });
  });
})();
