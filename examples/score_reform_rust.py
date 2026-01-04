#!/usr/bin/env python3
"""
Generate Rust code that scores baseline vs reform
"""

from datetime import date
from rac import parse, compile
from rac.codegen.rust import generate_rust

# Load baseline
with open("examples/uk_tax_benefit.rac") as f:
    baseline_source = f.read()

baseline = parse(baseline_source)

# Define reform
reform_source = """
amend gov/hmrc/it/personal_allowance:
    from 2024-04-06: 15000

amend gov/hmrc/it/basic_rate:
    from 2024-04-06: 0.18
"""
reform = parse(reform_source)

# Compile both
as_of = date(2024, 6, 1)
ir_baseline = compile([baseline], as_of=as_of)
ir_reform = compile([baseline, reform], as_of=as_of)

# Generate Rust for both (with different struct names)
class RustReformGenerator:
    def __init__(self, ir_baseline, ir_reform):
        self.ir_baseline = ir_baseline
        self.ir_reform = ir_reform

    def generate(self):
        from rac.codegen.rust import RustGenerator

        # Generate baseline
        baseline_gen = RustGenerator(self.ir_baseline, "baseline")
        reform_gen = RustGenerator(self.ir_reform, "reform")

        lines = ["//! Policy reform scoring - baseline vs reform", ""]

        # Input structs (same for both)
        for entity in self.ir_baseline.schema_.entities.values():
            lines.extend(baseline_gen._gen_input_struct(entity))
            lines.append("")

        # Baseline output structs
        for entity_name, var_paths in baseline_gen.entity_vars.items():
            struct_lines = baseline_gen._gen_output_struct(entity_name, var_paths)
            # Rename to BaselineXOutput
            struct_lines = [l.replace(f"{baseline_gen._rust_type_name(entity_name)}Output",
                                      f"Baseline{baseline_gen._rust_type_name(entity_name)}Output")
                          for l in struct_lines]
            lines.extend(struct_lines)
            lines.append("")

        # Reform output structs
        for entity_name, var_paths in reform_gen.entity_vars.items():
            struct_lines = reform_gen._gen_output_struct(entity_name, var_paths)
            struct_lines = [l.replace(f"{reform_gen._rust_type_name(entity_name)}Output",
                                      f"Reform{reform_gen._rust_type_name(entity_name)}Output")
                          for l in struct_lines]
            lines.extend(struct_lines)
            lines.append("")

        # Baseline scalars
        scalar_lines = baseline_gen._gen_scalars_struct()
        scalar_lines = [l.replace("Scalars", "BaselineScalars") for l in scalar_lines]
        lines.extend(scalar_lines)
        lines.append("")

        compute_lines = baseline_gen._gen_compute_scalars()
        compute_lines = [l.replace("Scalars", "BaselineScalars") for l in compute_lines]
        lines.extend(compute_lines)
        lines.append("")

        # Reform scalars
        scalar_lines = reform_gen._gen_scalars_struct()
        scalar_lines = [l.replace("Scalars", "ReformScalars") for l in scalar_lines]
        lines.extend(scalar_lines)
        lines.append("")

        compute_lines = reform_gen._gen_compute_scalars()
        compute_lines = [l.replace("Scalars", "ReformScalars") for l in compute_lines]
        lines.extend(compute_lines)
        lines.append("")

        # Baseline entity compute
        for entity_name in baseline_gen.entity_vars:
            entity_lines = baseline_gen._gen_compute_entity(entity_name)
            type_name = baseline_gen._rust_type_name(entity_name)
            entity_lines = [l.replace(f"{type_name}Output", f"Baseline{type_name}Output")
                              .replace("Scalars", "BaselineScalars")
                          for l in entity_lines]
            lines.extend(entity_lines)
            lines.append("")

        # Reform entity compute
        for entity_name in reform_gen.entity_vars:
            entity_lines = reform_gen._gen_compute_entity(entity_name)
            type_name = reform_gen._rust_type_name(entity_name)
            entity_lines = [l.replace(f"{type_name}Output", f"Reform{type_name}Output")
                              .replace("Scalars", "ReformScalars")
                          for l in entity_lines]
            lines.extend(entity_lines)
            lines.append("")

        return "\n".join(lines)

gen = RustReformGenerator(ir_baseline, ir_reform)
rust_code = gen.generate()

main_code = '''
use std::time::Instant;

fn main() {
    let baseline_scalars = BaselineScalars::compute();
    let reform_scalars = ReformScalars::compute();

    // Generate 1M people
    let n = 1_000_000;
    let mut people: Vec<PersonInput> = Vec::with_capacity(n);

    let mut seed: u64 = 42;
    for _ in 0..n {
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
    }

    println!("============================================================");
    println!("POLICY REFORM SCORING (Rust)");
    println!("============================================================");
    println!();
    println!("Reform: PA £12,570 -> £15,000, Basic rate 20% -> 18%");
    println!("Population: {} people", n);
    println!();

    let start = Instant::now();

    // Run baseline
    let baseline_results: Vec<BaselinePersonOutput> = people.iter()
        .map(|p| BaselinePersonOutput::compute(p, &baseline_scalars))
        .collect();

    // Run reform
    let reform_results: Vec<ReformPersonOutput> = people.iter()
        .map(|p| ReformPersonOutput::compute(p, &reform_scalars))
        .collect();

    let elapsed = start.elapsed();

    // Aggregate
    let baseline_tax: f64 = baseline_results.iter()
        .map(|p| p.person_income_tax + p.person_national_insurance)
        .sum();
    let reform_tax: f64 = reform_results.iter()
        .map(|p| p.person_income_tax + p.person_national_insurance)
        .sum();

    // Winners/losers
    let mut winners = 0u64;
    let mut total_gain = 0.0f64;
    let mut max_gain = 0.0f64;

    for (b, r) in baseline_results.iter().zip(reform_results.iter()) {
        let gain = (b.person_income_tax - r.person_income_tax)
                 + (b.person_national_insurance - r.person_national_insurance);
        if gain > 1.0 { winners += 1; }
        total_gain += gain;
        if gain > max_gain { max_gain = gain; }
    }

    // Decile analysis
    let mut indexed: Vec<(usize, f64)> = people.iter()
        .enumerate()
        .map(|(i, p)| (i, p.gross_income))
        .collect();
    indexed.sort_by(|a, b| a.1.partial_cmp(&b.1).unwrap());

    println!("Done in {:.2?} ({:.0} comparisons/sec)", elapsed, (n * 2) as f64 / elapsed.as_secs_f64());
    println!();
    println!("FISCAL IMPACT");
    println!("----------------------------------------");
    println!("Baseline revenue:  £{:.2}bn", baseline_tax / 1e9);
    println!("Reform revenue:    £{:.2}bn", reform_tax / 1e9);
    println!("Revenue change:    £{:.2}bn", (reform_tax - baseline_tax) / 1e9);
    println!();
    println!("WINNERS AND LOSERS");
    println!("----------------------------------------");
    println!("Winners (gain >£1): {:>8} ({:.1}%)", winners, winners as f64 / n as f64 * 100.0);
    println!("Average gain:       £{:.0}", total_gain / n as f64);
    println!("Max gain:           £{:.0}", max_gain);
    println!();
    println!("DISTRIBUTIONAL ANALYSIS (by income decile)");
    println!("----------------------------------------");
    println!("{:<8} {:>12} {:>12} {:>10}", "Decile", "Avg Income", "Avg Gain", "% Winners");

    let decile_size = n / 10;
    for d in 0..10 {
        let start_idx = d * decile_size;
        let end_idx = if d == 9 { n } else { (d + 1) * decile_size };

        let mut decile_income = 0.0f64;
        let mut decile_gain = 0.0f64;
        let mut decile_winners = 0u64;

        for i in start_idx..end_idx {
            let idx = indexed[i].0;
            decile_income += people[idx].gross_income;
            let gain = (baseline_results[idx].person_income_tax - reform_results[idx].person_income_tax)
                     + (baseline_results[idx].person_national_insurance - reform_results[idx].person_national_insurance);
            decile_gain += gain;
            if gain > 1.0 { decile_winners += 1; }
        }

        let count = (end_idx - start_idx) as f64;
        println!("{:<8} £{:>10.0} £{:>10.0} {:>9.0}%",
            d + 1,
            decile_income / count,
            decile_gain / count,
            decile_winners as f64 / count * 100.0);
    }
    println!();
    println!("============================================================");
}
'''

print(rust_code)
print(main_code)
