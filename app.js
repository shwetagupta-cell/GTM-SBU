const elements = {
  authShell: document.querySelector("#authShell"),
  appShell: document.querySelector("#appShell"),
  loginForm: document.querySelector("#loginForm"),
  loginType: document.querySelector("#loginType"),
  loginEmployeeId: document.querySelector("#loginEmployeeId"),
  loginPassword: document.querySelector("#loginPassword"),
  toggleLoginPasswordBtn: document.querySelector("#toggleLoginPasswordBtn"),
  loginNotice: document.querySelector("#loginNotice"),
  authGreetingTitle: document.querySelector("#authGreetingTitle"),
  authGreetingCopy: document.querySelector("#authGreetingCopy"),
  openResetModalBtn: document.querySelector("#openResetModalBtn"),
  resetPasswordForm: document.querySelector("#resetPasswordForm"),
  resetEmployeeId: document.querySelector("#resetEmployeeId"),
  resetEmail: document.querySelector("#resetEmail"),
  resetOtp: document.querySelector("#resetOtp"),
  resetNewPassword: document.querySelector("#resetNewPassword"),
  resetConfirmPassword: document.querySelector("#resetConfirmPassword"),
  toggleResetPasswordBtn: document.querySelector("#toggleResetPasswordBtn"),
  toggleResetConfirmPasswordBtn: document.querySelector("#toggleResetConfirmPasswordBtn"),
  resetNotice: document.querySelector("#resetNotice"),
  requestOtpBtn: document.querySelector("#requestOtpBtn"),
  resendOtpBtn: document.querySelector("#resendOtpBtn"),
  verifyOtpBtn: document.querySelector("#verifyOtpBtn"),
  resetModal: document.querySelector("#resetModal"),
  closeResetModalBtn: document.querySelector("#closeResetModalBtn"),
  sessionUser: document.querySelector("#sessionUser"),
  sessionMeta: document.querySelector("#sessionMeta"),
  dashboardTitle: document.querySelector("#dashboardTitle"),
  dashboardSubtitle: document.querySelector("#dashboardSubtitle"),
  welcomeHeadline: document.querySelector("#welcomeHeadline"),
  welcomeSubline: document.querySelector("#welcomeSubline"),
  logoutBtn: document.querySelector("#logoutBtn"),
  monthSelect: document.querySelector("#monthSelect"),
  employeeSwitch: document.querySelector("#employeeSwitch"),
  searchInput: document.querySelector("#searchInput"),
  adminEmployeeSearchShell: document.querySelector("#adminEmployeeSearchShell"),
  adminEmployeeSearchBtn: document.querySelector("#adminEmployeeSearchBtn"),
  adminEmployeeClearBtn: document.querySelector("#adminEmployeeClearBtn"),
  refreshDashboardBtn: document.querySelector("#refreshDashboardBtn"),
  selectedMonthLabel: document.querySelector("#selectedMonthLabel"),
  selectedMonthNote: document.querySelector("#selectedMonthNote"),
  monthCfValue: document.querySelector("#monthCfValue"),
  monthShareValue: document.querySelector("#monthShareValue"),
  futureValueValue: document.querySelector("#futureValueValue"),
  profileGrid: document.querySelector("#profileGrid"),
  projectCards: document.querySelector("#projectCards"),
  projectNotice: document.querySelector("#projectNotice"),
  rankingList: document.querySelector("#rankingList"),
  rankingNotice: document.querySelector("#rankingNotice"),
  incentiveStatusFilter: document.querySelector("#incentiveStatusFilter"),
  quarterFilter: document.querySelector("#quarterFilter"),
  yearFilter: document.querySelector("#yearFilter"),
  incentiveTableBody: document.querySelector("#incentiveTableBody"),
  adminPanel: document.querySelector("#adminPanel"),
  adminNavLink: document.querySelector("#adminNavLink"),
  adminEmployeeSearch: document.querySelector("#adminEmployeeSearch"),
  searchPageMeta: document.querySelector("#searchPageMeta"),
  datasetStatusList: document.querySelector("#datasetStatusList"),
  datasetUploadForm: document.querySelector("#datasetUploadForm"),
  uploadDatasetsBtn: document.querySelector("#uploadDatasetsBtn"),
  deleteDatasetsBtn: document.querySelector("#deleteDatasetsBtn"),
  reloadDatasetsBtn: document.querySelector("#reloadDatasetsBtn"),
  uploadNotice: document.querySelector("#uploadNotice"),
  passwordForm: document.querySelector("#passwordForm"),
  currentPassword: document.querySelector("#currentPassword"),
  newPassword: document.querySelector("#newPassword"),
  confirmPassword: document.querySelector("#confirmPassword"),
  changePasswordBtn: document.querySelector("#changePasswordBtn"),
  passwordNotice: document.querySelector("#passwordNotice"),
  projectDetailModal: document.querySelector("#projectDetailModal"),
  detailProjectName: document.querySelector("#detailProjectName"),
  projectDetailGrid: document.querySelector("#projectDetailGrid"),
  closeDetailModalBtn: document.querySelector("#closeDetailModalBtn"),
  confirmModal: document.querySelector("#confirmModal"),
  confirmMessage: document.querySelector("#confirmMessage"),
  confirmDeleteBtn: document.querySelector("#confirmDeleteBtn"),
  cancelDeleteBtn: document.querySelector("#cancelDeleteBtn"),
  loadingOverlay: document.querySelector("#loadingOverlay"),
  loadingLabel: document.querySelector("#loadingLabel"),
  toastStack: document.querySelector("#toastStack"),
};

const state = {
  dashboard: null,
  selectedMonth: "",
  selectedEmployeeId: "",
  searchTerm: "",
  incentiveStatus: "all",
  quarterFilter: "all",
  yearFilter: "all",
  adminSearch: "",
  adminSearchResults: null,
  confirmAction: null,
};

function money(value) {
  return `₹${Number(value || 0).toLocaleString("en-IN", {
    maximumFractionDigits: 2,
    minimumFractionDigits: Number(value || 0) % 1 ? 2 : 0,
  })}`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function setLoading(isLoading, label = "Loading...") {
  elements.loadingLabel.textContent = label;
  elements.loadingOverlay.classList.toggle("hidden", !isLoading);
}

function showToast(message, tone = "info") {
  const toast = document.createElement("article");
  toast.className = `toast toast--${tone}`;
  toast.textContent = message;
  elements.toastStack.appendChild(toast);
  requestAnimationFrame(() => toast.classList.add("toast--visible"));
  setTimeout(() => {
    toast.classList.remove("toast--visible");
    setTimeout(() => toast.remove(), 250);
  }, 3200);
}

function greetingPrefix() {
  const hour = new Date().getHours();
  if (hour >= 5 && hour < 12) {
    return "Good Morning";
  }
  if (hour >= 12 && hour < 17) {
    return "Good Afternoon";
  }
  if (hour >= 17 && hour < 22) {
    return "Good Evening";
  }
  return "Welcome Back";
}

function renderAuthGreeting() {
  const prefix = greetingPrefix();
  elements.authGreetingTitle.textContent = prefix;
  elements.authGreetingCopy.textContent = "Sign in to review your latest incentives, mapped projects, and performance updates.";
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    credentials: "same-origin",
    ...options,
  });
  const contentType = response.headers.get("Content-Type") || "";
  const data = contentType.includes("application/json") ? await response.json().catch(() => ({})) : {};
  if (!response.ok) {
    throw new Error(data.error || "Request failed");
  }
  return data;
}

function currentEmployee() {
  return state.dashboard?.viewedEmployee || null;
}

function currentMonthData() {
  const employee = currentEmployee();
  return employee?.months?.[state.selectedMonth] || null;
}

function setLoggedIn(loggedIn) {
  elements.authShell.classList.toggle("hidden", loggedIn);
  elements.appShell.classList.toggle("hidden", !loggedIn);
}

function togglePassword(input, button) {
  const isHidden = input.type === "password";
  input.type = isHidden ? "text" : "password";
  button.setAttribute("aria-label", isHidden ? "Hide password" : "Show password");
  button.classList.toggle("password-toggle--active", isHidden);
}

function renderSession() {
  const viewer = state.dashboard?.viewer;
  const employee = currentEmployee();
  if (!viewer || !employee) {
    return;
  }
  elements.sessionUser.textContent = viewer.name;
  const mode = viewer.isAdmin ? "Admin login" : viewer.isTeamHead ? "Team head login" : "Employee login";
  elements.sessionMeta.textContent = `${viewer.designation || "Employee"} | ${mode}`;
  elements.dashboardTitle.textContent =
    employee.employeeId === viewer.employeeId ? `${employee.name}'s dashboard` : `${employee.name} dashboard`;
  elements.dashboardSubtitle.textContent = employee.teamHeadName
    ? `Reports to ${employee.teamHeadName}. Dynamic data from the latest uploaded Excel sheets.`
    : "Dynamic data from the latest uploaded Excel sheets.";
  elements.welcomeHeadline.textContent = `${greetingPrefix()}, ${viewer.name}`;
  elements.welcomeSubline.textContent = "Hope you have a productive day!";
}

function renderMonthSelect() {
  const employee = currentEmployee();
  const monthOrder = employee?.monthOrder || [];
  elements.monthSelect.innerHTML = monthOrder.length
    ? monthOrder.map((month) => `<option value="${escapeHtml(month)}">${escapeHtml(month)}</option>`).join("")
    : `<option value="">No month available</option>`;
  state.selectedMonth = monthOrder.includes(state.selectedMonth)
    ? state.selectedMonth
    : employee?.latestMonth || monthOrder[0] || "";
  elements.monthSelect.value = state.selectedMonth;
}

function renderEmployeeSwitch() {
  const accessible = state.dashboard?.accessibleEmployees || [];
  const searchResults = state.dashboard?.viewer?.isAdmin && state.adminSearchResults?.items?.length
    ? state.adminSearchResults.items
    : accessible;
  elements.employeeSwitch.innerHTML = searchResults.length
    ? searchResults
        .map(
          (employee) =>
            `<option value="${escapeHtml(employee.employeeId)}">${escapeHtml(employee.name)}${employee.department ? ` · ${escapeHtml(employee.department)}` : ""}</option>`
        )
        .join("")
    : `<option value="">No employee available</option>`;
  elements.employeeSwitch.value = currentEmployee()?.employeeId || "";
}

function renderHero() {
  const employee = currentEmployee();
  const monthData = currentMonthData();
  const futureValue = Number(monthData?.futureTotal || 0);
  elements.selectedMonthLabel.textContent = state.selectedMonth || "No month";
  elements.selectedMonthNote.textContent = employee?.projectCount
    ? `${employee.projectCount} mapped projects with CF greater than zero`
    : "Upload data to see month totals";
  elements.monthCfValue.textContent = money(monthData?.totalCf || 0);
  elements.monthShareValue.textContent = money(monthData?.totalShare || 0);
  elements.futureValueValue.textContent = money(futureValue);
}

function renderProfile() {
  const employee = currentEmployee();
  if (!employee) {
    elements.profileGrid.innerHTML = "";
    return;
  }
  const rows = [
    ["Employee ID", employee.employeeId],
    ["Name", employee.name],
    ["Designation", employee.designation || "Not available"],
    ["Location", employee.location || "Not available"],
    ["Team Head", employee.teamHeadName || "Self / head level"],
    ["Access", employee.isTeamHead ? "Can view own + team dashboards" : "Own dashboard only"],
  ];
  elements.profileGrid.innerHTML = rows
    .map(
      ([label, value]) =>
        `<article class="summary-card"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></article>`
    )
    .join("");
}

function filteredEntries() {
  const monthData = currentMonthData();
  const entries = monthData?.entries || [];
  const term = state.searchTerm.trim().toLowerCase();
  if (!term) {
    return entries;
  }
  return entries.filter((entry) => entry.projectName.toLowerCase().includes(term));
}

function renderProjects() {
  const employee = currentEmployee();
  const entries = filteredEntries();
  if (!employee?.monthOrder?.length) {
    elements.projectCards.innerHTML = "";
    elements.projectNotice.textContent = `${employee?.name || "This employee"} does not currently have project-wise incentive rows for the selected workbook set.`;
    return;
  }
  if (!entries.length) {
    elements.projectCards.innerHTML = `<article class="empty-state">No mapped projects with CF greater than zero matched this search for ${escapeHtml(state.selectedMonth)}.</article>`;
    elements.projectNotice.textContent = "Try a different search or choose another month.";
    return;
  }
  elements.projectCards.innerHTML = entries
    .map(
      (entry) => `
      <button class="project-card" type="button" data-project-id="${escapeHtml(entry.projectId)}">
        <div>
          <strong>${escapeHtml(entry.projectName)}</strong>
          <p>${escapeHtml(entry.sourcingType || "Mapped project")} | This Month CF ${money(entry.thisMonthCf)} | Future Value Secured ${money(entry.futureValueSecured)}</p>
        </div>
        <div class="project-card__side">
          <span class="chip">${escapeHtml(state.selectedMonth)}</span>
          <strong>${money(entry.yourShare)}</strong>
        </div>
      </button>
    `
    )
    .join("");
  elements.projectNotice.textContent = "Only projects with CF value greater than zero are shown. Click any project row to open the detail view.";
}

function medalClass(index) {
  if (index === 0) return "ranking-card--gold";
  if (index === 1) return "ranking-card--silver";
  if (index === 2) return "ranking-card--bronze";
  return "";
}

function renderRanking() {
  const viewer = state.dashboard?.viewer;
  const accessible = state.dashboard?.accessibleEmployees || [];
  if (!viewer?.isAdmin && !viewer?.isTeamHead) {
    elements.rankingList.innerHTML = "";
    elements.rankingNotice.textContent = "Only team heads and admins can see team ranking and switch dashboards.";
    return;
  }
  const sorted = [...accessible]
    .map((employee) => ({
      ...employee,
      score: Number(employee.monthTotals?.[state.selectedMonth] || 0),
      incentive: Number(employee.monthTotals?.[state.selectedMonth] || 0),
    }))
    .sort((left, right) => right.score - left.score)
    .slice(0, 5);
  elements.rankingList.innerHTML = sorted.length
    ? sorted
        .map(
          (employee, index) => `
          <article class="ranking-card ${employee.employeeId === currentEmployee()?.employeeId ? "ranking-card--active" : ""} ${medalClass(index)}">
            <div>
              <span class="rank-badge">#${index + 1}</span>
              <strong>${escapeHtml(employee.name)}</strong>
              <p>${escapeHtml(employee.department || employee.designation || "Employee")}</p>
            </div>
            <div class="ranking-card__side">
              <strong class="ranking-card__score">${money(employee.score)}</strong>
              <p>Incentive ${money(employee.incentive)}</p>
            </div>
          </article>
        `
        )
        .join("")
    : `<article class="empty-state">No ranking data is available yet.</article>`;
  elements.rankingNotice.textContent = `Top 5 ranking is based on ${state.selectedMonth || "the selected month"} incentive share.`;
}

function renderQuarterAndYearFilters() {
  const timeline = currentEmployee()?.incentiveTimeline || [];
  const quarters = [...new Set(timeline.map((item) => item.quarter).filter(Boolean))];
  const years = [...new Set(timeline.map((item) => item.year).filter(Boolean))];
  elements.quarterFilter.innerHTML = ['<option value="all">All</option>', ...quarters.map((quarter) => `<option value="${escapeHtml(quarter)}">${escapeHtml(quarter)}</option>`)].join("");
  elements.yearFilter.innerHTML = ['<option value="all">All</option>', ...years.map((year) => `<option value="${escapeHtml(year)}">${escapeHtml(year)}</option>`)].join("");
  elements.quarterFilter.value = quarters.includes(state.quarterFilter) ? state.quarterFilter : "all";
  elements.yearFilter.value = years.includes(state.yearFilter) ? state.yearFilter : "all";
}

function filteredTimeline() {
  const timeline = currentEmployee()?.incentiveTimeline || [];
  return timeline.filter((item) => {
    if (state.incentiveStatus !== "all" && item.incentiveStatus !== state.incentiveStatus) {
      return false;
    }
    if (state.quarterFilter !== "all" && item.quarter !== state.quarterFilter) {
      return false;
    }
    if (state.yearFilter !== "all" && item.year !== state.yearFilter) {
      return false;
    }
    return true;
  });
}

function timelineRowClass(status) {
  if (status === "Past") return "incentive-row--past";
  if (status === "Future") return "incentive-row--future";
  return "incentive-row--current";
}

function renderIncentiveTable() {
  renderQuarterAndYearFilters();
  const timeline = filteredTimeline();
  elements.incentiveTableBody.innerHTML = timeline.length
    ? timeline
        .map(
          (item) => `
          <tr class="${timelineRowClass(item.incentiveStatus)}">
            <td>${escapeHtml(item.month)}</td>
            <td>${money(item.incentiveEarned)}</td>
            <td>${escapeHtml(item.incentiveStatus)}</td>
            <td>${money(item.futureProjection)}</td>
            <td>${escapeHtml(item.remarks)}</td>
          </tr>
        `
        )
        .join("")
    : `<tr><td colspan="5">No incentive rows matched the selected filters.</td></tr>`;
}

function renderAdminSearchMeta() {
  if (!state.dashboard?.viewer?.isAdmin) {
    elements.searchPageMeta.textContent = "";
    return;
  }
  const meta = state.adminSearchResults;
  if (!state.adminSearch) {
    elements.searchPageMeta.textContent = "Showing full employee list";
    return;
  }
  if (!meta) {
    elements.searchPageMeta.textContent = "No search result loaded";
    return;
  }
  elements.searchPageMeta.textContent = `${meta.total} matching employee${meta.total === 1 ? "" : "s"}`;
}

function renderAdmin() {
  const adminEnabled = Boolean(state.dashboard?.admin?.enabled);
  elements.adminPanel.classList.toggle("hidden", !adminEnabled);
  elements.adminNavLink.classList.toggle("hidden", !adminEnabled);
  elements.adminEmployeeSearchShell.classList.toggle("hidden", !adminEnabled);
  renderAdminSearchMeta();
  const datasets = state.dashboard?.admin?.datasets || [];
  elements.datasetStatusList.innerHTML = datasets.length
    ? datasets
        .map(
          (dataset) => `
          <article class="dataset-item">
            <div>
              <strong>${escapeHtml(dataset.label)}</strong>
              <p>${escapeHtml(dataset.fileName || "No file uploaded")}</p>
            </div>
            <div class="dataset-meta">
              <span class="chip ${dataset.exists ? "" : "chip--muted"}">${dataset.exists ? "Loaded" : "Missing"}</span>
              <code>${escapeHtml(dataset.path || "-")}</code>
              <div class="inline-actions inline-actions--tight">
                <button class="ghost-btn dataset-delete-btn" type="button" data-dataset-key="${escapeHtml(dataset.key)}" ${dataset.exists ? "" : "disabled"}>Delete</button>
              </div>
            </div>
          </article>
        `
        )
        .join("")
    : `<article class="empty-state">No dataset information available.</article>`;
}

function renderDashboard(dashboard) {
  state.dashboard = dashboard;
  renderSession();
  renderMonthSelect();
  renderEmployeeSwitch();
  renderHero();
  renderProfile();
  renderProjects();
  renderRanking();
  renderIncentiveTable();
  renderAdmin();
  setLoggedIn(true);
}

async function refreshDashboard(employeeId = "", refresh = false) {
  const params = new URLSearchParams();
  if (employeeId) {
    params.set("employeeId", employeeId);
  }
  if (refresh) {
    params.set("refresh", "1");
  }
  const suffix = params.toString() ? `?${params.toString()}` : "";
  const dashboard = await api(`/api/me${suffix}`);
  renderDashboard(dashboard);
}

async function handleLogin(event) {
  event.preventDefault();
  setLoading(true, "Signing in...");
  elements.loginNotice.textContent = "Signing in...";
  try {
    const dashboard = await api("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        loginType: elements.loginType.value,
        employeeId: elements.loginEmployeeId.value.trim(),
        password: elements.loginPassword.value,
      }),
    });
    elements.loginForm.reset();
    renderDashboard(dashboard);
    showToast("Login successful.", "success");
  } catch (error) {
    elements.loginNotice.textContent = error.message;
    showToast(error.message, "error");
  } finally {
    setLoading(false);
  }
}

async function handleLogout() {
  await api("/api/logout", { method: "POST" });
  state.dashboard = null;
  state.selectedMonth = "";
  state.selectedEmployeeId = "";
  state.adminSearchResults = null;
  setLoggedIn(false);
}

async function handleChangePassword() {
  setLoading(true, "Updating password...");
  elements.passwordNotice.textContent = "Updating password...";
  try {
    const response = await api("/api/change-password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        currentPassword: elements.currentPassword.value,
        newPassword: elements.newPassword.value,
        confirmPassword: elements.confirmPassword.value,
      }),
    });
    elements.passwordForm.reset();
    elements.passwordNotice.textContent = response.message || "Password updated successfully.";
    showToast(elements.passwordNotice.textContent, "success");
    await refreshDashboard(currentEmployee()?.employeeId || "");
  } catch (error) {
    elements.passwordNotice.textContent = error.message;
    showToast(error.message, "error");
  } finally {
    setLoading(false);
  }
}

async function handleRequestOtp(isResend = false) {
  setLoading(true, "Sending OTP...");
  elements.resetNotice.textContent = isResend ? "Resending OTP..." : "Sending OTP...";
  try {
    const response = await api("/api/request-reset-otp", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        employeeId: elements.resetEmployeeId.value.trim(),
        email: elements.resetEmail.value.trim(),
      }),
    });
    elements.resetNotice.textContent = response.message || "OTP sent.";
    showToast(elements.resetNotice.textContent, response.delivered ? "success" : "info");
  } catch (error) {
    elements.resetNotice.textContent = error.message;
    showToast(error.message, "error");
  } finally {
    setLoading(false);
  }
}

async function handleVerifyOtp() {
  setLoading(true, "Verifying OTP...");
  elements.resetNotice.textContent = "Verifying OTP...";
  try {
    const response = await api("/api/verify-reset-otp", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        employeeId: elements.resetEmployeeId.value.trim(),
        email: elements.resetEmail.value.trim(),
        otp: elements.resetOtp.value.trim(),
      }),
    });
    elements.resetNotice.textContent = response.message || "OTP verified successfully.";
    showToast(elements.resetNotice.textContent, "success");
  } catch (error) {
    elements.resetNotice.textContent = error.message;
    showToast(error.message, "error");
  } finally {
    setLoading(false);
  }
}

async function handleResetPassword(event) {
  event.preventDefault();
  setLoading(true, "Resetting password...");
  elements.resetNotice.textContent = "Resetting password...";
  try {
    const response = await api("/api/reset-password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        employeeId: elements.resetEmployeeId.value.trim(),
        email: elements.resetEmail.value.trim(),
        otp: elements.resetOtp.value.trim(),
        newPassword: elements.resetNewPassword.value,
        confirmPassword: elements.resetConfirmPassword.value,
      }),
    });
    elements.resetPasswordForm.reset();
    elements.resetNotice.textContent = response.message || "Password reset successfully.";
    showToast(elements.resetNotice.textContent, "success");
    elements.resetModal.close();
  } catch (error) {
    elements.resetNotice.textContent = error.message;
    showToast(error.message, "error");
  } finally {
    setLoading(false);
  }
}

async function handleDatasetUpload() {
  const formData = new FormData(elements.datasetUploadForm);
  let fileCount = 0;
  for (const value of formData.values()) {
    if (value instanceof File && value.size) {
      fileCount += 1;
    }
  }
  if (!fileCount) {
    elements.uploadNotice.textContent = "Choose at least one Excel file before uploading.";
    return;
  }
  setLoading(true, "Uploading files...");
  elements.uploadNotice.textContent = "Uploading and refreshing dashboard data...";
  try {
    const response = await api("/api/admin/upload-datasets", {
      method: "POST",
      body: formData,
    });
    elements.datasetUploadForm.reset();
    elements.uploadNotice.textContent = response.message || "Upload complete.";
    renderDashboard(response.dashboard);
    showToast(elements.uploadNotice.textContent, "success");
  } catch (error) {
    elements.uploadNotice.textContent = error.message;
    showToast(error.message, "error");
  } finally {
    setLoading(false);
  }
}

async function handleDeleteDatasets() {
  openConfirmModal(
    "Are you sure you want to delete all uploaded files and reset the current dashboard data?",
    async () => {
      setLoading(true, "Deleting uploaded files...");
      elements.uploadNotice.textContent = "Clearing current dataset...";
      try {
        const response = await api("/api/admin/delete-datasets", { method: "POST" });
        elements.uploadNotice.textContent = response.message || "Existing data deleted.";
        renderDashboard(response.dashboard);
        showToast(elements.uploadNotice.textContent, "success");
      } catch (error) {
        elements.uploadNotice.textContent = error.message;
        showToast(error.message, "error");
      } finally {
        setLoading(false);
      }
    }
  );
}

async function handleDeleteDataset(datasetKey) {
  openConfirmModal("Are you sure you want to delete this file?", async () => {
    setLoading(true, "Deleting file...");
      try {
        const response = await api("/api/admin/delete-dataset", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ datasetKey }),
        });
        elements.uploadNotice.textContent = response.message || "Selected file deleted.";
        renderDashboard(response.dashboard);
        showToast(elements.uploadNotice.textContent, "success");
      } catch (error) {
        elements.uploadNotice.textContent = error.message;
        showToast(error.message, "error");
      } finally {
        setLoading(false);
      }
  });
}

async function handleReloadDashboard() {
  setLoading(true, "Reloading latest data...");
  try {
    const response = await api("/api/admin/reload-dashboard", { method: "POST" });
    elements.uploadNotice.textContent = response.message || "Dashboard reloaded.";
    renderDashboard(response.dashboard);
    showToast(elements.uploadNotice.textContent, "success");
  } catch (error) {
    elements.uploadNotice.textContent = error.message;
    showToast(error.message, "error");
  } finally {
    setLoading(false);
  }
}

async function handleAdminEmployeeSearch() {
  if (!state.dashboard?.viewer?.isAdmin) {
    return;
  }
  if (!state.adminSearch) {
    clearAdminEmployeeSearch();
    return;
  }
  try {
    const query = new URLSearchParams({
      term: state.adminSearch,
      page: "1",
      perPage: "25",
    });
    const results = await api(`/api/admin/search-employees?${query.toString()}`);
    state.adminSearchResults = results;
    renderEmployeeSwitch();
    renderAdminSearchMeta();
    if (results.items?.length) {
      state.selectedEmployeeId = results.items[0].employeeId;
      await refreshDashboard(state.selectedEmployeeId);
      showToast(`Found ${results.total} matching employees.`, "success");
    } else {
      showToast("No employees matched that search.", "info");
    }
  } catch (error) {
    elements.uploadNotice.textContent = error.message;
    showToast(error.message, "error");
  }
}

function clearAdminEmployeeSearch() {
  state.adminSearch = "";
  state.adminSearchResults = null;
  elements.adminEmployeeSearch.value = "";
  renderEmployeeSwitch();
  renderAdminSearchMeta();
}

async function openProjectDetail(projectId) {
  const employee = currentEmployee();
  if (!employee || !state.selectedMonth) {
    return;
  }
  setLoading(true, "Loading project detail...");
  try {
    const detail = await api(
      `/api/project-detail?employeeId=${encodeURIComponent(employee.employeeId)}&projectId=${encodeURIComponent(projectId)}&month=${encodeURIComponent(state.selectedMonth)}`
    );
    elements.detailProjectName.textContent = detail.projectName;
    elements.projectDetailGrid.innerHTML = [
      { label: "Employee Name", value: detail.employeeName },
      { label: "Project Name", value: detail.projectName },
      { label: "Selected Month", value: detail.month },
      { label: "This Month CF", value: money(detail.thisMonthCf) },
      { label: "Your Share", value: money(detail.yourShare) },
      { label: "Future Value Secured", value: money(detail.futureValueSecured) },
      { label: "Sourcing Type", value: detail.sourcingType || "Not available" },
      {
        label: "Mapped Closure Roles",
        value: (detail.closureRoles || []).join(" | ") || "Not available",
        multiline: true,
        wide: true,
      },
      { label: "YTD Paid", value: money(detail.ytdMeta?.paid || 0) },
      { label: "YTD Remaining", value: money(detail.ytdMeta?.remaining || 0) },
    ]
      .map((item) => {
        const valueClass = item.multiline ? "detail-value detail-value--multiline" : "detail-value";
        const cardClass = item.wide ? "summary-card summary-card--detail summary-card--wide" : "summary-card summary-card--detail";
        return `<article class="${cardClass}"><span>${escapeHtml(item.label)}</span><div class="${valueClass}">${escapeHtml(item.value)}</div></article>`;
      })
      .join("");
    elements.projectDetailModal.showModal();
  } catch (error) {
    elements.projectNotice.textContent = error.message;
    showToast(error.message, "error");
  } finally {
    setLoading(false);
  }
}

async function restoreSession() {
  try {
    const dashboard = await api("/api/me");
    renderDashboard(dashboard);
  } catch {
    setLoggedIn(false);
  }
}

function openConfirmModal(message, callback) {
  state.confirmAction = callback;
  elements.confirmMessage.textContent = message;
  elements.confirmModal.showModal();
}

function bindEvents() {
  renderAuthGreeting();
  elements.loginForm.addEventListener("submit", handleLogin);
  elements.logoutBtn.addEventListener("click", handleLogout);
  elements.openResetModalBtn.addEventListener("click", () => elements.resetModal.showModal());
  elements.closeResetModalBtn.addEventListener("click", () => elements.resetModal.close());
  elements.resetModal.addEventListener("click", (event) => {
    if (event.target === elements.resetModal) {
      elements.resetModal.close();
    }
  });
  elements.requestOtpBtn.addEventListener("click", () => handleRequestOtp(false));
  elements.resendOtpBtn.addEventListener("click", () => handleRequestOtp(true));
  elements.verifyOtpBtn.addEventListener("click", handleVerifyOtp);
  elements.resetPasswordForm.addEventListener("submit", handleResetPassword);
  elements.changePasswordBtn.addEventListener("click", handleChangePassword);
  elements.uploadDatasetsBtn.addEventListener("click", handleDatasetUpload);
  elements.deleteDatasetsBtn.addEventListener("click", handleDeleteDatasets);
  elements.reloadDatasetsBtn.addEventListener("click", handleReloadDashboard);
  elements.refreshDashboardBtn.addEventListener("click", () => refreshDashboard(currentEmployee()?.employeeId || "", true));
  elements.closeDetailModalBtn.addEventListener("click", () => elements.projectDetailModal.close());
  elements.projectDetailModal.addEventListener("click", (event) => {
    if (event.target === elements.projectDetailModal) {
      elements.projectDetailModal.close();
    }
  });
  elements.confirmDeleteBtn.addEventListener("click", async () => {
    elements.confirmModal.close();
    if (state.confirmAction) {
      const action = state.confirmAction;
      state.confirmAction = null;
      await action();
    }
  });
  elements.cancelDeleteBtn.addEventListener("click", () => {
    state.confirmAction = null;
    elements.confirmModal.close();
  });

  elements.toggleLoginPasswordBtn.addEventListener("click", () =>
    togglePassword(elements.loginPassword, elements.toggleLoginPasswordBtn)
  );
  elements.toggleResetPasswordBtn.addEventListener("click", () =>
    togglePassword(elements.resetNewPassword, elements.toggleResetPasswordBtn)
  );
  elements.toggleResetConfirmPasswordBtn.addEventListener("click", () =>
    togglePassword(elements.resetConfirmPassword, elements.toggleResetConfirmPasswordBtn)
  );

  elements.monthSelect.addEventListener("change", (event) => {
    state.selectedMonth = event.target.value;
    renderHero();
    renderProjects();
    renderRanking();
  });

  elements.employeeSwitch.addEventListener("change", async (event) => {
    state.selectedEmployeeId = event.target.value;
    await refreshDashboard(state.selectedEmployeeId);
  });

  elements.searchInput.addEventListener("input", (event) => {
    state.searchTerm = event.target.value;
    renderProjects();
  });

  elements.projectCards.addEventListener("click", (event) => {
    const card = event.target.closest("[data-project-id]");
    if (!card) {
      return;
    }
    openProjectDetail(card.dataset.projectId);
  });

  elements.incentiveStatusFilter.addEventListener("change", (event) => {
    state.incentiveStatus = event.target.value;
    renderIncentiveTable();
  });
  elements.quarterFilter.addEventListener("change", (event) => {
    state.quarterFilter = event.target.value;
    renderIncentiveTable();
  });
  elements.yearFilter.addEventListener("change", (event) => {
    state.yearFilter = event.target.value;
    renderIncentiveTable();
  });

  elements.datasetStatusList.addEventListener("click", (event) => {
    const target = event.target.closest(".dataset-delete-btn");
    if (!target) {
      return;
    }
    handleDeleteDataset(target.dataset.datasetKey);
  });

  elements.adminEmployeeSearchBtn.addEventListener("click", async () => {
    state.adminSearch = elements.adminEmployeeSearch.value.trim();
    await handleAdminEmployeeSearch();
  });
  elements.adminEmployeeClearBtn.addEventListener("click", async () => {
    clearAdminEmployeeSearch();
    await refreshDashboard(currentEmployee()?.employeeId || "");
  });
  elements.adminEmployeeSearch.addEventListener("keydown", async (event) => {
    if (event.key !== "Enter") {
      return;
    }
    event.preventDefault();
    state.adminSearch = elements.adminEmployeeSearch.value.trim();
    await handleAdminEmployeeSearch();
  });
}

bindEvents();
restoreSession();
