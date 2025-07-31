use std::{
    path::PathBuf,
    process::Command,
};
use toml;

struct TypeshareConfig {
    output_folder: String,
    name: String,
}

fn parse_typeshare_config() -> TypeshareConfig {
    const TYPESHARE_TOML_FILE_NAME: &str = "typeshare.toml";
    const BUILD_CONFIG_SECTION: &str = "build";

    let typeshare_toml_raw = std::fs::read_to_string(TYPESHARE_TOML_FILE_NAME).expect(&format!("Failed to read {TYPESHARE_TOML_FILE_NAME}"));

    let typeshare_toml = toml::de::from_str::<toml::Value>(&typeshare_toml_raw).expect(&format!("Failed to parse {TYPESHARE_TOML_FILE_NAME}"));

    let build_config = typeshare_toml
        .get(BUILD_CONFIG_SECTION)
        .expect(&format!("{TYPESHARE_TOML_FILE_NAME} does not contain a [{BUILD_CONFIG_SECTION}] section"));

    let get_value = |key: &str| {
        build_config
            .get(key)
            .expect(&format!(
                "{key} not specified in {TYPESHARE_TOML_FILE_NAME} under [{BUILD_CONFIG_SECTION}] section"
            ))
            .as_str()
            .expect(&format!(
                "{key} in {TYPESHARE_TOML_FILE_NAME} under [{BUILD_CONFIG_SECTION}] section must be a string"
            ))
            .to_string()
    };

    let output_folder = get_value("output_folder");
    let name = get_value("name");

    TypeshareConfig { output_folder, name }
}

fn main() {
    println!("cargo:rerun-if-changed=src/models");

    let config = parse_typeshare_config();

    let output_file = PathBuf::from(&config.output_folder).join(format!("{}.ts", config.name));

    let output = Command::new("typeshare")
        .args([
            "--lang",
            "typescript",
            "--output-file",
            output_file.to_str().expect("Invalid output file path"),
            ".",
        ])
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

    println!("Successfully generated TypeScript types to {output_file:?}");

    println!("cargo:rerun-if-changed=build.rs");
}
