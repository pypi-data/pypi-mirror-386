
fn main() {
    // Try to find GSL using pkg-config
    if let Err(e) = pkg_config::probe_library("gsl") {
        // If pkg-config fails, try to find GSL manually on macOS
        #[cfg(target_os = "macos")]
        {
            // Common Homebrew paths
            let homebrew_paths = vec![
                "/opt/homebrew/lib",  // Apple Silicon
                "/usr/local/lib",     // Intel Mac
            ];
            
            for path in &homebrew_paths {
                if std::path::Path::new(&format!("{}/libgsl.dylib", path)).exists() {
                    println!("cargo:rustc-link-search=native={}", path);
                    println!("cargo:rustc-link-lib=gsl");
                    println!("cargo:rustc-link-lib=gslcblas");
                    return;
                }
            }
        }
        
        panic!("GSL library not found. Install it with: brew install gsl\nError: {}", e);
    }
}