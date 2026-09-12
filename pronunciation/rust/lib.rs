// SPDX-FileCopyrightText: 2026 Peter Bezemek
// SPDX-FileCopyrightText: 2025 lastleon
// SPDX-License-Identifier: MIT

use pyo3::exceptions::{PyRuntimeError, PyValueError};
use pyo3::prelude::*;
use pyo3::types::PyBytes;
use rustfst::algorithms::compose;
use rustfst::prelude::*;
use std::sync::Arc;

fn runtime_error(error: impl std::fmt::Display) -> PyErr {
    PyRuntimeError::new_err(error.to_string())
}

fn input_lattice(
    model: &VectorFst<TropicalWeight>,
    word: &str,
) -> PyResult<VectorFst<TropicalWeight>> {
    let symbols = model
        .input_symbols()
        .ok_or_else(|| PyValueError::new_err("model has no input symbol table"))?;
    let chars: Vec<char> = word.chars().collect();
    let mut fst = VectorFst::new();
    let states: Vec<_> = (0..=chars.len()).map(|_| fst.add_state()).collect();
    fst.set_start(states[0]).map_err(runtime_error)?;
    fst.set_final(states[chars.len()], TropicalWeight::one())
        .map_err(runtime_error)?;

    for start in 0..chars.len() {
        for (label, symbol) in symbols.iter() {
            if label == 0 || symbol == "_" || symbol == "|" {
                continue;
            }
            let spelling: Vec<char> = symbol.split('|').flat_map(str::chars).collect();
            let end = start + spelling.len();
            if end <= chars.len() && chars[start..end] == spelling {
                fst.add_tr(
                    states[start],
                    Tr::new(label, label, TropicalWeight::one(), states[end]),
                )
                .map_err(runtime_error)?;
            }
        }
    }
    Ok(fst)
}

#[pyclass(frozen)]
struct Model {
    model: Arc<VectorFst<TropicalWeight>>,
}

#[pymethods]
impl Model {
    #[new]
    fn new(data: &Bound<'_, PyBytes>) -> PyResult<Self> {
        let model = VectorFst::<TropicalWeight>::load(data.as_bytes()).map_err(runtime_error)?;
        Ok(Self {
            model: Arc::new(model),
        })
    }

    fn phonemize(&self, word: &str) -> PyResult<(f32, String, Vec<(String, Vec<String>)>)> {
        if word.is_empty() {
            return Err(PyValueError::new_err("word must not be empty"));
        }
        let lattice = input_lattice(&self.model, word)?;
        let composed: VectorFst<TropicalWeight> =
            compose::compose::<_, _, VectorFst<TropicalWeight>, _, _, _>(
                lattice,
                self.model.clone(),
            )
            .map_err(runtime_error)?;
        let shortest: VectorFst<TropicalWeight> =
            shortest_path(&composed).map_err(runtime_error)?;
        let path = shortest
            .paths_iter()
            .next()
            .ok_or_else(|| PyValueError::new_err("the model has no pronunciation for this word"))?;
        let inputs = self
            .model
            .input_symbols()
            .ok_or_else(|| PyValueError::new_err("model has no input symbol table"))?;
        let outputs = self
            .model
            .output_symbols()
            .ok_or_else(|| PyValueError::new_err("model has no output symbol table"))?;
        let phones = path
            .olabels
            .iter()
            .filter_map(|label| outputs.get_symbol(*label))
            .filter(|symbol| *symbol != "_")
            .collect::<Vec<_>>()
            .join("")
            .replace('|', "");

        let mut spans: Vec<(String, Vec<String>)> = Vec::new();
        let mut state = shortest
            .start()
            .ok_or_else(|| PyRuntimeError::new_err("shortest path has no start state"))?;
        while shortest
            .final_weight(state)
            .map_err(runtime_error)?
            .is_none()
        {
            let transitions = shortest.get_trs(state).map_err(runtime_error)?;
            let transition = transitions
                .trs()
                .first()
                .ok_or_else(|| PyRuntimeError::new_err("shortest path is incomplete"))?;
            let input = inputs.get_symbol(transition.ilabel).unwrap_or("<eps>");
            let output = outputs.get_symbol(transition.olabel).unwrap_or("<eps>");
            if input != "<eps>" {
                spans.push((input.replace('|', ""), Vec::new()));
            }
            if output != "<eps>" && output != "_" {
                let span = spans.last_mut().ok_or_else(|| {
                    PyRuntimeError::new_err("model emitted a phone before the first grapheme")
                })?;
                span.1.extend(output.split('|').map(str::to_owned));
            }
            state = transition.nextstate;
        }
        Ok((*path.weight.value(), phones, spans))
    }
}

#[pymodule]
fn _native(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_class::<Model>()?;
    Ok(())
}
