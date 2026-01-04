//! RAC Rust executor - PyO3 bindings for high-performance tax-benefit calculations

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use rayon::prelude::*;
use std::collections::HashMap;

/// Evaluate an expression given variable values
fn eval_expr(expr: &Expr, scalars: &HashMap<String, f64>, row: &HashMap<String, f64>) -> f64 {
    match expr {
        Expr::Literal(v) => *v,
        Expr::Var(name) => {
            if let Some(v) = row.get(name) {
                *v
            } else if let Some(v) = scalars.get(name) {
                *v
            } else {
                0.0
            }
        }
        Expr::BinOp { op, left, right } => {
            let l = eval_expr(left, scalars, row);
            let r = eval_expr(right, scalars, row);
            match op.as_str() {
                "+" => l + r,
                "-" => l - r,
                "*" => l * r,
                "/" => if r != 0.0 { l / r } else { 0.0 },
                ">" => if l > r { 1.0 } else { 0.0 },
                ">=" => if l >= r { 1.0 } else { 0.0 },
                "<" => if l < r { 1.0 } else { 0.0 },
                "<=" => if l <= r { 1.0 } else { 0.0 },
                "==" => if (l - r).abs() < 1e-10 { 1.0 } else { 0.0 },
                _ => 0.0,
            }
        }
        Expr::Call { func, args } => {
            let arg_vals: Vec<f64> = args.iter().map(|a| eval_expr(a, scalars, row)).collect();
            match func.as_str() {
                "min" => arg_vals.iter().cloned().fold(f64::INFINITY, f64::min),
                "max" => arg_vals.iter().cloned().fold(f64::NEG_INFINITY, f64::max),
                "abs" => arg_vals.first().map(|v| v.abs()).unwrap_or(0.0),
                "round" => arg_vals.first().map(|v| v.round()).unwrap_or(0.0),
                _ => 0.0,
            }
        }
        Expr::Cond { cond, then_expr, else_expr } => {
            let c = eval_expr(cond, scalars, row);
            if c != 0.0 {
                eval_expr(then_expr, scalars, row)
            } else {
                eval_expr(else_expr, scalars, row)
            }
        }
    }
}

#[derive(Clone, Debug)]
enum Expr {
    Literal(f64),
    Var(String),
    BinOp { op: String, left: Box<Expr>, right: Box<Expr> },
    Call { func: String, args: Vec<Expr> },
    Cond { cond: Box<Expr>, then_expr: Box<Expr>, else_expr: Box<Expr> },
}

fn parse_expr(py: Python<'_>, obj: &Bound<'_, PyAny>) -> PyResult<Expr> {
    let type_str: String = obj.get_item("type")?.extract()?;

    match type_str.as_str() {
        "literal" => {
            let value: f64 = obj.get_item("value")?.extract()?;
            Ok(Expr::Literal(value))
        }
        "var" => {
            let path: String = obj.get_item("path")?.extract()?;
            Ok(Expr::Var(path))
        }
        "binop" => {
            let op: String = obj.get_item("op")?.extract()?;
            let left = parse_expr(py, &obj.get_item("left")?)?;
            let right = parse_expr(py, &obj.get_item("right")?)?;
            Ok(Expr::BinOp { op, left: Box::new(left), right: Box::new(right) })
        }
        "call" => {
            let func: String = obj.get_item("func")?.extract()?;
            let args_list = obj.get_item("args")?;
            let args_list = args_list.downcast::<PyList>()?;
            let args: Vec<Expr> = args_list.iter()
                .map(|a| parse_expr(py, &a))
                .collect::<PyResult<Vec<_>>>()?;
            Ok(Expr::Call { func, args })
        }
        "cond" => {
            let cond = parse_expr(py, &obj.get_item("cond")?)?;
            let then_expr = parse_expr(py, &obj.get_item("then")?)?;
            let else_expr = parse_expr(py, &obj.get_item("else")?)?;
            Ok(Expr::Cond {
                cond: Box::new(cond),
                then_expr: Box::new(then_expr),
                else_expr: Box::new(else_expr)
            })
        }
        _ => Ok(Expr::Literal(0.0)),
    }
}

#[derive(Clone)]
struct Variable {
    path: String,
    entity: Option<String>,
    expr: Expr,
}

/// Execute IR on entity data using parallel processing
#[pyfunction]
fn execute_fast(
    py: Python<'_>,
    variables: &Bound<'_, PyList>,
    order: &Bound<'_, PyList>,
    entity_name: &str,
    data: &Bound<'_, PyList>,
) -> PyResult<PyObject> {
    // Parse variables
    let mut var_map: HashMap<String, Variable> = HashMap::new();

    for var_obj in variables.iter() {
        let path: String = var_obj.get_item("path")?.extract()?;
        let entity: Option<String> = var_obj.get_item("entity")?.extract().ok();
        let expr = parse_expr(py, &var_obj.get_item("expr")?)?;
        var_map.insert(path.clone(), Variable { path, entity, expr });
    }

    // Get execution order
    let exec_order: Vec<String> = order.iter()
        .map(|o| o.extract::<String>())
        .collect::<PyResult<Vec<_>>>()?;

    // Compute scalars first
    let mut scalars: HashMap<String, f64> = HashMap::new();
    for path in &exec_order {
        if let Some(var) = var_map.get(path) {
            if var.entity.is_none() {
                let val = eval_expr(&var.expr, &scalars, &HashMap::new());
                scalars.insert(path.clone(), val);
            }
        }
    }

    // Parse input data
    let rows: Vec<HashMap<String, f64>> = data.iter()
        .map(|row| {
            let dict = row.downcast::<PyDict>().unwrap();
            dict.iter()
                .filter_map(|(k, v)| {
                    let key: String = k.extract().ok()?;
                    let val: f64 = v.extract().ok()?;
                    Some((key, val))
                })
                .collect()
        })
        .collect();

    // Get entity variables in order
    let entity_vars: Vec<&Variable> = exec_order.iter()
        .filter_map(|path| var_map.get(path))
        .filter(|v| v.entity.as_deref() == Some(entity_name))
        .collect();

    // Process rows in parallel
    let results: Vec<HashMap<String, f64>> = rows.par_iter()
        .map(|row| {
            let mut row_data = row.clone();
            for var in &entity_vars {
                let val = eval_expr(&var.expr, &scalars, &row_data);
                row_data.insert(var.path.clone(), val);
            }
            row_data
        })
        .collect();

    // Convert back to Python
    let py_results = PyList::empty_bound(py);
    for row in results {
        let dict = PyDict::new_bound(py);
        for (k, v) in row {
            dict.set_item(k, v)?;
        }
        py_results.append(dict)?;
    }

    Ok(py_results.into())
}

/// Python module
#[pymodule]
fn rac_rust(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(execute_fast, m)?)?;
    Ok(())
}
