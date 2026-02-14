const fs = require('fs');

// Mock Browser Environment
const window = {};

// Load Data
const dataContent = fs.readFileSync('/Users/manuelv/FreeLancing/data.js', 'utf8');
eval(dataContent); // Populates window.calculatorData

// Load Calculator
const calcContent = fs.readFileSync('/Users/manuelv/FreeLancing/calculator.js', 'utf8');
eval(calcContent); // Defines PensionCalculator class in global scope

// Load Piedad Data
const jsonContent = fs.readFileSync('/Users/manuelv/FreeLancing/last_json_response.json', 'utf8');
const piedadData = JSON.parse(jsonContent).data;

// Prepare History
const history = piedadData.map(r => ({
    start: reformatDate(r.Desde),
    end: reformatDate(r.Hasta),
    salary: parseFloat(r.Salario),
    semanas: parseFloat(r.Semanas),
    sim: parseFloat(r.Sim),
    total: parseFloat(r.Total)
}));

// Helper to convert DD/MM/YYYY to YYYY-MM-DD
function reformatDate(dateStr) {
    const parts = dateStr.split('/');
    return `${parts[2]}-${parts[1]}-${parts[0]}`;
}

// Find Liquidation Date (Max Date)
let maxDate = new Date(0);
history.forEach(h => {
    const d = new Date(h.end);
    if (d > maxDate) maxDate = d;
});
// Adjust for timezone/midnight issues if needed, but for now just use the date part
console.log("Liquidation Date:", maxDate.toISOString().substring(0, 10));

// Determine correct liquidation date for IBL (usually Month-1 of last contribution, or correct month)
// Piedad's calculation used 2025-10-01 in the text ?? 
// "Mayores salarios indexados... 2025-10-01" suggests the projection went to 2025.
// WAIT. The user's text showed "2025-10-01" in the Top 5.
// Does Piedad's history go to 2025?
// Let's check the history tail.
const last = history[history.length - 1];
console.log("Last History Entry:", last);


// Initialize Calculator
const calculator = new PensionCalculator(window.calculatorData);
// Update SMMLV to max date year
// calculator.smmlvHistory is already loaded from data.js

// Run Logic
console.log("--- RUNNING CALCULATION ---");
const weeks = calculator.calculateWeeks(history);
const ibl = calculator.calculateIBL(history, maxDate, true);
const rate = calculator.calculateReplacementRate(ibl.value, weeks, maxDate);

console.log("Weeks:", weeks);
console.log("IBL Value:", ibl.value);
console.log("Rate %:", rate.rate);
console.log("Pension:", rate.pension);
console.log("Pension Formatted:", new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP' }).format(rate.pension));

