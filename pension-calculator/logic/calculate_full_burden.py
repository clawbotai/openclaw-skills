
# Constants for Independent/Voluntary Contributors
PENSION_RATE = 0.16
HEALTH_RATE = 0.125
ARL_1_RATE = 0.00522 # Risk Level 1

# Boosted Scenarios for Piedad (Assumed 80% Rate)
scenarios = [
    {"years": 1, "ibc": 27992947},
    {"years": 2, "ibc": 18751400},
    {"years": 3, "ibc": 15670885},
    {"years": 5, "ibc": 13649296},
]

print(f"{'Plan':^10} | {'IBC (Base)':^14} | {'Pension (16%)':^14} | {'Salud (12.5%)':^14} | {'ARL 1 (0.522%)':^14} | {'TOTAL MONTHLY':^18}")
print("-" * 100)

for s in scenarios:
    ibc = s['ibc']
    
    val_pension = ibc * PENSION_RATE
    val_health = ibc * HEALTH_RATE
    val_arl = ibc * ARL_1_RATE
    
    total_monthly = val_pension + val_health + val_arl
    
    print(f"{s['years']} Years   | ${ibc:,.0f} | ${val_pension:,.0f} | ${val_health:,.0f} | ${val_arl:,.0f} | ${total_monthly:,.0f}")
