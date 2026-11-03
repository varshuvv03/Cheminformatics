// ============================================================================
// Cheminformatics Virtual Laboratory Client Application (Non-Streamlit)
// Developed by Varshini A & Vismitha Parasa — SRMIST Trichy
// ============================================================================

const DEFAULT_SMILES = "CC(=O)OC1=CC=CC=C1C(=O)O"; // Aspirin

// Application State
const state = {
  currentPage: "home",
  studentName: localStorage.getItem("studentName") || "Varshini A & Vismitha Parasa",
  regNo: localStorage.getItem("regNo") || "RA2611030050040 / RA2611030050047",
  currentSmiles: localStorage.getItem("currentSmiles") || DEFAULT_SMILES,
  molSource: "example",
  mol3dCache: {},
  theory3dLoaded: false,
};

// DOM ready initialization
document.addEventListener("DOMContentLoaded", () => {
  initSidebar();
  initNavigation();
  initPages();
  syncInputs();
  loadCurrentMolecule();
});

// Initialize Sidebar
function initSidebar() {
  const sidebar = document.getElementById("app-sidebar");
  const toggleButton = document.getElementById("sidebar-toggle");
  const toggleLabel = document.getElementById("sidebar-toggle-label");
  const closeButton = document.getElementById("sidebar-close");
  const backdrop = document.getElementById("sidebar-backdrop");
  const mobileViewport = window.matchMedia("(max-width: 900px)");

  const setSidebarOpen = (open) => {
    document.body.classList.toggle("sidebar-open", open && mobileViewport.matches);
    document.body.classList.toggle("sidebar-collapsed", !open && !mobileViewport.matches);
    sidebar.inert = !open;
    sidebar.setAttribute("aria-hidden", String(!open));
    toggleButton.setAttribute("aria-expanded", String(open));
    toggleLabel.textContent = open ? "Close panel" : "Open panel";
    backdrop.hidden = !(open && mobileViewport.matches);
  };

  setSidebarOpen(!mobileViewport.matches);
  toggleButton.addEventListener("click", () => {
    setSidebarOpen(toggleButton.getAttribute("aria-expanded") !== "true");
  });
  closeButton.addEventListener("click", () => setSidebarOpen(false));
  backdrop.addEventListener("click", () => setSidebarOpen(false));
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && toggleButton.getAttribute("aria-expanded") === "true") {
      setSidebarOpen(false);
      toggleButton.focus();
    }
  });
  mobileViewport.addEventListener("change", (event) => setSidebarOpen(!event.matches));

  const nameInput = document.getElementById("sidebar-name");
  const regInput = document.getElementById("sidebar-reg");
  const molSelect = document.getElementById("sidebar-example-select");
  const customSmilesInput = document.getElementById("sidebar-custom-smiles");
  const smilesCode = document.getElementById("sidebar-smiles-code");

  nameInput.value = state.studentName;
  regInput.value = state.regNo;
  customSmilesInput.value = state.currentSmiles;
  smilesCode.innerText = state.currentSmiles;

  nameInput.addEventListener("input", (e) => {
    state.studentName = e.target.value;
    localStorage.setItem("studentName", state.studentName);
    const finalName = document.getElementById("final-name");
    if (finalName) finalName.value = state.studentName;
  });

  regInput.addEventListener("input", (e) => {
    state.regNo = e.target.value;
    localStorage.setItem("regNo", state.regNo);
    const finalReg = document.getElementById("final-reg");
    if (finalReg) finalReg.value = state.regNo;
  });

  // Toggle input method (Select Example vs Enter SMILES)
  const btnExample = document.getElementById("btn-source-example");
  const btnCustom = document.getElementById("btn-source-custom");
  const groupExample = document.getElementById("group-source-example");
  const groupCustom = document.getElementById("group-source-custom");

  btnExample.addEventListener("click", () => {
    btnExample.classList.add("active");
    btnCustom.classList.remove("active");
    groupExample.style.display = "block";
    groupCustom.style.display = "none";
    state.molSource = "example";
    updateSmiles(molSelect.value);
  });

  btnCustom.addEventListener("click", () => {
    btnCustom.classList.add("active");
    btnExample.classList.remove("active");
    groupExample.style.display = "none";
    groupCustom.style.display = "block";
    state.molSource = "custom";
    updateSmiles(customSmilesInput.value);
  });

  molSelect.addEventListener("change", (e) => {
    updateSmiles(e.target.value);
  });

  customSmilesInput.addEventListener("input", (e) => {
    updateSmiles(e.target.value);
  });
}

function updateSmiles(smiles) {
  state.currentSmiles = (smiles || "").trim();
  localStorage.setItem("currentSmiles", state.currentSmiles);
  document.getElementById("sidebar-smiles-code").innerText = state.currentSmiles;
  loadCurrentMolecule();
}

function selectMolecule(smiles, name = "") {
  updateSmiles(smiles);
  const selectElem = document.getElementById("sidebar-example-select");
  if (selectElem) {
    for (let opt of selectElem.options) {
      if (opt.value === smiles) {
        selectElem.value = smiles;
        break;
      }
    }
  }
  const customInput = document.getElementById("sidebar-custom-smiles");
  if (customInput) customInput.value = smiles;

  showPage("visualization");
  window.scrollTo({ top: 0, behavior: "smooth" });
}
window.selectMolecule = selectMolecule;

// Navigation between 8 pages
function initNavigation() {
  const navItems = document.querySelectorAll(".nav-radio-item");
  navItems.forEach((item) => {
    item.addEventListener("click", () => {
      const pageKey = item.dataset.page;
      showPage(pageKey);
    });
  });
}

function showPage(pageKey) {
  state.currentPage = pageKey;
  if (window.matchMedia("(max-width: 900px)").matches) {
    document.getElementById("sidebar-close").click();
  }

  // Update navigation highlighting
  document.querySelectorAll(".nav-radio-item").forEach((item) => {
    if (item.dataset.page === pageKey) {
      item.classList.add("active");
    } else {
      item.classList.remove("active");
    }
  });

  // Update page visibility
  document.querySelectorAll(".page-view").forEach((view) => {
    if (view.id === `page-${pageKey}`) {
      view.style.display = "block";
    } else {
      view.style.display = "none";
    }
  });

  // Trigger page-specific loaders
  if (pageKey === "theory") {
    const activeTab = document.querySelector("#theory-tabs .tab-btn.active");
    if (activeTab && activeTab.dataset.pane === "theory-pane-models") {
      setTimeout(() => loadTheory3DModels(), 50);
    }
  } else if (pageKey === "visualization") {
    loadVisualizationPage();
  } else if (pageKey === "properties") {
    loadPropertiesPage();
  } else if (pageKey === "advanced") {
    loadAdvancedTools();
  } else if (pageKey === "final-report") {
    syncFinalReportInputs();
  }
}

function syncInputs() {
  const finalName = document.getElementById("final-name");
  const finalReg = document.getElementById("final-reg");
  if (finalName) finalName.value = state.studentName;
  if (finalReg) finalReg.value = state.regNo;
}

function syncFinalReportInputs() {
  syncInputs();
}

// Triggered when SMILES changes
function loadCurrentMolecule() {
  if (state.currentPage === "visualization") {
    loadVisualizationPage();
  } else if (state.currentPage === "properties") {
    loadPropertiesPage();
  } else if (state.currentPage === "advanced") {
    loadAdvancedTools();
  }
}

// ============================================================================
// 3D MOLECULAR VIEWER (3Dmol.js)
// ============================================================================
function render3DModel(containerId, molBlock, style, showSurface) {
  const container = document.getElementById(containerId);
  if (!container) return;
  container.innerHTML = "";
  container.style.position = "relative";
  container.style.overflow = "hidden";

  if (!molBlock) {
    container.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#888;">Generating 3D Coordinates...</div>';
    return;
  }

  try {
    const config = { backgroundColor: "white" };
    const viewer = $3Dmol.createViewer(container, config);
    viewer.addModel(molBlock, "mol");

    if (style === "stick") {
      viewer.setStyle({ stick: { radius: 0.15 } });
    } else if (style === "ball_and_stick") {
      viewer.setStyle({ stick: { radius: 0.1 }, sphere: { scale: 0.25 } });
    } else if (style === "space_filling") {
      viewer.setStyle({ sphere: { scale: 1.0 } });
    } else if (style === "wireframe") {
      viewer.setStyle({ line: { linewidth: 2 } });
    } else {
      viewer.setStyle({ stick: {} });
    }

    if (showSurface) {
      viewer.addSurface($3Dmol.SurfaceType.VDW, { opacity: 0.7, color: "lightblue" });
    }

    viewer.zoomTo();
    viewer.render();
  } catch (err) {
    console.error("3Dmol render error:", err);
    container.innerHTML = `<div style="padding:20px;color:red;">Error rendering 3D model: ${err.message}</div>`;
  }
}

async function fetchMol3DBlock(smiles) {
  if (state.mol3dCache[smiles]) {
    return state.mol3dCache[smiles];
  }
  try {
    const res = await fetch("/api/mol3d", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ smiles }),
    });
    const data = await res.json();
    if (data.success && data.mol_block) {
      state.mol3dCache[smiles] = data.mol_block;
      return data.mol_block;
    }
    return null;
  } catch (e) {
    console.error("fetchMol3DBlock error:", e);
    return null;
  }
}

// ============================================================================
// PAGE: THEORY
// ============================================================================
function initPages() {
  initTheoryTabs();
  initVisualizationControls();
  initPropertiesControls();
  initComparisonPage();
  initAdvancedTabs();
  initQuizPage();
  initFinalReportPage();
}

function initTheoryTabs() {
  const tabs = document.querySelectorAll("#theory-tabs .tab-btn");
  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      const targetPane = tab.dataset.pane;
      document.querySelectorAll("#theory-tabs-content .tab-pane").forEach((p) => {
        if (p.id === targetPane) {
          p.classList.add("active");
        } else {
          p.classList.remove("active");
        }
      });
      if (targetPane === "theory-pane-models") {
        setTimeout(() => loadTheory3DModels(), 50);
      }
    });
  });
}

async function loadTheory3DModels() {
  const aspirinSmiles = "CC(=O)OC1=CC=CC=C1C(=O)O";
  let molBlock = await fetchMol3DBlock(aspirinSmiles);
  if (!molBlock && state.currentSmiles) {
    molBlock = await fetchMol3DBlock(state.currentSmiles);
  }
  if (molBlock) {
    setTimeout(() => {
      render3DModel("theory-3d-ball-stick", molBlock, "ball_and_stick", false);
      render3DModel("theory-3d-stick", molBlock, "stick", false);
      render3DModel("theory-3d-space-filling", molBlock, "space_filling", false);
      render3DModel("theory-3d-wireframe", molBlock, "wireframe", false);
    }, 60);
  }
}

// ============================================================================
// PAGE: MOLECULAR VISUALIZATION
// ============================================================================
function initVisualizationControls() {
  const styleSelect = document.getElementById("viz-3d-style");
  const surfaceCheck = document.getElementById("viz-surface-check");

  styleSelect.addEventListener("change", () => updateViz3D());
  surfaceCheck.addEventListener("change", () => updateViz3D());
}

async function loadVisualizationPage() {
  const smiles = state.currentSmiles;
  const validBanner = document.getElementById("viz-valid-banner");
  const img2d = document.getElementById("viz-2d-img");
  const infoTbody = document.getElementById("viz-info-tbody");

  if (!smiles) {
    validBanner.className = "warning-box";
    validBanner.innerHTML = "⚠️ Please enter a valid SMILES string in the sidebar.";
    img2d.src = "";
    infoTbody.innerHTML = "";
    return;
  }

  // Validate and get info
  try {
    const res = await fetch("/api/validate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ smiles }),
    });
    const data = await res.json();
    if (!data.valid) {
      validBanner.className = "warning-box";
      validBanner.innerHTML = `⚠️ Invalid SMILES string: <code>${escapeHtml(smiles)}</code>`;
      img2d.src = "";
      infoTbody.innerHTML = "";
      document.getElementById("viz-3d-container").innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#888;">Invalid molecule</div>';
      return;
    }

    validBanner.className = "success-box";
    validBanner.innerHTML = `✅ Valid SMILES: <code>${escapeHtml(smiles)}</code>`;

    // 2D Image
    img2d.src = `/api/mol2d?smiles=${encodeURIComponent(smiles)}&w=450&h=450`;

    // Info Table
    infoTbody.innerHTML = `
      <tr><td><b>Molecular Formula</b></td><td>${data.formula}</td></tr>
      <tr><td><b>Number of Atoms (non-H)</b></td><td>${data.heavy_atoms}</td></tr>
      <tr><td><b>Number of Bonds</b></td><td>${data.bonds}</td></tr>
      <tr><td><b>σ (Sigma) Bonds</b></td><td>${data.sigma_bonds}</td></tr>
      <tr><td><b>π (Pi) Bonds</b></td><td>${data.pi_bonds}</td></tr>
      <tr><td><b>Aromatic Rings</b></td><td>${data.aromatic_rings}</td></tr>
      <tr><td><b>Total Rings</b></td><td>${data.total_rings}</td></tr>
    `;

    updateViz3D();
  } catch (e) {
    console.error("loadVisualizationPage error:", e);
  }
}

async function updateViz3D() {
  const smiles = state.currentSmiles;
  const styleSelect = document.getElementById("viz-3d-style");
  const surfaceCheck = document.getElementById("viz-surface-check");
  const style = styleSelect.value;
  const showSurface = surfaceCheck.checked;

  const molBlock = await fetchMol3DBlock(smiles);
  render3DModel("viz-3d-container", molBlock, style, showSurface);
}

// ============================================================================
// PAGE: MOLECULAR PROPERTIES REPORT
// ============================================================================
function initPropertiesControls() {
  const styleSelect = document.getElementById("prop-3d-style");
  const surfaceCheck = document.getElementById("prop-surface-check");
  const staticBtn = document.getElementById("prop-gen-static-btn");

  styleSelect.addEventListener("change", () => updateProp3D());
  surfaceCheck.addEventListener("change", () => updateProp3D());

  staticBtn.addEventListener("click", () => {
    const smiles = state.currentSmiles;
    const style = styleSelect.value;
    const staticImgContainer = document.getElementById("prop-static-img-container");
    staticImgContainer.style.display = "block";
    staticImgContainer.innerHTML = `
      <div style="margin-top:14px; text-align:center;">
        <p style="font-weight:600; margin-bottom:8px; color:#1b4d32;">3D Molecular Model (Static Matplotlib Render)</p>
        <img src="/api/mol3d_static?smiles=${encodeURIComponent(smiles)}&style=${style}&t=${Date.now()}" style="max-width:450px; border:1px solid #d1e7dd; border-radius:6px; box-shadow:0 2px 6px rgba(0,0,0,0.06);" />
      </div>
    `;
  });

  // CSV download button
  document.getElementById("prop-csv-btn").addEventListener("click", () => {
    downloadPropertiesCSV();
  });

  // Single PDF download button
  document.getElementById("prop-pdf-btn").addEventListener("click", () => {
    downloadSinglePDF();
  });
}

async function loadPropertiesPage() {
  const smiles = state.currentSmiles;
  const banner = document.getElementById("prop-banner");
  const img2d = document.getElementById("prop-2d-img");

  if (!smiles) {
    banner.className = "warning-box";
    banner.innerHTML = "⚠️ Please enter a valid SMILES string in the sidebar.";
    return;
  }

  try {
    const res = await fetch("/api/properties", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ smiles }),
    });
    const data = await res.json();
    if (!data.success) {
      banner.className = "warning-box";
      banner.innerHTML = `⚠️ Invalid SMILES string: <code>${escapeHtml(smiles)}</code>`;
      return;
    }

    banner.className = "success-box";
    banner.innerHTML = `✅ Analyzing: <code>${escapeHtml(smiles)}</code>`;

    img2d.src = `/api/mol2d?smiles=${encodeURIComponent(smiles)}&w=350&h=350`;

    const props = data.properties;

    // Basic Info table
    document.getElementById("prop-basic-tbody").innerHTML = `
      <tr><td><b>Molecular Formula</b></td><td>${props["Molecular Formula"]}</td></tr>
      <tr><td><b>Molecular Weight</b></td><td>${props["Molecular Weight (g/mol)"]} g/mol</td></tr>
      <tr><td><b>Exact Mass</b></td><td>${props["Exact Mass"]}</td></tr>
      <tr><td><b>SMILES</b></td><td><code>${escapeHtml(smiles)}</code></td></tr>
      <tr><td><b>Heavy Atoms</b></td><td>${props["Number of Heavy Atoms"]}</td></tr>
      <tr><td><b>Formal Charge</b></td><td>${props["Formal Charge"]}</td></tr>
    `;

    // 6 Key metrics
    document.getElementById("prop-metric-logp").innerText = props["LogP"];
    document.getElementById("prop-metric-tpsa").innerText = props["TPSA (Å²)"];
    document.getElementById("prop-metric-hbd").innerText = props["H-Bond Donors"];
    document.getElementById("prop-metric-hba").innerText = props["H-Bond Acceptors"];
    document.getElementById("prop-metric-rb").innerText = props["Rotatable Bonds"];
    document.getElementById("prop-metric-ar").innerText = props["Aromatic Rings"];

    // Complete 21 Descriptors Table
    let tableHtml = "";
    for (const [propName, propVal] of Object.entries(props)) {
      tableHtml += `<tr><td><b>${escapeHtml(propName)}</b></td><td>${escapeHtml(String(propVal))}</td></tr>`;
    }
    document.getElementById("prop-full-tbody").innerHTML = tableHtml;

    updateProp3D();
  } catch (e) {
    console.error("loadPropertiesPage error:", e);
  }
}

async function updateProp3D() {
  const smiles = state.currentSmiles;
  const style = document.getElementById("prop-3d-style").value;
  const showSurface = document.getElementById("prop-surface-check").checked;
  const molBlock = await fetchMol3DBlock(smiles);
  render3DModel("prop-3d-container", molBlock, style, showSurface);
}

async function downloadPropertiesCSV() {
  const smiles = state.currentSmiles;
  const res = await fetch("/api/properties_csv", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ smiles }),
  });
  if (res.ok) {
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `molecular_properties_${smiles.slice(0, 15)}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  }
}

async function downloadSinglePDF() {
  const smiles = state.currentSmiles;
  const style = document.getElementById("prop-3d-style").value;
  const btn = document.getElementById("prop-pdf-btn");
  btn.innerText = "⏳ Generating PDF...";
  btn.disabled = true;

  try {
    const res = await fetch("/api/single_pdf", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        student_name: state.studentName,
        reg_no: state.regNo,
        smiles: smiles,
        style_3d: style,
      }),
    });
    if (res.ok) {
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `molecular_report_${smiles.slice(0, 15).replace(/\//g, "_")}.pdf`;
      a.click();
      window.URL.revokeObjectURL(url);
    }
  } finally {
    btn.innerText = "📄 Generate Molecular PDF Report";
    btn.disabled = false;
  }
}

// ============================================================================
// PAGE: STRUCTURE-PROPERTY ANALYSIS
// ============================================================================
let comparisonBarChart = null;
let comparisonScatterChart = null;
let lastComparisonData = [];

function initComparisonPage() {
  const analyzeBtn = document.getElementById("compare-analyze-btn");
  const chartPropSelect = document.getElementById("compare-chart-prop");
  const csvBtn = document.getElementById("compare-csv-btn");

  analyzeBtn.addEventListener("click", () => runComparison());
  chartPropSelect.addEventListener("change", () => renderComparisonBarChart());
  csvBtn.addEventListener("click", () => downloadComparisonCSV());
}

async function runComparison() {
  const input = document.getElementById("compare-input").value;
  const resultsArea = document.getElementById("compare-results-area");
  const invalidBox = document.getElementById("compare-invalid-box");

  const res = await fetch("/api/compare", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ input_text: input }),
  });
  const data = await res.json();
  const molecules = data.molecules || [];

  if (data.invalid_lines && data.invalid_lines.length > 0) {
    invalidBox.style.display = "block";
    invalidBox.innerHTML = `⚠️ Invalid SMILES skipped:<br/>` + data.invalid_lines.map(escapeHtml).join("<br/>");
  } else {
    invalidBox.style.display = "none";
  }

  if (molecules.length < 2) {
    resultsArea.style.display = "none";
    alert("Please enter at least 2 valid molecules to compare.");
    return;
  }

  resultsArea.style.display = "block";
  lastComparisonData = molecules;

  // Render Comparison Table
  let tbodyHtml = "";
  molecules.forEach((m) => {
    tbodyHtml += `
      <tr>
        <td><b>${escapeHtml(m.name)}</b></td>
        <td><code>${escapeHtml(m.smiles)}</code></td>
        <td>${m.mw}</td>
        <td>${m.logp}</td>
        <td>${m.tpsa}</td>
        <td>${m.hbd}</td>
        <td>${m.hba}</td>
        <td>${m.rotatable_bonds}</td>
        <td>${m.aromatic_rings}</td>
        <td>${m.heavy_atoms}</td>
        <td>${m.fraction_csp3}</td>
        <td>${m.molar_refractivity}</td>
        <td>${m.lipinski_violations === 0 ? "0 (Pass)" : m.lipinski_violations + " Viol."}</td>
      </tr>
    `;
  });
  document.getElementById("compare-table-tbody").innerHTML = tbodyHtml;

  // Render Charts
  renderComparisonBarChart();
  renderComparisonScatterChart(molecules);

  // Render Lipinski Violations Cards
  let lipCardsHtml = "";
  molecules.forEach((m) => {
    const v = m.lipinski_violations;
    if (v === 0) {
      lipCardsHtml += `<div class="success-box" style="margin:6px 0;">✅ <b>${escapeHtml(m.name)}</b>: 0 violations — Drug-like</div>`;
    } else if (v === 1) {
      lipCardsHtml += `<div class="warning-box" style="margin:6px 0;">⚠️ <b>${escapeHtml(m.name)}</b>: 1 violation — Borderline</div>`;
    } else {
      lipCardsHtml += `<div class="info-box" style="margin:6px 0; border-left-color:#e11d48; background:#fff1f2;">❌ <b>${escapeHtml(m.name)}</b>: ${v} violations — Poor oral bioavailability predicted</div>`;
    }
  });
  document.getElementById("compare-lipinski-cards").innerHTML = lipCardsHtml;
}

function renderComparisonBarChart() {
  const prop = document.getElementById("compare-chart-prop").value;
  const propMap = {
    "MW (g/mol)": "mw",
    "LogP": "logp",
    "TPSA (Å²)": "tpsa",
    "HBD": "hbd",
    "HBA": "hba",
    "Rotatable Bonds": "rotatable_bonds",
    "Molar Refractivity": "molar_refractivity",
  };
  const key = propMap[prop] || "mw";

  const labels = lastComparisonData.map((m) => m.name);
  const values = lastComparisonData.map((m) => m[key]);

  const ctx = document.getElementById("compare-bar-chart").getContext("2d");
  if (comparisonBarChart) comparisonBarChart.destroy();

  comparisonBarChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        {
          label: prop,
          data: values,
          backgroundColor: "#2e8b57",
          borderColor: "#1b4d32",
          borderWidth: 1,
          borderRadius: 4,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        title: { display: true, text: `Comparison: ${prop}`, color: "#1b4d32", font: { size: 14, weight: "bold" } },
      },
      scales: {
        y: { beginAtZero: key !== "logp" },
      },
    },
  });
}

function renderComparisonScatterChart(molecules) {
  const ctx = document.getElementById("compare-scatter-chart").getContext("2d");
  if (comparisonScatterChart) comparisonScatterChart.destroy();

  const points = molecules.map((m) => ({ x: m.mw, y: m.logp, name: m.name }));

  comparisonScatterChart = new Chart(ctx, {
    type: "scatter",
    data: {
      datasets: [
        {
          label: "Molecules",
          data: points,
          backgroundColor: "#2e8b57",
          borderColor: "#1b4d32",
          borderWidth: 1.5,
          pointRadius: 8,
          pointHoverRadius: 10,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        title: { display: true, text: "MW vs LogP (Lipinski Chemical Space)", color: "#1b4d32", font: { size: 14, weight: "bold" } },
        tooltip: {
          callbacks: {
            label: function (ctx) {
              const p = ctx.raw;
              return `${p.name}: MW=${p.x}, LogP=${p.y}`;
            },
          },
        },
      },
      scales: {
        x: {
          title: { display: true, text: "Molecular Weight (g/mol)" },
          suggestedMax: 600,
        },
        y: {
          title: { display: true, text: "LogP (Lipophilicity)" },
          suggestedMax: 7,
        },
      },
    },
  });
}

async function downloadComparisonCSV() {
  if (!lastComparisonData.length) return;
  const res = await fetch("/api/compare_csv", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ molecules: lastComparisonData }),
  });
  if (res.ok) {
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "molecule_comparison.csv";
    a.click();
    window.URL.revokeObjectURL(url);
  }
}

// ============================================================================
// PAGE: ADVANCED & INNOVATIVE TOOLS
// ============================================================================
function initAdvancedTabs() {
  const tabs = document.querySelectorAll("#advanced-tabs .tab-btn");
  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      const targetPane = tab.dataset.pane;
      document.querySelectorAll("#advanced-tabs-content .tab-pane").forEach((p) => {
        if (p.id === targetPane) {
          p.classList.add("active");
        } else {
          p.classList.remove("active");
        }
      });
    });
  });

  document.getElementById("tan-calc-btn").addEventListener("click", () => {
    runSimilarityCalculator();
  });
}

async function loadAdvancedTools() {
  const smilesA = state.currentSmiles;
  const smilesB = document.getElementById("tan-smi-b").value || "CC(=O)NC1=CC=C(O)C=C1";
  document.getElementById("tan-smi-a").value = smilesA;

  try {
    const res = await fetch("/api/advanced", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ smiles_a: smilesA, smiles_b: smilesB }),
    });
    const data = await res.json();

    if (!data.mol_a_valid) {
      document.getElementById("adv-hash-target").innerText = "Invalid molecule";
      return;
    }

    // Hashes
    const h = data.hashes;
    document.getElementById("adv-hash-target").innerText = smilesA;
    document.getElementById("adv-hash-canonical").innerText = h.canonical_smiles;
    document.getElementById("adv-hash-sha256").innerText = h.sha256;
    document.getElementById("adv-hash-sha3").innerText = h.sha3_256;
    document.getElementById("adv-hash-md5").innerText = h.md5;
    document.getElementById("adv-hash-inchikey").innerText = h.inchikey;
    document.getElementById("adv-hash-inchi").innerText = h.inchi;

    // QED
    const q = data.qed;
    document.getElementById("adv-qed-score").innerText = q.score.toFixed(3);
    document.getElementById("adv-qed-progress").style.width = `${Math.min(Math.max(q.score * 100, 0), 100)}%`;

    const qedEval = document.getElementById("adv-qed-eval");
    if (q.score >= 0.67) {
      qedEval.className = "success-box";
      qedEval.innerHTML = "🌟 Highly Attractive Drug Candidate (QED ≥ 0.67)";
    } else if (q.score >= 0.49) {
      qedEval.className = "info-box";
      qedEval.innerHTML = "👍 Moderate Drug-Likeness (0.49 ≤ QED < 0.67)";
    } else {
      qedEval.className = "warning-box";
      qedEval.innerHTML = "⚠️ Low Drug-Likeness (QED < 0.49)";
    }

    document.getElementById("adv-qed-tbody").innerHTML = `
      <tr><td>MW</td><td>${q.mw}</td></tr>
      <tr><td>LogP</td><td>${q.logp}</td></tr>
      <tr><td>H-Bond Donors</td><td>${q.hbd}</td></tr>
      <tr><td>H-Bond Acceptors</td><td>${q.hba}</td></tr>
      <tr><td>TPSA (Å²)</td><td>${q.tpsa}</td></tr>
      <tr><td>Rotatable Bonds</td><td>${q.rotatable_bonds}</td></tr>
      <tr><td>Aromatic Rings</td><td>${q.aromatic_rings}</td></tr>
      <tr><td>Structural Alerts</td><td>${q.alerts}</td></tr>
    `;

    // Scaffold
    document.getElementById("adv-scaff-orig-img").src = `/api/mol2d?smiles=${encodeURIComponent(smilesA)}&w=300&h=250`;
    document.getElementById("adv-scaff-orig-smi").innerText = `SMILES: ${smilesA}`;

    const scaffImg = document.getElementById("adv-scaff-img");
    const scaffBanner = document.getElementById("adv-scaff-banner");
    if (data.scaffold.has_scaffold) {
      scaffImg.src = `/api/mol2d?smiles=${encodeURIComponent(data.scaffold.scaffold_smiles)}&w=300&h=250`;
      scaffImg.style.display = "block";
      scaffBanner.className = "success-box";
      scaffBanner.innerHTML = `<b>Murcko SMILES:</b> <code>${escapeHtml(data.scaffold.scaffold_smiles)}</code>`;
    } else {
      scaffImg.style.display = "none";
      scaffBanner.className = "info-box";
      scaffBanner.innerHTML = "This molecule is acyclic (contains no rings), so it has no cyclic Murcko core.";
    }

    // Similarity
    updateSimilarityView(data);
  } catch (e) {
    console.error("loadAdvancedTools error:", e);
  }
}

async function runSimilarityCalculator() {
  const smilesA = document.getElementById("tan-smi-a").value;
  const smilesB = document.getElementById("tan-smi-b").value;

  const res = await fetch("/api/advanced", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ smiles_a: smilesA, smiles_b: smilesB }),
  });
  const data = await res.json();
  updateSimilarityView(data);
}

function updateSimilarityView(data) {
  const smiA = document.getElementById("tan-smi-a").value;
  const smiB = document.getElementById("tan-smi-b").value;

  if (!data.mol_a_valid || !data.mol_b_valid || !data.similarity) {
    alert("Please provide valid SMILES for both molecules.");
    return;
  }

  const s = data.similarity;
  document.getElementById("tan-metric-tanimoto").innerText = s.tanimoto.toFixed(4);
  document.getElementById("tan-metric-dice").innerText = s.dice.toFixed(4);
  document.getElementById("tan-metric-cosine").innerText = s.cosine.toFixed(4);

  document.getElementById("tan-img-a").src = `/api/mol2d?smiles=${encodeURIComponent(smiA)}&w=280&h=200`;
  document.getElementById("tan-img-b").src = `/api/mol2d?smiles=${encodeURIComponent(smiB)}&w=280&h=200`;

  const interpBox = document.getElementById("tan-interpretation");
  if (s.tanimoto >= 0.85) {
    interpBox.className = "success-box";
    interpBox.innerHTML = "🎯 <b>High Structural Congruence</b> (Tanimoto ≥ 0.85) — High probability of similar biological target affinity.";
  } else if (s.tanimoto >= 0.50) {
    interpBox.className = "info-box";
    interpBox.innerHTML = "⚖️ <b>Moderate Similarity</b> (0.50 ≤ Tanimoto < 0.85) — Related scaffold or functional groups.";
  } else {
    interpBox.className = "warning-box";
    interpBox.innerHTML = "🔍 <b>Divergent Scaffolds</b> (Tanimoto < 0.50) — Distinct chemotypes.";
  }
}

// ============================================================================
// PAGE: ASSESSMENT (24 QUESTIONS) & STUDENT AUTHENTICATION GATE
// ============================================================================
let quizStudent = JSON.parse(localStorage.getItem("quizStudent") || "null");

function initQuizPage() {
  checkQuizAuth();
  const submitBtn = document.getElementById("quiz-submit-btn");
  if (submitBtn) {
    submitBtn.addEventListener("click", () => submitQuiz());
  }
}

function checkQuizAuth() {
  const authGate = document.getElementById("quiz-auth-gate");
  const verifiedBanner = document.getElementById("quiz-verified-banner");
  const quizForm = document.getElementById("quiz-form");

  if (!authGate || !quizForm) return;

  if (quizStudent && quizStudent.name) {
    authGate.style.display = "none";
    if (verifiedBanner) {
      verifiedBanner.style.display = "flex";
      const nameEl = document.getElementById("quiz-verified-name");
      const emailEl = document.getElementById("quiz-verified-email");
      const regEl = document.getElementById("quiz-verified-reg");
      if (nameEl) nameEl.innerText = quizStudent.name;
      if (emailEl) emailEl.innerText = quizStudent.email || "Google Account";
      if (regEl) regEl.innerText = quizStudent.reg || "N/A";
    }
    quizForm.style.display = "block";
  } else {
    authGate.style.display = "block";
    if (verifiedBanner) verifiedBanner.style.display = "none";
    quizForm.style.display = "none";
  }
}

function handleGoogleSignIn() {
  const defaultEmail = "student@gmail.com";
  const googleEmail = prompt("Sign in with Google - Enter your Google Account email:", defaultEmail);
  if (!googleEmail || !googleEmail.trim()) return;

  let googleName = googleEmail.split("@")[0].replace(/[._]/g, " ").replace(/\b\w/g, (l) => l.toUpperCase());
  const regPrompt = prompt("Enter your Student Registration Number:", "RA2611030050040");

  quizStudent = {
    name: googleName || "Verified Student",
    email: googleEmail.trim(),
    reg: regPrompt ? regPrompt.trim() : "RA2611030050040",
    authProvider: "Google",
    signedInAt: new Date().toISOString(),
  };

  localStorage.setItem("quizStudent", JSON.stringify(quizStudent));

  const sNameInput = document.getElementById("sidebar-student-name");
  const sRegInput = document.getElementById("sidebar-reg-no");
  if (sNameInput) sNameInput.value = quizStudent.name;
  if (sRegInput && quizStudent.reg) sRegInput.value = quizStudent.reg;

  checkQuizAuth();
}

function handleManualSignUp() {
  const nameInput = document.getElementById("quiz-auth-name");
  const emailInput = document.getElementById("quiz-auth-email");
  const regInput = document.getElementById("quiz-auth-reg");

  const name = nameInput ? nameInput.value.trim() : "";
  const email = emailInput ? emailInput.value.trim() : "";
  const reg = regInput ? regInput.value.trim() : "";

  if (!name) {
    alert("Please enter your Student Full Name.");
    return;
  }
  if (!email || !email.includes("@")) {
    alert("Please enter a valid Student Email Address.");
    return;
  }

  quizStudent = {
    name: name,
    email: email,
    reg: reg || "N/A",
    authProvider: "Email",
    signedInAt: new Date().toISOString(),
  };

  localStorage.setItem("quizStudent", JSON.stringify(quizStudent));

  const sNameInput = document.getElementById("sidebar-student-name");
  const sRegInput = document.getElementById("sidebar-reg-no");
  if (sNameInput) sNameInput.value = quizStudent.name;
  if (sRegInput && quizStudent.reg) sRegInput.value = quizStudent.reg;

  checkQuizAuth();
}

function signOutQuizUser() {
  if (confirm("Sign out of current student account?")) {
    quizStudent = null;
    localStorage.removeItem("quizStudent");
    checkQuizAuth();
  }
}

async function submitQuiz() {
  if (!quizStudent || !quizStudent.name) {
    alert("Please sign up or sign in with Google before submitting your test.");
    checkQuizAuth();
    return;
  }

  const submitBtn = document.getElementById("quiz-submit-btn");
  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.innerText = "⏳ Grading & Connecting Results...";
  }

  const answers = {};
  for (let i = 0; i < 24; i++) {
    const selected = document.querySelector(`input[name="quiz_q_${i}"]:checked`);
    if (selected) {
      answers[String(i)] = parseInt(selected.value);
    }
  }

  try {
    const res = await fetch("/api/quiz/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        answers,
        student_name: quizStudent.name,
        student_email: quizStudent.email,
        reg_no: quizStudent.reg,
      }),
    });
    const data = await res.json();

    const resultsArea = document.getElementById("quiz-results-area");
    resultsArea.style.display = "block";

    document.getElementById("quiz-score-text").innerText = `${data.score}/${data.total} (${data.percentage}%)`;
    document.getElementById("quiz-progress-bar").style.width = `${data.percentage}%`;

    const feedbackBox = document.getElementById("quiz-feedback-box");
    const pct = data.percentage;
    if (pct >= 80) {
      feedbackBox.className = "success-box";
      feedbackBox.innerHTML = `🎉 <b>Excellent!</b> ${data.feedback || "You have a strong understanding of cheminformatics concepts!"}`;
    } else if (pct >= 60) {
      feedbackBox.className = "info-box";
      feedbackBox.innerHTML = `👍 <b>Good job!</b> ${data.feedback || "Review the topics you missed to strengthen your knowledge."}`;
    } else if (pct >= 40) {
      feedbackBox.className = "warning-box";
      feedbackBox.innerHTML = `📚 <b>Fair performance.</b> ${data.feedback || "Please revisit the Theory section for better understanding."}`;
    } else {
      feedbackBox.className = "info-box";
      feedbackBox.style.borderLeftColor = "#e11d48";
      feedbackBox.style.backgroundColor = "#fff1f2";
      feedbackBox.innerHTML = `📖 <b>Needs improvement.</b> ${data.feedback || "We recommend going through the Theory section carefully."}`;
    }

    const emailStatusBanner = document.getElementById("quiz-email-status-banner");
    if (emailStatusBanner) {
      emailStatusBanner.style.display = "block";
      if (data.email_sent) {
        emailStatusBanner.className = "success-box";
        emailStatusBanner.innerHTML = `✉️ <b>Results Sent:</b> Your assessment report has been emailed directly to instructor <b>${data.instructor_email || "ss.ravibharathi@gmail.com"}</b>.`;
      } else {
        emailStatusBanner.className = "info-box";
        emailStatusBanner.innerHTML = `📋 <b>Connected to Instructor:</b> Results logged & linked to instructor <b>${data.instructor_email || "ss.ravibharathi@gmail.com"}</b> (${data.email_status || "Recorded"}).`;
      }
    }

    const missedContainer = document.getElementById("quiz-missed-list");
    if (data.wrong && data.wrong.length > 0) {
      document.getElementById("quiz-missed-header").style.display = "block";
      missedContainer.innerHTML = data.wrong
        .map(
          (w) => `
          <div class="missed-question-box">
            <b>❌ Q${w.index}. ${escapeHtml(w.question)}</b><br/>
            <span style="color:#64748b;">Your Answer:</span> ${escapeHtml(w.your_answer)}<br/>
            <span style="color:#1b4d32; font-weight:600;">Correct Answer:</span> ✅ ${escapeHtml(w.correct_answer)}
          </div>
        `
        )
        .join("");
    } else {
      document.getElementById("quiz-missed-header").style.display = "none";
      missedContainer.innerHTML = "";
    }

    resultsArea.scrollIntoView({ behavior: "smooth" });
  } catch (err) {
    console.error("Quiz submission error:", err);
    alert("An error occurred while submitting the quiz. Please try again.");
  } finally {
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.innerText = "📝 Submit Quiz";
    }
  }
}

// ============================================================================
// PAGE: FINAL STUDENT REPORT (10-PAGE PDF)
// ============================================================================
function initFinalReportPage() {
  const genBtn = document.getElementById("final-pdf-btn");
  genBtn.addEventListener("click", () => generateFinalPDFReport());
}

async function generateFinalPDFReport() {
  const sName = document.getElementById("final-name").value.trim();
  const sReg = document.getElementById("final-reg").value.trim();
  const smilesText = document.getElementById("final-smiles").value.trim();
  const style3d = document.getElementById("final-3d-style").value;
  const statusMsg = document.getElementById("final-pdf-status");
  const genBtn = document.getElementById("final-pdf-btn");

  if (!sName || !sReg) {
    alert("Please enter both Student Name and Registration Number.");
    return;
  }
  if (!smilesText) {
    alert("Please enter at least one SMILES string.");
    return;
  }

  genBtn.disabled = true;
  genBtn.innerText = "⏳ Building 10-Page Laboratory Report...";
  statusMsg.style.display = "block";
  statusMsg.className = "info-box";
  statusMsg.innerHTML = "⏳ Processing 7 molecular conformers and compiling full 10-page institutional report...";

  try {
    const res = await fetch("/api/final_pdf", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        student_name: sName,
        reg_no: sReg,
        smiles_text: smilesText,
        style_3d: style3d,
      }),
    });

    if (!res.ok) {
      const err = await res.text();
      statusMsg.className = "warning-box";
      statusMsg.innerHTML = `⚠️ Failed to build PDF: ${escapeHtml(err)}`;
      return;
    }

    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `Student_Report_${sReg.replace(/[\/\s\\]/g, "_")}.pdf`;
    a.click();
    window.URL.revokeObjectURL(url);

    statusMsg.className = "success-box";
    statusMsg.innerHTML = "✅ Combined 10-Page Student Molecular Analysis Report generated and downloaded successfully!";
  } catch (err) {
    console.error("PDF generation error:", err);
    statusMsg.className = "warning-box";
    statusMsg.innerHTML = `⚠️ Error generating report: ${err.message}`;
  } finally {
    genBtn.disabled = false;
    genBtn.innerText = "📄 Generate Combined PDF Report";
  }
}

// Helper: Escape HTML
function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

