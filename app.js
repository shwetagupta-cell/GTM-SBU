const incentiveRules = [
  {
    bucket: "Sourcing",
    role: "Head - Marketing",
    formulaLabel: "20% sourcing bucket x (25% of VT contribution + 25% of DM contribution)",
    calculateShare: ({ vt, dm }) => 0.2 * (0.25 * vt + 0.25 * dm),
  },
  {
    bucket: "Sourcing",
    role: "VT & DM - National Head",
    formulaLabel: "20% sourcing bucket x (20% of VT contribution + 20% of DM contribution)",
    calculateShare: ({ vt, dm }) => 0.2 * (0.2 * vt + 0.2 * dm),
  },
  {
    bucket: "Sourcing",
    role: "VT - Regional Head",
    formulaLabel: "20% sourcing bucket x 55% VT layer x 70%",
    calculateShare: ({ vt }) => 0.2 * 0.55 * vt * 0.7,
  },
  {
    bucket: "Sourcing",
    role: "VT - BD Manager",
    formulaLabel: "20% sourcing bucket x 55% VT layer x 30%",
    calculateShare: ({ vt }) => 0.2 * 0.55 * vt * 0.3,
  },
  {
    bucket: "Sourcing",
    role: "DM - DGM",
    formulaLabel: "20% sourcing bucket x 55% DM layer x 70%",
    calculateShare: ({ dm }) => 0.2 * 0.55 * dm * 0.7,
  },
  {
    bucket: "Sourcing",
    role: "DM - Executive",
    formulaLabel: "20% sourcing bucket x 55% DM layer x 30%",
    calculateShare: ({ dm }) => 0.2 * 0.55 * dm * 0.3,
  },
  {
    bucket: "Sourcing",
    role: "KAM - National Head",
    formulaLabel: "20% sourcing bucket x KAM contribution x 30%",
    calculateShare: ({ kam }) => 0.2 * kam * 0.3,
  },
  {
    bucket: "Sourcing",
    role: "KAM - Regional Head",
    formulaLabel: "20% sourcing bucket x KAM contribution x 45%",
    calculateShare: ({ kam }) => 0.2 * kam * 0.45,
  },
  {
    bucket: "Sourcing",
    role: "KAM - Sourcing Mgr",
    formulaLabel: "20% sourcing bucket x KAM contribution x 25%",
    calculateShare: ({ kam }) => 0.2 * kam * 0.25,
  },
  {
    bucket: "Closing",
    role: "Sales Leadership",
    formulaLabel: "30% closing bucket x 25%",
    calculateShare: () => 0.3 * 0.25,
  },
  {
    bucket: "Closing",
    role: "BDM - Sales",
    formulaLabel: "30% closing bucket x 75% x 73%",
    calculateShare: () => 0.3 * 0.75 * 0.73,
  },
  {
    bucket: "Closing",
    role: "Sales Support Mgr",
    formulaLabel: "30% closing bucket x 75% x 19%",
    calculateShare: () => 0.3 * 0.75 * 0.19,
  },
  {
    bucket: "Closing",
    role: "MEP",
    formulaLabel: "30% closing bucket x 75% x 8%",
    calculateShare: () => 0.3 * 0.75 * 0.08,
  },
  {
    bucket: "Pre Sales Design",
    role: "DGM/AGM Design",
    formulaLabel: "16% design bucket x 20%",
    calculateShare: () => 0.16 * 0.2,
  },
  {
    bucket: "Pre Sales Design",
    role: "Design Manager - Pre Sales",
    formulaLabel: "16% design bucket x 15%",
    calculateShare: () => 0.16 * 0.15,
  },
  {
    bucket: "Pre Sales Design",
    role: "Interior Designer - Pre Sales",
    formulaLabel: "16% design bucket x 10%",
    calculateShare: () => 0.16 * 0.1,
  },
  {
    bucket: "Pre Sales Design",
    role: "3D Artist - Pre Sales",
    formulaLabel: "16% design bucket x 10%",
    calculateShare: () => 0.16 * 0.1,
  },
  {
    bucket: "Pre Sales Design",
    role: "Developer / Modeller",
    formulaLabel: "16% design bucket x 3%",
    calculateShare: () => 0.16 * 0.03,
  },
  {
    bucket: "Pre Sales Design",
    role: "Design Manager - Post Sales",
    formulaLabel: "16% design bucket x 15%",
    calculateShare: () => 0.16 * 0.15,
  },
  {
    bucket: "Pre Sales Design",
    role: "Interior Designer - Post Sales",
    formulaLabel: "16% design bucket x 10%",
    calculateShare: () => 0.16 * 0.1,
  },
  {
    bucket: "Pre Sales Design",
    role: "3D Artist - Post Sales",
    formulaLabel: "16% design bucket x 6%",
    calculateShare: () => 0.16 * 0.06,
  },
  {
    bucket: "Pre Sales Design",
    role: "MEP Designer - Post Sales",
    formulaLabel: "16% design bucket x 6%",
    calculateShare: () => 0.16 * 0.06,
  },
  {
    bucket: "Pre Sales Design",
    role: "QS",
    formulaLabel: "16% design bucket x 5%",
    calculateShare: () => 0.16 * 0.05,
  },
  {
    bucket: "Operations",
    role: "AVP/GM Ops",
    formulaLabel: "34% operations bucket x 26%",
    calculateShare: () => 0.34 * 0.26,
  },
  {
    bucket: "Operations",
    role: "AGM/DGM Ops",
    formulaLabel: "34% operations bucket x 74% x 35%",
    calculateShare: () => 0.34 * 0.74 * 0.35,
  },
  {
    bucket: "Operations",
    role: "Sr Mgr/SPM",
    formulaLabel: "34% operations bucket x 74% x 16%",
    calculateShare: () => 0.34 * 0.74 * 0.16,
  },
  {
    bucket: "Operations",
    role: "PM",
    formulaLabel: "34% operations bucket x 74% x 11%",
    calculateShare: () => 0.34 * 0.74 * 0.11,
  },
  {
    bucket: "Operations",
    role: "Client Delight (Mgr)",
    formulaLabel: "34% operations bucket x 74% x 3%",
    calculateShare: () => 0.34 * 0.74 * 0.03,
  },
  {
    bucket: "Operations",
    role: "Client Delight (MST)",
    formulaLabel: "34% operations bucket x 74% x 3%",
    calculateShare: () => 0.34 * 0.74 * 0.03,
  },
  {
    bucket: "Operations",
    role: "SS/APM",
    formulaLabel: "34% operations bucket x 74% x 9%",
    calculateShare: () => 0.34 * 0.74 * 0.09,
  },
  {
    bucket: "Operations",
    role: "GM - CSC",
    formulaLabel: "34% operations bucket x 74% x 8%",
    calculateShare: () => 0.34 * 0.74 * 0.08,
  },
  {
    bucket: "Operations",
    role: "Cat Mgr",
    formulaLabel: "34% operations bucket x 74% x 8%",
    calculateShare: () => 0.34 * 0.74 * 0.08,
  },
  {
    bucket: "Operations",
    role: "Exec",
    formulaLabel: "34% operations bucket x 74% x 3%",
    calculateShare: () => 0.34 * 0.74 * 0.03,
  },
  {
    bucket: "Operations",
    role: "Procurement Manager",
    formulaLabel: "34% operations bucket x 74% x 4%",
    calculateShare: () => 0.34 * 0.74 * 0.04,
  },
];

const sampleData = {
  employees: [
    {
      name: "Neha Singh",
      actualDesignation: "Senior Vice President - Marketing & PR",
      incentiveRole: "Head - Marketing",
      department: "Marketing and PR",
    },
    {
      name: "Amrit Singh",
      actualDesignation: "Vice President - Marketing and PR",
      incentiveRole: "VT & DM - National Head",
      department: "Business Development",
    },
    {
      name: "Jayesh Patidar",
      actualDesignation: "3D Design Lead",
      incentiveRole: "3D Artist - Pre Sales",
      department: "Design",
    },
    {
      name: "Mohammed Sufiyan Shaikh",
      actualDesignation: "Senior 3D Artist",
      incentiveRole: "3D Artist - Post Sales",
      department: "Design",
    },
    {
      name: "Utsav Nitin Rathod",
      actualDesignation: "Assistant General Manager- Design",
      incentiveRole: "Design Manager - Post Sales",
      department: "Design",
    },
    {
      name: "Syed Humayun",
      actualDesignation: "Project Manager",
      incentiveRole: "PM",
      department: "Operations",
    },
    {
      name: "Akash Behra",
      actualDesignation: "Senior Category Manager",
      incentiveRole: "Cat Mgr",
      department: "Operations",
    },
  ],
  projects: [
    {
      name: "Phi Capital",
      client: "Phi Capital",
      cashflow: 3451000,
      vtPercent: 0,
      dmPercent: 0,
      kamPercent: 100,
      assignedEmployeeIds: [],
    },
    {
      name: "66Degrees",
      client: "66Degrees",
      cashflow: 2987000,
      vtPercent: 0,
      dmPercent: 100,
      kamPercent: 0,
      assignedEmployeeIds: [],
    },
    {
      name: "VentureX",
      client: "VentureX",
      cashflow: 40009000,
      vtPercent: 0,
      dmPercent: 0,
      kamPercent: 100,
      assignedEmployeeIds: [],
    },
  ],
};

const incentiveRoleOptions = incentiveRules.map((rule) => rule.role);

const state = {
  employees: [],
  projects: [],
};

const elements = {
  currencySymbol: document.querySelector("#currencySymbol"),
  monthLabel: document.querySelector("#monthLabel"),
  incentivePercent: document.querySelector("#incentivePercent"),
  rulesNotice: document.querySelector("#rulesNotice"),
  heroCashflow: document.querySelector("#heroCashflow"),
  heroPool: document.querySelector("#heroPool"),
  heroPayout: document.querySelector("#heroPayout"),
  summaryGrid: document.querySelector("#summaryGrid"),
  employeeTableBody: document.querySelector("#employeeTableBody"),
  ruleTableBody: document.querySelector("#ruleTableBody"),
  projectsContainer: document.querySelector("#projectsContainer"),
  resultsTableBody: document.querySelector("#resultsTableBody"),
  addEmployeeBtn: document.querySelector("#addEmployeeBtn"),
  addProjectBtn: document.querySelector("#addProjectBtn"),
  loadSampleBtn: document.querySelector("#loadSampleBtn"),
  exportCsvBtn: document.querySelector("#exportCsvBtn"),
  employeeRowTemplate: document.querySelector("#employeeRowTemplate"),
  projectCardTemplate: document.querySelector("#projectCardTemplate"),
};

function uid() {
  if (globalThis.crypto?.randomUUID) {
    return globalThis.crypto.randomUUID();
  }
  return `id-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function createEmployee(employee = {}) {
  return {
    id: employee.id || uid(),
    name: employee.name || "",
    actualDesignation: employee.actualDesignation || "",
    incentiveRole: employee.incentiveRole || incentiveRoleOptions[0],
    department: employee.department || "",
  };
}

function createProject(project = {}) {
  return {
    id: project.id || uid(),
    name: project.name || "",
    client: project.client || "",
    cashflow: Number(project.cashflow) || 0,
    vtPercent: Number(project.vtPercent) || 0,
    dmPercent: Number(project.dmPercent) || 0,
    kamPercent: Number(project.kamPercent) || 0,
    assignedEmployeeIds: Array.isArray(project.assignedEmployeeIds) ? [...project.assignedEmployeeIds] : [],
  };
}

function currency() {
  return elements.currencySymbol.value.trim() || "₹";
}

function money(value) {
  return `${currency()}${Math.round(Number(value) || 0).toLocaleString("en-IN")}`;
}

function getIncentivePercent() {
  return Math.max(Number(elements.incentivePercent.value) || 0, 0);
}

function normalizedMix(project) {
  const vt = Math.max(Number(project.vtPercent) || 0, 0);
  const dm = Math.max(Number(project.dmPercent) || 0, 0);
  const kam = Math.max(Number(project.kamPercent) || 0, 0);
  const total = vt + dm + kam;
  if (!total) {
    return { vt: 0, dm: 0, kam: 0, totalPercent: 0 };
  }
  return {
    vt: vt / total,
    dm: dm / total,
    kam: kam / total,
    totalPercent: total,
  };
}

function updateRulesNotice() {
  elements.rulesNotice.textContent =
    "Derived from the workbook: Sourcing 20%, Closing 30%, Pre Sales Design 16%, Operations 34%. " +
    "For each project, cashflow x incentive % creates the pool. VT/DM/KAM inputs are normalized per project and " +
    "employees with the same incentive role split that role amount equally.";
}

function calculateResults() {
  const employeeMap = new Map(state.employees.map((employee) => [employee.id, employee]));
  const totals = new Map(
    state.employees.map((employee) => [
      employee.id,
      {
        employee,
        total: 0,
        projectCount: 0,
        breakdown: [],
      },
    ])
  );

  let totalCashflow = 0;
  let totalPool = 0;
  let totalPayout = 0;
  let unallocatedPool = 0;

  state.projects.forEach((project) => {
    const cashflow = Math.max(Number(project.cashflow) || 0, 0);
    const pool = cashflow * (getIncentivePercent() / 100);
    const mix = normalizedMix(project);
    totalCashflow += cashflow;
    totalPool += pool;

    const assigned = project.assignedEmployeeIds.map((id) => employeeMap.get(id)).filter(Boolean);
    const assignedByRole = assigned.reduce((map, employee) => {
      if (!map.has(employee.incentiveRole)) {
        map.set(employee.incentiveRole, []);
      }
      map.get(employee.incentiveRole).push(employee);
      return map;
    }, new Map());

    incentiveRules.forEach((rule) => {
      const rolePool = pool * rule.calculateShare(mix);
      if (!rolePool) {
        return;
      }

      const assignedEmployees = assignedByRole.get(rule.role) || [];
      if (!assignedEmployees.length) {
        unallocatedPool += rolePool;
        return;
      }

      const splitAmount = rolePool / assignedEmployees.length;
      assignedEmployees.forEach((employee) => {
        const entry = totals.get(employee.id);
        entry.total += splitAmount;
        entry.projectCount += 1;
        entry.breakdown.push({
          projectName: project.name || "Untitled project",
          role: rule.role,
          amount: splitAmount,
        });
      });
      totalPayout += rolePool;
    });
  });

  return {
    totalCashflow,
    totalPool,
    totalPayout,
    unallocatedPool,
    employeeResults: Array.from(totals.values())
      .filter((item) => item.total > 0)
      .sort((left, right) => right.total - left.total || left.employee.name.localeCompare(right.employee.name)),
  };
}

function renderEmployees() {
  elements.employeeTableBody.innerHTML = "";

  state.employees.forEach((employee) => {
    const fragment = elements.employeeRowTemplate.content.cloneNode(true);
    const row = fragment.querySelector("tr");

    row.querySelectorAll("input[data-field], select[data-field]").forEach((input) => {
      const field = input.dataset.field;
      if (input.tagName === "SELECT") {
        input.innerHTML = incentiveRoleOptions
          .map(
            (role) => `<option value="${role}" ${employee[field] === role ? "selected" : ""}>${role}</option>`
          )
          .join("");
      } else {
        input.value = employee[field];
      }

      input.addEventListener("input", (event) => {
        const value = event.currentTarget.value;
        state.employees = state.employees.map((current) =>
          current.id === employee.id ? { ...current, [field]: value } : current
        );
        renderAll();
      });

      input.addEventListener("change", (event) => {
        const value = event.currentTarget.value;
        state.employees = state.employees.map((current) =>
          current.id === employee.id ? { ...current, [field]: value } : current
        );
        renderAll();
      });
    });

    row.querySelector("[data-action='remove']").addEventListener("click", () => {
      state.employees = state.employees.filter((current) => current.id !== employee.id);
      state.projects = state.projects.map((project) => ({
        ...project,
        assignedEmployeeIds: project.assignedEmployeeIds.filter((employeeId) => employeeId !== employee.id),
      }));
      renderAll();
    });

    elements.employeeTableBody.appendChild(fragment);
  });
}

function renderRules() {
  elements.ruleTableBody.innerHTML = incentiveRules
    .map(
      (rule) => `
        <tr>
          <td>${rule.bucket}</td>
          <td>${rule.role}</td>
          <td class="formula-text">${rule.formulaLabel}</td>
        </tr>
      `
    )
    .join("");
}

function renderProjects() {
  elements.projectsContainer.innerHTML = "";

  state.projects.forEach((project) => {
    const fragment = elements.projectCardTemplate.content.cloneNode(true);
    const card = fragment.querySelector(".project-card");
    const checkboxArea = card.querySelector('[data-role="employee-checkboxes"]');
    const meta = card.querySelector('[data-role="meta"]');

    card.querySelectorAll("input[data-field]").forEach((input) => {
      const field = input.dataset.field;
      input.value = project[field];
      input.addEventListener("input", (event) => {
        const rawValue = event.currentTarget.value;
        state.projects = state.projects.map((current) =>
          current.id === project.id
            ? { ...current, [field]: event.currentTarget.type === "number" ? Number(rawValue) || 0 : rawValue }
            : current
        );
        renderAll();
      });
    });

    card.querySelector("[data-action='remove-project']").addEventListener("click", () => {
      state.projects = state.projects.filter((current) => current.id !== project.id);
      renderAll();
    });

    const mix = normalizedMix(project);
    const selectedEmployees = state.employees.filter((employee) => project.assignedEmployeeIds.includes(employee.id));
    const countsByRole = selectedEmployees.reduce((map, employee) => {
      map.set(employee.incentiveRole, (map.get(employee.incentiveRole) || 0) + 1);
      return map;
    }, new Map());

    meta.innerHTML = `
      <span class="pill">VT ${Math.round(mix.vt * 100)}%</span>
      <span class="pill">DM ${Math.round(mix.dm * 100)}%</span>
      <span class="pill">KAM ${Math.round(mix.kam * 100)}%</span>
      <span class="pill">Pool ${money((Number(project.cashflow) || 0) * (getIncentivePercent() / 100))}</span>
    `;

    Array.from(countsByRole.entries()).forEach(([role, count]) => {
      meta.innerHTML += ` <span class="pill">${role}: ${count}</span>`;
    });

    state.employees.forEach((employee) => {
      const wrapper = document.createElement("label");
      wrapper.className = "checkbox-item";
      const checked = project.assignedEmployeeIds.includes(employee.id);
      wrapper.innerHTML = `
        <input type="checkbox" ${checked ? "checked" : ""} />
        <span>
          <strong>${employee.name || "Unnamed employee"}</strong><br />
          <span class="muted">${employee.incentiveRole || "No role"}</span>
        </span>
      `;

      wrapper.querySelector("input").addEventListener("change", (event) => {
        const nextIds = new Set(project.assignedEmployeeIds);
        if (event.currentTarget.checked) {
          nextIds.add(employee.id);
        } else {
          nextIds.delete(employee.id);
        }

        state.projects = state.projects.map((current) =>
          current.id === project.id ? { ...current, assignedEmployeeIds: Array.from(nextIds) } : current
        );
        renderAll();
      });

      checkboxArea.appendChild(wrapper);
    });

    if (!state.employees.length) {
      checkboxArea.innerHTML = '<p class="muted">Add employees first, then assign them to projects here.</p>';
    }

    elements.projectsContainer.appendChild(fragment);
  });
}

function renderSummary(result) {
  const cards = [
    ["Month", elements.monthLabel.value.trim() || "Current month"],
    ["Projects", String(state.projects.length)],
    ["Unallocated pool", money(result.unallocatedPool)],
    ["Paid employees", String(result.employeeResults.length)],
  ];

  elements.summaryGrid.innerHTML = cards
    .map(
      ([label, value]) => `
        <article class="summary-card">
          <span>${label}</span>
          <strong>${value}</strong>
        </article>
      `
    )
    .join("");
}

function renderResults(result) {
  if (!result.employeeResults.length) {
    elements.resultsTableBody.innerHTML = `
      <tr>
        <td colspan="5" class="muted">No employee incentive has been generated yet. Add employees, projects, and project assignments.</td>
      </tr>
    `;
    return;
  }

  elements.resultsTableBody.innerHTML = result.employeeResults
    .map(({ employee, total, projectCount, breakdown }) => {
      const breakdownHtml = breakdown
        .map((item) => `${item.projectName} (${item.role}) ${money(item.amount)}`)
        .join("<br />");

      return `
        <tr>
          <td>${employee.name}</td>
          <td>${employee.incentiveRole}</td>
          <td>${projectCount}</td>
          <td class="mono">${money(total)}</td>
          <td>${breakdownHtml}</td>
        </tr>
      `;
    })
    .join("");
}

function renderHero(result) {
  elements.heroCashflow.textContent = money(result.totalCashflow);
  elements.heroPool.textContent = money(result.totalPool);
  elements.heroPayout.textContent = money(result.totalPayout);
}

function renderAll() {
  updateRulesNotice();
  renderEmployees();
  renderRules();
  renderProjects();
  const result = calculateResults();
  renderSummary(result);
  renderResults(result);
  renderHero(result);
}

function loadSampleData() {
  state.employees = sampleData.employees.map((employee) => createEmployee(employee));
  state.projects = sampleData.projects.map((project) => createProject(project));

  if (state.projects[0]) {
    state.projects[0].assignedEmployeeIds = [
      state.employees[2].id,
      state.employees[3].id,
      state.employees[4].id,
    ];
  }
  if (state.projects[1]) {
    state.projects[1].assignedEmployeeIds = [state.employees[0].id, state.employees[5].id];
  }
  if (state.projects[2]) {
    state.projects[2].assignedEmployeeIds = [state.employees[1].id, state.employees[2].id, state.employees[6].id];
  }

  renderAll();
}

function exportCsv() {
  const result = calculateResults();
  const header = ["employee_name", "actual_designation", "incentive_role", "project_count", "total_incentive", "breakdown"];
  const lines = result.employeeResults.map(({ employee, total, projectCount, breakdown }) =>
    [
      employee.name,
      employee.actualDesignation,
      employee.incentiveRole,
      projectCount,
      Math.round(total),
      breakdown.map((item) => `${item.projectName} - ${item.role} - ${Math.round(item.amount)}`).join(" | "),
    ]
      .map((value) => `"${String(value ?? "").replaceAll('"', '""')}"`)
      .join(",")
  );

  const csv = [header.join(","), ...lines].join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "monthly-incentive-results.csv";
  link.click();
  URL.revokeObjectURL(url);
}

elements.addEmployeeBtn.addEventListener("click", () => {
  state.employees.push(createEmployee());
  renderAll();
});

elements.addProjectBtn.addEventListener("click", () => {
  state.projects.push(createProject({ vtPercent: 0, dmPercent: 0, kamPercent: 100 }));
  renderAll();
});

elements.loadSampleBtn.addEventListener("click", loadSampleData);
elements.exportCsvBtn.addEventListener("click", exportCsv);

[elements.currencySymbol, elements.monthLabel, elements.incentivePercent].forEach((input) =>
  input.addEventListener("input", renderAll)
);

loadSampleData();
