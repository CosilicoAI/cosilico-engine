# Appendix: Provision Details

This appendix lists all provisions in the study with their statutory text, complexity scores, and encoding results.

## Phase 1: Simple Provisions

### 1. EITC Phase-In (26 USC § 32(a)(1))

**Complexity Score:** 2
- Conditionals: 0
- Parameters: 2 (phase_in_rate, earned_income_amount)
- References: 1 (earned_income)
- Nesting: 0

**Statutory Text:**
> In the case of an eligible individual, there shall be allowed as a credit against the tax imposed by this subtitle for the taxable year an amount equal to the credit percentage of so much of the taxpayer's earned income for the taxable year as does not exceed the earned income amount.

**Result:** TBD

---

### 2. Standard Deduction (26 USC § 63(c))

**Complexity Score:** 3
- Conditionals: 1 (filing status switch)
- Parameters: 4 (amounts by filing status)
- References: 0
- Nesting: 0

**Statutory Text:**
> For purposes of this subtitle, the term "standard deduction" means the sum of—
> (A) the basic standard deduction, and
> (B) the additional standard deduction.

**Result:** TBD

---

### 3. Child Tax Credit Base (26 USC § 24(a))

**Complexity Score:** 2
- Conditionals: 0
- Parameters: 1 (credit amount)
- References: 1 (qualifying children)
- Nesting: 0

**Statutory Text:**
> There shall be allowed as a credit against the tax imposed by this chapter for the taxable year with respect to each qualifying child of the taxpayer for which the taxpayer is allowed a deduction under section 151 an amount equal to $1,000.

**Result:** TBD

---

### 4. Personal Exemption (26 USC § 151) [Historical]

**Complexity Score:** 2
- Conditionals: 0
- Parameters: 1 (exemption amount)
- References: 1 (dependents)
- Nesting: 0

**Statutory Text:**
> In the case of an individual, the exemptions provided by this section shall be allowed as deductions in computing taxable income.

**Result:** TBD

---

### 5. SALT Deduction Cap (26 USC § 164(b)(6))

**Complexity Score:** 2
- Conditionals: 0
- Parameters: 1 (cap amount)
- References: 1 (state_and_local_taxes)
- Nesting: 0

**Statutory Text:**
> In the case of an individual, the aggregate amount of taxes taken into account under paragraphs (1), (2), and (3) of subsection (a) and paragraph (5) of this subsection for any taxable year shall not exceed $10,000.

**Result:** TBD

---

## Phase 2: Medium Provisions

### 6. Full EITC (26 USC § 32)

**Complexity Score:** 6
- Conditionals: 3 (phase-in, plateau, phase-out)
- Parameters: 6 (rates, amounts, thresholds)
- References: 2 (earned_income, AGI)
- Nesting: 0

**Result:** 100% accuracy, 6 iterations (preliminary)

---

### 7. Child and Dependent Care Credit (26 USC § 21)

**Complexity Score:** 5
- Conditionals: 2 (AGI brackets, expense limits)
- Parameters: 4 (rates, limits)
- References: 2 (AGI, care expenses)
- Nesting: 0

**Result:** TBD

---

### 8. Premium Tax Credit (26 USC § 36B)

**Complexity Score:** 6
- Conditionals: 2 (income eligibility, subsidy phase-out)
- Parameters: 5 (FPL thresholds, applicable percentages)
- References: 3 (household income, SLCSP, enrollment)
- Nesting: 0

**Result:** TBD

---

### 9. Saver's Credit (26 USC § 25B)

**Complexity Score:** 4
- Conditionals: 1 (income brackets)
- Parameters: 3 (credit rates by AGI)
- References: 2 (AGI, retirement contributions)
- Nesting: 0

**Result:** TBD

---

### 10. Adoption Credit (26 USC § 23)

**Complexity Score:** 5
- Conditionals: 2 (domestic vs. foreign, phase-out)
- Parameters: 4 (max credit, phase-out thresholds)
- References: 2 (qualified expenses, AGI)
- Nesting: 0

**Result:** TBD

---

## Phase 3: Complex Provisions

### 11. Alternative Minimum Tax (26 USC § 55-59)

**Complexity Score:** 12
- Conditionals: 5+ (exemption phase-out, rate brackets, preferences)
- Parameters: 8+ (exemption, phase-out, rates)
- References: 5+ (regular tax, itemized deductions, etc.)
- Nesting: 2

**Result:** TBD

---

### 12. Net Investment Income Tax (26 USC § 1411)

**Complexity Score:** 7
- Conditionals: 2 (threshold by filing status, income type)
- Parameters: 3 (rate, thresholds)
- References: 4 (NII, MAGI, threshold)
- Nesting: 1

**Result:** TBD

---

### 13. Social Security Benefit Taxation (26 USC § 86)

**Complexity Score:** 8
- Conditionals: 3 (0%, 50%, 85% inclusion tiers)
- Parameters: 4 (base amounts by filing status)
- References: 3 (benefits, combined income)
- Nesting: 1

**Result:** TBD

---

### 14. Qualified Business Income Deduction (26 USC § 199A)

**Complexity Score:** 10
- Conditionals: 4+ (SSTB rules, wage/basis limits, phase-outs)
- Parameters: 6+ (thresholds, limits)
- References: 4+ (QBI, W-2 wages, UBIA)
- Nesting: 2

**Result:** TBD

---

### 15. Foreign Tax Credit (26 USC § 27)

**Complexity Score:** 9
- Conditionals: 3 (limitation categories, carryover)
- Parameters: 5 (limits, baskets)
- References: 5 (foreign taxes, foreign income, total income)
- Nesting: 1

**Result:** TBD
