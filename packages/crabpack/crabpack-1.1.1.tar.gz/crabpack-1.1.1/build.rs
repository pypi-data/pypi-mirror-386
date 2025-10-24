fn main() {
    #[cfg(feature = "python")]
    {
        if std::env::var_os("CARGO_FEATURE_PYTHON").is_some() {
            pyo3_build_config::add_extension_module_link_args();
        }
    }
}
