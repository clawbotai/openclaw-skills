/**
 * Pension Calculator Controller (Stitch UI Version)
 * Binds the new Tailwind UI to the preserved PensionCalculator logic.
 * Uses 'Hidden DOM' strategy to maintain compatibility with existing logic.
 */

// Global Calculator Instance
let calculator;
let calculationMode = 'vejez';

document.addEventListener('DOMContentLoaded', async () => {
    // 1. Initialize Calculator with Data
    if (typeof window.calculatorData !== 'undefined') {
        calculator = new PensionCalculator(window.calculatorData);
        console.log("Calculator Initialized via data.js");
        updateCurrentSMMLV();
    } else {
        console.error("Critical: duplicate data.js import or missing file.");
    }

    // 2. Set Version Info
    const feVer = document.getElementById('fe-version');
    if (feVer) feVer.innerText = "v3.0 (Stitch UI)";
});

/* ==========================================================================
   VIEW MANAGEMENT
   ========================================================================== */
function switchView(viewName) {
    // Hide all views
    document.getElementById('view-upload').classList.add('hidden-view');
    document.getElementById('view-dashboard').classList.add('hidden-view');

    // Show Target
    document.getElementById(viewName).classList.remove('hidden-view');

    // Scroll to top
    window.scrollTo(0, 0);
}

/* ==========================================================================
   FILE HANDLING & PARSING
   ========================================================================== */
window.importFile = async function (input) {
    if (!input.files || input.files.length === 0) return;
    const file = input.files[0];
    const fileName = file.name.toLowerCase();

    // Show Loading State (Optional: Add spinner overlay here if requested)
    document.getElementById('sys-status').innerText = "Procesando...";
    document.getElementById('sys-status').className = "text-xs text-blue-600 font-bold animate-pulse";

    try {
        if (fileName.endsWith('.pdf')) {
            console.log("Processing PDF...");
            const formData = new FormData();
            formData.append('file', file);

            // Determine API URL (handle local file opening)
            const apiBase = (window.location.protocol === 'file:') ? 'http://127.0.0.1:8080' : '';
            console.log("DEBUG: Using API Base:", apiBase);
            console.log("DEBUG: Fetching...", `${apiBase}/upload_pdf`);

            const response = await fetch(`${apiBase}/upload_pdf`, { method: 'POST', body: formData });
            console.log("DEBUG: Response Received", response.status);

            if (!response.ok) throw new Error("Error del Servidor");

            const result = await response.json();
            if (result.status === 'success') {
                // Immediate feedback
                document.getElementById('sys-status').innerText = "Datos Cargados";

                populateHiddenTable(result.data);
                switchView('view-dashboard');
                setTimeout(() => {
                    try {
                        calculate();
                    } catch (err) {
                        console.error("Calculation Error:", err);
                        alert("Error en el cálculo: " + err.message);
                        document.getElementById('sys-status').innerText = "Error";
                        document.getElementById('sys-status').className = "text-xs text-red-600 font-bold";
                    }
                }, 100);
            } else {
                throw new Error(result.error);
            }
        }
        else if (fileName.endsWith('.xlsx')) {
            // Excel Logic (Client Side)
            const reader = new FileReader();
            reader.onload = function (e) {
                const data = new Uint8Array(e.target.result);
                const workbook = XLSX.read(data, { type: 'array' });
                const json = XLSX.utils.sheet_to_json(workbook.Sheets[workbook.SheetNames[0]], { header: 1 });
                processExcelData(json);
            };
            reader.readAsArrayBuffer(file);
        }
    } catch (e) {
        console.error(e);
        alert("Error: " + e.message);
        document.getElementById('sys-status').innerText = "Error";
        document.getElementById('sys-status').className = "text-xs text-red-600 font-bold";
    }
};

/* ==========================================================================
   DATA POPULATION (Hidden DOM Strategy)
   ========================================================================== */
function populateHiddenTable(data) {
    const container = document.getElementById('input-rows');
    container.innerHTML = ''; // Clear

    data.forEach((row, i) => {
        // Create hidden inputs to store state for calculate()
        const div = document.createElement('div');
        div.className = 'data-row'; // Class used by calculate()

        // Parse Dates
        let start = formatDateForInput(row['Desde']);
        let end = formatDateForInput(row['Hasta']);

        // Mapping
        div.innerHTML = `
            <input class="date-start" value="${start}" type="hidden">
            <input class="date-end" value="${end}" type="hidden">
            <input class="salary" value="${row['Salario'] || 0}" type="hidden">
            <input class="val-sem" value="${row['Semanas'] || 0}" type="hidden">
            <input class="val-lic" value="${row['Lic'] || 0}" type="hidden">
            <input class="val-sim" value="${row['Sim'] || 0}" type="hidden">
            <span class="val-total">${row['Total'] || row['Semanas']}</span>
        `;
        container.appendChild(div);
    });

    // Check Adjustment
    const adjRow = data.find(r => r["Desde"] === '2024-12-31' || r["Total"] % 1 !== 0);
    const adjStatus = document.getElementById('adj-row-status');
    if (adjRow) {
        adjStatus.innerText = "Ajuste Aplicado";
        adjStatus.className = "text-green-600 font-bold";
    } else {
        adjStatus.innerText = "Suma Bruta";
    }
}


function processExcelData(rows) {
    // Simplified Excel Processor for Hidden DOM
    const container = document.getElementById('input-rows');
    container.innerHTML = '';

    let startIdx = 0;
    if (rows.length > 0 && typeof rows[0][0] === 'string' && isNaN(Date.parse(rows[0][0]))) startIdx = 1;

    for (let i = startIdx; i < rows.length; i++) {
        const r = rows[i];
        if (r.length < 3) continue;

        const div = document.createElement('div');
        div.className = 'data-row';
        div.innerHTML = `
            <input class="date-start" value="${parseExcelDate(r[0])}" type="hidden">
            <input class="date-end" value="${parseExcelDate(r[1])}" type="hidden">
            <input class="salary" value="${parseSalary(r[2])}" type="hidden">
            <input class="val-sem" value="${r[3] || 0}" type="hidden">
            <input class="val-lic" value="${r[4] || 0}" type="hidden">
            <input class="val-sim" value="${r[5] || 0}" type="hidden">
            <span class="val-total">${r[6] || 0}</span>
        `;
        container.appendChild(div);
    }

    switchView('view-dashboard');
    setTimeout(calculate, 100);
}

/* ==========================================================================
   CORE CALCULATION TRIGGER
   ========================================================================== */
/* ==========================================================================
   CORE CALCULATION TRIGGER
   ========================================================================== */
function calculate() {
    if (typeof calculator === 'undefined' || !calculator) {
        alert("Error crítico: Lógica de cálculo no cargada (calculator.js).");
        document.getElementById('sys-status').innerText = "Error de Carga";
        document.getElementById('sys-status').className = "text-xs text-red-600 font-bold";
        return;
    }

    // 1. Scrape Hidden DOM & Find Max Date
    const rows = document.querySelectorAll('.data-row');
    let history = [];
    let maxDateTimestamp = 0;

    rows.forEach(r => {
        const start = r.querySelector('.date-start').value;
        const end = r.querySelector('.date-end').value;
        const salary = parseFloat(r.querySelector('.salary').value) || 0;
        const sem = parseFloat(r.querySelector('.val-sem').value) || 0;
        const total = parseFloat(r.querySelector('.val-total').innerText) || 0;

        if (start && end) {
            // Track latest date for Liquidation Date
            // 'end' is YYYY-MM-DD
            // We treat the liquidation date as the very last day of contribution
            const endObj = new Date(end); // UTC/Local parsing caveat, but consistent within app
            // Fix timezone offset issue manually to be safe or just use timestamp comparison
            // Since inputs are YYYY-MM-DD, new Date() is usually UTC, but let's just compare strings or timestamps
            if (endObj.getTime() > maxDateTimestamp) {
                maxDateTimestamp = endObj.getTime();
            }

            history.push({
                start, end, salary,
                semanas: sem,
                lic: parseFloat(r.querySelector('.val-lic').value) || 0,
                sim: parseFloat(r.querySelector('.val-sim').value) || 0,
                total: total
            });
        }
    });

    if (history.length === 0) {
        alert("No se encontraron datos válidos para calcular.");
        return;
    }

    // Auto-determined Liquidation Date (Final Date of Person)
    // If invalid for some reason, default to today
    let liquidationDate = new Date();
    if (maxDateTimestamp > 0) {
        // Add one day to ensure full coverage? No, usually it's the date of withdrawal.
        // But for IPC indexation we need the month.
        // Let's use the date exactly as parsed (assuming timezone consistency).
        // To be safe against "previous day" bugs, we'll construct it from the YYYY-MM-DD string of the max entry if we tracked it,
        // but timestamp is fine if we ignore hours.
        liquidationDate = new Date(maxDateTimestamp);
        // Correct for potential timezone shift if needed, but usually fine if treated consistently
        // Actually, let's explicitly use the UTC components to avoid 'yesterday'
        const userTimezoneOffset = liquidationDate.getTimezoneOffset() * 60000;
        liquidationDate = new Date(liquidationDate.getTime() + userTimezoneOffset);
    }

    console.log("Auto-Detected Liquidation Date:", liquidationDate.toISOString().substring(0, 10));

    // Update SMMLV Context for that year
    updateCurrentSMMLV(liquidationDate.getFullYear());

    // 2. Execute Gold Master Logic
    const weeks = calculator.calculateWeeks(history);
    const iblResult = calculator.calculateIBL(history, liquidationDate, true);

    // 3. Update UI
    // Weeks
    document.getElementById('res-weeks').innerText = weeks.toFixed(2);

    // IBL
    document.getElementById('res-ibl').innerText = formatCurrency(iblResult.value);
    document.getElementById('res-method').innerText = iblResult.method;

    // Rate & Pension
    const rateResult = calculator.calculateReplacementRate(iblResult.value, weeks, liquidationDate);

    document.getElementById('res-rate').innerText = `${rateResult.rate}%`; // Simplified for Stitch
    document.getElementById('res-pension').innerText = formatCurrency(rateResult.pension);

    // Populate Blurred Projection View
    const blurVal = document.getElementById('proj-blur-value');
    if (blurVal) blurVal.innerText = formatCurrency(rateResult.pension);

    // Update System Status
    document.getElementById('sys-status').innerText = "Verificado";
    document.getElementById('sys-status').className = "text-xs text-green-600 font-bold";

    // Render Detailed Logic
    renderMathExplanation(iblResult, rateResult, weeks);
}


/* ==========================================================================
   HELPERS
   ========================================================================== */
function renderMathExplanation(ibl, rate, weeks) {
    const container = document.getElementById('math-explanation-content');
    if (!container) return;

    // Sort salaries for Top 5 / Bottom 5
    // ibl.details contains { date, indexedSalary, ... }
    const sorted = [...ibl.details].sort((a, b) => b.indexedSalary - a.indexedSalary);
    const top5 = sorted.slice(0, 5);
    const bottom5 = sorted.slice(-5);

    let html = `
        <h3 class="text-lg font-bold mt-4 mb-2 text-slate-800 dark:text-slate-200">1. Análisis del IBL (Ingreso Base de Liquidación)</h3>
        <p>El sistema indexa (trae a valor presente) cada salario histórico usando el IPC.<br>
        <strong>Fórmula:</strong> <code>Salario Indexado = Salario * (IPC Fecha Liquidación / IPC Fecha Salario)</code></p>
        
        <p class="mt-2">Se toman los últimos 10 años (120 meses):<br>
        - Meses con aportes encontrados: <strong>${ibl.details.length}</strong><br>
        - Meses faltantes (se asumen ceros): <strong>${120 - ibl.details.length < 0 ? 0 : 120 - ibl.details.length}</strong></p>

        <p class="font-bold mt-2">Mayores salarios indexados (Top 5):</p>
        <ul class="list-disc pl-5 text-xs">
            ${top5.map(d => `<li>${d.date}: ${formatCurrency(d.indexedSalary)}</li>`).join('')}
        </ul>

        <p class="font-bold mt-2">Menores salarios o ceros (Base):</p>
        <ul class="list-disc pl-5 text-xs">
            ${bottom5.map(d => `<li>${d.date}: ${formatCurrency(d.indexedSalary)}</li>`).join('')}
        </ul>

        <p class="mt-2 font-bold text-primary">Promedio IBL Calculado: ${formatCurrency(ibl.value)}</p>
        <p class="text-xs text-slate-500">(Nota: Si el promedio de "Toda la Vida" fuera superior, el sistema lo usaría automáticamente).</p>

        <h3 class="text-lg font-bold mt-6 mb-2 text-slate-800 dark:text-slate-200">2. Cálculo de la Tasa de Reemplazo (r)</h3>
        <p><strong>Fórmula de Ley:</strong> <code>r = 65.5 - 0.5 * (s)</code>, donde <code>s = IBL / Salario Mínimo</code>.</p>
        <p>s = ${Math.round(ibl.value)} / ${1300000} (Est) = ${(ibl.value / 1300000).toFixed(2)} salarios mínimos.</p>
        <p><strong>Tasa Base Calculada:</strong> ${rate.baseRate}%</p>

        <h3 class="text-lg font-bold mt-6 mb-2 text-slate-800 dark:text-slate-200">3. Semanas y Regla de No Simultaneidad</h3>
        <p><strong>Semanas Cotizadas Totales:</strong> ${weeks.toFixed(2)}</p>
        <p class="text-xs text-slate-500">Regla Contable: Si usted trabajó en dos empresas el mismo mes, el sistema suma ambos salarios para el IBL, pero solo cuenta el tiempo una vez (máximo 4.29 semanas por mes).</p>
        
        <p class="mt-2">Semanas Mínimas Requeridas: 1300<br>
        Exceso: ${(weeks - 1300).toFixed(2)} semanas.<br>
        <strong>Bono (1.5% por cada 50 semanas extra):</strong> +${rate.bonus}%</p>

        <h3 class="text-lg font-bold mt-6 mb-2 text-slate-800 dark:text-slate-200">4. Resultado Final</h3>
        <p><strong>Tasa Final:</strong> ${rate.rate}% (Max 80%)<br>
        <strong>Mesada:</strong> ${formatCurrency(ibl.value)} * ${rate.rate}% = <span class="text-xl font-bold text-emerald-600">${formatCurrency(rate.pension)}</span></p>
    `;

    container.innerHTML = html;
}

/* ==========================================================================
   PREMIUM SIMULATION LOGIC (BETA)
   ========================================================================== */
window.quickFill = function (type) {
    const minWage = 1300000;
    const maxWage = minWage * 25;
    let val = 0;

    // Grab current salary from last history entry if available
    if (type === 'current') {
        const rows = document.querySelectorAll('.data-row');
        if (rows.length > 0) {
            const lastRow = rows[rows.length - 1];
            val = parseFloat(lastRow.querySelector('.salary').value) || minWage;
        } else {
            val = minWage;
        }
    } else if (type === 'max') {
        val = maxWage;
    } else {
        val = minWage;
    }

    document.getElementById('sim-forward-input').value = Math.round(val);
};

window.runForwardSimulation = function () {
    const contribution = parseFloat(document.getElementById('sim-forward-input').value);
    if (!contribution || contribution <= 0) {
        alert("Por favor ingrese un monto válido.");
        return;
    }

    const result = runSimulationInternal(contribution);

    // Display
    const resEl = document.getElementById('sim-forward-result');
    const valEl = document.getElementById('sim-forward-val');
    resEl.classList.remove('hidden');
    valEl.innerText = formatCurrency(result.pension);
};

window.runGoalSeeker = function () {
    const targetPension = parseFloat(document.getElementById('sim-goal-input').value);
    if (!targetPension || targetPension <= 0) {
        alert("Por favor ingrese una pensión deseada válida.");
        return;
    }

    // Iterative approach: Binary Search for contribution
    // Range: 1 SMMLV to 25 SMMLV
    const minWage = 1300000;
    const maxWage = minWage * 25;
    let low = minWage;
    let high = maxWage;
    let found = false;
    let bestContribution = 0;

    // Safety break
    let attempts = 0;

    while (low <= high && attempts < 20) {
        const mid = (low + high) / 2;
        const res = runSimulationInternal(mid);

        if (Math.abs(res.pension - targetPension) < 10000) {
            // Close enough ($10k COP tolerance)
            bestContribution = mid;
            found = true;
            break;
        } else if (res.pension < targetPension) {
            low = mid + 1000; // Need more money
        } else {
            high = mid - 1000; // Overkill
        }
        bestContribution = mid; // Track closest
        attempts++;
    }

    // Check if goal is possibly unreachable (even with max contribution)
    const maxRes = runSimulationInternal(maxWage);

    const resEl = document.getElementById('sim-goal-result');
    const valEl = document.getElementById('sim-goal-val');
    resEl.classList.remove('hidden');

    if (targetPension > maxRes.pension) {
        valEl.innerText = "Imposible (Max Legal: " + formatCurrency(maxRes.pension) + ")";
        valEl.className = "text-lg font-bold text-red-500";
    } else {
        valEl.innerText = formatCurrency(bestContribution);
        valEl.className = "text-lg font-bold text-primary dark:text-blue-400";
    }
};

function runSimulationInternal(monthlyContribution) {
    if (!calculator) return { pension: 0 };

    // 1. Clone History
    const rows = document.querySelectorAll('.data-row');
    let history = [];
    rows.forEach(r => {
        history.push({
            start: r.querySelector('.date-start').value,
            end: r.querySelector('.date-end').value,
            salary: parseFloat(r.querySelector('.salary').value) || 0,
            semanas: parseFloat(r.querySelector('.val-sem').value) || 0,
            total: parseFloat(r.querySelector('.val-total').innerText) || 0
        });
    });

    if (history.length === 0) return { pension: 0 };

    // 2. Project IPC (Inflation) for Future Dates
    // We need synthetic IPC data so calculateIBL doesn't crash on future dates.
    // Strategy: Calculate average monthly inflation from the last 10 years of REAL data.

    // Find last available IPC
    const ipcData = calculator.ipcSeries; // Direct access to array
    if (!ipcData || ipcData.length === 0) return { pension: 0 };

    // Sort by Year/Month just in case
    ipcData.sort((a, b) => (a.year - b.year) || (a.month - b.month));
    const lastRealIPC = ipcData[ipcData.length - 1];

    // Get stats from 10 years ago to now
    const cutOffYear = lastRealIPC.year - 10;
    const pastIPC = ipcData.find(e => e.year === cutOffYear && e.month === lastRealIPC.month);

    let avgMonthlyInflation = 0;
    if (pastIPC) {
        // Geometric Mean of Growth: (Final / Initial) ^ (1/Months) - 1
        const totalGrowth = lastRealIPC.value / pastIPC.value;
        const monthsDiff = (lastRealIPC.year - pastIPC.year) * 12 + (lastRealIPC.month - pastIPC.month);
        if (monthsDiff > 0) {
            avgMonthlyInflation = Math.pow(totalGrowth, 1 / monthsDiff) - 1;
        }
    }

    // Fallback if data is sparse: 0.3% monthly (~3.66% annual)
    if (avgMonthlyInflation === 0) avgMonthlyInflation = 0.003;

    // console.log(`Projecting Future IPC with Monthly Rate: ${(avgMonthlyInflation * 100).toFixed(4)}%`);

    // 3. Project Future History
    const futureMonths = 60; // 5 Years Fixed Projection
    const today = new Date();
    let currentDate = new Date(today);

    // We need to inject synthetic IPCs into the calculator instance
    // Important: We must CLEAN UP afterwards to not pollute global state.
    const injectedIPCs = [];

    let currentIPCValue = lastRealIPC.value;
    let currentIPCDate = new Date(lastRealIPC.year, lastRealIPC.month - 1); // JS Month is 0-indexed

    // Advance IPC projection to cover the gap from 'Last Data' to 'Today + 5 Years'
    // First, fill gap to today if any

    // Actually, we just need to ensure `calculator.getIPC` finds data when asked.
    // The simulation will ask for dates starting next month.

    // Append Future Data to History
    for (let i = 0; i < futureMonths; i++) {
        // Next Month
        currentDate.setMonth(currentDate.getMonth() + 1);
        const dateStr = currentDate.toISOString().substring(0, 10);

        // Add History Row
        history.push({
            start: dateStr,
            end: dateStr,
            salary: monthlyContribution,
            semanas: 4.28,
            total: 4.28
        });

        // Project IPC for this date (Roughly matches Year/Month)
        // We might be way ahead of 'lastRealIPC'.
        // Let's project linearly from lastRealIPC until we cover this future date.
        while (currentIPCDate < currentDate) {
            currentIPCDate.setMonth(currentIPCDate.getMonth() + 1);
            currentIPCValue = currentIPCValue * (1 + avgMonthlyInflation);

            // Register this synthetic IPC
            const synth = {
                year: currentIPCDate.getFullYear(),
                month: currentIPCDate.getMonth() + 1,
                value: currentIPCValue,
                isSynthetic: true
            };

            // Only add if not exists (avoid overwriting real data if overlap)
            if (!calculator.getIPC(synth.year, synth.month)) {
                calculator.ipcSeries.push(synth);
                injectedIPCs.push(synth);
            }
        }
    }

    // 4. Run Calculation
    const liquidationDate = currentDate; // Future date

    // Update SMMLV for future context (Naive: project it too? or keep constant?)
    // Realistically, pension limits are in SMMLV. 
    // If we project Salary (static) but keep SMMLV static, it's safer.
    // Indexing everything is complex. Let's assume constant purchase power (Real Terms).
    // Or, if we project IPC, we should strictly project SMMLV too for the Replacement Rate formula.
    // However, Ley 797 uses 's' = IBL / SMMLV.
    // If we inflate IBL (via IPC) but don't inflate SMMLV, 's' skyrockets, lowering the rate 'r'.
    // WAIT. IBL is indexed to the Liquidation Date.
    // If we move Liquidation Date to 2030, current salaries get HUGE indexing.
    // The Future Salary (e.g. 1M) entered by user... is it 1M in Today's money or 2030 money?
    // User thinks in Today's money.
    // If user enters 1M today, and we project 1M in 2030, that 1M is worth much less.
    // Correct approach for a "Real Terms" simulator:
    // Assume 0% Inflation for the projection? 
    // OR: Inflate the User's Contribution by the same rate?
    // The User asked to "Use Average IPC". This implies nominal projection.
    // So we MUST project SMMLV too, otherwise the 's' ratio breaks.
    // We will inject projected SMMLV into calculator.smmlvHistory as well.

    // Project SMMLV
    const injectedSMMLVs = [];
    const lastSMMLV = calculator.smmlvHistory[calculator.smmlvHistory.length - 1];
    let currSMMLVVal = lastSMMLV.value;
    let currSMMLVYear = lastSMMLV.year;

    while (currSMMLVYear < liquidationDate.getFullYear()) {
        currSMMLVYear++;
        // SMMLV usually grows slightly above inflation. Let's use same rate for safety.
        // Or Avg Inflation + 1%? Let's stick to Inflation to be conservative.
        // Annual Inflation = (1+monthly)^12 - 1
        const annualInf = Math.pow(1 + avgMonthlyInflation, 12) - 1;
        currSMMLVVal = currSMMLVVal * (1 + annualInf);

        const synthS = { year: currSMMLVYear, value: Math.round(currSMMLVVal), isSynthetic: true };
        if (!calculator.getSMMLV(currSMMLVYear)) {
            calculator.smmlvHistory.push(synthS);
            injectedSMMLVs.push(synthS);
        }
    }

    try {
        const weeks = calculator.calculateWeeks(history);
        const iblResult = calculator.calculateIBL(history, liquidationDate, true); // true = strict IPC (now satisfied)
        const rateResult = calculator.calculateReplacementRate(iblResult.value, weeks, liquidationDate);
        return rateResult;
    } finally {
        // 5. Cleanup: Remove injected data to prevent polluting the main app state
        // Remove IPCs
        injectedIPCs.forEach(synth => {
            const idx = calculator.ipcSeries.indexOf(synth);
            if (idx > -1) calculator.ipcSeries.splice(idx, 1);
        });

        // Remove SMMLVs
        injectedSMMLVs.forEach(synth => {
            const idx = calculator.smmlvHistory.indexOf(synth);
            if (idx > -1) calculator.smmlvHistory.splice(idx, 1);
        });
    }
}


/* ==========================================================================
   HELPERS & BYPASS
   ========================================================================== */
// Temp Bypass: Auto-unlock full report if URL has ?debug=true OR just override action
// Actually, user wants to see it now. I'll just change the button action in the HTML or hook it here.
// Let's hook the button with ID 'unlock-btn' if it existed, but we have onclick="switchView...".
// The switchView logic already works. The issue is likely the 'lock' visual.
// The user requests "let me over pass".
// I will ensure switchView('view-full-report') works directly, which it does in app.js.
// The "Lock" button in index.html already calls switchView('view-full-report'). 
// So, effectively, it IS unlocked. I just need to remove the payment text? 
// The user said "add a premium option AFTER unlocking... let me over pass".
// I'll assume they mean "Access without paying". 
// The current implementation allows access on click.

function updateCurrentSMMLV(yearOverride) {
    const year = yearOverride || new Date().getFullYear();
    if (calculator) {
        // Just for system state, logic handles it internally
        // Could update UI if we had a SMMLV display
        console.log("SMMLV Context Updated for Year:", year);
    }
}

function formatCurrency(val) {
    return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(val);
}

function formatDateForInput(dateStr) {
    if (!dateStr) return '';
    // Handle DD/MM/YYYY
    if (dateStr.includes('/')) {
        const parts = dateStr.split('/');
        if (parts.length === 3) return `${parts[2]}-${parts[1]}-${parts[0]}`;
    }
    return dateStr.substring(0, 10);
}

function parseSalary(val) {
    if (typeof val === 'number') return val;
    if (!val) return 0;
    return parseFloat(val.toString().replace(/[^\d.,]/g, '').replace(',', '.')) || 0;
}

function parseExcelDate(val) {
    // Reuse logic if strictly needed, or trust simple robust parser
    if (val instanceof Date) return val.toISOString().split('T')[0];
    if (typeof val === 'number') {
        return new Date(Math.round((val - 25569) * 86400 * 1000)).toISOString().split('T')[0];
    }
    return formatDateForInput(String(val));
}
