use crate::models::GateResult;
use std::fs;
use std::path::Path;

pub struct FastGate;

impl FastGate {
    /// Inspects the content of a file for delimiter balance, bracket matching, and structural syntax integrity.
    pub fn check_content(file_path: &str, content: &str) -> GateResult {
        let is_py = file_path.ends_with(".py") || file_path.ends_with(".pyw");
        let is_c_like = file_path.ends_with(".js")
            || file_path.ends_with(".jsx")
            || file_path.ends_with(".ts")
            || file_path.ends_with(".tsx")
            || file_path.ends_with(".kt")
            || file_path.ends_with(".kts")
            || file_path.ends_with(".rs")
            || file_path.ends_with(".css");

        // Stack contains (char, line_number)
        let mut stack: Vec<(char, usize)> = Vec::new();

        let chars: Vec<char> = content.chars().collect();
        let len = chars.len();
        let mut i = 0;
        let mut line = 1;

        while i < len {
            let c = chars[i];

            if c == '\n' {
                line += 1;
                i += 1;
                continue;
            }

            // 1. Python comments (#)
            if is_py && c == '#' {
                while i < len && chars[i] != '\n' {
                    i += 1;
                }
                continue;
            }

            // 2. C-like comments (// and /* */)
            if is_c_like && c == '/' && i + 1 < len {
                if chars[i + 1] == '/' {
                    while i < len && chars[i] != '\n' {
                        i += 1;
                    }
                    continue;
                } else if chars[i + 1] == '*' {
                    i += 2;
                    while i + 1 < len && !(chars[i] == '*' && chars[i + 1] == '/') {
                        if chars[i] == '\n' {
                            line += 1;
                        }
                        i += 1;
                    }
                    if i + 1 < len {
                        i += 2; // skip */
                    }
                    continue;
                }
            }

            // 3. Python triple quotes (""" or ''')
            if is_py && (c == '"' || c == '\'') && i + 2 < len && chars[i + 1] == c && chars[i + 2] == c {
                let quote_char = c;
                i += 3;
                while i + 2 < len && !(chars[i] == quote_char && chars[i + 1] == quote_char && chars[i + 2] == quote_char) {
                    if chars[i] == '\\' && i + 1 < len {
                        i += 2;
                        continue;
                    }
                    if chars[i] == '\n' {
                        line += 1;
                    }
                    i += 1;
                }
                if i + 2 < len {
                    i += 3; // skip closing triple quote
                } else {
                    return GateResult {
                        file_path: file_path.to_string(),
                        passed: false,
                        gate: "FastGate:Syntax".to_string(),
                        message: format!("Unterminated triple-quoted string starting near line {}", line),
                        line_number: Some(line),
                    };
                }
                continue;
            }

            // 4. Standard strings ('...', "...", and JS template strings `...`)
            if c == '"' || c == '\'' || (is_c_like && c == '`') {
                let quote_char = c;
                let start_line = line;
                i += 1;
                let mut closed = false;
                while i < len {
                    let sc = chars[i];
                    if sc == '\\' && i + 1 < len {
                        i += 2;
                        continue;
                    }
                    if sc == '\n' {
                        if quote_char == '`' {
                            line += 1;
                        } else if !is_py {
                            // Non-template JS/TS/Rust string cannot span raw newlines without escape
                            break;
                        } else {
                            line += 1;
                        }
                    }
                    if sc == quote_char {
                        closed = true;
                        i += 1;
                        break;
                    }
                    i += 1;
                }

                if !closed && quote_char != '`' {
                    return GateResult {
                        file_path: file_path.to_string(),
                        passed: false,
                        gate: "FastGate:Syntax".to_string(),
                        message: format!("Unterminated string literal ({}) starting at line {}", quote_char, start_line),
                        line_number: Some(start_line),
                    };
                }
                continue;
            }

            // 5. Brackets
            match c {
                '(' | '[' | '{' => {
                    stack.push((c, line));
                }
                ')' => {
                    match stack.pop() {
                        Some(('(', _)) => {}
                        Some((expected, start_line)) => {
                            return GateResult {
                                file_path: file_path.to_string(),
                                passed: false,
                                gate: "FastGate:BracketBalance".to_string(),
                                message: format!(
                                    "Mismatched delimiter at line {}: found ')' but expected closing for '{}' from line {}",
                                    line, expected, start_line
                                ),
                                line_number: Some(line),
                            };
                        }
                        None => {
                            return GateResult {
                                file_path: file_path.to_string(),
                                passed: false,
                                gate: "FastGate:BracketBalance".to_string(),
                                message: format!("Unexpected closing ')' at line {} with no matching opening bracket", line),
                                line_number: Some(line),
                            };
                        }
                    }
                }
                ']' => {
                    match stack.pop() {
                        Some(('[', _)) => {}
                        Some((expected, start_line)) => {
                            return GateResult {
                                file_path: file_path.to_string(),
                                passed: false,
                                gate: "FastGate:BracketBalance".to_string(),
                                message: format!(
                                    "Mismatched delimiter at line {}: found ']' but expected closing for '{}' from line {}",
                                    line, expected, start_line
                                ),
                                line_number: Some(line),
                            };
                        }
                        None => {
                            return GateResult {
                                file_path: file_path.to_string(),
                                passed: false,
                                gate: "FastGate:BracketBalance".to_string(),
                                message: format!("Unexpected closing ']' at line {} with no matching opening bracket", line),
                                line_number: Some(line),
                            };
                        }
                    }
                }
                '}' => {
                    match stack.pop() {
                        Some(('{', _)) => {}
                        Some((expected, start_line)) => {
                            return GateResult {
                                file_path: file_path.to_string(),
                                passed: false,
                                gate: "FastGate:BracketBalance".to_string(),
                                message: format!(
                                    "Mismatched delimiter at line {}: found '}}' but expected closing for '{}' from line {}",
                                    line, expected, start_line
                                ),
                                line_number: Some(line),
                            };
                        }
                        None => {
                            return GateResult {
                                file_path: file_path.to_string(),
                                passed: false,
                                gate: "FastGate:BracketBalance".to_string(),
                                message: format!("Unexpected closing '}}' at line {} with no matching opening bracket", line),
                                line_number: Some(line),
                            };
                        }
                    }
                }
                _ => {}
            }

            i += 1;
        }

        if let Some((unclosed, start_line)) = stack.pop() {
            return GateResult {
                file_path: file_path.to_string(),
                passed: false,
                gate: "FastGate:BracketBalance".to_string(),
                message: format!("Unclosed delimiter '{}' starting at line {}", unclosed, start_line),
                line_number: Some(start_line),
            };
        }

        GateResult {
            file_path: file_path.to_string(),
            passed: true,
            gate: "FastGate".to_string(),
            message: "Structural and delimiter integrity verified (OK)".to_string(),
            line_number: None,
        }
    }

    /// Reads a file from disk and runs structural delimiter check.
    pub fn check_file(file_path: &Path) -> GateResult {
        let path_str = file_path.to_string_lossy().to_string();
        match fs::read_to_string(file_path) {
            Ok(content) => Self::check_content(&path_str, &content),
            Err(e) => GateResult {
                file_path: path_str,
                passed: false,
                gate: "FastGate:IO".to_string(),
                message: format!("Failed to read file: {}", e),
                line_number: None,
            },
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_valid_python_brackets() {
        let code = r#"
def foo(a, b):
    items = [1, 2, 3, {"key": (4 + 5)}]
    # comment with unmatched ) ] }
    """docstring with (unmatched { bracket"""
    return len(items)
"#;
        let res = FastGate::check_content("test.py", code);
        assert!(res.passed);
    }

    #[test]
    fn test_unclosed_python_bracket() {
        let code = r#"
def broken():
    data = {"key": [1, 2, 3]
"#;
        let res = FastGate::check_content("broken.py", code);
        assert!(!res.passed);
        assert!(res.message.contains("Unclosed delimiter '{'"));
    }

    #[test]
    fn test_mismatched_js_brackets() {
        let code = r#"
function test() {
    const list = [1, 2, 3);
}
"#;
        let res = FastGate::check_content("test.js", code);
        assert!(!res.passed);
        assert!(res.message.contains("Mismatched delimiter"));
    }

    #[test]
    fn test_valid_js_template_string_and_comments() {
        let code = r#"
// comment with unmatched )
/* multi-line comment
   with [ unmatched {
*/
const msg = `hello ${"world"} (with bracket)`;
const obj = { a: [1, 2], b: () => true };
"#;
        let res = FastGate::check_content("app.ts", code);
        assert!(res.passed);
    }
}
