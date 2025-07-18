# syntax_validator.py
import subprocess
import re
import os
from pathlib import Path

max_passes = 20

def find_lint_path(filename, base_dir="Config_Linter"):
    """
    Recursively searches for the specified file (.yamllint) within the given base directory.

    Args:
        filename (str): Name of the file to search for.
        base_dir (str): Directory to start the search from.

    Returns:
        str or None: Full path to the file if found, otherwise None.
    """

    for root, _, files in os.walk(base_dir):
        
        if filename in files:
            return os.path.join(root, filename)
    return None

def yamllint_check(filepath, lint_path=".yamllint"):
    """
    Runs yamllint on the specified YAML file using a given configuration.

    Args:
        filepath (str or Path): Path to the YAML file.
        lint_path (str): Path to the yamllint config file (default: '.yamllint').

    Returns:
        tuple[bool or None, str or None]: 
            - Boolean indicating if the file passed yamllint (None if yamllint failed to run).
            - Stdout output from yamllint or None.
    """


    lint_path = find_lint_path(lint_path)

    result = subprocess.run(['yamllint', '-c', lint_path, filepath], capture_output=True, text=True)
    if result.returncode not in [0, 1]:
        print("There was a problem running .yamllint. Please ensure your system has the yamllint library installed.")
        return None, None
    else:
        return result.returncode == 0, result.stdout

def parse_yamllint_errors(output):
    """
    Uses regex to break up yamllint's output in 'parsable' format into structured error dictionaries.

    Args:
        output (str): Raw string output from yamllint.

    Returns:
        list[dict]: A list of dictionaries, each representing a linting error.
    """

    parsed = []
    for line in output.strip().splitlines():
        match = re.match(r"(.+):(\d+):(\d+): \[(\w+)\] (.+?) \((.+)\)", line)
        if match:
            parsed.append({
                'file': match.group(1),
                'line': int(match.group(2)) - 1,
                'column': int(match.group(3)) - 1,
                'level': match.group(4),
                'message': match.group(5),
                'rule': match.group(6)
            })
    return parsed

def fix_indentation(lines, i, message):
    """
    Attempts to correct indentation errors and recursively re-indents child lines if necessary.

    Args:
        lines (list[str]): List of all lines in the YAML file.
        i (int): Index of the line with the indentation error.
        message (str): Error message from yamllint.

    Returns:
        list[str]: Modified list of lines with indentation adjustments.
    """

    expected_match = re.search(r"expected (\d+)", message)
    found_match = re.search(r"found (\d+)", message)
    at_least_match = re.search(r"at least (\d+)", message)

    if at_least_match:
        at_least_indent = int(at_least_match.group(1))
        lines[i] = " " * at_least_indent + lines[i].lstrip()

    if not expected_match:
        return lines  # No expected indentation found; skip
    if not found_match:
        return lines
    
    expected_indent = int(expected_match.group(1))
    found_indent = int(found_match.group(1))
    current_line = lines[i]
    #print("indented line: ", i+1," with fix_indentation() -> ", lines[i])
    lines[i] = " " * expected_indent + current_line.lstrip()

    # Fix child lines — look ahead
    j = i + 1
    while j < len(lines):
        next_line = lines[j]

        # Stop if it's blank or a comment
        if not next_line.strip() or next_line.strip().startswith("#"):
            j += 1
            continue

        next_line = lines[j]

        #print("looking at child line: ", j+1, " -> ", next_line)

        current_indent = len(next_line) - len(next_line.lstrip())

        # Stop if we've reached a sibling or parent line
        if current_indent <= found_indent:
            
            #print("indent of line: ", j+1, " is: ", current_indent, " and indent of found indent: ", found_indent, " so breaking out of loop")
            break

        # Re-indent child line: add 2 spaces for nesting
        #print("indented child line: ", j+1," with fix_indentation() -> ", lines[j])
        lines[j] = " " * (expected_indent) + next_line
        j += 1


    return lines

def fix_document_start(lines):
    """
    Ensures the YAML document starts with '---' by inserting it if missing.

    Args:
        lines (list[str]): List of lines in the YAML file.

    Returns:
        list[str]: Updated list with document start marker inserted if needed.
    """

    if not lines[0].strip().startswith("---"):
        lines.insert(0, "---\n")
    return lines

def fix_colon_spacing(line_text, col_index):
    """
    Fixes spacing after a colon by stripping leading spaces before/after it.

    Args:
        line_text (str): The full text of the line containing the colon.
        col_index (int): The index of the colon character.

    Returns:
        str: Line with corrected spacing after the colon.
    """

    before = line_text[:col_index + 1]
    after = line_text[col_index + 1:].lstrip()
    return before + after

def fix_syntax_error(lines, i, message):
    """
    Attempts to auto-correct certain block structure and indentation-related syntax errors.

    Args:
        lines (list[str]): List of all lines in the YAML file.
        i (int): Line number where the syntax error occurs.
        message (str): Error message detailing the syntax issue.

    Returns:
        list[str]: Modified list of lines with attempted syntax fixes applied.
    """

    def get_indent_level(line):
        return len(line) - len(line.lstrip())

    def is_block_line(line):
        # Check if the line is part of the block (not blank, not top-level)
        stripped = line.strip()
        return bool(stripped) and not stripped.startswith("#")
    
    error = re.search(r"but found '([^']+)'", message)
    if error:
        symbol = error.group(1)
        line = lines[i]
        if "<block end>" in message and symbol in ['-', '?']:
            # Look for previous non-empty line to estimate correct indent
            j = i - 1
            while j >= 0 and lines[j].strip() == "":
                j -= 1

            if j >= 0:
                prev_indent = get_indent_level(lines[j])

                # If previous line starts with a dash and this item does not, this is part of the list item
                if lines[j].lstrip().startswith("-") and not lines[i].lstrip().startswith("-"):
                    new_indent = prev_indent + 2
                else:
                    new_indent = prev_indent

                # Step 2: Fix the current line
                #print("indented line: ", i+1, " with fix_syntax() -> ", lines[i])
                lines[i] = " " * new_indent + line.lstrip()

                # Step 3: Fix the block beneath it
                for k in range(i + 1, len(lines)):
                    next_line = lines[k]
                    #print("looking at children line: ", k+1, " -> ", next_line)
                    if not is_block_line(next_line):
                        continue

                    # Check if we've reached a less-indented block or a new section
                    if get_indent_level(next_line) <= prev_indent:
                        #print("line: ", k+1, " is less indented than line: ", i+1, " -> ", next_line)
                        break

                    # Fix child line
                    #print("indented children line: ", k+1, " with fix_syntax() -> ", lines[k])
                    lines[k] = " " * (new_indent + 2) + next_line.lstrip() # took a +2 out of the new_indent bracket
                return lines
  

    # Otherwise just mark it
    current_indent = get_indent_level(lines[i])
    #lines[i] = " " * current_indent + "# SYNTAX ERROR - check manually:\n" + line
    return lines

def fix_trailing_spaces(line):
    """
    Removes trailing whitespace from a line and ensures it ends with a newline character.

    Args:
        line (str): A single line from the YAML file.

    Returns:
        str: Cleaned-up line with no trailing spaces.
    """

    line = line.rstrip() + "\n"
    return line

def auto_fix_yaml(filepath, lintpath = ".yamllint"):
    """
    Iteratively applies yamllint, parses issues, and attempts automatic fixes for supported rules.

    Args:
        filepath (str): Path to the YAML file to fix.
        lintpath (str): Path to the yamllint config file.

    Returns:
        str: Path to the final (possibly modified) YAML file.
    """

    with open(filepath, 'r') as f:
        lines = f.readlines()

    base_name = os.path.basename(filepath)
    name, ext = os.path.splitext(base_name)
    new_name = f"{name}_Corrected_Errors{ext}"
    #output_path = os.path.join(output_dir, new_name) if output_dir else os.path.join(os.path.dirname(filepath), new_name)
    output_path = filepath  # overwrite original file

    previous_output = ""

    passes = 0

    while passes < max_passes:
        with open(output_path, 'w') as f:
            f.writelines(lines)

        # Run yamllint
        lint_path = '.yamllint'
        lint_path = find_lint_path(lint_path)
        result = subprocess.run(
            ['yamllint', '--format', 'parsable', '-c', lint_path, output_path],
            capture_output=True, text=True
        )
        output = result.stdout.strip()

        if previous_output == output:
            print("No more fixes possible but more errors are present. Please review your .yaml file. The errors are as follows: \n")
            print(output)
            return output_path

        previous_output = output
        #print(f"\n=== Pass {passes} ===\n")
        #print(output)
        #print("======\n")
        
        if not output:
            print(filepath, "has been cleaned.")
            break

        # Fix errors
        parsed_errors = parse_yamllint_errors(output)
        parsed_errors = sorted(parsed_errors, key=lambda e: -e['line'])

        # Re-read the current state of the file after writing
        with open(output_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for error in parsed_errors:
            i = error['line']
            rule = error['rule']
            if i >= len(lines): continue

            if rule == "indentation":
                lines = fix_indentation(lines, i, error['message'])
            elif rule == "colons":
                lines[i] = fix_colon_spacing(lines[i], error['column'])
            elif rule == "trailing-spaces":
                lines[i] = fix_trailing_spaces(lines[i])
            elif rule == "document-start":
                lines = fix_document_start(lines)
            elif rule == "syntax":
                lines = fix_syntax_error(lines, i, error['message'])

        passes += 1

    else:
        print(f"Max passes ({max_passes}) reached. YAML may still contain issues.")

    return output_path

def validate_syntax(config_path):
    """
    Validates and optionally auto-fixes a YAML file's formatting using yamllint.

    Args:
        config_path (str): Path to the YAML file.

    Returns:
        str: Path to the validated YAML file.
    """

    ok, output = yamllint_check(config_path)

    if ok == None:
        print("Error with finding initial errors in .yaml file.")
        return config_path

    if ok:
        print("\nThe provided .yaml file has no formatting errors.\n")
    else:
        config_path = auto_fix_yaml(config_path)

    return config_path