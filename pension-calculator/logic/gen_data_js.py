import json

# Historic SMMLV
smmlv_data = [
    { "year": 1980, "value": 4500 }, { "year": 1981, "value": 5700 }, { "year": 1982, "value": 7410 },
    { "year": 1983, "value": 9261 }, { "year": 1984, "value": 11298 }, { "year": 1985, "value": 13558 },
    { "year": 1986, "value": 16811 }, { "year": 1987, "value": 20510 }, { "year": 1988, "value": 25637 },
    { "year": 1989, "value": 32560 }, { "year": 1990, "value": 41025 }, { "year": 1991, "value": 51720 },
    { "year": 1992, "value": 65190 }, { "year": 1993, "value": 81510 }, { "year": 1994, "value": 98700 },
    { "year": 1995, "value": 118934 }, { "year": 1996, "value": 142125 }, { "year": 1997, "value": 172005 },
    { "year": 1998, "value": 203826 }, { "year": 1999, "value": 236460 }, { "year": 2000, "value": 260100 },
    { "year": 2001, "value": 286000 }, { "year": 2002, "value": 309000 }, { "year": 2003, "value": 332000 },
    { "year": 2004, "value": 358000 }, { "year": 2005, "value": 381500 }, { "year": 2006, "value": 408000 },
    { "year": 2007, "value": 433700 }, { "year": 2008, "value": 461500 }, { "year": 2009, "value": 496900 },
    { "year": 2010, "value": 515000 }, { "year": 2011, "value": 535600 }, { "year": 2012, "value": 566700 },
    { "year": 2013, "value": 589500 }, { "year": 2014, "value": 616000 }, { "year": 2015, "value": 644350 },
    { "year": 2016, "value": 689455 }, { "year": 2017, "value": 737717 }, { "year": 2018, "value": 781242 },
    { "year": 2019, "value": 828116 }, { "year": 2020, "value": 877803 }, { "year": 2021, "value": 908526 },
    { "year": 2022, "value": 1000000 }, { "year": 2023, "value": 1160000 }, { "year": 2024, "value": 1300000 },
    { "year": 2025, "value": 1423500 }
]

# Annual Inflation Rates (Approx)
inflation_rates = {
    1995: 19.46, 1996: 21.63, 1997: 17.68, 1998: 16.70, 1999: 9.23,
    2000: 8.75, 2001: 7.65, 2002: 6.99, 2003: 6.49, 2004: 5.50,
    2005: 4.85, 2006: 4.48, 2007: 5.69, 2008: 7.67, 2009: 2.00,
    2010: 3.17, 2011: 3.73, 2012: 2.44, 2013: 1.94, 2014: 3.66,
    2015: 6.77, 2016: 5.75, 2017: 4.09, 2018: 3.18, 2019: 3.80,
    2020: 1.61, 2021: 5.62, 2022: 13.12, 2023: 9.28, 2024: 5.5,
    2025: 4.0 # Projected
}

# Generate Monthly IPC
# Base 2008 = 100? Or just chaining.
# Let's start with an arbitrary base in 1995 and compound.
current_ipc = 10.0
ipc_data = []

for year in range(1995, 2026):
    rate = inflation_rates.get(year, 3.0) / 100.0
    monthly_rate = (1 + rate)**(1/12) - 1
    
    for month in range(1, 13):
        current_ipc *= (1 + monthly_rate)
        ipc_data.append({
            "year": year,
            "month": month,
            "value": round(current_ipc, 2)
        })

data = {
    "smmlv": smmlv_data,
    "ipc": ipc_data,
    "contributionRates": [
        { "startYear": 1967, "endYear": 1993, "rate": 0.10 },
        { "startYear": 1994, "endYear": 1995, "rate": 0.115 },
        { "startYear": 1996, "endYear": 2003, "rate": 0.135 },
        { "startYear": 2004, "endYear": 2007, "rate": 0.145 },
        { "startYear": 2008, "endYear": 2025, "rate": 0.16 }
    ]
}

js_content = f"window.calculatorData = {json.dumps(data, indent=2)};"

with open("data.js", "w") as f:
    f.write(js_content)

print("data.js generated successfully with", len(ipc_data), "IPC records.")
