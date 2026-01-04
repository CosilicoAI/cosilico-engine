#!/usr/bin/env python3
"""
Compile RAC to Rust for high-performance scoring

Generates a complete Rust binary that can score millions of households/sec.
"""

from datetime import date
from rac import parse, compile
from rac.codegen.rust import generate_rust

# Load baseline
with open("examples/uk_tax_benefit.rac") as f:
    baseline_source = f.read()

baseline = parse(baseline_source)

# Compile to IR
ir = compile([baseline], as_of=date(2024, 6, 1))

# Generate Rust
rust_code = generate_rust(ir)

# Add main function for benchmarking
main_code = '''
use std::time::Instant;

fn main() {
    let scalars = Scalars::compute();

    // Generate 1M households
    let n = 1_000_000;
    let mut people: Vec<PersonInput> = Vec::with_capacity(n);
    let mut benefit_units: Vec<BenefitUnitInput> = Vec::with_capacity(n / 2);

    let mut seed: u64 = 42;
    for i in 0..n {
        seed = seed.wrapping_mul(6364136223846793005).wrapping_add(1);
        let u1 = (seed >> 33) as f64 / (1u64 << 31) as f64;
        seed = seed.wrapping_mul(6364136223846793005).wrapping_add(1);
        let u2 = (seed >> 33) as f64 / (1u64 << 31) as f64;
        let z = (-2.0 * u1.ln()).sqrt() * (2.0 * std::f64::consts::PI * u2).cos();
        let income = (10.2 + 0.7 * z).exp().max(0.0).min(500000.0);

        people.push(PersonInput {
            gross_income: income,
            hours_worked: if income > 15000.0 { 35.0 } else { u1 * 20.0 },
            is_adult: 1.0,
            is_child: 0.0,
        });

        if i % 2 == 0 {
            let num_adults = if u1 > 0.4 { 2.0 } else { 1.0 };
            let num_children = ((u2 * 4.0) as i32).min(3) as f64;
            benefit_units.push(BenefitUnitInput {
                num_adults,
                num_children,
                total_earnings: income * num_adults * 0.7,
                housing_costs: if u1 > 0.3 { u2 * 1200.0 } else { 0.0 },
            });
        }
    }

    println!("Scoring {} people, {} benefit units...", people.len(), benefit_units.len());

    let start = Instant::now();

    let person_results: Vec<PersonOutput> = people.iter()
        .map(|p| PersonOutput::compute(p, &scalars))
        .collect();

    let bu_results: Vec<BenefitUnitOutput> = benefit_units.iter()
        .map(|bu| BenefitUnitOutput::compute(bu, &scalars))
        .collect();

    let elapsed = start.elapsed();

    // Aggregate results
    let total_it: f64 = person_results.iter().map(|p| p.person_income_tax).sum();
    let total_ni: f64 = person_results.iter().map(|p| p.person_national_insurance).sum();
    let total_uc: f64 = bu_results.iter().map(|bu| bu.benefit_unit_universal_credit).sum();
    let total_cb: f64 = bu_results.iter().map(|bu| bu.benefit_unit_child_benefit).sum();

    println!("Done in {:.2?} ({:.0} people/sec)", elapsed, people.len() as f64 / elapsed.as_secs_f64());
    println!();
    println!("=== Tax Revenue ===");
    println!("Income tax:  £{:.2}bn", total_it / 1e9);
    println!("NICs:        £{:.2}bn", total_ni / 1e9);
    println!();
    println!("=== Benefit Spend ===");
    println!("UC:          £{:.2}bn", total_uc / 1e9);
    println!("Child Ben:   £{:.2}bn", total_cb / 1e9);
}
'''

# Output
output = rust_code + main_code

print("// Compile with: rustc -O uk_tax_benefit.rs -o uk_tax_benefit")
print("// Run with: ./uk_tax_benefit")
print()
print(output)
