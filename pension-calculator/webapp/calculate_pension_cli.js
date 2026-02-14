const fs = require('fs');
const vm = require('vm');

// 1. Load Data
const dataJs = fs.readFileSync('data.js', 'utf8');
const windowMock = {};
vm.runInNewContext(dataJs, { window: windowMock });
const data = windowMock.calculatorData;

// 2. Load Calculator Class
const calculatorJs = fs.readFileSync('calculator.js', 'utf8');
const sandbox = {
    console: console,
    window: {},
    Date: Date,
    Math: Math,
    parseFloat: parseFloat,
    parseInt: parseInt,
    Object: Object,
    Array: Array
};
vm.runInNewContext(calculatorJs, sandbox);
const PensionCalculator = sandbox.PensionCalculator;

// 3. Extracted History (Paste JSON here)
const history = [{ "start": "1988-06-22", "end": "1990-10-31", "salary": 12321.0 }, { "start": "1991-01-14", "end": "1994-04-30", "salary": 19791.0 }, { "start": "1995-01-06", "end": "1995-06-30", "salary": 4200.0 }, { "start": "1995-01-07", "end": "1997-03-31", "salary": 2000.0 }, { "start": "1997-01-04", "end": "1997-05-31", "salary": 2500.0 }, { "start": "1997-01-09", "end": "1997-12-31", "salary": 1720.0 }, { "start": "1998-01-01", "end": "1998-12-31", "salary": 2040.0 }, { "start": "1999-01-01", "end": "1999-01-31", "salary": 2370.0 }, { "start": "1999-01-02", "end": "1999-11-30", "salary": 2450.0 }, { "start": "1999-01-12", "end": "1999-12-31", "salary": 2450.0 }, { "start": "2000-01-01", "end": "2000-01-31", "salary": 2600.0 }, { "start": "2000-01-02", "end": "2000-12-31", "salary": 2690.0 }, { "start": "2001-01-01", "end": "2001-01-31", "salary": 2860.0 }, { "start": "2001-01-02", "end": "2001-02-28", "salary": 3230.0 }, { "start": "2001-01-03", "end": "2001-12-31", "salary": 2960.0 }, { "start": "2002-01-01", "end": "2002-01-31", "salary": 3090.0 }, { "start": "2002-01-02", "end": "2002-12-31", "salary": 3400.0 }, { "start": "2003-01-01", "end": "2003-01-31", "salary": 3560.0 }, { "start": "2003-01-02", "end": "2004-01-31", "salary": 3670.0 }, { "start": "2004-01-02", "end": "2005-01-31", "salary": 4040.0 }, { "start": "2005-01-02", "end": "2006-01-31", "salary": 4300.0 }, { "start": "2006-01-02", "end": "2007-01-31", "salary": 5000.0 }, { "start": "2007-01-02", "end": "2008-01-31", "salary": 5500.0 }, { "start": "2008-01-02", "end": "2009-01-31", "salary": 5880.0 }, { "start": "2009-01-02", "end": "2010-01-31", "salary": 6360.0 }, { "start": "2010-01-02", "end": "2011-01-31", "salary": 6600.0 }, { "start": "2011-01-02", "end": "2012-01-31", "salary": 6930.0 }, { "start": "2012-01-02", "end": "2013-01-31", "salary": 7350.0 }, { "start": "2013-01-02", "end": "2014-01-31", "salary": 7710.0 }, { "start": "2014-01-02", "end": "2015-01-31", "salary": 8640.0 }, { "start": "2015-01-02", "end": "2016-01-31", "salary": 8980.0 }, { "start": "2016-01-02", "end": "2016-07-31", "salary": 9610.0 }, { "start": "2016-01-08", "end": "2017-01-31", "salary": 18000000.0 }, { "start": "2017-01-02", "end": "2018-01-31", "salary": 25000000.0 }, { "start": "2018-01-02", "end": "2018-06-30", "salary": 30000000.0 }, { "start": "2018-01-07", "end": "2018-07-31", "salary": 13800000.0 }, { "start": "2018-01-07", "end": "2018-07-31", "salary": 30000000.0 }, { "start": "2018-01-08", "end": "2018-08-31", "salary": 13800000.0 }, { "start": "2018-01-08", "end": "2018-08-31", "salary": 30000000.0 }, { "start": "2018-01-09", "end": "2018-09-30", "salary": 13800000.0 }, { "start": "2018-01-09", "end": "2018-09-30", "salary": 30000000.0 }, { "start": "2018-01-10", "end": "2018-10-31", "salary": 13800000.0 }, { "start": "2018-01-10", "end": "2018-10-31", "salary": 30000000.0 }, { "start": "2018-01-11", "end": "2018-11-30", "salary": 13800000.0 }, { "start": "2018-01-11", "end": "2018-11-30", "salary": 30000000.0 }, { "start": "2018-01-12", "end": "2018-12-31", "salary": 13800000.0 }, { "start": "2018-01-12", "end": "2018-12-31", "salary": 30000000.0 }, { "start": "2019-01-01", "end": "2019-01-31", "salary": 13800000.0 }, { "start": "2019-01-01", "end": "2019-01-31", "salary": 30000000.0 }, { "start": "2019-01-02", "end": "2019-02-28", "salary": 13800000.0 }, { "start": "2019-01-02", "end": "2019-02-28", "salary": 40000000.0 }, { "start": "2019-01-03", "end": "2019-03-31", "salary": 13800000.0 }, { "start": "2019-01-03", "end": "2019-03-31", "salary": 40000000.0 }, { "start": "2019-01-04", "end": "2019-04-30", "salary": 13800000.0 }, { "start": "2019-01-04", "end": "2019-04-30", "salary": 40000000.0 }, { "start": "2019-01-05", "end": "2019-05-31", "salary": 13800000.0 }, { "start": "2019-01-05", "end": "2019-05-31", "salary": 40000000.0 }, { "start": "2019-01-06", "end": "2019-06-30", "salary": 13800000.0 }, { "start": "2019-01-06", "end": "2019-06-30", "salary": 40000000.0 }, { "start": "2019-01-07", "end": "2019-07-31", "salary": 13800000.0 }, { "start": "2019-01-07", "end": "2019-07-31", "salary": 40000000.0 }, { "start": "2019-01-08", "end": "2019-08-31", "salary": 13800000.0 }, { "start": "2019-01-08", "end": "2019-08-31", "salary": 40000000.0 }, { "start": "2019-01-09", "end": "2019-09-30", "salary": 13800000.0 }, { "start": "2019-01-09", "end": "2019-09-30", "salary": 40000000.0 }, { "start": "2019-01-10", "end": "2019-10-31", "salary": 13800000.0 }, { "start": "2019-01-10", "end": "2019-10-31", "salary": 40000000.0 }, { "start": "2019-01-11", "end": "2019-11-30", "salary": 13800000.0 }, { "start": "2019-01-11", "end": "2019-11-30", "salary": 40000000.0 }, { "start": "2019-01-12", "end": "2019-12-31", "salary": 13800000.0 }, { "start": "2019-01-12", "end": "2019-12-31", "salary": 40000000.0 }, { "start": "2020-01-01", "end": "2020-01-31", "salary": 13800000.0 }, { "start": "2020-01-01", "end": "2020-01-31", "salary": 40000000.0 }, { "start": "2020-01-02", "end": "2020-02-29", "salary": 50000000.0 }, { "start": "2020-01-03", "end": "2020-03-31", "salary": 57666670.0 }, { "start": "2020-01-04", "end": "2020-04-30", "salary": 30389020.0 }, { "start": "2020-01-05", "end": "2020-07-31", "salary": 8778.0 }, { "start": "2020-01-08", "end": "2020-09-30", "salary": 60000000.0 }, { "start": "2020-01-10", "end": "2021-06-30", "salary": 80000000.0 }, { "start": "2021-01-07", "end": "2021-07-31", "salary": 80000010.0 }, { "start": "2021-01-08", "end": "2022-01-31", "salary": 80000000.0 }, { "start": "2022-01-02", "end": "2023-01-31", "salary": 98000000.0 }, { "start": "2023-01-02", "end": "2024-02-29", "salary": 107800000.0 }, { "start": "2024-01-03", "end": "2024-03-31", "salary": 117300000.0 }, { "start": "2024-01-04", "end": "2024-09-30", "salary": 107800000.0 }, { "start": "2024-01-10", "end": "2024-10-31", "salary": 129300000.0 }, { "start": "2024-01-11", "end": "2024-11-30", "salary": 124300000.0 }, { "start": "2024-01-12", "end": "2025-02-28", "salary": 117300000.0 }, { "start": "2025-01-03", "end": "2025-11-30", "salary": 150000000.0 }];

// 4. Calculate
const calculator = new PensionCalculator(data);
const today = '2025-12-29'; // Use specific or today
console.log("Liquidation Date:", today);

// a. Calculate Weeks
let totalDays = 0;
// Need to reproduce the exact logic from app.js 'totalDays += diffDays' if Calculator doesn't do it itself for the final sum
// Calculator.calculateWeeks takes totalDays.
history.forEach(item => {
    const d1 = new Date(item.start);
    const d2 = new Date(item.end);
    const diffTime = Math.abs(d2 - d1);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
    totalDays += diffDays;
});
const weeks = calculator.calculateWeeks(totalDays);
console.log("Total Weeks:", weeks);

// b. Calculate IBL
const iblResult = calculator.calculateIBL(history, today);
if (iblResult.error) {
    console.error("IBL Error:", iblResult.error);
} else {
    console.log("Method Used:", iblResult.method);
    console.log("IBL:", iblResult.value);

    // c. Calculate Pension
    const rateResult = calculator.calculateReplacementRate(iblResult.value, weeks, today);
    if (rateResult.error) {
        console.error("Rate Error:", rateResult.error);
    } else {
        console.log("Replacement Rate:", rateResult.rate + "%");
        console.log("Pension (Mesada):", rateResult.pension);
        console.log("Formatted Pension: $ " + new Intl.NumberFormat('es-CO').format(rateResult.pension));
    }
}
