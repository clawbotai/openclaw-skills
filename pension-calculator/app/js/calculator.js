// calculator.js — Matemáticas pensionales RPM (Colpensiones)
// Ley 797 de 2003. Semanas, IBL, tasa de reemplazo, indemnización sustitutiva.

/**
 * Días entre dos fechas usando convención 360 días (estándar Colpensiones).
 * 30 días por mes. Conteo inclusivo (+1).
 */
function days360(start, end) {
  const y1 = start.getFullYear(), m1 = start.getMonth(), d1 = Math.min(start.getDate(), 30);
  const y2 = end.getFullYear(), m2 = end.getMonth();
  const d2raw = end.getDate();
  const d2 = d2raw === 31 ? 30 : d2raw;

  return (y2 - y1) * 360 + (m2 - m1) * 30 + (d2 - d1) + 1;
}

/**
 * Calcular semanas totales cotizadas.
 *
 * Prioridad:
 * 1. Suma columna "Total" del resumen PDF (dato contable autorizado)
 * 2. Item [26] extraído del texto del PDF
 * 3. Cálculo por fechas fusionadas (360 días, con manejo de solapamientos)
 *
 * @param {Object} parsed - documento parseado con employers, totalWeeksReported
 * @returns {{weeks: number, source: string, calculated: number}}
 */
function calculateWeeks(parsed) {
  // Fuente 1: Suma de columna "Total" del resumen
  let sumTotal = 0;
  if (parsed.employers && parsed.employers.length > 0) {
    for (const emp of parsed.employers) {
      const t = parseFloat(emp.total) || 0;
      sumTotal += t;
    }
  }
  if (sumTotal > 100) {
    // La columna Total es la fuente más confiable
    const calculated = _calculateWeeksByDates(parsed.employers);
    return {
      weeks: parseFloat(sumTotal.toFixed(2)),
      source: 'Resumen PDF (columna Total)',
      calculated: parseFloat(calculated.toFixed(2))
    };
  }

  // Fuente 2: Item [26] del texto del PDF
  if (parsed.totalWeeksReported && parsed.totalWeeksReported > 100) {
    const calculated = _calculateWeeksByDates(parsed.employers);
    return {
      weeks: parseFloat(parsed.totalWeeksReported.toFixed(2)),
      source: 'Ítem [26] TOTAL SEMANAS',
      calculated: parseFloat(calculated.toFixed(2))
    };
  }

  // Fuente 3: Cálculo por fechas
  const calculated = _calculateWeeksByDates(parsed.employers);
  return {
    weeks: parseFloat(calculated.toFixed(2)),
    source: 'Cálculo por fechas (estimación)',
    calculated: parseFloat(calculated.toFixed(2))
  };
}

/**
 * Calcular semanas por fusión de intervalos de fecha.
 * Contabilidad 360 días estándar Colpensiones.
 */
function _calculateWeeksByDates(employers) {
  if (!employers || employers.length === 0) return 0;

  const intervals = employers
    .filter(e => e.startDate && e.endDate)
    .map(e => ({
      start: e.startDate instanceof Date ? e.startDate : new Date(e.startDate),
      end: e.endDate instanceof Date ? e.endDate : new Date(e.endDate)
    }))
    .sort((a, b) => a.start - b.start);

  if (intervals.length === 0) return 0;

  // Fusionar solapamientos
  const merged = [{ ...intervals[0] }];
  for (let i = 1; i < intervals.length; i++) {
    const last = merged[merged.length - 1];
    const next = intervals[i];
    // Contiguo o solapado (1 día de buffer)
    if (next.start.getTime() <= last.end.getTime() + 86400000) {
      if (next.end > last.end) last.end = next.end;
    } else {
      merged.push({ ...next });
    }
  }

  let totalDays360 = 0;
  for (const p of merged) {
    totalDays360 += days360(p.start, p.end);
  }

  return totalDays360 / 7;
}

/**
 * Calcular IBL (Ingreso Base de Liquidación) según Ley 797/2003
 *
 * Para cada mes en los últimos 10 años:
 *   1. Sumar IBC de empleadores concurrentes
 *   2. Tope: 25 × SMMLV del año
 *   3. Indexar por IPC (IPC_final / IPC_inicial)
 *   4. Promediar sobre meses efectivamente cotizados (divisor dinámico)
 *
 * Se compara con promedio toda la vida; se usa el mayor.
 *
 * @param {Array} history - registros con {year, month, ibc} o {startDate, endDate, salary}
 * @param {Date} liquidationDate
 * @returns {{ibl: number, method: string, iblLast10: number, iblLifetime: number, months: number, details: Array}}
 */
function calculateIBL(history, liquidationDate) {
  if (!history || history.length === 0) {
    return { ibl: SMMLV_ACTUAL, method: 'mínimo', iblLast10: 0, iblLifetime: 0, months: 0, details: [] };
  }

  const liqDate = liquidationDate || new Date();
  const liqYear = liqDate.getFullYear();
  const liqMonth = liqDate.getMonth() + 1;

  // IPC de referencia final (mes de liquidación)
  const ipcFinal = getIPCMonthly(liqYear, liqMonth);
  if (!ipcFinal) {
    console.error('No hay IPC para fecha de liquidación:', liqYear, liqMonth);
    return { ibl: SMMLV_ACTUAL, method: 'sin IPC', iblLast10: 0, iblLifetime: 0, months: 0, details: [] };
  }

  // Agrupar IBC por mes "YYYY-MM" (sumar concurrentes)
  const monthlyMap = {};

  for (const rec of history) {
    let year, month, ibc;

    if (rec.year && rec.month && rec.ibc != null) {
      // Formato detallado
      year = rec.year;
      month = rec.month;
      ibc = parseFloat(rec.ibc) || 0;
    } else if (rec.startDate && rec.salary != null) {
      // Formato resumen: expandir período a meses
      const start = rec.startDate instanceof Date ? rec.startDate : new Date(rec.startDate);
      const end = rec.endDate instanceof Date ? rec.endDate : new Date(rec.endDate);
      const salary = parseFloat(rec.salary) || 0;
      if (salary <= 0) continue;

      // Iterar cada mes del período
      let cur = new Date(start.getFullYear(), start.getMonth(), 1);
      const endMonth = new Date(end.getFullYear(), end.getMonth(), 1);
      while (cur <= endMonth) {
        const key = `${cur.getFullYear()}-${String(cur.getMonth() + 1).padStart(2, '0')}`;
        if (!monthlyMap[key]) monthlyMap[key] = { year: cur.getFullYear(), month: cur.getMonth() + 1, totalIBC: 0 };
        monthlyMap[key].totalIBC += salary;
        cur.setMonth(cur.getMonth() + 1);
      }
      continue;
    } else {
      continue;
    }

    if (ibc <= 0) continue;
    const key = `${year}-${String(month).padStart(2, '0')}`;
    if (!monthlyMap[key]) monthlyMap[key] = { year, month, totalIBC: 0 };
    monthlyMap[key].totalIBC += ibc;
  }

  // Aplicar tope 25 SMMLV + indexar
  const allEntries = [];
  for (const key of Object.keys(monthlyMap).sort()) {
    const m = monthlyMap[key];
    const smmlvYear = SMMLV[m.year] || SMMLV_ACTUAL;
    const cap = smmlvYear * IBC_CAP_SMMLV;
    const capped = Math.min(m.totalIBC, cap);

    const ipcInitial = getIPCMonthly(m.year, m.month);
    if (!ipcInitial) {
      // Sin IPC para este período — no se puede indexar
      continue;
    }

    const factor = ipcFinal / ipcInitial;
    const indexed = capped * factor;

    allEntries.push({
      key,
      year: m.year,
      month: m.month,
      rawIBC: m.totalIBC,
      capped,
      factor: parseFloat(factor.toFixed(4)),
      indexed: parseFloat(indexed.toFixed(0))
    });
  }

  // Separar últimos 10 años
  const cutoffYear = liqYear - 10;
  const last10 = allEntries.filter(e =>
    e.year > cutoffYear || (e.year === cutoffYear && e.month >= liqMonth)
  );

  // IBL últimos 10 años: divisor FIJO = 120 (estándar Colpensiones)
  // Si hay menos de 120 meses cotizados, se divide por 120 igual (penaliza gaps)
  const IBL_DIVISOR = 120;

  function sumIndexed(entries) {
    return entries.reduce((a, e) => a + e.indexed, 0);
  }

  const iblLast10 = last10.length > 0 ? sumIndexed(last10) / IBL_DIVISOR : 0;
  // Vida laboral: divisor = total de meses (no hay regla de 120 para este método)
  const iblLifetime = allEntries.length > 0 ? sumIndexed(allEntries) / allEntries.length : 0;
  const best = Math.max(iblLast10, iblLifetime);
  const method = best === iblLast10 ? 'Últimos 10 años' : 'Toda la vida laboral';

  return {
    ibl: Math.max(best, SMMLV_ACTUAL), // Piso: 1 SMMLV
    method,
    iblLast10: parseFloat(iblLast10.toFixed(0)),
    iblLifetime: parseFloat(iblLifetime.toFixed(0)),
    months: last10.length,
    details: last10
  };
}

/**
 * Calcular tasa de reemplazo según Ley 797/2003
 *
 * r = 65.5% - 0.5% × s   donde s = IBL / SMMLV_actual
 * Bonificación: +1.5% por cada 50 semanas sobre 1,300
 * Mínimo 55%, Máximo 80%
 */
function calculateReplacementRate(ibl, totalWeeks) {
  const s = ibl / SMMLV_ACTUAL;
  const baseRate = 65.5 - (0.5 * s);

  let bonus = 0;
  if (totalWeeks > MIN_WEEKS) {
    const extraWeeks = totalWeeks - MIN_WEEKS;
    bonus = Math.floor(extraWeeks / 50) * 1.5;
  }

  let rate = baseRate + bonus;
  rate = Math.max(55, Math.min(80, rate));

  return {
    rate,
    rateDecimal: rate / 100,
    baseRate: parseFloat(baseRate.toFixed(2)),
    bonus: parseFloat(bonus.toFixed(2)),
    sValue: parseFloat(s.toFixed(2)),
    extraWeeks: Math.max(0, totalWeeks - MIN_WEEKS)
  };
}

/**
 * Calcular mesada pensional
 * Piso: 1 SMMLV, Techo: 25 SMMLV
 */
function calculateMonthlyPension(ibl, rateDecimal) {
  let pension = ibl * rateDecimal;
  pension = Math.max(SMMLV_ACTUAL, Math.min(SMMLV_ACTUAL * IBC_CAP_SMMLV, pension));
  return Math.round(pension);
}

/**
 * Calcular indemnización sustitutiva (lump sum si semanas < 1,300)
 * ISP = IBL × semanas × tasa_cotización_promedio_ponderada
 */
function calculateIndemnizacion(ibl, totalWeeks, employers) {
  let totalDays = 0;
  let weightedRate = 0;

  for (const emp of (employers || [])) {
    if (!emp.startDate || !emp.endDate) continue;
    const start = emp.startDate instanceof Date ? emp.startDate : new Date(emp.startDate);
    const end = emp.endDate instanceof Date ? emp.endDate : new Date(emp.endDate);
    const d = days360(start, end);
    const midYear = Math.floor((start.getFullYear() + end.getFullYear()) / 2);
    const rate = getContributionRate(midYear);
    weightedRate += rate * d;
    totalDays += d;
  }

  const avgRate = totalDays > 0 ? weightedRate / totalDays : 0.16;
  return Math.round(ibl * totalWeeks * avgRate);
}

/**
 * Evaluar elegibilidad pensional
 */
function evaluateEligibility(totalWeeks, age, gender) {
  const requiredAge = PENSION_AGE[gender] || 62;
  const weeksRemaining = Math.max(0, MIN_WEEKS - totalWeeks);
  const yearsToAge = Math.max(0, requiredAge - age);

  const weeksPerYear = 48; // ~48 semanas cotizadas por año calendario
  const yearsForWeeks = weeksRemaining / weeksPerYear;
  const yearsNeeded = Math.max(yearsForWeeks, yearsToAge);

  const projectedDate = new Date();
  projectedDate.setFullYear(projectedDate.getFullYear() + Math.ceil(yearsNeeded));

  return {
    eligible: totalWeeks >= MIN_WEEKS && age >= requiredAge,
    weeksRemaining: parseFloat(weeksRemaining.toFixed(2)),
    yearsToAge,
    yearsForWeeks: parseFloat(yearsForWeeks.toFixed(1)),
    projectedDate: projectedDate.toLocaleDateString('es-CO', { year: 'numeric', month: 'long' })
  };
}

/**
 * Generar reporte completo de pensión
 */
function generateFullReport(parsed, age, gender) {
  const weeksResult = calculateWeeks(parsed);
  const totalWeeks = weeksResult.weeks;

  // IBL: preferir detalle mensual si existe, sino expandir desde resumen
  const iblInput = (parsed.details && parsed.details.length > 0) ? parsed.details : parsed.employers;
  const iblResult = calculateIBL(iblInput, new Date());
  const rateResult = calculateReplacementRate(iblResult.ibl, totalWeeks);
  const monthlyPension = calculateMonthlyPension(iblResult.ibl, rateResult.rateDecimal);
  const eligibility = evaluateEligibility(totalWeeks, age, gender);

  const indemnizacion = totalWeeks < MIN_WEEKS
    ? calculateIndemnizacion(iblResult.ibl, totalWeeks, parsed.employers)
    : 0;

  return {
    // Datos gratuitos
    totalWeeks,
    weeksSource: weeksResult.source,
    weeksCalculated: weeksResult.calculated,
    weeksVerified: Math.abs(totalWeeks - weeksResult.calculated) < 5,
    employers: parsed.employers,

    // Datos premium
    ibl: iblResult,
    replacementRate: rateResult,
    monthlyPension,
    eligibility,
    indemnizacion,
  };
}
