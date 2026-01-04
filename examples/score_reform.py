#!/usr/bin/env python3
"""
Score policy reforms using RAC

This example shows how to:
1. Load a tax-benefit system
2. Create a reform (amendment)
3. Run baseline vs reform on sample data
4. Compute distributional impacts
"""

from datetime import date
from rac import parse, compile, execute

# Load baseline system
with open("examples/uk_tax_benefit.rac") as f:
    baseline_source = f.read()

baseline = parse(baseline_source)


# =============================================================================
# DEFINE A REFORM
# =============================================================================
# Let's test: Raise personal allowance to £15,000 and cut basic rate to 18%

reform_source = """
# Reform: Higher personal allowance, lower basic rate

amend gov/hmrc/it/personal_allowance:
    from 2024-04-06: 15000

amend gov/hmrc/it/basic_rate:
    from 2024-04-06: 0.18
"""

reform = parse(reform_source)


# =============================================================================
# COMPILE BOTH SCENARIOS
# =============================================================================

as_of = date(2024, 6, 1)

ir_baseline = compile([baseline], as_of=as_of)
ir_reform = compile([baseline, reform], as_of=as_of)  # Reform amends baseline


# =============================================================================
# GENERATE SAMPLE POPULATION
# =============================================================================
# Simple synthetic population for demonstration

import random
random.seed(42)

n_people = 10000
n_benefit_units = 5000

# Generate people with income distribution
people = []
for i in range(n_people):
    income = max(0, random.lognormvariate(10.2, 0.7))  # UK-ish distribution
    people.append({
        "id": i,
        "gross_income": income,
        "hours_worked": 35 if income > 15000 else random.uniform(0, 20),
        "is_adult": 1 if i < n_benefit_units * 1.5 else 0,
        "is_child": 1 if i >= n_benefit_units * 1.5 else 0,
    })

# Generate benefit units
benefit_units = []
for i in range(n_benefit_units):
    num_adults = random.choices([1, 2], weights=[0.4, 0.6])[0]
    num_children = random.choices([0, 1, 2, 3], weights=[0.4, 0.25, 0.25, 0.1])[0]

    # Assign earnings (rough)
    base_income = random.lognormvariate(10.2, 0.7) * num_adults * 0.7

    benefit_units.append({
        "id": i,
        "num_adults": num_adults,
        "num_children": num_children,
        "total_earnings": base_income,
        "housing_costs": random.uniform(0, 1200) if random.random() > 0.3 else 0,
    })


# =============================================================================
# RUN SIMULATIONS
# =============================================================================

print("=" * 60)
print("POLICY REFORM ANALYSIS")
print("=" * 60)
print()
print("Reform: PA £12,570 → £15,000, Basic rate 20% → 18%")
print()

# Run baseline
data_person = {"person": people}
data_bu = {"benefit_unit": benefit_units}

result_baseline_person = execute(ir_baseline, data_person)
result_baseline_bu = execute(ir_baseline, data_bu)

result_reform_person = execute(ir_reform, data_person)
result_reform_bu = execute(ir_reform, data_bu)


# =============================================================================
# COMPUTE IMPACTS
# =============================================================================

# Person-level impacts
baseline_it = result_baseline_person.entities["person"]["person/income_tax"]
reform_it = result_reform_person.entities["person"]["person/income_tax"]
baseline_ni = result_baseline_person.entities["person"]["person/national_insurance"]
reform_ni = result_reform_person.entities["person"]["person/national_insurance"]

total_baseline_tax = sum(baseline_it) + sum(baseline_ni)
total_reform_tax = sum(reform_it) + sum(reform_ni)
tax_cut = total_baseline_tax - total_reform_tax

print("FISCAL IMPACT (annualised)")
print("-" * 40)
print(f"Baseline tax revenue:  £{total_baseline_tax/1e6:,.1f}m")
print(f"Reform tax revenue:    £{total_reform_tax/1e6:,.1f}m")
print(f"Revenue change:        £{-tax_cut/1e6:,.1f}m")
print()

# Individual gains
gains = [b - r for b, r in zip(baseline_it, reform_it)]
winners = sum(1 for g in gains if g > 1)
losers = sum(1 for g in gains if g < -1)

print("WINNERS AND LOSERS")
print("-" * 40)
print(f"Winners (gain >£1):    {winners:,} ({winners/n_people*100:.1f}%)")
print(f"Losers (lose >£1):     {losers:,} ({losers/n_people*100:.1f}%)")
print(f"Unchanged:             {n_people - winners - losers:,}")
print()

# Distributional analysis by income decile
print("DISTRIBUTIONAL ANALYSIS (by income decile)")
print("-" * 40)

# Sort people by income and split into deciles
sorted_indices = sorted(range(n_people), key=lambda i: people[i]["gross_income"])
decile_size = n_people // 10

print(f"{'Decile':<8} {'Avg Income':>12} {'Avg Gain':>12} {'% Winners':>10}")
for d in range(10):
    start = d * decile_size
    end = (d + 1) * decile_size if d < 9 else n_people
    indices = sorted_indices[start:end]

    avg_income = sum(people[i]["gross_income"] for i in indices) / len(indices)
    avg_gain = sum(gains[i] for i in indices) / len(indices)
    pct_winners = sum(1 for i in indices if gains[i] > 1) / len(indices) * 100

    print(f"{d+1:<8} £{avg_income:>10,.0f} £{avg_gain:>10,.0f} {pct_winners:>9.0f}%")

print()

# Benefit unit impacts
baseline_uc = result_baseline_bu.entities["benefit_unit"]["benefit_unit/universal_credit"]
reform_uc = result_reform_bu.entities["benefit_unit"]["benefit_unit/universal_credit"]
baseline_cb = result_baseline_bu.entities["benefit_unit"]["benefit_unit/child_benefit"]
reform_cb = result_reform_bu.entities["benefit_unit"]["benefit_unit/child_benefit"]

total_baseline_uc = sum(baseline_uc)
total_reform_uc = sum(reform_uc)

print("BENEFIT IMPACTS")
print("-" * 40)
print(f"Baseline UC spend:     £{total_baseline_uc/1e6:,.1f}m")
print(f"Reform UC spend:       £{total_reform_uc/1e6:,.1f}m")
print(f"UC change:             £{(total_reform_uc - total_baseline_uc)/1e6:,.1f}m")
print()

# Summary
net_cost = tax_cut + (total_reform_uc - total_baseline_uc)
print("=" * 60)
print(f"NET FISCAL COST:       £{net_cost/1e6:,.1f}m")
print("=" * 60)
