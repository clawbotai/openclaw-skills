from solve_pension_gap import simulate_pension

# Helper to inspect the natural rate for 3 years ($15.6M IBC)
# We need to temporarily disable the "force 80%" in solve_pension_gap or just copy logic here.
# Easier to just monkey-patch or copy the logic since solve_pension_gap now has the override hardcoded.

import pandas as pd
import datetime
import json
import re

# ... (Copying minimal logic for verification) ...
# Actually, I can just write a fresh standalone checker to be safe and clean.
# Using values from Step 507 (Boosted, Standard):
# IBC: 15670885
# Weeks Baseline: 1823

SMMLV_2025 = 1423500
IBC = 15670885
MONTHS_ADDED = 36
WEEKS_BASE = 1823
# Future weeks = 36 * 4.2857 = 154
TOTAL_WEEKS = WEEKS_BASE + 154 # ~1977

# 1. Calculate Rate based on this IBC being the IBL (Simplified for rate check)
# In reality IBL != IBC, but let's assume IBL ~ IBC for the "Rate Formula" impact check
# or better, use the IBL from the log? 
# Log 507 just said "Final Pension $9.99M".
# $9.99M / 80% = $12.5M IBL.
# IBC is $15.6M. The IBL is lower because of averaging with history.

# Let's check Rate Formula for IBL = $12.5M
IBL = 12_500_000

# s = IBL / SMMLV
s = IBL / SMMLV_2025 # ~8.78
r_formula = 65.5 - (0.5 * s) # 65.5 - 4.39 = ~61.1

# Weeks Bonus
extra_weeks = TOTAL_WEEKS - 1300 # ~677
blocks = int(extra_weeks / 50) # 13
bonus = blocks * 1.5 # 19.5

total_r = r_formula + bonus # 61.1 + 19.5 = 80.6%
# Capped at 80%

print(f"Natural Rate Check:")
print(f"  Weeks: {TOTAL_WEEKS}")
print(f"  IBL Approx: ${IBL:,.0f} (s={s:.2f})")
print(f"  Formula R: {r_formula:.2f}%")
print(f"  Bonus: +{bonus}%")
print(f"  Total: {total_r:.2f}% (Capped at 80%)")
