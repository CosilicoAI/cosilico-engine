"""Native compilation for maximum performance (97M/sec).

Automatically downloads Rust toolchain if needed, compiles IR to native binary.
"""

import hashlib
import json
import os
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .compiler import IR
from .codegen.rust import generate_rust

CACHE_DIR = Path.home() / ".cache" / "rac"
RUSTUP_URL = "https://sh.rustup.rs"


def _get_cargo() -> Path | None:
    """Find cargo binary."""
    cargo = shutil.which("cargo")
    if cargo:
        return Path(cargo)

    cargo_home = Path.home() / ".cargo" / "bin" / "cargo"
    if cargo_home.exists():
        return cargo_home

    return None


def _install_rust() -> Path:
    """Install Rust via rustup."""
    print("Installing Rust toolchain (one-time setup)...")

    if platform.system() == "Windows":
        import urllib.request
        rustup_init = CACHE_DIR / "rustup-init.exe"
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve("https://win.rustup.rs/x86_64", rustup_init)
        subprocess.run([str(rustup_init), "-y", "--quiet"], check=True)
    else:
        subprocess.run(
            ["sh", "-c", f"curl --proto '=https' --tlsv1.2 -sSf {RUSTUP_URL} | sh -s -- -y --quiet"],
            check=True,
            capture_output=True
        )

    cargo = Path.home() / ".cargo" / "bin" / "cargo"
    if not cargo.exists():
        raise RuntimeError("Failed to install Rust")

    print("Rust installed successfully")
    return cargo


def ensure_cargo() -> Path:
    """Ensure cargo is available, installing if needed."""
    cargo = _get_cargo()
    if cargo:
        return cargo
    return _install_rust()


def _ir_hash(ir: IR) -> str:
    """Hash IR for caching."""
    data = json.dumps({
        "order": ir.order,
        "vars": {k: str(v.expr) for k, v in ir.variables.items()}
    }, sort_keys=True)
    return hashlib.sha256(data.encode()).hexdigest()[:16]


class CompiledBinary:
    """A compiled RAC binary for maximum performance."""

    def __init__(self, binary_path: Path, ir: IR):
        self.binary_path = binary_path
        self.ir = ir

    def run(self, data: dict[str, list[dict]]) -> dict[str, list[dict]]:
        """Run the binary on data and return results."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            input_path = f.name

        output_path = tempfile.mktemp(suffix='.json')

        try:
            result = subprocess.run(
                [str(self.binary_path), input_path, output_path],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                raise RuntimeError(f"Binary failed: {result.stderr}")

            with open(output_path) as f:
                return json.load(f)
        finally:
            os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)


def compile_to_binary(ir: IR, cache: bool = True) -> CompiledBinary:
    """Compile IR to native binary for maximum performance.

    Args:
        ir: Compiled IR from rac.compile()
        cache: Cache compiled binaries (default True)

    Returns:
        CompiledBinary that can run data at ~100M rows/sec

    Example:
        >>> from rac import parse, compile
        >>> from rac.native import compile_to_binary
        >>>
        >>> module = parse(open('rules.rac').read())
        >>> ir = compile([module], as_of=date(2024, 6, 1))
        >>> binary = compile_to_binary(ir)
        >>>
        >>> result = binary.run({'person': [{'income': 50000}, ...]})
    """
    cargo = ensure_cargo()

    ir_hash = _ir_hash(ir)
    project_dir = CACHE_DIR / "projects" / ir_hash

    binary_name = "rac_native.exe" if platform.system() == "Windows" else "rac_native"
    binary_path = project_dir / "target" / "release" / binary_name

    if cache and binary_path.exists():
        return CompiledBinary(binary_path, ir)

    # Create Cargo project
    project_dir.mkdir(parents=True, exist_ok=True)

    # Cargo.toml
    (project_dir / "Cargo.toml").write_text('''[package]
name = "rac_native"
version = "0.1.0"
edition = "2021"

[dependencies]
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
rayon = "1.10"

[profile.release]
lto = true
codegen-units = 1
''')

    # Generate Rust code
    rust_code = generate_rust(ir)
    main_code = _generate_main(ir)

    src_dir = project_dir / "src"
    src_dir.mkdir(exist_ok=True)
    (src_dir / "main.rs").write_text(rust_code + "\n" + main_code)

    # Build
    print("Compiling native binary...")
    result = subprocess.run(
        [str(cargo), "build", "--release", "--quiet"],
        cwd=project_dir,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed:\n{result.stderr}")

    print("Compilation complete")
    return CompiledBinary(binary_path, ir)


def _generate_main(ir: IR) -> str:
    """Generate main function with JSON I/O."""
    entities = {}
    for path in ir.order:
        var = ir.variables[path]
        if var.entity:
            if var.entity not in entities:
                entities[var.entity] = []
            entities[var.entity].append(path)

    # Generate struct derives and input parsing
    input_structs = []
    entity_processing = []
    output_building = []

    for entity_name, var_paths in entities.items():
        type_name = "".join(part.capitalize() for part in entity_name.split("_"))
        safe_name = entity_name.replace("-", "_").replace("/", "_")

        # Get fields from schema with types
        fields = []
        field_types = {}
        if entity_name in ir.schema_.entities:
            for fname, fdef in ir.schema_.entities[entity_name].fields.items():
                fields.append(fname)
                field_types[fname] = fdef.dtype

        # Type mapping for JSON
        def json_type(dtype: str) -> str:
            return {"int": "i64", "float": "f64", "str": "String", "bool": "bool"}.get(dtype, "f64")

        # Input struct with serde
        field_defs = "\n    ".join(f"pub {f}: {json_type(field_types.get(f, 'float'))}," for f in fields)
        input_structs.append(f'''
#[derive(Debug, Deserialize)]
struct {type_name}JsonInput {{
    {field_defs}
}}''')

        # Parse and process
        field_copies = ", ".join(f"{f}: inp.{f}" for f in fields)
        entity_processing.append(f'''
    let {safe_name}_inputs: Vec<{type_name}JsonInput> = input.get("{entity_name}")
        .and_then(|v| serde_json::from_value(v.clone()).ok())
        .unwrap_or_default();

    let {safe_name}_outputs: Vec<{type_name}Output> = {safe_name}_inputs
        .par_iter()
        .map(|inp| {{
            let input = {type_name}Input {{ {field_copies} }};
            {type_name}Output::compute(&input, &scalars)
        }})
        .collect();''')

        # Output JSON
        output_fields = []
        for p in var_paths:
            safe_p = p.replace("/", "_")
            output_fields.append(f'"{p}": o.{safe_p}')

        output_building.append(f'''
    let {safe_name}_json: Vec<serde_json::Value> = {safe_name}_outputs
        .iter()
        .zip({safe_name}_inputs.iter())
        .map(|(o, inp)| {{
            serde_json::json!({{
                {", ".join(output_fields)}
            }})
        }})
        .collect();
    output.insert("{entity_name}".to_string(), serde_json::json!({safe_name}_json));''')

    return f'''
use rayon::prelude::*;
use serde::Deserialize;
use std::collections::HashMap;
use std::env;
use std::fs;

{chr(10).join(input_structs)}

fn main() {{
    let args: Vec<String> = env::args().collect();
    if args.len() != 3 {{
        eprintln!("Usage: {{}} <input.json> <output.json>", args[0]);
        std::process::exit(1);
    }}

    let input_str = fs::read_to_string(&args[1]).expect("Failed to read input");
    let input: HashMap<String, serde_json::Value> = serde_json::from_str(&input_str).expect("Invalid JSON");

    let scalars = Scalars::compute();
    let mut output: HashMap<String, serde_json::Value> = HashMap::new();

    {chr(10).join(entity_processing)}
    {chr(10).join(output_building)}

    let output_str = serde_json::to_string(&output).expect("Failed to serialize");
    fs::write(&args[2], output_str).expect("Failed to write output");
}}
'''
