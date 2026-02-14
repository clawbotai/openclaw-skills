
# Salary Bases from Piedad's simulation
scenarios = [
    {"years": 3, "months": 36, "salary_base": 28859342},
    {"years": 5, "months": 60, "salary_base": 18655134},
    {"years": 10, "months": 120, "salary_base": 12999500},
]

print(f"{'Time':^10} | {'Base Salary':^15} | {'Monthly Payment (16%)':^22} | {'Total Cost (Full Period)':^25}")
print("-" * 80)

for s in scenarios:
    base = s['salary_base']
    monthly_cost = base * 0.16 # Pension contribution is usually 16%
    total_cost = monthly_cost * s['months']
    
    print(f"{s['years']} Years   | ${base:,.0f} | ${monthly_cost:,.0f} / mo      | ${total_cost:,.0f}")
