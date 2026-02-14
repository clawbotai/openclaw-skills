// app.js — Controlador principal de la aplicación

(function() {
  'use strict';

  const state = {
    cedula: '',
    file: null,
    parsed: null,
    report: null,
    age: 55,
    gender: 'M',
    isPremium: false
  };

  const views = {
    welcome: document.getElementById('view-welcome'),
    upload: document.getElementById('view-upload'),
    terms: document.getElementById('view-terms'),
    free: document.getElementById('view-free'),
    paywall: document.getElementById('view-paywall'),
    dashboard: document.getElementById('view-dashboard'),
    loading: document.getElementById('view-loading')
  };

  function showView(name) {
    Object.values(views).forEach(v => { if (v) v.classList.add('hidden'); });
    if (views[name]) views[name].classList.remove('hidden');
    const startOver = document.getElementById('btn-start-over');
    if (startOver) startOver.classList.toggle('hidden', name === 'welcome');
    window.scrollTo(0, 0);
  }

  function showError(msg) {
    const el = document.getElementById('error-toast');
    if (el) {
      el.textContent = msg;
      el.classList.remove('hidden');
      setTimeout(() => el.classList.add('hidden'), 5000);
    }
    console.error(msg);
  }

  // === VISTA 1: Bienvenida ===
  document.getElementById('btn-cedula')?.addEventListener('click', () => {
    const input = document.getElementById('input-cedula');
    const cedula = input.value.trim().replace(/\D/g, '');
    if (cedula.length < 5 || cedula.length > 15) {
      showError('Ingrese un número de cédula válido (5-15 dígitos)');
      return;
    }
    state.cedula = cedula;
    showView('upload');
  });

  document.getElementById('input-cedula')?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') document.getElementById('btn-cedula')?.click();
  });

  // === VISTA 2: Carga de archivo ===
  const dropZone = document.getElementById('drop-zone');
  const fileInput = document.getElementById('file-input');

  dropZone?.addEventListener('click', () => fileInput?.click());
  dropZone?.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('border-blue-400', 'bg-slate-700');
  });
  dropZone?.addEventListener('dragleave', () => {
    dropZone.classList.remove('border-blue-400', 'bg-slate-700');
  });
  dropZone?.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('border-blue-400', 'bg-slate-700');
    if (e.dataTransfer.files.length > 0) handleFile(e.dataTransfer.files[0]);
  });
  fileInput?.addEventListener('change', (e) => {
    if (e.target.files.length > 0) handleFile(e.target.files[0]);
  });

  async function handleFile(file) {
    state.file = file;
    document.getElementById('file-name').textContent = file.name;
    showView('loading');
    document.getElementById('loading-text').textContent = 'Descifrando documento...';

    try {
      state.parsed = await processFile(file, state.cedula);
      document.getElementById('loading-text').textContent = 'Analizando historia laboral...';
      setTimeout(() => showView('terms'), 500);
    } catch (err) {
      showView('upload');
      if (err.message && err.message.includes('password')) {
        showError('Contraseña incorrecta. Verifique que su número de cédula sea correcto.');
      } else {
        showError('Error al procesar el documento: ' + (err.message || 'Error desconocido'));
      }
    }
  }

  // === VISTA 3: Términos de Servicio ===
  document.getElementById('btn-accept-terms')?.addEventListener('click', () => {
    if (!document.getElementById('terms-checkbox').checked) {
      showError('Debe aceptar los términos de servicio para continuar');
      return;
    }
    runCalculation();
    showView('free');
  });

  function runCalculation() {
    state.age = parseInt(document.getElementById('input-age')?.value) || 55;
    state.gender = document.getElementById('select-gender')?.value || 'M';
    state.report = generateFullReport(state.parsed, state.age, state.gender);
    renderFreeView();
  }

  // === VISTA 4: Resultados Gratuitos ===
  function renderFreeView() {
    const r = state.report;

    // Semanas
    document.getElementById('total-weeks').textContent =
      r.totalWeeks.toLocaleString('es-CO', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

    // Verificación
    const badge = document.getElementById('verification-badge');
    if (r.weeksVerified) {
      badge.innerHTML = `<span class="text-green-400">✓ Verificado</span>
        <span class="text-slate-500 text-xs ml-2">(${r.weeksSource})</span>`;
    } else {
      badge.innerHTML = `<span class="text-yellow-400">⚠ Estimación</span>
        <span class="text-slate-500 text-xs ml-2">(${r.weeksSource})</span>`;
    }

    // Empleadores
    const list = document.getElementById('employer-list');
    list.innerHTML = '';
    if (!r.employers || r.employers.length === 0) {
      list.innerHTML = '<p class="text-slate-400 text-sm">No se encontraron empleadores</p>';
    } else {
      r.employers.forEach(emp => {
        const start = emp.startDate ? (emp.startDate instanceof Date ? emp.startDate : new Date(emp.startDate)).toLocaleDateString('es-CO') : '—';
        const end = emp.endDate ? (emp.endDate instanceof Date ? emp.endDate : new Date(emp.endDate)).toLocaleDateString('es-CO') : '—';
        const div = document.createElement('div');
        div.className = 'bg-slate-700 rounded-lg p-4 mb-3';
        div.innerHTML = `
          <div class="font-semibold text-white text-sm">${emp.name || 'Sin nombre'}</div>
          <div class="text-xs text-slate-400 mt-1">NIT: ${emp.nit || '—'}</div>
          <div class="flex justify-between text-sm text-slate-300 mt-2">
            <span>${start} → ${end}</span>
            <span class="font-medium">${parseFloat(emp.total || emp.weeks || 0).toFixed(2)} sem.</span>
          </div>
          ${emp.salary ? `<div class="text-xs text-slate-400 mt-1">Último salario: ${formatCOP(emp.salary)}</div>` : ''}
        `;
        list.appendChild(div);
      });
    }

    // Teaser de pensión
    document.getElementById('pension-teaser').textContent = formatCOP(r.monthlyPension);

    // Edad/género
    document.getElementById('input-age').value = state.age;
    document.getElementById('select-gender').value = state.gender;
  }

  // Recalcular al cambiar edad/género
  document.getElementById('input-age')?.addEventListener('change', () => {
    runCalculation();
    if (state.isPremium) renderDashboard();
  });
  document.getElementById('select-gender')?.addEventListener('change', () => {
    runCalculation();
    if (state.isPremium) renderDashboard();
  });

  // === VISTA 5: Paywall ===
  document.getElementById('btn-paywall')?.addEventListener('click', () => showView('paywall'));
  document.getElementById('btn-simulate-payment')?.addEventListener('click', () => {
    state.isPremium = true;
    renderDashboard();
    showView('dashboard');
  });

  // === VISTA 6: Dashboard Premium ===
  function renderDashboard() {
    const r = state.report;

    // Mesada
    document.getElementById('dash-pension').textContent = formatCOP(r.monthlyPension);

    // IBL
    document.getElementById('dash-ibl').textContent = formatCOP(r.ibl.ibl);
    document.getElementById('dash-ibl-method').textContent = r.ibl.method;
    document.getElementById('dash-ibl-last10').textContent = formatCOP(r.ibl.iblLast10);
    document.getElementById('dash-ibl-lifetime').textContent = formatCOP(r.ibl.iblLifetime);

    // Tasa de reemplazo
    document.getElementById('dash-rate').textContent = r.replacementRate.rate.toFixed(1) + '%';
    document.getElementById('dash-rate-base').textContent = r.replacementRate.baseRate.toFixed(1) + '%';
    document.getElementById('dash-rate-bonus').textContent = '+' + r.replacementRate.bonus.toFixed(1) + '%';

    // Semanas y meses
    document.getElementById('dash-weeks').textContent =
      r.totalWeeks.toLocaleString('es-CO', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    document.getElementById('dash-months').textContent = (r.ibl.months || 0).toLocaleString('es-CO');

    // Elegibilidad
    const elig = r.eligibility;
    const eligEl = document.getElementById('dash-eligibility');
    if (elig.eligible) {
      eligEl.innerHTML = '<span class="text-green-400 text-xl font-bold">✓ Cumple requisitos</span>';
    } else {
      const reasons = [];
      if (elig.weeksRemaining > 0) reasons.push(`Faltan ${elig.weeksRemaining.toFixed(0)} semanas`);
      if (elig.yearsToAge > 0) reasons.push(`Faltan ${elig.yearsToAge} años de edad`);
      eligEl.innerHTML = `
        <span class="text-yellow-400 text-xl font-bold">⏳ Aún no cumple</span>
        <div class="text-slate-300 text-sm mt-2">${reasons.join(' • ')}</div>
        <div class="text-slate-400 text-xs mt-1">Fecha proyectada: ${elig.projectedDate}</div>
      `;
    }

    // Indemnización
    const indemnEl = document.getElementById('dash-indemnizacion');
    if (r.totalWeeks < MIN_WEEKS && r.indemnizacion > 0) {
      indemnEl.classList.remove('hidden');
      document.getElementById('dash-indemnizacion-value').textContent = formatCOP(r.indemnizacion);
    } else {
      indemnEl.classList.add('hidden');
    }

    initGoalSeeker();
    initBurdenCalculator();
  }

  // === Goal Seeker ===
  function initGoalSeeker() {
    const input = document.getElementById('goal-target');
    const btn = document.getElementById('btn-goal-seek');
    const resultsEl = document.getElementById('goal-results');
    if (!btn) return;

    // Valor por defecto: pensión actual redondeada
    if (input && !input.dataset.initialized) {
      input.value = Math.round(state.report.monthlyPension * 1.5).toLocaleString('es-CO');
      input.dataset.initialized = 'true';
    }

    // Remover listeners previos clonando el botón
    const newBtn = btn.cloneNode(true);
    btn.parentNode.replaceChild(newBtn, btn);

    newBtn.addEventListener('click', () => {
      const target = parseColNumber(input.value);
      if (target < SMMLV_ACTUAL) {
        showError('La mesada objetivo debe ser al menos 1 SMMLV (' + formatCOP(SMMLV_ACTUAL) + ')');
        return;
      }

      // Obtener datos actuales para el solver
      const iblData = state.report.ibl;
      const currentIBLSum = iblData.ibl * (iblData.months || 1);
      const currentIBLMonths = iblData.months || 1;

      // Calcular parámetros para el solver
      // existingIndexedSum = IBL * 120 (reconstruir la suma total de la ventana de 120 meses)
      const existingIndexedSum = iblData.iblLast10 * 120;
      const existingMonthsInWindow = Math.min(iblData.months || 0, 120);

      const results = goalSeeker(target, state.report.totalWeeks, existingIndexedSum, existingMonthsInWindow);

      resultsEl.innerHTML = '';
      results.forEach(r => {
        const feasibleClass = r.feasible ? 'border-slate-600' : 'border-red-800 opacity-60';
        const extraLabel = r.extraWeeks >= 0
          ? `${r.extraWeeks} semanas extra`
          : `${Math.abs(r.extraWeeks)} semanas faltantes`;
        const row = document.createElement('div');
        row.className = `bg-slate-700 rounded-lg p-4 border ${feasibleClass} mb-3`;
        row.innerHTML = `
          <div class="flex justify-between items-center">
            <div>
              <div class="text-white font-semibold">${r.years} año${r.years > 1 ? 's' : ''}</div>
              <div class="text-slate-400 text-xs">${extraLabel}</div>
            </div>
            <div class="text-right">
              <div class="text-blue-400 font-bold">${formatCOP(r.monthlyIBC)}</div>
              <div class="text-slate-400 text-xs">IBC mensual requerido</div>
            </div>
          </div>
          <div class="flex justify-between text-xs text-slate-400 mt-2 pt-2 border-t border-slate-600">
            <span>Aporte mensual: ${formatCOP(r.burden.total)}</span>
            <span>Pensión: ${formatCOP(r.projectedPension)}</span>
          </div>
          ${!r.feasible ? '<div class="text-red-400 text-xs mt-1">⚠ Excede 25 SMMLV — no factible</div>' : ''}
        `;
        resultsEl.appendChild(row);
      });
    });
  }

  // === Burden Calculator ===
  function initBurdenCalculator() {
    const input = document.getElementById('burden-ibc');
    const btn = document.getElementById('btn-burden');
    const resultsEl = document.getElementById('burden-results');
    if (!btn) return;

    if (input && !input.dataset.initialized) {
      input.value = Math.round(state.report.ibl.ibl).toLocaleString('es-CO');
      input.dataset.initialized = 'true';
    }

    const newBtn = btn.cloneNode(true);
    btn.parentNode.replaceChild(newBtn, btn);

    newBtn.addEventListener('click', () => {
      const ibc = parseColNumber(input.value);
      if (ibc < SMMLV_ACTUAL) {
        showError('El IBC mínimo es 1 SMMLV (' + formatCOP(SMMLV_ACTUAL) + ')');
        return;
      }

      const result = calculateBurden(ibc);

      resultsEl.innerHTML = `
        <div class="space-y-3">
          <div class="flex justify-between items-center bg-slate-700 rounded-lg p-3">
            <span class="text-slate-300">Pensión (16%)</span>
            <span class="text-white font-bold">${formatCOP(result.pension)}</span>
          </div>
          <div class="flex justify-between items-center bg-slate-700 rounded-lg p-3">
            <span class="text-slate-300">Salud (12.5%)</span>
            <span class="text-white font-bold">${formatCOP(result.health)}</span>
          </div>
          <div class="flex justify-between items-center bg-slate-700 rounded-lg p-3">
            <span class="text-slate-300">ARL Nivel I (0.522%)</span>
            <span class="text-white font-bold">${formatCOP(result.arl)}</span>
          </div>
          <div class="flex justify-between items-center bg-blue-900 rounded-lg p-4 border border-blue-500">
            <span class="text-blue-200 font-semibold">TOTAL MENSUAL</span>
            <span class="text-blue-300 font-bold text-xl">${formatCOP(result.total)}</span>
          </div>
          <div class="text-center text-slate-400 text-sm">
            ${result.percentTotal} del IBC (${formatCOP(result.ibc)})
          </div>
        </div>
      `;
    });
  }

  // === Navegación ===
  document.getElementById('btn-back-upload')?.addEventListener('click', () => showView('welcome'));
  document.getElementById('btn-back-free')?.addEventListener('click', () => showView('free'));
  document.getElementById('btn-start-over')?.addEventListener('click', () => {
    state.cedula = '';
    state.file = null;
    state.parsed = null;
    state.report = null;
    state.isPremium = false;
    document.getElementById('input-cedula').value = '';
    showView('welcome');
  });

  // Inicializar
  showView('welcome');

})();
