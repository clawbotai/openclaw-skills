// optimizer.js — Herramientas de optimización pensional RPM
// Buscador de meta (calculadora inversa) y calculadora de carga total

/**
 * Buscador de Meta (Calculadora Inversa)
 *
 * Dado un objetivo de mesada pensional, calcula el IBC mensual requerido
 * para alcanzarlo en distintos horizontes de tiempo (1, 2, 3, 5, 10 años).
 *
 * Usa búsqueda binaria para encontrar el IBC que produce la pensión objetivo.
 *
 * @param {number} targetPension - mesada pensional deseada (COP/mes)
 * @param {number} currentWeeks - semanas actuales cotizadas
 * @param {number} currentIBLSum - suma actual de salarios indexados (últimos 10 años)
 * @param {number} currentIBLMonths - meses actuales en el cálculo IBL
 * @returns {Array<{years: number, monthlyIBC: number, totalCost: number, burden: Object}>}
 */
/**
 * @param {number} targetPension - mesada pensional deseada
 * @param {number} currentWeeks - semanas actuales
 * @param {number} existingIndexedSum - suma de salarios indexados en la ventana de 120 meses
 * @param {number} existingMonthsInWindow - meses existentes dentro de la ventana de 10 años
 */
function goalSeeker(targetPension, currentWeeks, existingIndexedSum, existingMonthsInWindow) {
  const horizons = [1, 2, 3, 5, 10];
  const results = [];
  const IBL_DIVISOR = 120;

  for (const years of horizons) {
    const newMonths = years * 12;
    const totalWeeks = currentWeeks + (years * 48);
    const extraWeeks = totalWeeks - MIN_WEEKS; // Semanas sobre 1,300 (puede ser negativo)

    // Meses nuevos que caen dentro de la ventana de 120 meses
    const newMonthsInWindow = Math.min(newMonths, IBL_DIVISOR);
    // Meses existentes que quedan en la ventana después de agregar los nuevos
    const remainingExistingMonths = Math.max(0, IBL_DIVISOR - newMonthsInWindow);
    // Proporción del sum existente que queda en la ventana
    const existingProportion = existingMonthsInWindow > 0
      ? remainingExistingMonths / existingMonthsInWindow
      : 0;
    const remainingExistingSum = existingIndexedSum * existingProportion;

    // Búsqueda binaria del IBC requerido
    let lo = SMMLV_ACTUAL;
    let hi = SMMLV_ACTUAL * IBC_CAP_SMMLV;
    let bestIBC = hi;

    for (let iter = 0; iter < 60; iter++) {
      const mid = (lo + hi) / 2;

      // IBL = (suma existente restante + nuevos meses * IBC) / 120
      const simulatedIBL = (remainingExistingSum + mid * newMonthsInWindow) / IBL_DIVISOR;

      const rate = calculateReplacementRate(simulatedIBL, totalWeeks);
      const pension = calculateMonthlyPension(simulatedIBL, rate.rateDecimal);

      if (pension >= targetPension) {
        bestIBC = mid;
        hi = mid;
      } else {
        lo = mid;
      }
    }

    const maxIBC = SMMLV_ACTUAL * IBC_CAP_SMMLV;
    const feasible = bestIBC <= maxIBC;
    const burden = calculateBurden(bestIBC);

    // Verificar pensión final
    const finalIBL = (remainingExistingSum + bestIBC * newMonthsInWindow) / IBL_DIVISOR;
    const finalRate = calculateReplacementRate(finalIBL, totalWeeks);
    const finalPension = calculateMonthlyPension(finalIBL, finalRate.rateDecimal);

    results.push({
      years,
      monthlyIBC: Math.round(bestIBC),
      totalCost: Math.round(bestIBC * 12 * years),
      feasible,
      burden,
      extraWeeks: parseFloat(extraWeeks.toFixed(0)),
      projectedWeeks: parseFloat(totalWeeks.toFixed(2)),
      projectedPension: finalPension
    });
  }

  return results;
}

/**
 * Proyector de Pensión Futura
 *
 * Dado un IBC mensual futuro, proyecta la mesada pensional.
 *
 * @param {number} futureMonthlyIBC - IBC que el usuario planea aportar
 * @param {number} currentWeeks
 * @param {number} currentIBLSum
 * @param {number} currentIBLMonths
 * @param {number} years - horizonte en años
 * @returns {{projectedPension: number, projectedWeeks: number, rate: Object, ibl: number}}
 */
function projectPension(futureMonthlyIBC, currentWeeks, currentIBLSum, currentIBLMonths, years) {
  const newMonths = years * 12;
  const newWeeks = currentWeeks + (years * 48);

  const totalSum = currentIBLSum + (futureMonthlyIBC * newMonths);
  const totalMonths = currentIBLMonths + newMonths;
  const ibl = Math.max(totalSum / totalMonths, SMMLV_ACTUAL);

  const rate = calculateReplacementRate(ibl, newWeeks);
  const pension = calculateMonthlyPension(ibl, rate.rateDecimal);

  return {
    projectedPension: pension,
    projectedWeeks: parseFloat(newWeeks.toFixed(2)),
    rate,
    ibl: Math.round(ibl)
  };
}

/**
 * Calculadora de Carga Total (Full Burden)
 *
 * Para independientes/freelancers:
 * - Pensión: 16% del IBC
 * - Salud: 12.5% del IBC
 * - ARL: 0.522% del IBC (Riesgo Nivel I)
 * - Total: ~29.022% del IBC
 *
 * @param {number} ibc - Ingreso Base de Cotización mensual
 * @returns {{pension: number, health: number, arl: number, total: number, ibc: number, percentTotal: string}}
 */
function calculateBurden(ibc) {
  const pension = ibc * 0.16;
  const health = ibc * 0.125;
  const arl = ibc * 0.00522;
  const total = pension + health + arl;

  return {
    ibc: Math.round(ibc),
    pension: Math.round(pension),
    health: Math.round(health),
    arl: Math.round(arl),
    total: Math.round(total),
    percentTotal: '29.02%'
  };
}

/**
 * Simulador de History Booster
 *
 * Calcula el ROI de aumentar retroactivamente las contribuciones.
 * "¿Qué pasaría si hubiéramos cotizado $X más durante los últimos N años?"
 *
 * @param {number} boostAmount - aumento mensual adicional al IBC histórico
 * @param {number} boostYears - años hacia atrás para aplicar el boost
 * @param {number} currentIBLSum
 * @param {number} currentIBLMonths
 * @param {number} currentWeeks
 * @returns {{boostedIBL: number, boostedPension: number, originalPension: number, savings: number}}
 */
function simulateBoost(boostAmount, boostYears, currentIBLSum, currentIBLMonths, currentWeeks) {
  // Pensión original
  const originalIBL = Math.max(currentIBLSum / currentIBLMonths, SMMLV_ACTUAL);
  const originalRate = calculateReplacementRate(originalIBL, currentWeeks);
  const originalPension = calculateMonthlyPension(originalIBL, originalRate.rateDecimal);

  // Pensión con boost (últimos N años = N*12 meses con IBC aumentado)
  const boostMonths = boostYears * 12;
  // Los meses boosteados reemplazan meses existentes, no se suman nuevos
  // Simplificación: asumimos que el boost se suma al IBC de esos meses
  const boostedSum = currentIBLSum + (boostAmount * boostMonths);
  const boostedIBL = Math.max(boostedSum / currentIBLMonths, SMMLV_ACTUAL);
  const boostedRate = calculateReplacementRate(boostedIBL, currentWeeks);
  const boostedPension = calculateMonthlyPension(boostedIBL, boostedRate.rateDecimal);

  // Costo del boost
  const boostTotalCost = boostAmount * 0.16 * boostMonths; // Solo aporte pensión adicional

  // Ahorro mensual
  const monthlySavings = boostedPension - originalPension;

  return {
    originalIBL: Math.round(originalIBL),
    boostedIBL: Math.round(boostedIBL),
    originalPension,
    boostedPension,
    monthlySavings,
    boostTotalCost: Math.round(boostTotalCost),
    roiMonths: monthlySavings > 0 ? Math.ceil(boostTotalCost / monthlySavings) : Infinity
  };
}
