use goby_core::{FastGate, RepositoryScanner};
use std::env;
use std::io::{self, Read};
use std::path::Path;
use std::process;

fn print_help() {
    println!("Goby Core Native Accelerator v0.1.0 (Rust Fast Gate & Scanner)");
    println!("Usage:");
    println!("  goby-core scan <dir_path> [--max-files N]   Scan directory and emit SymbolMap JSON");
    println!("  goby-core scan-file <file_path>             Scan single file and emit FileSymbolMap JSON");
    println!("  goby-core check <file_path>                 Fast delimiter & structural gate check on file");
    println!("  goby-core check-stdin <file_path>           Fast check reading content from stdin");
    println!("  goby-core version                           Print version");
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        print_help();
        process::exit(0);
    }

    let cmd = args[1].as_str();
    match cmd {
        "version" | "--version" | "-v" => {
            println!("goby-core 0.1.0");
            process::exit(0);
        }
        "help" | "--help" | "-h" => {
            print_help();
            process::exit(0);
        }
        "scan" => {
            if args.len() < 3 {
                eprintln!("[ERROR] Please provide directory path to scan.");
                process::exit(1);
            }
            let dir_path = Path::new(&args[2]);
            let mut max_files = 1000;
            if args.len() >= 5 && args[3] == "--max-files" {
                if let Ok(n) = args[4].parse::<usize>() {
                    max_files = n;
                }
            }
            let sym_map = RepositoryScanner::scan_directory(dir_path, max_files);
            match serde_json::to_string(&sym_map) {
                Ok(json_str) => {
                    println!("{}", json_str);
                    process::exit(0);
                }
                Err(e) => {
                    eprintln!("[ERROR] JSON serialization failed: {}", e);
                    process::exit(1);
                }
            }
        }
        "scan-file" => {
            if args.len() < 3 {
                eprintln!("[ERROR] Please provide file path to scan.");
                process::exit(1);
            }
            let file_path = Path::new(&args[2]);
            let fmap = RepositoryScanner::scan_file(file_path, None);
            match serde_json::to_string(&fmap) {
                Ok(json_str) => {
                    println!("{}", json_str);
                    process::exit(0);
                }
                Err(e) => {
                    eprintln!("[ERROR] JSON serialization failed: {}", e);
                    process::exit(1);
                }
            }
        }
        "check" => {
            if args.len() < 3 {
                eprintln!("[ERROR] Please provide file path to check.");
                process::exit(1);
            }
            let file_path = Path::new(&args[2]);
            let res = FastGate::check_file(file_path);
            if res.passed {
                eprintln!("[GOBY NATIVE FAST-GATE ✅] {} passed delimiter integrity.", res.file_path);
                process::exit(0);
            } else {
                eprintln!(
                    "[GOBY NATIVE FAST-GATE ❌] {} failed: {} (Line: {:?})",
                    res.file_path, res.message, res.line_number
                );
                process::exit(1);
            }
        }
        "check-stdin" => {
            if args.len() < 3 {
                eprintln!("[ERROR] Please provide virtual file path for stdin check.");
                process::exit(1);
            }
            let file_path = &args[2];
            let mut buffer = String::new();
            if io::stdin().read_to_string(&mut buffer).is_err() {
                eprintln!("[ERROR] Failed to read from stdin.");
                process::exit(1);
            }
            let res = FastGate::check_content(file_path, &buffer);
            if res.passed {
                eprintln!("[GOBY NATIVE FAST-GATE ✅] {} passed delimiter integrity.", res.file_path);
                process::exit(0);
            } else {
                eprintln!(
                    "[GOBY NATIVE FAST-GATE ❌] {} failed: {} (Line: {:?})",
                    res.file_path, res.message, res.line_number
                );
                process::exit(1);
            }
        }
        other => {
            eprintln!("[ERROR] Unknown command: {}", other);
            print_help();
            process::exit(1);
        }
    }
}
