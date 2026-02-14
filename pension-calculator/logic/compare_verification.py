
# Data from previous runs (verified from logs)

# 1. Original Piedad (Pre-Boost, Standard Rate)
# From Step 481
original_3yr_ibc = 28859342
original_3yr_cost = 8375558

original_5yr_ibc = 18655134
original_5yr_cost = 5414093

# 2. Current Piedad (Boosted + 80% Rate)
# From Step 584
current_3yr_ibc = 15670885
current_3yr_cost = 4548004

current_5yr_ibc = 13649296
current_5yr_cost = 3961299

print(f"{'Metric':^20} | {'3-Year Plan (Original)':^25} | {'3-Year Plan (Boosted)':^25} | {'SAVINGS':^15}")
print("-" * 90)
print(f"{'Required IBC':^20} | ${original_3yr_ibc:^24,.0f} | ${current_3yr_ibc:^24,.0f} | -${original_3yr_ibc - current_3yr_ibc:,.0f}")
print(f"{'Monthly Cost':^20} | ${original_3yr_cost:^24,.0f} | ${current_3yr_cost:^24,.0f} | -${original_3yr_cost - current_3yr_cost:,.0f}")

print("\n")

print(f"{'Metric':^20} | {'5-Year Plan (Original)':^25} | {'5-Year Plan (Boosted)':^25} | {'SAVINGS':^15}")
print("-" * 90)
print(f"{'Required IBC':^20} | ${original_5yr_ibc:^24,.0f} | ${current_5yr_ibc:^24,.0f} | -${original_5yr_ibc - current_5yr_ibc:,.0f}")
print(f"{'Monthly Cost':^20} | ${original_5yr_cost:^24,.0f} | ${current_5yr_cost:^24,.0f} | -${original_5yr_cost - current_5yr_cost:,.0f}")
