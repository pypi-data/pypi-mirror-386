use pyo3::types::PyTypeMethods;
use pyo3::Python;
use pyruvate;

#[test]
fn create_async_logger() {
    Python::attach(|py| {
        match pyruvate::async_logger(py, "foo") {
            Ok(()) => (),
            _ => assert!(false),
        }
        // can't initialize logger twice
        match pyruvate::async_logger(py, "foo") {
            Err(e) => {
                assert!(e.get_type(py).name().unwrap() == "ValueError");
            }
            _ => assert!(false),
        }
    });
}
