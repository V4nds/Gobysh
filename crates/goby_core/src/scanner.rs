use crate::models::{FileSymbolMap, Symbol, SymbolMap};
use regex::Regex;
use std::collections::HashSet;
use std::fs;
use std::path::Path;
use walkdir::WalkDir;

pub struct RepositoryScanner;

impl RepositoryScanner {
    /// Scans a single source file either from disk or from an in-memory string.
    pub fn scan_file(file_path: &Path, content: Option<&str>) -> FileSymbolMap {
        let norm_path = file_path.to_string_lossy().replace('\\', "/");
        let owned_content;
        let text = match content {
            Some(c) => c,
            None => match fs::read_to_string(file_path) {
                Ok(c) => {
                    owned_content = c;
                    &owned_content
                }
                Err(_) => return FileSymbolMap::new(&norm_path),
            },
        };

        if norm_path.ends_with(".py") || norm_path.ends_with(".pyw") {
            Self::scan_python(&norm_path, text)
        } else if norm_path.ends_with(".js")
            || norm_path.ends_with(".jsx")
            || norm_path.ends_with(".ts")
            || norm_path.ends_with(".tsx")
            || norm_path.ends_with(".mjs")
            || norm_path.ends_with(".cjs")
        {
            Self::scan_javascript(&norm_path, text)
        } else if norm_path.ends_with(".kt") || norm_path.ends_with(".kts") {
            Self::scan_kotlin(&norm_path, text)
        } else if norm_path.ends_with(".rs") {
            Self::scan_rust(&norm_path, text)
        } else {
            FileSymbolMap::new(&norm_path)
        }
    }

    /// Scans a Python source file for imports, classes, methods, and functions.
    pub fn scan_python(file_path: &str, code: &str) -> FileSymbolMap {
        let mut symbols: Vec<Symbol> = Vec::new();
        let mut imports: Vec<String> = Vec::new();

        let re_import = Regex::new(r"^\s*import\s+([a-zA-Z0-9_.,\s]+)").unwrap();
        let re_from = Regex::new(r"^\s*from\s+([a-zA-Z0-9_.]+)\s+import\s+([a-zA-Z0-9_.,\s*]+)").unwrap();
        let re_class = Regex::new(r"^\s*class\s+([a-zA-Z0-9_]+)(?:\s*\([^)]*\))?\s*:").unwrap();
        let re_def = Regex::new(r"^(\s*)(?:async\s+)?def\s+([a-zA-Z0-9_]+)\s*\(([^)]*)\)").unwrap();

        let lines: Vec<&str> = code.lines().collect();
        let mut current_class: Option<(String, usize)> = None; // (name, indent_level)

        for (idx, line) in lines.iter().enumerate() {
            let line_num = idx + 1;
            let trimmed = line.trim_start();
            let indent = line.len() - trimmed.len();

            // Check if we exited current class scope
            if let Some((_, class_indent)) = &current_class {
                if !trimmed.is_empty() && indent <= *class_indent && !trimmed.starts_with('#') {
                    current_class = None;
                }
            }

            // 1. Imports
            if let Some(caps) = re_import.captures(line) {
                if let Some(m) = caps.get(1) {
                    for item in m.as_str().split(',') {
                        let name = item.trim().split_whitespace().next().unwrap_or("");
                        if !name.is_empty() {
                            imports.push(name.to_string());
                        }
                    }
                }
                continue;
            }

            if let Some(caps) = re_from.captures(line) {
                let mod_name = caps.get(1).map_or("", |m| m.as_str());
                if let Some(m) = caps.get(2) {
                    for item in m.as_str().split(',') {
                        let sym = item.trim().split_whitespace().next().unwrap_or("");
                        if !sym.is_empty() {
                            if mod_name.is_empty() {
                                imports.push(sym.to_string());
                            } else {
                                imports.push(format!("{}.{}", mod_name, sym));
                            }
                        }
                    }
                }
                continue;
            }

            // 2. Class definition
            if let Some(caps) = re_class.captures(line) {
                if let Some(name_match) = caps.get(1) {
                    let class_name = name_match.as_str().to_string();
                    current_class = Some((class_name.clone(), indent));

                    symbols.push(Symbol {
                        name: class_name,
                        kind: "class".to_string(),
                        file_path: file_path.to_string(),
                        line_start: line_num,
                        line_end: line_num,
                        docstring: String::new(),
                        parameters: Vec::new(),
                    });
                }
                continue;
            }

            // 3. Function or Method definition
            if let Some(caps) = re_def.captures(line) {
                if let Some(fn_match) = caps.get(2) {
                    let fn_name = fn_match.as_str();
                    let raw_params = caps.get(3).map_or("", |m| m.as_str());
                    let params: Vec<String> = raw_params
                        .split(',')
                        .map(|p| p.trim().split(':').next().unwrap_or("").trim().to_string())
                        .filter(|p| !p.is_empty())
                        .collect();

                    if let Some((cls_name, class_indent)) = &current_class {
                        if indent > *class_indent {
                            symbols.push(Symbol {
                                name: format!("{}.{}", cls_name, fn_name),
                                kind: "method".to_string(),
                                file_path: file_path.to_string(),
                                line_start: line_num,
                                line_end: line_num,
                                docstring: String::new(),
                                parameters: params,
                            });
                            continue;
                        }
                    }

                    symbols.push(Symbol {
                        name: fn_name.to_string(),
                        kind: "function".to_string(),
                        file_path: file_path.to_string(),
                        line_start: line_num,
                        line_end: line_num,
                        docstring: String::new(),
                        parameters: params,
                    });
                }
            }
        }

        FileSymbolMap {
            file_path: file_path.to_string(),
            symbols,
            imports,
        }
    }

    /// Scans JavaScript/TypeScript source files.
    pub fn scan_javascript(file_path: &str, code: &str) -> FileSymbolMap {
        let mut symbols: Vec<Symbol> = Vec::new();
        let mut imports: Vec<String> = Vec::new();

        let re_import = Regex::new(r#"(?:import\s+.*?from\s+['"]([^'"]+)['"]|require\(['"]([^'"]+)['"]\))"#).unwrap();
        for caps in re_import.captures_iter(code) {
            let m = caps.get(1).or_else(|| caps.get(2));
            if let Some(mat) = m {
                imports.push(mat.as_str().to_string());
            }
        }

        let re_fn = Regex::new(r#"(?:function\s+([a-zA-Z0-9_$]+)\s*\(|const\s+([a-zA-Z0-9_$]+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>)"#).unwrap();
        for caps in re_fn.captures_iter(code) {
            let m = caps.get(1).or_else(|| caps.get(2));
            if let Some(mat) = m {
                let start_idx = mat.start();
                let line_num = code[..start_idx].chars().filter(|&c| c == '\n').count() + 1;
                symbols.push(Symbol {
                    name: mat.as_str().to_string(),
                    kind: "function".to_string(),
                    file_path: file_path.to_string(),
                    line_start: line_num,
                    line_end: line_num,
                    docstring: String::new(),
                    parameters: Vec::new(),
                });
            }
        }

        let re_class = Regex::new(r#"class\s+([a-zA-Z0-9_$]+)"#).unwrap();
        for caps in re_class.captures_iter(code) {
            if let Some(mat) = caps.get(1) {
                let start_idx = mat.start();
                let line_num = code[..start_idx].chars().filter(|&c| c == '\n').count() + 1;
                symbols.push(Symbol {
                    name: mat.as_str().to_string(),
                    kind: "class".to_string(),
                    file_path: file_path.to_string(),
                    line_start: line_num,
                    line_end: line_num,
                    docstring: String::new(),
                    parameters: Vec::new(),
                });
            }
        }

        FileSymbolMap {
            file_path: file_path.to_string(),
            symbols,
            imports,
        }
    }

    /// Scans Kotlin source files.
    pub fn scan_kotlin(file_path: &str, code: &str) -> FileSymbolMap {
        let mut symbols: Vec<Symbol> = Vec::new();
        let mut imports: Vec<String> = Vec::new();

        let re_import = Regex::new(r#"(?m)^\s*import\s+([a-zA-Z0-9_.*]+)"#).unwrap();
        for caps in re_import.captures_iter(code) {
            if let Some(mat) = caps.get(1) {
                imports.push(mat.as_str().trim().to_string());
            }
        }

        let re_class = Regex::new(r#"\b(?:data\s+class|enum\s+class|sealed\s+class|sealed\s+interface|class|interface|object)\s+([a-zA-Z0-9_]+)"#).unwrap();
        for caps in re_class.captures_iter(code) {
            if let Some(mat) = caps.get(1) {
                let start_idx = mat.start();
                let line_num = code[..start_idx].chars().filter(|&c| c == '\n').count() + 1;
                symbols.push(Symbol {
                    name: mat.as_str().to_string(),
                    kind: "class".to_string(),
                    file_path: file_path.to_string(),
                    line_start: line_num,
                    line_end: line_num,
                    docstring: String::new(),
                    parameters: Vec::new(),
                });
            }
        }

        let re_fn = Regex::new(r#"\b(?:fun|suspend\s+fun|override\s+fun)\s+(?:<[^>]+>\s+)?([a-zA-Z0-9_]+)\s*\("#).unwrap();
        for caps in re_fn.captures_iter(code) {
            if let Some(mat) = caps.get(1) {
                let start_idx = mat.start();
                let line_num = code[..start_idx].chars().filter(|&c| c == '\n').count() + 1;
                symbols.push(Symbol {
                    name: mat.as_str().to_string(),
                    kind: "function".to_string(),
                    file_path: file_path.to_string(),
                    line_start: line_num,
                    line_end: line_num,
                    docstring: String::new(),
                    parameters: Vec::new(),
                });
            }
        }

        FileSymbolMap {
            file_path: file_path.to_string(),
            symbols,
            imports,
        }
    }

    /// Scans Rust source files.
    pub fn scan_rust(file_path: &str, code: &str) -> FileSymbolMap {
        let mut symbols: Vec<Symbol> = Vec::new();
        let mut imports: Vec<String> = Vec::new();

        let re_use = Regex::new(r#"(?m)^\s*use\s+([^;]+);"#).unwrap();
        for caps in re_use.captures_iter(code) {
            if let Some(mat) = caps.get(1) {
                imports.push(mat.as_str().trim().to_string());
            }
        }

        let re_type = Regex::new(r#"\b(?:pub\s+)?(?:struct|enum|trait|type)\s+([a-zA-Z0-9_]+)"#).unwrap();
        for caps in re_type.captures_iter(code) {
            if let Some(mat) = caps.get(1) {
                let start_idx = mat.start();
                let line_num = code[..start_idx].chars().filter(|&c| c == '\n').count() + 1;
                symbols.push(Symbol {
                    name: mat.as_str().to_string(),
                    kind: "class".to_string(),
                    file_path: file_path.to_string(),
                    line_start: line_num,
                    line_end: line_num,
                    docstring: String::new(),
                    parameters: Vec::new(),
                });
            }
        }

        let re_fn = Regex::new(r#"\b(?:pub(?:\([^)]*\))?\s+)?(?:async\s+)?fn\s+([a-zA-Z0-9_]+)\s*(?:<[^>]*>)?\s*\("#).unwrap();
        for caps in re_fn.captures_iter(code) {
            if let Some(mat) = caps.get(1) {
                let start_idx = mat.start();
                let line_num = code[..start_idx].chars().filter(|&c| c == '\n').count() + 1;
                symbols.push(Symbol {
                    name: mat.as_str().to_string(),
                    kind: "function".to_string(),
                    file_path: file_path.to_string(),
                    line_start: line_num,
                    line_end: line_num,
                    docstring: String::new(),
                    parameters: Vec::new(),
                });
            }
        }

        FileSymbolMap {
            file_path: file_path.to_string(),
            symbols,
            imports,
        }
    }

    /// Scans an entire directory tree up to max_files.
    pub fn scan_directory(dir_path: &Path, max_files: usize) -> SymbolMap {
        let mut sym_map = SymbolMap::new();
        let mut count = 0;

        let mut ignored_dirs: HashSet<&str> = HashSet::new();
        for d in &[
            ".git", ".venv", "venv", "node_modules", "__pycache__", ".kilo",
            "build", ".gradle", "gradle", ".idea", "dist", "out", "bin", "target"
        ] {
            ignored_dirs.insert(d);
        }

        let walker = WalkDir::new(dir_path)
            .into_iter()
            .filter_entry(|entry| {
                if entry.file_type().is_dir() {
                    let name = entry.file_name().to_string_lossy();
                    !ignored_dirs.contains(name.as_ref())
                } else {
                    true
                }
            });

        for entry_res in walker {
            let entry = match entry_res {
                Ok(e) => e,
                Err(_) => continue,
            };

            if entry.file_type().is_file() {
                let path = entry.path();
                let path_str = path.to_string_lossy();
                let is_supported = path_str.ends_with(".py")
                    || path_str.ends_with(".pyw")
                    || path_str.ends_with(".js")
                    || path_str.ends_with(".jsx")
                    || path_str.ends_with(".ts")
                    || path_str.ends_with(".tsx")
                    || path_str.ends_with(".mjs")
                    || path_str.ends_with(".cjs")
                    || path_str.ends_with(".kt")
                    || path_str.ends_with(".kts")
                    || path_str.ends_with(".rs");

                if is_supported {
                    let rel_path = match path.strip_prefix(dir_path) {
                        Ok(p) => p.to_string_lossy().replace('\\', "/"),
                        Err(_) => path.to_string_lossy().replace('\\', "/"),
                    };

                    let mut fmap = Self::scan_file(path, None);
                    fmap.file_path = rel_path.clone();
                    for s in &mut fmap.symbols {
                        s.file_path = rel_path.clone();
                    }

                    sym_map.add_file(fmap);
                    count += 1;
                    if count >= max_files {
                        break;
                    }
                }
            }
        }

        sym_map
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_scan_python_symbols() {
        let py_code = r#"
import os, sys
from core.models import Symbol

class Engine:
    def __init__(self, mode: str):
        pass

    def run(self):
        pass

def top_level(x, y):
    return x + y
"#;
        let res = RepositoryScanner::scan_python("engine.py", py_code);
        assert_eq!(res.imports.len(), 3);
        assert_eq!(res.symbols.len(), 4);

        let names: Vec<&str> = res.symbols.iter().map(|s| s.name.as_str()).collect();
        assert!(names.contains(&"Engine"));
        assert!(names.contains(&"Engine.__init__"));
        assert!(names.contains(&"Engine.run"));
        assert!(names.contains(&"top_level"));
    }

    #[test]
    fn test_scan_javascript_symbols() {
        let js_code = r#"
import React from 'react';
const { helper } = require('./helper');

export class ViewContainer {
}

export const renderButton = (label) => {
    return label;
};
"#;
        let res = RepositoryScanner::scan_javascript("view.tsx", js_code);
        assert_eq!(res.imports.len(), 2);
        assert!(res.symbols.iter().any(|s| s.name == "ViewContainer" && s.kind == "class"));
        assert!(res.symbols.iter().any(|s| s.name == "renderButton" && s.kind == "function"));
    }

    #[test]
    fn test_scan_rust_symbols() {
        let rs_code = r#"
use std::collections::HashMap;

pub struct Service {
    id: u32,
}

pub async fn start_service() {
}
"#;
        let res = RepositoryScanner::scan_rust("service.rs", rs_code);
        assert_eq!(res.imports.len(), 1);
        assert!(res.symbols.iter().any(|s| s.name == "Service" && s.kind == "class"));
        assert!(res.symbols.iter().any(|s| s.name == "start_service" && s.kind == "function"));
    }
}
