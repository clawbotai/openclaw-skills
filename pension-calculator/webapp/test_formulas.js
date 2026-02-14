/**
 * Verification Script for Pension Calculator Formulas
 * Runs in Node.js
 */
const PensionCalculator = require('./calculator.js');
const fs = require('fs');

// Load real data for SMMLV/IPC context
const dataJs = fs.readFileSync('./data.js', 'utf8');
const dataClean = dataJs.replace('window.calculatorData =', '').strip().replace(/;$/, '');
const calculatorData = JSON.parse(dataClean);

const calc = new PensionCalculator(calculatorData);
const LIQ_DATE = '2025-01-01';
const SMMLV_2025 = 1423500;

console.log("=== PENSION FORMULA VERIFICATION ===\n");

function test(name, weeks, ibl, expectedRate, expectedPension) {
    console.log(`Test: ${name}`);
    console.log(`  Input: Weeks=${weeks}, IBL=${ibl}`);

    const res = calc.calculateReplacementRate(ibl, weeks, LIQ_DATE);

    console.log(`  Result: Rate=${res.rate}%, Pension=${res.pension}`);
    console.log(`  Expected: Rate=${expectedRate}%, Pension=${expectedPension}`);

    const rateDiff = Math.abs(parseFloat(res.rate) - expectedRate);
    const penDiff = Math.abs(res.pension - expectedPension);

    if (rateDiff < 0.1 && penDiff < 10) {
        console.log("  STATUS: ✅ PASS\n");
    } else {
        console.log("  STATUS: ❌ FAIL\n");
    }
}

// Case 1: Standard (1300 weeks)
// s = 3.51 -> r = 63.74%
test("Standard 1300 weeks", 1300, 5000000, 63.74, 3187000);

// Case 2: Bonus (1500 weeks)
// s = 1.40 -> r_base = 64.8% -> r_final = 70.8%
// Pension: 2,000,000 * 0.708 = 1,416,000 -> Min SMMLV = 1,423,500
test("Bonus 1500 weeks (Min Adjustment)", 1500, 2000000, 70.80, 1423500);

// Case 3: High Weeks & Salary (1850 weeks)
// s = 28.10 -> r_base = 51.45% -> chunks = 11 -> bonus = 16.5% -> r_final = 67.95%
test("High Salary (67.95% rate)", 1850, 40000000, 67.95, 27180000);

// Case 4: Max Cap (80%)
// If bonus pushes above 80%? 
// 1300 + 600 weeks = 1900. Bonus = 12 * 1.5 = 18%.
// s = 1.0 (IBL = SMMLV) -> r_base = 65% -> r_final = 83% -> capped at 80%
test("Max Rate Cap (80%)", 1900, 1423500, 80.00, 1138800);
// Note: 1423500 * 0.8 = 1138800. 
// BUT pension cannot be less than SMMLV if eligible. 
// So 1138800 -> 1423500.
test("Max Rate Cap (80%) with Min Adjustment", 1900, 1423500, 80.00, 1423500);
