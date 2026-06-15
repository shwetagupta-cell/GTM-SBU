const els = {
  authShell: document.getElementById("authShell"),
  appShell: document.getElementById("appShell"),
  loginForm: document.getElementById("loginForm"),
  loginType: document.getElementById("loginType"),
  loginEmployeeId: document.getElementById("loginEmployeeId"),
  loginPassword: document.getElementById("loginPassword"),
  toggleLoginPassword: document.getElementById("toggleLoginPassword"),
  loginNotice: document.getElementById("loginNotice"),
  resetEmployeeId: document.getElementById("resetEmployeeId"),
  resetEmployeeName: document.getElementById("resetEmployeeName"),
  resetEmail: document.getElementById("resetEmail"),
  resetOtp: document.getElementById("resetOtp"),
  resetNewPassword: document.getElementById("resetNewPassword"),
  resetConfirmPassword: document.getElementById("resetConfirmPassword"),
  requestOtpBtn: document.getElementById("requestOtpBtn"),
  verifyOtpBtn: document.getElementById("verifyOtpBtn"),
  resetPasswordBtn: document.getElementById("resetPasswordBtn"),
  resetNotice: document.getElementById("resetNotice"),
  sessionUser: document.getElementById("sessionUser"),
  sessionMeta: document.getElementById("sessionMeta"),
  logoutBtn: document.getElementById("logoutBtn"),
  greetingText: document.getElementById("greetingText"),
  dashboardTitle: document.getElementById("dashboardTitle"),
  dashboardSubtitle: document.getElementById("dashboardSubtitle"),
  employeePickerInput: document.getElementById("employeePickerInput"),
  employeeOptions: document.getElementById("employeeOptions"),
  startDateInput: document.getElementById("startDateInput"),
  endDateInput: document.getElementById("endDateInput"),
  searchInput: document.getElementById("searchInput"),
  applyFiltersBtn: document.getElementById("applyFiltersBtn"),
  downloadReportLink: document.getElementById("downloadReportLink"),
  downloadCompleteReportLink: document.getElementById("downloadCompleteReportLink"),
  downloadEmployeePickerInput: document.getElementById("downloadEmployeePickerInput"),
  downloadEmployeeReportLink: document.getElementById("downloadEmployeeReportLink"),
  resetFiltersBtn: document.getElementById("resetFiltersBtn"),
  npsScoreValue: document.getElementById("npsScoreValue"),
  npsScoreLabel: document.getElementById("npsScoreLabel"),
  npsDisbursalValue: document.getElementById("npsDisbursalValue"),
  npsDisbursalLabel: document.getElementById("npsDisbursalLabel"),
  accruedValue: document.getElementById("accruedValue"),
  accruedLabel: document.getElementById("accruedLabel"),
  disbursalStatusValue: document.getElementById("disbursalStatusValue"),
  disbursalStatusInput: document.getElementById("disbursalStatusInput"),
  saveStatusBtn: document.getElementById("saveStatusBtn"),
  hierarchyGrid: document.getElementById("hierarchyGrid"),
  quarterTabs: document.getElementById("quarterTabs"),
  trendList: document.getElementById("trendList"),
  periodSelect: document.getElementById("periodSelect"),
  kpiNotice: document.getElementById("kpiNotice"),
  kpiTableBody: document.getElementById("kpiTableBody"),
  projectMonthSelect: document.getElementById("projectMonthSelect"),
  projectValueTotal: document.getElementById("projectValueTotal"),
  projectDepartmentPercent: document.getElementById("projectDepartmentPercent"),
  projectTeamSharePercent: document.getElementById("projectTeamSharePercent"),
  projectMyShareValue: document.getElementById("projectMyShareValue"),
  projectDisbursalPercent: document.getElementById("projectDisbursalPercent"),
  projectFinalDisbursal: document.getElementById("projectFinalDisbursal"),
  projectTableBody: document.getElementById("projectTableBody"),
  adminPanel: document.getElementById("adminPanel"),
  adminNav: document.getElementById("adminNav"),
  totalEmployeesValue: document.getElementById("totalEmployeesValue"),
  totalPayoutValue: document.getElementById("totalPayoutValue"),
  quarterlyPayoutValue: document.getElementById("quarterlyPayoutValue"),
  annualPayoutValue: document.getElementById("annualPayoutValue"),
  dataUpdatedMeta: document.getElementById("dataUpdatedMeta"),
  disbursalStatusSummary: document.getElementById("disbursalStatusSummary"),
  departmentList: document.getElementById("departmentList"),
  uploadHistory: document.getElementById("uploadHistory"),
  uploadNotice: document.getElementById("uploadNotice"),
  employeeForm: document.getElementById("employeeForm"),
  employeeIdInput: document.getElementById("employeeIdInput"),
  employeeNameInput: document.getElementById("employeeNameInput"),
  employeeEmailInput: document.getElementById("employeeEmailInput"),
  employeeGradeInput: document.getElementById("employeeGradeInput"),
  employeeLocationInput: document.getElementById("employeeLocationInput"),
  employeeDepartmentInput: document.getElementById("employeeDepartmentInput"),
  employeeBusinessUnitInput: document.getElementById("employeeBusinessUnitInput"),
  employeeLogicKeyInput: document.getElementById("employeeLogicKeyInput"),
  employeeDesignationInput: document.getElementById("employeeDesignationInput"),
  employeeReportingToInput: document.getElementById("employeeReportingToInput"),
  employeeReportingNameInput: document.getElementById("employeeReportingNameInput"),
  employeeManagerDesignationInput: document.getElementById("employeeManagerDesignationInput"),
  employeeHierarchyRoleInput: document.getElementById("employeeHierarchyRoleInput"),
  employeeDisbursalInput: document.getElementById("employeeDisbursalInput"),
  employeeProjectIncentiveInput: document.getElementById("employeeProjectIncentiveInput"),
  employeeTempPasswordInput: document.getElementById("employeeTempPasswordInput"),
  employeeAdminAccessInput: document.getElementById("employeeAdminAccessInput"),
  employeeDepartmentPercentInput: document.getElementById("employeeDepartmentPercentInput"),
  employeeTeamSharePercentInput: document.getElementById("employeeTeamSharePercentInput"),
  employeeNpsInput: document.getElementById("employeeNpsInput"),
  formulaProjectValue: document.getElementById("formulaProjectValue"),
  formulaDepartmentPercent: document.getElementById("formulaDepartmentPercent"),
  formulaTeamSharePercent: document.getElementById("formulaTeamSharePercent"),
  formulaMySharePercent: document.getElementById("formulaMySharePercent"),
  formulaNpsPercent: document.getElementById("formulaNpsPercent"),
  formulaFinalValue: document.getElementById("formulaFinalValue"),
  saveEmployeeBtn: document.getElementById("saveEmployeeBtn"),
  deleteEmployeeBtn: document.getElementById("deleteEmployeeBtn"),
  undoEmployeeBtn: document.getElementById("undoEmployeeBtn"),
  employeeNotice: document.getElementById("employeeNotice"),
  teamWorkbookInput: document.getElementById("teamWorkbookInput"),
  logicWorkbookInput: document.getElementById("logicWorkbookInput"),
  sbuWorkbookInput: document.getElementById("sbuWorkbookInput"),
  projectWorkbookInput: document.getElementById("projectWorkbookInput"),
  passwordForm: document.getElementById("passwordForm"),
  currentPassword: document.getElementById("currentPassword"),
  newPassword: document.getElementById("newPassword"),
  confirmPassword: document.getElementById("confirmPassword"),
  changePasswordBtn: document.getElementById("changePasswordBtn"),
  passwordNotice: document.getElementById("passwordNotice"),
};

const state = {
  dashboard: null,
  selectedEmployeeId: "",
  searchTerm: "",
  startDate: "",
  endDate: "",
  selectedPeriod: "",
  selectedQuarter: "",
};

const EYE_ICON = `
  <svg viewBox="0 0 24 24" aria-hidden="true">
    <path d="M12 5C6.5 5 2.2 8.4 1 12c1.2 3.6 5.5 7 11 7s9.8-3.4 11-7c-1.2-3.6-5.5-7-11-7Zm0 11.2A4.2 4.2 0 1 1 12 7.8a4.2 4.2 0 0 1 0 8.4Zm0-6.7a2.5 2.5 0 1 0 0 5a2.5 2.5 0 0 0 0-5Z"></path>
  </svg>
`;

const QUARTER_SEQUENCE = ["Q1", "Q2", "Q3", "Q4"];
const REQUIRED_UPLOAD_TYPES = [
  ["team_master", "Team Sheet"],
  ["gtm_logic", "GTM Logic"],
  ["sbu_logic", "SBU Logic"],
  ["project_cf", "Project Sheet"],
];
const WORKBOOK_BACKUP_DB = "gtm-workbook-backups";
const WORKBOOK_BACKUP_STORE = "workbooks";

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function openWorkbookBackupDb() {
  if (!window.indexedDB) return Promise.resolve(null);
  return new Promise((resolve) => {
    let settled = false;
    let timeoutId;
    const finish = (db = null) => {
      if (settled) return;
      settled = true;
      if (timeoutId) clearTimeout(timeoutId);
      resolve(db);
    };
    let request;
    try {
      request = window.indexedDB.open(WORKBOOK_BACKUP_DB, 1);
    } catch (error) {
      finish(null);
      return;
    }
    timeoutId = setTimeout(() => finish(null), 2000);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(WORKBOOK_BACKUP_STORE)) {
        db.createObjectStore(WORKBOOK_BACKUP_STORE, { keyPath: "uploadType" });
      }
    };
    request.onsuccess = () => finish(request.result);
    request.onerror = () => finish(null);
    request.onblocked = () => finish(null);
  });
}

async function withWorkbookBackupStore(mode, action) {
  const db = await openWorkbookBackupDb();
  if (!db) return null;
  return new Promise((resolve) => {
    let transaction;
    let result;
    try {
      transaction = db.transaction(WORKBOOK_BACKUP_STORE, mode);
      const store = transaction.objectStore(WORKBOOK_BACKUP_STORE);
      result = action(store);
    } catch (error) {
      db.close();
      resolve(null);
      return;
    }
    transaction.oncomplete = () => {
      db.close();
      resolve(result?.result ?? result ?? null);
    };
    transaction.onerror = () => {
      db.close();
      resolve(null);
    };
    transaction.onabort = () => {
      db.close();
      resolve(null);
    };
  });
}

async function backupWorkbook(uploadType, file, uploadedAt = "") {
  const arrayBuffer = await file.arrayBuffer();
  const saved = await withWorkbookBackupStore("readwrite", (store) =>
    store.put({
      uploadType,
      fileName: file.name,
      mimeType: file.type || "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      updatedAt: uploadedAt || new Date().toISOString(),
      arrayBuffer,
    })
  );
  return saved !== null;
}

async function removeWorkbookBackup(uploadType) {
  if (!uploadType) return;
  await withWorkbookBackupStore("readwrite", (store) => store.delete(uploadType));
}

async function getWorkbookBackups() {
  return (await withWorkbookBackupStore("readonly", (store) => store.getAll())) || [];
}

function isNetworkError(error) {
  return error instanceof TypeError || /load failed|failed to fetch|network/i.test(error?.message || "");
}

async function api(path, options = {}) {
  const fetchOptions = { credentials: "same-origin", ...options };
  const retries = Number(options.retries ?? 1);
  for (let attempt = 0; attempt <= retries; attempt += 1) {
    try {
      const response = await fetch(path, fetchOptions);
      const contentType = response.headers.get("Content-Type") || "";
      const data = contentType.includes("application/json") ? await response.json().catch(() => ({})) : {};
      if (!response.ok) {
        throw new Error(data.error || "Request failed");
      }
      return data;
    } catch (error) {
      if (attempt < retries && isNetworkError(error)) {
        await sleep(800);
        continue;
      }
      if (isNetworkError(error)) {
        throw new Error("Unable to reach the server. Please refresh the page and try again.");
      }
      throw error;
    }
  }
  throw new Error("Request failed");
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function money(value) {
  return `Rs ${Number(value || 0).toLocaleString("en-IN", { minimumFractionDigits: 0, maximumFractionDigits: 2 })}`;
}

function percent(value) {
  return `${Number(value || 0).toLocaleString("en-IN", { maximumFractionDigits: 2 })}%`;
}

function rawPercent(value) {
  return Number(value || 0);
}

function setLoggedIn(loggedIn) {
  els.authShell.classList.toggle("hidden", loggedIn);
  els.appShell.classList.toggle("hidden", !loggedIn);
}

function isAdmin() {
  return Boolean(state.dashboard?.viewer?.isAdmin);
}

function currentEmployee() {
  return state.dashboard?.viewedEmployee || null;
}

function currentSummary() {
  return currentEmployee()?.latestSummary || null;
}

function greetingForNow() {
  const hour = new Date().getHours();
  if (hour >= 5 && hour < 12) return "Good Morning";
  if (hour >= 12 && hour < 17) return "Good Afternoon";
  if (hour >= 17 && hour < 22) return "Good Evening";
  return "Welcome Back";
}

function firstName(value) {
  const clean = String(value || "").trim();
  return clean ? clean.split(/\s+/)[0] : "";
}

function periodLabelToDate(periodLabel) {
  if (!periodLabel || !/^\d{4}-\d{2}$/.test(periodLabel)) return null;
  const [year, month] = periodLabel.split("-").map(Number);
  return new Date(year, month - 1, 1);
}

function displayPeriod(periodLabel) {
  const date = periodLabelToDate(periodLabel);
  return date ? date.toLocaleDateString("en-IN", { month: "short", year: "numeric" }) : periodLabel || "-";
}

function quarterForPeriod(periodLabel) {
  const date = periodLabelToDate(periodLabel);
  if (!date) return "Q1";
  const month = date.getMonth() + 1;
  if (month >= 4 && month <= 6) return "Q1";
  if (month >= 7 && month <= 9) return "Q2";
  if (month >= 10 && month <= 12) return "Q3";
  return "Q4";
}

function groupPeriodsByQuarter(periods) {
  const grouped = { Q1: [], Q2: [], Q3: [], Q4: [] };
  periods.forEach((periodLabel) => {
    grouped[quarterForPeriod(periodLabel)].push(periodLabel);
  });
  return grouped;
}

function formatLoadedAt(value) {
  if (!value) return { primary: "-", secondary: "-" };
  const normalized = String(value).replace(" ", "T");
  const date = new Date(normalized);
  if (Number.isNaN(date.getTime())) {
    return { primary: value, secondary: "" };
  }
  return {
    primary: date.toLocaleDateString("en-GB"),
    secondary: date.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }),
  };
}

function employeeChoiceFromPicker() {
  const lookup = els.employeePickerInput.value.trim().toLowerCase();
  const employees = state.dashboard?.employees || [];
  if (!lookup) return null;
  return (
    employees.find((employee) => employee.employeeId.toLowerCase() === lookup) ||
    employees.find((employee) => employee.name.toLowerCase() === lookup) ||
    employees.find((employee) => `${employee.name} (${employee.employeeId})`.toLowerCase() === lookup) ||
    null
  );
}

function employeeChoiceFromDownloadPicker() {
  const lookup = els.downloadEmployeePickerInput.value.trim().toLowerCase();
  const employees = state.dashboard?.employees || [];
  if (!lookup) return null;
  return (
    employees.find((employee) => employee.employeeId.toLowerCase() === lookup) ||
    employees.find((employee) => employee.name.toLowerCase() === lookup) ||
    employees.find((employee) => `${employee.name} (${employee.employeeId})`.toLowerCase() === lookup) ||
    null
  );
}

function updateDownloadLinks() {
  const query = new URLSearchParams();
  if (state.selectedEmployeeId) query.set("employeeId", state.selectedEmployeeId);
  if (state.startDate) query.set("startDate", state.startDate);
  if (state.endDate) query.set("endDate", state.endDate);
  if (state.selectedPeriod) query.set("period", state.selectedPeriod);
  els.downloadReportLink.href = `/api/report.csv?${query.toString()}`;

  const fullQuery = new URLSearchParams();
  if (state.startDate) fullQuery.set("startDate", state.startDate);
  if (state.endDate) fullQuery.set("endDate", state.endDate);
  if (state.selectedPeriod) fullQuery.set("period", state.selectedPeriod);
  els.downloadCompleteReportLink.href = `/api/report.csv?${fullQuery.toString()}`;

  const selectedEmployee = employeeChoiceFromDownloadPicker() || currentEmployee();
  const employeeQuery = new URLSearchParams(fullQuery);
  if (selectedEmployee?.employeeId) employeeQuery.set("employeeId", selectedEmployee.employeeId);
  els.downloadEmployeeReportLink.href = `/api/report.csv?${employeeQuery.toString()}`;
}

function renderDepartmentOptions() {
  const departments = state.dashboard?.departments || ["Viztown", "Events", "Digital Marketing", "Marketing", "Founder Connect", "Operations", "Design"];
  els.employeeDepartmentInput.innerHTML = departments.map((department) => `<option value="${escapeHtml(department)}">${escapeHtml(department)}</option>`).join("");
}

function renderEmployeeOptions() {
  const employees = state.dashboard?.employees || [];
  els.employeeOptions.innerHTML = employees
    .map((employee) => `<option value="${escapeHtml(`${employee.name} (${employee.employeeId})`)}"></option>`)
    .join("");
  const selectedEmployee = employees.find((employee) => employee.employeeId === state.selectedEmployeeId);
  els.employeePickerInput.value = selectedEmployee ? `${selectedEmployee.name} (${selectedEmployee.employeeId})` : "";
  if (!els.downloadEmployeePickerInput.value && selectedEmployee) {
    els.downloadEmployeePickerInput.value = `${selectedEmployee.name} (${selectedEmployee.employeeId})`;
  }
  els.searchInput.value = state.searchTerm;
}

function syncPeriodControls() {
  const employee = currentEmployee();
  const availablePeriods = employee?.periodOrder?.length ? employee.periodOrder : state.dashboard?.periodOptions || [];
  const selected = employee?.selectedPeriod || state.selectedPeriod || availablePeriods[availablePeriods.length - 1] || state.dashboard?.currentPeriod || "";
  state.selectedPeriod = selected;
  state.selectedQuarter = quarterForPeriod(selected);
  const optionsMarkup = availablePeriods
    .map((periodLabel) => `<option value="${escapeHtml(periodLabel)}">${escapeHtml(displayPeriod(periodLabel))}</option>`)
    .join("");
  els.periodSelect.innerHTML = optionsMarkup;
  els.projectMonthSelect.innerHTML = optionsMarkup;
  if (selected) {
    els.periodSelect.value = selected;
    els.projectMonthSelect.value = selected;
  }
}

function renderSummary() {
  const viewer = state.dashboard?.viewer || {};
  const employee = currentEmployee();
  const summary = currentSummary();
  const headerName = firstName(viewer.name || employee?.name || "Team");
  const subtitleParts = [employee?.grade, employee?.designation, employee?.department, employee?.location].filter(Boolean);

  els.sessionUser.textContent = viewer.name || "-";
  els.sessionMeta.textContent = [viewer.grade, viewer.designation, viewer.department, viewer.location].filter(Boolean).join(" | ") || viewer.businessUnit || "-";
  els.greetingText.textContent = headerName ? `${greetingForNow()}, ${headerName}` : greetingForNow();
  els.dashboardTitle.textContent = employee?.name ? `Performance Dashboard of ${employee.name}` : "Performance Dashboard";
  els.dashboardSubtitle.textContent = subtitleParts.join(" | ") || "Grade | Designation | Department | Location";

  els.npsScoreValue.textContent = summary ? Number(summary.npsScore || 0).toLocaleString("en-IN", { maximumFractionDigits: 2 }) : "0";
  els.npsScoreLabel.textContent = summary ? `Average score for ${summary.displayPeriod}` : "Average score for selected month";
  els.npsDisbursalValue.textContent = percent(summary?.disbursalPercent || 0);
  els.npsDisbursalLabel.textContent = employee ? `${String(employee.disbursalType || "quarterly").replace(/^./, (value) => value.toUpperCase())} payout logic` : "Based on incentive rules";
  els.accruedValue.textContent = money(summary?.accruedRs || 0);
  els.accruedLabel.textContent = summary ? `Final disbursal ${money(summary.finalDisbursal || 0)}` : "Final value after project formula";

  els.disbursalStatusValue.textContent = summary?.disbursalStatus || "Pending";
  els.disbursalStatusInput.value = summary?.disbursalStatus || "Pending";
  els.disbursalStatusInput.classList.toggle("hidden", !isAdmin());
  els.saveStatusBtn.classList.toggle("hidden", !isAdmin());
}

function renderHierarchy() {
  const employee = currentEmployee();
  const hierarchy = employee?.hierarchy || {};
  const rows = [
    ["Reporting To", hierarchy.reportingTo || "-"],
    ["Manager Name", hierarchy.managerName || "-"],
    ["Designation", hierarchy.designation || "-"],
  ];
  els.hierarchyGrid.innerHTML = rows
    .map(
      ([label, value]) => `
        <article class="summary-item">
          <span>${escapeHtml(label)}</span>
          <strong>${escapeHtml(value)}</strong>
        </article>
      `
    )
    .join("");
}

function renderQuarterTrend() {
  const employee = currentEmployee();
  const periods = employee?.periodOrder || [];
  if (!periods.length) {
    els.quarterTabs.innerHTML = "";
    els.trendList.innerHTML = `<article class="trend-item empty-state">Quarterly trend will appear after month-wise KPI data is saved.</article>`;
    return;
  }

  const grouped = groupPeriodsByQuarter(periods);
  if (!QUARTER_SEQUENCE.includes(state.selectedQuarter)) {
    state.selectedQuarter = quarterForPeriod(employee.selectedPeriod || periods[periods.length - 1]);
  }

  els.quarterTabs.innerHTML = QUARTER_SEQUENCE.map((quarter) => {
    const activeClass = quarter === state.selectedQuarter ? " is-active" : "";
    return `<button class="quarter-tab${activeClass}" data-quarter="${quarter}" type="button">${quarter}</button>`;
  }).join("");

  const activePeriods = grouped[state.selectedQuarter] || [];
  const quarterAccrued = activePeriods.reduce((sum, periodLabel) => sum + Number(employee.periods[periodLabel]?.accruedRs || 0), 0);
  const quarterDisbursal = activePeriods.reduce((sum, periodLabel) => sum + Number(employee.periods[periodLabel]?.finalDisbursal || 0), 0);

  els.trendList.innerHTML = `
    <article class="trend-item trend-item--metric">
      <strong>${state.selectedQuarter} Total</strong>
      <p>${money(quarterAccrued)} accrued | ${money(quarterDisbursal)} disbursal</p>
    </article>
  ` + activePeriods
    .map((periodLabel) => {
      const summary = employee.periods[periodLabel];
      return `
        <article class="trend-item">
          <strong>${escapeHtml(summary.displayPeriod)}</strong>
          <p>Score ${escapeHtml(summary.finalScore)} | NPS ${escapeHtml(summary.npsScore)} | ${money(summary.accruedRs)}</p>
        </article>
      `;
    })
    .join("");
}

function renderKpis() {
  const employee = currentEmployee();
  const summary = currentSummary();
  const rows = summary?.kpis || [];

  els.kpiNotice.textContent = summary
    ? `${rows.length} KPI rows loaded for ${summary.displayPeriod}. Target, score slabs, and weightage are mapped from the ${employee?.businessUnit || "GTM"} ${employee?.logicKey || employee?.department || ""} logic sheet.`
    : "KPI scorecard will appear here.";

  els.kpiTableBody.innerHTML = rows.length
    ? rows
        .map((row) => {
          const saveButton = isAdmin() ? `<button class="ghost-btn small-btn save-kpi-btn" type="button">Save</button>` : "";
          return `
            <tr data-record-id="${escapeHtml(row.recordId)}">
              <td>${escapeHtml(row.kraCategory || "-")}</td>
              <td>${escapeHtml(row.kpiName || "-")}</td>
              <td><input class="small-input target-input" type="number" step="0.01" value="${escapeHtml(row.target)}" ${isAdmin() ? "" : "disabled"} /></td>
              <td><input class="small-input achieved-input" type="number" step="0.01" value="${escapeHtml(row.achieved)}" ${isAdmin() ? "" : "disabled"} /></td>
              <td>${escapeHtml(row.achievementPercent)}%</td>
              <td>${escapeHtml(row.score)}</td>
              <td>${escapeHtml(row.weightage)}</td>
              <td>${escapeHtml(row.finalWeightedScore)}</td>
              <td>${escapeHtml(row.npsScore)}</td>
              <td>
                <div class="action-cell">
                  <span class="status-badge">${escapeHtml(row.action)}</span>
                  ${saveButton}
                </div>
              </td>
            </tr>
          `;
        })
        .join("")
    : `<tr><td colspan="10">No KPI rows are available for this employee yet.</td></tr>`;
}

function renderProjects() {
  const employee = currentEmployee();
  const summary = currentSummary();
  const rows = summary?.projects || [];
  const currentMyShare = Number(employee?.mySharePercent ?? employee?.projectIncentivePercent ?? 0);

  els.projectValueTotal.textContent = money(summary?.projectValue || 0);
  els.projectDepartmentPercent.textContent = percent(employee?.departmentPercent || 0);
  els.projectTeamSharePercent.textContent = percent(employee?.teamSharePercent || 0);
  els.projectMyShareValue.textContent = percent(currentMyShare || 0);
  els.projectDisbursalPercent.textContent = Number(summary?.npsScore || 0).toLocaleString("en-IN", { maximumFractionDigits: 2 });
  els.projectFinalDisbursal.textContent = money(summary?.finalDisbursal || 0);

  els.projectTableBody.innerHTML = rows.length
    ? rows
        .map((row) => {
          const adminControls = isAdmin()
            ? `
              <td><input class="small-input project-share-input" type="number" min="0" step="0.01" value="${escapeHtml(row.sharePercent)}" /></td>
              <td><input class="small-input project-department-input" type="number" min="0" step="0.01" value="${escapeHtml(row.departmentPercent)}" /></td>
              <td><input class="small-input project-team-input" type="number" min="0" step="0.01" value="${escapeHtml(row.teamSharePercent)}" /></td>
              <td>${percent(row.mySharePercent)}</td>
              <td>${money(row.accruedValue)}</td>
              <td>${percent(row.npsDisbursalPercent)}</td>
              <td>${money(row.finalDisbursalValue)}</td>
              <td><button class="ghost-btn small-btn save-project-btn" type="button">Save</button></td>
            `
            : `
              <td>${percent(row.sharePercent)}</td>
              <td>${percent(row.departmentPercent)}</td>
              <td>${percent(row.teamSharePercent)}</td>
              <td>${percent(row.mySharePercent)}</td>
              <td>${money(row.accruedValue)}</td>
              <td>${percent(row.npsDisbursalPercent)}</td>
              <td>${money(row.finalDisbursalValue)}</td>
              <td><span class="status-badge">View Only</span></td>
            `;
          return `
            <tr data-project-id="${escapeHtml(row.projectId || row.projectName)}">
              <td>${escapeHtml(row.projectName || "-")}</td>
              <td>${escapeHtml(row.projectId || "-")}</td>
              <td>${money(row.projectValue || 0)}</td>
              <td>${money(row.cashflowValue || 0)}</td>
              ${adminControls}
            </tr>
          `;
        })
        .join("")
    : `<tr><td colspan="12">No mapped projects are available for this employee in the selected month.</td></tr>`;
}

function renderAdmin() {
  const admin = state.dashboard?.admin || { enabled: false };
  const showAdmin = Boolean(admin.enabled) && isAdmin();
  els.adminPanel.classList.toggle("hidden", !showAdmin);
  els.adminNav.classList.toggle("hidden", !showAdmin);
  if (!showAdmin) {
    renderDepartmentOptions();
    return;
  }

  const updated = formatLoadedAt(admin.dataUpdated);
  els.totalEmployeesValue.textContent = admin.totalEmployees || 0;
  els.totalPayoutValue.textContent = money(admin.totalAccrued || 0);
  els.quarterlyPayoutValue.textContent = money(admin.totalDisbursal || 0);
  els.annualPayoutValue.textContent = updated.primary;
  els.dataUpdatedMeta.textContent = updated.secondary;
  els.disbursalStatusSummary.textContent = admin.disbursalStatus || "-";

  els.departmentList.innerHTML = (admin.departmentPerformance || []).length
    ? admin.departmentPerformance
        .map(
          (item) => `
            <article class="trend-item trend-item--metric">
              <div>
                <strong>${escapeHtml(item.department)}</strong>
                <p>${item.headcount} employees</p>
              </div>
              <div class="trend-metrics">
                <span>${percent(item.averagePerformance)} average</span>
              </div>
            </article>
          `
        )
        .join("")
    : `<article class="trend-item empty-state">Department summaries will appear after KPI updates.</article>`;

  const activeUploads = (admin.uploadHistory || []).filter((item) => !item.deleted);
  const activeUploadTypes = new Set(activeUploads.map((item) => item.uploadType).filter(Boolean));
  const missingUploadCards = REQUIRED_UPLOAD_TYPES.filter(([uploadType]) => !activeUploadTypes.has(uploadType))
    .map(
      ([, label]) => `
        <article class="upload-item empty-state">
          <div>
            <strong>${escapeHtml(label)} missing</strong>
            <p>Upload the latest workbook so dashboards stay fully mapped.</p>
          </div>
        </article>
      `
    )
    .join("");

  els.uploadHistory.innerHTML = activeUploads.length
    ? activeUploads
        .map((item) => {
          const uploaded = formatLoadedAt(item.uploadedAt);
          return `
            <article class="upload-item">
              <div>
                <strong>${escapeHtml(item.fileName)}</strong>
                <p>${escapeHtml(String(item.uploadType || "").replaceAll("_", " "))} | ${escapeHtml(item.recordCount || 0)} records</p>
                <small>${escapeHtml(uploaded.primary)} ${escapeHtml(uploaded.secondary)}</small>
              </div>
              <div class="inline-actions compact">
                <span class="mono">${escapeHtml(item.fileId)}</span>
                <button class="ghost-btn small-btn delete-upload-btn" data-file-id="${escapeHtml(item.fileId)}" type="button">Delete</button>
              </div>
            </article>
          `;
        })
        .join("") + missingUploadCards
    : `<article class="upload-item empty-state">Uploaded workbooks will appear here.</article>`;

  renderDepartmentOptions();
}

function fillEmployeeForm(employee) {
  if (!employee) {
    els.employeeForm.reset();
    return;
  }
  const source = state.dashboard?.employees?.find((item) => item.employeeId === employee.employeeId) || {};
  els.employeeIdInput.value = employee.employeeId || "";
  els.employeeNameInput.value = employee.name || "";
  els.employeeEmailInput.value = employee.email || "";
  els.employeeGradeInput.value = employee.grade || "";
  els.employeeLocationInput.value = employee.location || "";
  els.employeeDepartmentInput.value = employee.department || "";
  els.employeeBusinessUnitInput.value = employee.businessUnit || source.businessUnit || "GTM";
  els.employeeLogicKeyInput.value = employee.logicKey || employee.department || "Marketing";
  els.employeeDesignationInput.value = employee.designation || "";
  els.employeeReportingToInput.value = employee.hierarchy?.reportingTo || "";
  els.employeeReportingNameInput.value = employee.hierarchy?.managerName || "";
  els.employeeManagerDesignationInput.value = employee.hierarchy?.designation || "";
  els.employeeHierarchyRoleInput.value = source.hierarchyRole || "manager";
  els.employeeDisbursalInput.value = employee.disbursalType || source.disbursalType || "quarterly";
  els.employeeProjectIncentiveInput.value = employee.mySharePercent ?? source.mySharePercent ?? employee.projectIncentivePercent ?? source.projectIncentivePercent ?? "";
  els.employeeTempPasswordInput.value = "";
  els.employeeAdminAccessInput.value = employee.adminAccess || source.adminAccess ? "true" : "false";
  els.employeeDepartmentPercentInput.value = employee.departmentPercent ?? source.departmentPercent ?? "";
  els.employeeTeamSharePercentInput.value = employee.teamSharePercent ?? source.teamSharePercent ?? "";
  els.employeeNpsInput.value = currentSummary()?.npsScore ?? employee.npsScore ?? source.npsScore ?? "";
}

function renderFormulaPreview() {
  const summary = currentSummary();
  const projectValue = Number(summary?.projectValue || 0);
  const departmentPercent = rawPercent(els.employeeDepartmentPercentInput.value || currentEmployee()?.departmentPercent || 0);
  const teamSharePercent = rawPercent(els.employeeTeamSharePercentInput.value || currentEmployee()?.teamSharePercent || 0);
  const mySharePercent = rawPercent(els.employeeProjectIncentiveInput.value || currentEmployee()?.mySharePercent || currentEmployee()?.projectIncentivePercent || 0);
  const npsPercent = rawPercent(currentSummary()?.disbursalPercent || 0);
  const hiddenSharePercent = rawPercent(currentEmployee()?.sharePercent || 100);
  const finalValue =
    projectValue *
    (hiddenSharePercent / 100) *
    (departmentPercent / 100) *
    (teamSharePercent / 100) *
    (mySharePercent / 100) *
    (npsPercent / 100);

  els.formulaProjectValue.textContent = money(projectValue);
  els.formulaDepartmentPercent.textContent = percent(departmentPercent);
  els.formulaTeamSharePercent.textContent = percent(teamSharePercent);
  els.formulaMySharePercent.textContent = percent(mySharePercent);
  els.formulaNpsPercent.textContent = Number(summary?.npsScore || 0).toLocaleString("en-IN", { maximumFractionDigits: 2 });
  els.formulaFinalValue.textContent = money(finalValue);
  els.projectMyShareValue.textContent = percent(mySharePercent || 0);
}

function renderAll() {
  renderEmployeeOptions();
  syncPeriodControls();
  renderSummary();
  renderHierarchy();
  renderQuarterTrend();
  renderKpis();
  renderProjects();
  renderAdmin();
  fillEmployeeForm(currentEmployee());
  renderFormulaPreview();
  updateDownloadLinks();
}

function scheduleWorkbookRestore() {
  if (!state.dashboard?.viewer?.isAdmin || state.restoreInProgress) return;
  restoreMissingWorkbookBackups()
    .then((restored) => {
      if (restored) return refreshDashboard({ skipRestore: true });
      return null;
    })
    .catch((error) => {
      console.error(error);
      if (els.uploadNotice) {
        els.uploadNotice.textContent = "Signed in. Workbook restore will retry after the next upload or refresh.";
      }
    });
}

async function refreshDashboard(options = {}) {
  const query = new URLSearchParams();
  if (state.selectedEmployeeId) query.set("employeeId", state.selectedEmployeeId);
  if (state.searchTerm) query.set("search", state.searchTerm);
  if (state.startDate) query.set("startDate", state.startDate);
  if (state.endDate) query.set("endDate", state.endDate);
  if (state.selectedPeriod) query.set("period", state.selectedPeriod);
  state.dashboard = await api(`/api/me?${query.toString()}`);
  state.selectedEmployeeId = state.dashboard?.viewedEmployee?.employeeId || state.selectedEmployeeId;
  state.selectedPeriod = state.dashboard?.viewedEmployee?.selectedPeriod || state.selectedPeriod || state.dashboard?.currentPeriod || "";
  state.selectedQuarter = quarterForPeriod(state.selectedPeriod);
  renderAll();
  if (!options.skipRestore) scheduleWorkbookRestore();
}

async function restoreMissingWorkbookBackups() {
  if (!state.dashboard?.viewer?.isAdmin || state.restoreInProgress) return false;
  const activeByType = new Map();
  (state.dashboard?.admin?.uploadHistory || [])
    .filter((item) => !item.deleted && item.uploadType)
    .forEach((item) => {
      const current = activeByType.get(item.uploadType);
      if (!current || String(item.uploadedAt || "") > String(current.uploadedAt || "")) {
        activeByType.set(item.uploadType, item);
      }
    });
  const backups = (await getWorkbookBackups()).filter((item) => item?.uploadType && (item?.arrayBuffer || item?.blob));
  const missingBackups = backups.filter((item) => {
    const active = activeByType.get(item.uploadType);
    return !active || Number(active.recordCount || 0) <= 0 || String(item.updatedAt || "") > String(active.uploadedAt || "");
  });
  if (!missingBackups.length) return false;

  state.restoreInProgress = true;
  let restored = 0;
  try {
    for (const backup of missingBackups) {
      const workbookData = backup.arrayBuffer || backup.blob;
      const file = new File([workbookData], backup.fileName || `${backup.uploadType}.xlsx`, {
        type: backup.mimeType || "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      });
      const formData = new FormData();
      formData.append("workbook", file);
      formData.append("uploadType", backup.uploadType);
      await api("/api/admin/upload-workbook", { method: "POST", body: formData });
      restored += 1;
    }
    if (restored && els.uploadNotice) {
      els.uploadNotice.textContent = `${restored} last uploaded workbook${restored === 1 ? "" : "s"} restored automatically.`;
    }
    return restored > 0;
  } catch (error) {
    if (els.uploadNotice) {
      els.uploadNotice.textContent = `Could not restore saved workbook backup: ${error.message}`;
    }
    return false;
  } finally {
    state.restoreInProgress = false;
  }
}

async function login(event) {
  event.preventDefault();
  els.loginNotice.textContent = "Signing you in...";
  let dashboard;
  try {
    dashboard = await api("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        loginType: els.loginType.value,
        employeeId: els.loginEmployeeId.value.trim(),
        password: els.loginPassword.value,
      }),
    });
  } catch (error) {
    els.loginNotice.textContent = error.message;
    return;
  }

  try {
    state.dashboard = dashboard;
    state.selectedEmployeeId = state.dashboard?.viewedEmployee?.employeeId || "";
    state.selectedPeriod = state.dashboard?.viewedEmployee?.selectedPeriod || state.dashboard?.currentPeriod || "";
    state.selectedQuarter = quarterForPeriod(state.selectedPeriod);
    setLoggedIn(true);
    renderAll();
    scheduleWorkbookRestore();
    els.loginNotice.textContent = "Use your employee ID and password to continue.";
  } catch (error) {
    console.error(error);
    els.loginNotice.textContent = "Signed in, but the dashboard could not load. Please refresh once.";
  }
}

async function logout() {
  try {
    await api("/api/logout", { method: "POST" });
  } catch (error) {
    console.error(error);
  }
  state.dashboard = null;
  state.selectedEmployeeId = "";
  state.searchTerm = "";
  state.startDate = "";
  state.endDate = "";
  state.selectedPeriod = "";
  state.selectedQuarter = "";
  setLoggedIn(false);
}

async function saveEmployee() {
  try {
    await api("/api/admin/employees", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        employeeId: els.employeeIdInput.value.trim(),
        name: els.employeeNameInput.value.trim(),
        email: els.employeeEmailInput.value.trim(),
        grade: els.employeeGradeInput.value.trim(),
        location: els.employeeLocationInput.value.trim(),
        department: els.employeeDepartmentInput.value,
        businessUnit: els.employeeBusinessUnitInput.value,
        logicKey: els.employeeLogicKeyInput.value,
        designation: els.employeeDesignationInput.value.trim(),
        reportingTo: els.employeeReportingToInput.value.trim(),
        reportingName: els.employeeReportingNameInput.value.trim(),
        managerName: els.employeeReportingNameInput.value.trim(),
        managerDesignation: els.employeeManagerDesignationInput.value.trim(),
        hierarchyRole: els.employeeHierarchyRoleInput.value,
        disbursalType: els.employeeDisbursalInput.value,
        sharePercent: currentEmployee()?.sharePercent ?? 100,
        projectIncentivePercent: els.employeeProjectIncentiveInput.value,
        mySharePercent: els.employeeProjectIncentiveInput.value,
        tempPassword: els.employeeTempPasswordInput.value.trim(),
        adminAccess: els.employeeAdminAccessInput.value === "true",
        departmentPercent: els.employeeDepartmentPercentInput.value,
        teamSharePercent: els.employeeTeamSharePercentInput.value,
        npsScore: els.employeeNpsInput.value,
      }),
    });
    els.employeeNotice.textContent = "Employee record saved successfully.";
    els.employeeTempPasswordInput.value = "";
    await refreshDashboard();
  } catch (error) {
    els.employeeNotice.textContent = error.message;
  }
}

async function deleteEmployee() {
  if (!window.confirm("Delete this employee from the active dashboard?")) return;
  try {
    await api("/api/admin/employees/delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ employeeId: els.employeeIdInput.value.trim() }),
    });
    els.employeeNotice.textContent = "Employee deleted successfully.";
    state.selectedEmployeeId = "";
    await refreshDashboard();
  } catch (error) {
    els.employeeNotice.textContent = error.message;
  }
}

async function undoDeleteEmployee() {
  try {
    await api("/api/admin/employees/undo", { method: "POST" });
    els.employeeNotice.textContent = "Previous employee deletion has been restored.";
    await refreshDashboard();
  } catch (error) {
    els.employeeNotice.textContent = error.message;
  }
}

async function saveKpi(event) {
  const row = event.target.closest("tr");
  if (!row) return;
  try {
    await api("/api/admin/kpi/update", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        recordId: row.dataset.recordId,
        target: row.querySelector(".target-input")?.value,
        achieved: row.querySelector(".achieved-input")?.value,
      }),
    });
    els.kpiNotice.textContent = "KPI row saved successfully.";
    await refreshDashboard();
  } catch (error) {
    els.kpiNotice.textContent = error.message;
  }
}

async function saveProject(event) {
  const row = event.target.closest("tr");
  const employee = currentEmployee();
  if (!row || !employee) return;
  try {
    await api("/api/admin/project/update", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        employeeId: employee.employeeId,
        periodLabel: state.selectedPeriod,
        projectId: row.dataset.projectId,
        sharePercent: row.querySelector(".project-share-input")?.value,
        departmentPercent: row.querySelector(".project-department-input")?.value,
        teamSharePercent: row.querySelector(".project-team-input")?.value,
      }),
    });
    await refreshDashboard();
  } catch (error) {
    els.uploadNotice.textContent = error.message;
  }
}

async function saveDisbursalStatus() {
  const employee = currentEmployee();
  if (!employee) return;
  try {
    await api("/api/admin/status/update", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        employeeId: employee.employeeId,
        periodLabel: state.selectedPeriod,
        status: els.disbursalStatusInput.value,
      }),
    });
    await refreshDashboard();
  } catch (error) {
    els.disbursalStatusValue.textContent = error.message;
  }
}

async function uploadWorkbook(uploadType, inputId) {
  const input = document.getElementById(inputId);
  const file = input?.files?.[0];
  if (!file) {
    els.uploadNotice.textContent = "Choose an .xlsx file before uploading.";
    return;
  }
  const formData = new FormData();
  formData.append("workbook", file);
  formData.append("uploadType", uploadType);
  try {
    const result = await api("/api/admin/upload-workbook", { method: "POST", body: formData });
    const backedUp = await backupWorkbook(uploadType, file, result.upload?.uploadedAt);
    els.uploadNotice.textContent = backedUp
      ? `${file.name} uploaded successfully and replaced the active file for this upload type.`
      : `${file.name} uploaded successfully, but the browser backup could not be saved. Please keep this file available.`;
    input.value = "";
    await refreshDashboard();
  } catch (error) {
    els.uploadNotice.textContent = error.message;
  }
}

async function deleteUpload(fileId) {
  if (!window.confirm("Delete this uploaded file from the dashboard history?")) return;
  const uploadType = (state.dashboard?.admin?.uploadHistory || []).find((item) => item.fileId === fileId)?.uploadType || "";
  try {
    await api("/api/admin/delete-upload", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ fileId }),
    });
    await removeWorkbookBackup(uploadType);
    els.uploadNotice.textContent = "Uploaded file deleted successfully. Upload the updated workbook to rebuild the mapping.";
    await refreshDashboard();
  } catch (error) {
    els.uploadNotice.textContent = error.message;
  }
}

async function updatePassword() {
  try {
    const result = await api("/api/change-password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        currentPassword: els.currentPassword.value,
        newPassword: els.newPassword.value,
        confirmPassword: els.confirmPassword.value,
      }),
    });
    els.passwordNotice.textContent = result.message;
    els.passwordForm.reset();
  } catch (error) {
    els.passwordNotice.textContent = error.message;
  }
}

async function requestResetOtp() {
  els.resetNotice.textContent = "Sending OTP...";
  try {
    const result = await api("/api/request-reset-otp", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        employeeId: els.resetEmployeeId.value.trim(),
        employeeName: els.resetEmployeeName.value.trim(),
        email: els.resetEmail.value.trim(),
      }),
    });
    if (result.employeeId) {
      els.resetEmployeeId.value = result.employeeId;
    }
    els.resetNotice.textContent = result.message || "OTP sent successfully.";
  } catch (error) {
    els.resetNotice.textContent = error.message;
  }
}

async function verifyResetOtp() {
  els.resetNotice.textContent = "Verifying OTP...";
  try {
    const result = await api("/api/verify-reset-otp", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        employeeId: els.resetEmployeeId.value.trim(),
        email: els.resetEmail.value.trim(),
        otp: els.resetOtp.value.trim(),
      }),
    });
    els.resetNotice.textContent = result.message || "OTP verified.";
  } catch (error) {
    els.resetNotice.textContent = error.message;
  }
}

async function resetPassword() {
  els.resetNotice.textContent = "Saving new password...";
  try {
    const result = await api("/api/reset-password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        employeeId: els.resetEmployeeId.value.trim(),
        email: els.resetEmail.value.trim(),
        otp: els.resetOtp.value.trim(),
        newPassword: els.resetNewPassword.value,
        confirmPassword: els.resetConfirmPassword.value,
      }),
    });
    els.resetOtp.value = "";
    els.resetNewPassword.value = "";
    els.resetConfirmPassword.value = "";
    els.resetNotice.textContent = result.message || "Password reset successfully. You can log in now.";
  } catch (error) {
    els.resetNotice.textContent = error.message;
  }
}

function togglePassword(inputId, button) {
  const input = document.getElementById(inputId);
  if (!input) return;
  input.type = input.type === "password" ? "text" : "password";
  button.classList.toggle("is-visible", input.type === "text");
}

function applyFilters() {
  const employeeMatch = employeeChoiceFromPicker();
  state.selectedEmployeeId = employeeMatch?.employeeId || "";
  state.searchTerm = els.searchInput.value.trim();
  state.startDate = els.startDateInput.value;
  state.endDate = els.endDateInput.value;
  refreshDashboard().catch((error) => {
    els.kpiNotice.textContent = error.message;
  });
}

function resetFilters() {
  state.selectedEmployeeId = "";
  state.searchTerm = "";
  state.startDate = "";
  state.endDate = "";
  state.selectedPeriod = "";
  state.selectedQuarter = "";
  els.employeePickerInput.value = "";
  els.searchInput.value = "";
  els.startDateInput.value = "";
  els.endDateInput.value = "";
  refreshDashboard().catch((error) => {
    els.kpiNotice.textContent = error.message;
  });
}

function bindEvents() {
  document.querySelectorAll(".icon-btn").forEach((button) => {
    button.innerHTML = EYE_ICON;
  });

  els.loginForm.addEventListener("submit", login);
  els.logoutBtn.addEventListener("click", logout);
  els.toggleLoginPassword.addEventListener("click", () => togglePassword("loginPassword", els.toggleLoginPassword));
  els.requestOtpBtn.addEventListener("click", requestResetOtp);
  els.verifyOtpBtn.addEventListener("click", verifyResetOtp);
  els.resetPasswordBtn.addEventListener("click", resetPassword);
  document.querySelectorAll(".toggle-password").forEach((button) => {
    button.addEventListener("click", () => togglePassword(button.dataset.target, button));
  });

  els.employeePickerInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      applyFilters();
    }
  });
  els.searchInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      applyFilters();
    }
  });
  els.downloadEmployeePickerInput.addEventListener("input", updateDownloadLinks);
  [
    els.employeeProjectIncentiveInput,
    els.employeeDepartmentPercentInput,
    els.employeeTeamSharePercentInput,
    els.employeeNpsInput,
  ].forEach((input) => {
    input.addEventListener("input", renderFormulaPreview);
  });
  els.applyFiltersBtn.addEventListener("click", applyFilters);
  els.resetFiltersBtn.addEventListener("click", resetFilters);
  els.periodSelect.addEventListener("change", () => {
    state.selectedPeriod = els.periodSelect.value;
    state.selectedQuarter = quarterForPeriod(state.selectedPeriod);
    refreshDashboard().catch((error) => {
      els.kpiNotice.textContent = error.message;
    });
  });
  els.projectMonthSelect.addEventListener("change", () => {
    state.selectedPeriod = els.projectMonthSelect.value;
    state.selectedQuarter = quarterForPeriod(state.selectedPeriod);
    refreshDashboard().catch((error) => {
      els.kpiNotice.textContent = error.message;
    });
  });

  els.quarterTabs.addEventListener("click", (event) => {
    const button = event.target.closest(".quarter-tab");
    if (!button) return;
    state.selectedQuarter = button.dataset.quarter;
    renderQuarterTrend();
  });

  els.kpiTableBody.addEventListener("click", (event) => {
    if (event.target.classList.contains("save-kpi-btn")) {
      saveKpi(event);
    }
  });
  els.projectTableBody.addEventListener("click", (event) => {
    if (event.target.classList.contains("save-project-btn")) {
      saveProject(event);
    }
  });

  els.saveStatusBtn.addEventListener("click", saveDisbursalStatus);
  els.saveEmployeeBtn.addEventListener("click", saveEmployee);
  els.deleteEmployeeBtn.addEventListener("click", deleteEmployee);
  els.undoEmployeeBtn.addEventListener("click", undoDeleteEmployee);
  els.changePasswordBtn.addEventListener("click", updatePassword);

  document.querySelectorAll(".upload-trigger").forEach((button) => {
    button.addEventListener("click", () => uploadWorkbook(button.dataset.uploadType, button.dataset.inputId));
  });

  els.uploadHistory.addEventListener("click", (event) => {
    const button = event.target.closest(".delete-upload-btn");
    if (!button) return;
    deleteUpload(button.dataset.fileId);
  });
}

async function bootstrap() {
  bindEvents();
  try {
    await refreshDashboard();
    setLoggedIn(true);
  } catch (error) {
    setLoggedIn(false);
    els.loginNotice.textContent = "Use your employee ID and password to continue.";
  }
}

bootstrap();
