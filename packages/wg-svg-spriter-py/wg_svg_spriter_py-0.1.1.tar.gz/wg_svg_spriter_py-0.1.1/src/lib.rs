use std::collections::HashMap;

use pyo3::prelude::*;

use optimize::optimize;

mod optimize;
mod spriter;

#[pyfunction]
fn svg_sprite(svgs: Vec<HashMap<String, String>>, dest: String) {
    let optimized_svgs = svgs
        .iter()
        .map(|svg| {
            let mut map = HashMap::new();
            let id = svg.get("id").unwrap();
            let content = svg.get("content").unwrap();
            let optimized_content = optimize(content);
            map.insert("id".to_string(), id.to_string());
            map.insert("content".to_string(), optimized_content.to_string());
            map
        })
        .collect::<Vec<HashMap<String, String>>>();

    spriter::process(optimized_svgs, dest)
}

#[pyfunction]
fn svg_optimize(source: String) -> String {
    optimize(&source)
}

/// A Python module implemented in Rust.
#[pymodule]
fn svg_spriter_py(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(svg_sprite, m)?)?;
    m.add_function(wrap_pyfunction!(svg_optimize, m)?)?;
    Ok(())
}
