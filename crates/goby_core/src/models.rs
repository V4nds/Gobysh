use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Symbol {
    pub name: String,
    pub kind: String,
    pub file_path: String,
    #[serde(default = "default_line")]
    pub line_start: usize,
    #[serde(default = "default_line")]
    pub line_end: usize,
    #[serde(default)]
    pub docstring: String,
    #[serde(default)]
    pub parameters: Vec<String>,
}

fn default_line() -> usize {
    1
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct FileSymbolMap {
    pub file_path: String,
    #[serde(default)]
    pub symbols: Vec<Symbol>,
    #[serde(default)]
    pub imports: Vec<String>,
}

impl FileSymbolMap {
    pub fn new(file_path: &str) -> Self {
        Self {
            file_path: file_path.to_string(),
            symbols: Vec::new(),
            imports: Vec::new(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Default)]
pub struct SymbolMap {
    pub files: HashMap<String, FileSymbolMap>,
}

impl SymbolMap {
    pub fn new() -> Self {
        Self {
            files: HashMap::new(),
        }
    }

    pub fn add_file(&mut self, file_map: FileSymbolMap) {
        self.files.insert(file_map.file_path.clone(), file_map);
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct GateResult {
    pub file_path: String,
    pub passed: bool,
    pub gate: String,
    pub message: String,
    #[serde(default)]
    pub line_number: Option<usize>,
}
