use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;
use pyo3::types::{PyBytes, PyModule};
use pyo3::Bound;

// This macro exposes the Rust function to Python.
// The name in Python will be `xor_decrypt`.
#[pyfunction]
fn xor_decrypt(py: Python, encrypted_data: &[u8], key_hex: &str) -> PyResult<Py<PyBytes>> {
    // If the key is empty, just return a copy of the original data.
    if key_hex.is_empty() {
        return Ok(PyBytes::new(py, encrypted_data).into());
    }

    // Decode the hexadecimal key string into bytes.
    // If the string is invalid hex, map the error to a Python ValueError.
    let key_bytes = hex::decode(key_hex)
        .map_err(|e| PyValueError::new_err(format!("Invalid hex key: {}", e)))?;
    
    // Create a mutable copy of the encrypted data. Working on a Vec<u8> is fast.
    let mut decrypted = encrypted_data.to_vec();
    let key_len = key_bytes.len();

    // The high-performance loop. This is where Rust shines.
    // The compiler will often optimize this loop using SIMD (vector instructions)
    // making it much faster than a Python loop.
    for (i, byte) in decrypted.iter_mut().enumerate() {
        *byte ^= key_bytes[i % key_len];
    }

    // Return the decrypted bytes back to Python.
    Ok(PyBytes::new(py, &decrypted).into())
}

// This macro defines the Python module.
// When you `import xor_decryptor`, this is what gets created.
#[pymodule]
fn xor_decryptor(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(xor_decrypt, m)?)?;
    Ok(())
}