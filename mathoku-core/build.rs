use std::process::Command;

fn main() {
    println!("cargo:rerun-if-changed=src/models");

    let output_file = "../mathoku_ui/src/types/backend.ts";

    let output = Command::new("typeshare")
        .args(["--lang", "typescript", "--output-file", output_file, "."])
        .output()
        .expect("Failed to execute typeshare command");

    if !output.status.success() {
        let stdout = String::from_utf8_lossy(&output.stdout);
        let stderr = String::from_utf8_lossy(&output.stderr);
        panic!(
            "typeshare command failed with status: {}\nstdout: {}\nstderr: {}",
            output.status, stdout, stderr
        );
    }

    println!("Successfully generated TypeScript types to {}", output_file);

    println!("cargo:rerun-if-changed=build.rs");
}
