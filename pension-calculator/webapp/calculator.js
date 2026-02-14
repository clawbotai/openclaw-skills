/**
 * Colombian Pension Calculator Core Logic
 * Replicates Colpensiones (RPM) calculations for Pension and Indemnización Sustitutiva.
 */
class PensionCalculator {
  constructor(data) {
    this.smmlvHistory = data.smmlv;
    this.ipcSeries = data.ipc;
    this.contributionRates = data.contributionRates;
  }

  getSMMLV(year) {
    const entry = this.smmlvHistory.find(e => e.year === year);
    return entry ? entry.value : 0;
  }

  getIPC(year, month) {
    const entry = this.ipcSeries.find(e => e.year === year && e.month === month);
    return entry ? entry.value : null;
  }

  /**
   * Calculates the number of weeks from a total number of days.
   * Standard: 1 month = 30 days, 1 week = 7 days.
   * @param {number} totalDays 
   * @returns {number} weeks
   */
  /**
   * Calculates valid Pension Weeks (Time) handling overlaps.
   * Uses 360-day accounting (Colpensiones Standard).
   * @param {Array} history 
   * @returns {number} weeks
   */
  calculateWeeks(history) {
    if (!history || history.length === 0) return 0;

    // Rule: If the history items have explicit 'semanas' and 'sim' values, 
    // we use them directly as they represent the accounting truth.
    let explicitSum = 0;
    let hasExplicit = false;

    history.forEach(h => {
      // Correct Logic for Summary Table:
      // Valid Weeks = Reported Weeks - Simultaneous Weeks
      // We ignore 'Total' because it often doesn't subtract Sim in the PDF display.

      const sem = parseFloat(h.semanas) || 0;
      const sim = parseFloat(h.sim) || 0;
      // Lic (Licencias) are usually included in Pension time, so we don't subtract.

    });

    // Debugging Discrepancy Fix
    // The 'Total' column in the PDF is the AUTHORITATIVE Net Weeks from Colpensiones.
    // It accounts for Simultaneity, Suspensions, and other adjustments we might miss.
    // Debugging Discrepancy Fix
    // The 'Total' column in the PDF is the AUTHORITATIVE Net Weeks from Colpensiones.
    // It accounts for Simultaneity, Suspensions, and other adjustments we might miss.
    let sumTotalCol = 0;
    history.forEach((h, i) => {
      const val = (parseFloat(h.total) || 0);
      sumTotalCol += val;
      if (val > 50) {
        console.log(`Row ${i} (${h.start}): adding high value ${val}`);
      }
    });

    // Always prioritize the explicit total sum if it exists and is significant
    if (sumTotalCol > 100) {
      console.log("FINAL Weeks from sumTotalCol (FORCED): " + sumTotalCol);
      return parseFloat(sumTotalCol.toFixed(2));
    }

    // Legacy fallback (should rarely be reached with current backend logic)

    if (hasExplicit && explicitSum > 0) {
      console.log("Fallback: Using Calculated Net (Semanas - Sim): " + explicitSum);
      return parseFloat(explicitSum.toFixed(2));
    }

    // Fallback: Date-based logic with overlap handling (Estimation)
    // Sort by start date
    const intervals = history.map(h => ({
      start: new Date(h.start),
      end: new Date(h.end)
    })).sort((a, b) => a.start - b.start);

    let merged = [];
    if (intervals.length > 0) {
      let currStart = intervals[0].start;
      let currEnd = intervals[0].end;

      for (let i = 1; i < intervals.length; i++) {
        const nextStart = intervals[i].start;
        const nextEnd = intervals[i].end;

        // Check overlap (nextStart <= currEnd + 1 day)
        // In JS Dates, direct comparison works.
        // Add 1 day buffer for contiguity? 
        // Colpensiones treats 31st and 1st as contiguous.
        // Let's us loose inclusive check.
        if (nextStart <= new Date(currEnd.getTime() + 86400000)) {
          if (nextEnd > currEnd) currEnd = nextEnd;
        } else {
          merged.push({ start: currStart, end: currEnd });
          currStart = nextStart;
          currEnd = nextEnd;
        }
      }
      merged.push({ start: currStart, end: currEnd });
    }

    // 360-Day Accounting Sum
    let totalDays360 = 0;
    merged.forEach(interval => {
      const s = interval.start;
      const e = interval.end;
      // Formula: (Y2-Y1)*360 + (M2-M1)*30 + (D2-D1) + 1
      const d1 = Math.min(s.getDate(), 30);
      const d2 = e.getDate() === 31 ? 30 : e.getDate();

      const days = (e.getFullYear() - s.getFullYear()) * 360 +
        (e.getMonth() - s.getMonth()) * 30 +
        (d2 - d1) + 1;
      totalDays360 += days;
    });

    return parseFloat((totalDays360 / 7).toFixed(2));
  }

  calculateIBL(history, liquidationDate, strictMode = true) {
    if (!history || history.length === 0) return { value: 0, method: "Sin Datos" };

    // Verify we have IPC for Final Date
    const ipcFinal = this.getIPCForDate(liquidationDate.toISOString());
    if (!ipcFinal) {
      console.error("CRITICAL: No IPC found for Liquidation Date:", liquidationDate);
      return { error: "No existe IPC para la fecha de liquidación: " + liquidationDate.toISOString().substring(0, 10) };
    }

    const last10YearsRecords = [];
    const processedRecords = [];
    let sum10 = 0;
    let count10 = 0;

    // 10 Years Threshold
    const tenYearsAgo = new Date(liquidationDate);
    tenYearsAgo.setFullYear(tenYearsAgo.getFullYear() - 10);

    history.forEach(h => {
      const d = new Date(h.start);
      const salary = parseFloat(h.salary);
      if (isNaN(salary) || salary <= 0) return;

      // Get IPC Initial
      const ipcInitial = this.getIPC(d.getFullYear(), d.getMonth() + 1);

      // If IPC missing (e.g. year < 1995), Colpensiones usually ignores or uses base.
      // For now, if no IPC, we can't index properly. Skip or use factor 1?
      // Safe bet: Skip if really old, or default to 1 if just missing month?
      // Better: Skip and Log
      if (!ipcInitial) {
        console.warn(`Skipping IBL row ${h.start}: No IPC for ${d.getFullYear()}-${d.getMonth() + 1}`);
        return;
      }

      const factor = ipcFinal / ipcInitial;
      const indexedSalary = salary * factor;

      const record = {
        date: h.start,
        rawSalary: salary,
        indexedSalary: indexedSalary,
        factor: factor
      };

      processedRecords.push(record);

      // Check 10 years
      if (d >= tenYearsAgo) {
        sum10 += indexedSalary;
        count10++;
        last10YearsRecords.push(record);
      }
    });

    // Dynamic Denominator (Sparse Calculation) per Expert Request
    // We do NOT default to 120. We use the actual count of contributed months.
    let divisor = count10;

    console.log(`IBL Calculation: Sum=${sum10}, Count=${count10}, Divisor=${divisor}`);

    const ibl10Years = divisor > 0 ? (sum10 / divisor) : 0;

    const sumLife = processedRecords.reduce((acc, r) => acc + r.indexedSalary, 0);
    const countLife = processedRecords.length;
    const iblLifetime = countLife > 0 ? (sumLife / countLife) : 0;

    const bestIBL = Math.max(ibl10Years, iblLifetime);

    // Get Trace for Explanation
    // Sort by indexed salary to show extremes
    const sorted = [...last10YearsRecords].sort((a, b) => b.indexedSalary - a.indexedSalary);
    const top5 = sorted.slice(0, 5).map(r => ({ date: r.date, val: r.indexedSalary }));
    const bottom5 = sorted.slice(-5).map(r => ({ date: r.date, val: r.indexedSalary }));

    return {
      value: bestIBL,
      method: ibl10Years >= iblLifetime ? "Últimos 10 Años" : "Toda la Vida",
      details: last10YearsRecords,
      top5,
      bottom5,
      count: count10,
      totalMonths: divisor
    };
  }

  // Helper removed (expandToMonthly) as it is inline now

  getIPCForDate(dateStr) {
    const d = new Date(dateStr);
    return this.getIPC(d.getFullYear(), d.getMonth() + 1);
  }

  average(arr) {
    if (arr.length === 0) return 0;
    return arr.reduce((a, b) => a + b, 0) / arr.length;
  }

  /**
   * Calculates Replacement Rate (Tasa de Reemplazo).
   * r = 65.5 - 0.5 * s
   * @param {number} ibl 
   * @param {number} totalWeeks 
   * @returns {Object} Rate and Final Pension
   */
  calculateReplacementRate(ibl, totalWeeks, date) {
    const year = new Date(date).getFullYear();
    const smmlv = this.getSMMLV(year);
    if (!smmlv) return { error: "SMMLV no encontrado para " + year };

    const s = ibl / smmlv;
    let r = 65.5 - (0.5 * s);
    const baseRate = r;

    // Additional weeks
    let bonus = 0;
    let extraWeeks = 0;
    if (totalWeeks > 1300) {
      extraWeeks = parseFloat((totalWeeks - 1300).toFixed(2));
      const chunks = Math.floor(extraWeeks / 50);
      bonus = chunks * 1.5;
      r += bonus;
    }

    // Cap at 80%, Min at 55%
    if (r > 80) r = 80;
    if (r < 55) r = 55;

    const pension = ibl * (r / 100);

    // Final check: Pension cannot be lower than SMMLV if eligible
    // Also cannot exceed 25 SMMLV
    const maxPension = 25 * smmlv;
    const finalPension = Math.min(Math.max(pension, smmlv), maxPension);

    return {
      rate: r.toFixed(2),
      baseRate: baseRate.toFixed(2),
      bonus: bonus.toFixed(2),
      extraWeeks: extraWeeks,
      s_value: s.toFixed(2),
      ibl: ibl,
      pension: finalPension,
      smmlv: smmlv
    };
  }

  /**
   * Calculates Indemnización Sustitutiva.
   * ISP = SBC * SC * PPC
   */
  calculateIndemnity(history, liquidationDate, totalWeeks) {
    const iblResult = this.calculateIBL(history, liquidationDate);
    const sbc = iblResult.value; // SBC is essentially the IBL (average indexed salary)

    // Calculate PPC (Weighted Contribution Percentage)
    // We need to map history to rate
    let totalWeightedRate = 0;
    let count = 0;

    const monthly = iblResult.details;
    monthly.forEach(record => {
      const rate = this.getContributionRate(record.year);
      totalWeightedRate += rate;
      count++;
    });

    const ppc = count > 0 ? (totalWeightedRate / count) : 0; // Average of rates

    const isp = sbc * totalWeeks * ppc;

    return {
      isp: isp,
      sbc: sbc,
      sc: totalWeeks,
      ppc: (ppc * 100).toFixed(2) + "%"
    };
  }

  getContributionRate(year) {
    const row = this.contributionRates.find(r => year >= r.startYear && year <= r.endYear);
    return row ? row.rate : 0.16; // Default to 0.16 if not found
  }
}

// Export for usage
if (typeof module !== 'undefined') module.exports = PensionCalculator;
