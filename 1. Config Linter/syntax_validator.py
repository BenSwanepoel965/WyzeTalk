# syntax_validator.py
import subprocess
import re
import os

max_passes = 20

def yamllint_check(filepath, lint_path=".yamllint"):
    result = subprocess.run(['yamllint', '-c', lint_path, filepath], capture_output=True, text=True)
    if result.returncode not in [0, 1]:
        print("There was a problem running .yamllint. Please ensure your system has the yamllint library installed.")
        return
    else:
        return result.returncode == 0, result.stdout

def parse_yamllint_errors(output):
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
    expected_match = re.search(r"expected (\d+)", message)
    found_match = re.search(r"found (\d+)", message)
    if not expected_match:
        return lines  # No expected indentation found; skip
    
    expected_indent = int(expected_match.group(1))
    found_indent = int(found_match.group(1))
    current_line = lines[i]
    print("indented line: ", i+1," with fix_indentation() -> ", lines[i])
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

        print("looking at child line: ", j+1, " -> ", next_line)

        current_indent = len(next_line) - len(next_line.lstrip())

        # Stop if we've reached a sibling or parent line
        if current_indent <= found_indent:
            print("indent of line: ", j+1, " is: ", current_indent, " and indent of found indent: ", found_indent, " so breaking out of loop")
            break

        # Re-indent child line: add 2 spaces for nesting
        print("indented child line: ", j+1," with fix_indentation() -> ", lines[j])
        lines[j] = " " * (expected_indent) + next_line
        j += 1


    return lines


def fix_document_start(lines):
    if not lines[0].strip().startswith("---"):
        lines.insert(0, "---\n")
    return lines

def fix_colon_spacing(line_text, col_index):
    before = line_text[:col_index + 1]
    after = line_text[col_index + 1:].lstrip()
    return before + after

def fix_line_length(line_text, max_length=80):
    # Just truncate for now or ignore in config instead
    return line_text[:max_length] + "\n"

def fix_syntax_error(lines, i):
    def get_indent_level(line):
        return len(line) - len(line.lstrip())

    def is_block_line(line):
        # Check if the line is part of the block (not blank, not top-level)
        stripped = line.strip()
        return bool(stripped) and not stripped.startswith("#")
    

    line = lines[i]
    if "<block end>" in line or line.lstrip().startswith("-"):
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
            print("indented line: ", i+1, " with fix_syntax() -> ", lines[i])
            lines[i] = " " * new_indent + line.lstrip()

            # Step 3: Fix the block beneath it
            for k in range(i + 1, len(lines)):
                next_line = lines[k]
                print("looking at children line: ", k+1, " -> ", next_line)
                if not is_block_line(next_line):
                    continue

                # Check if we've reached a less-indented block or a new section
                if get_indent_level(next_line) <= prev_indent:
                    print("line: ", k+1, " is less indented than line: ", i+1, " -> ", next_line)
                    break

                # Fix child line
                print("indented children line: ", k+1, " with fix_syntax() -> ", lines[k])
                lines[k] = " " * (new_indent + 2) + next_line.lstrip()
            return lines
    # Otherwise just mark it
    current_indent = get_indent_level(lines[i])
    #lines[i] = " " * current_indent + "# SYNTAX ERROR - check manually:\n" + line
    return lines

def auto_fix_yaml(filepath, output_dir=None):
    with open(filepath, 'r') as f:
        lines = f.readlines()

    base_name = os.path.basename(filepath)
    name, ext = os.path.splitext(base_name)
    new_name = f"{name}_Corrected_Errors{ext}"
    output_path = os.path.join(output_dir, new_name) if output_dir else os.path.join(os.path.dirname(filepath), new_name)

    passes = 0

    while passes < max_passes:
        with open(output_path, 'w') as f:
            f.writelines(lines)

        # Run yamllint
        result = subprocess.run(
            ['yamllint', '--format', 'parsable', output_path],
            capture_output=True, text=True
        )
        output = result.stdout.strip()
        print(f"\n=== Pass {passes} ===\n")
        print(output)
        print("======\n")
        
        if not output:
            print(f"✅ YAML clean after {passes} pass(es)")
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
            elif rule == "document-start":
                lines = fix_document_start(lines)
            elif rule == "line-length":
                # Could also ignore in config instead
                lines[i] = fix_line_length(lines[i])
            elif rule == "syntax":
                lines = fix_syntax_error(lines, i)

        passes += 1

    else:
        print(f"⚠️ Max passes ({max_passes}) reached. YAML may still contain issues.")

    return output_path, passes

def validate_syntax(config_path):
    ok, output = yamllint_check(config_path)

    if ok:
        print("\nThe provided .yaml file has no formatting errors.\n")
    else:
        print('The provided .yaml file has initial formatting errors listed below:\n', output)
        yes_no = input('Would you like to auto-repair the file? A new file will be created rather than modifying the provided one.\nyes/no\n').lower().strip()

        if yes_no in ['yes', 'y']:
            print('making new corrected file')
            old_config_path = config_path
            config_path = auto_fix_yaml(config_path, "Configs\\Corrected Versions")
            print("Corrected file has been saved as: ", config_path)
        elif yes_no in ['no', 'n']:
            print('No corrected file will be made. The linting cannot continue, however, without a syntactically correct .yaml file.')
            return None, None
        else:
            print("Invalid input. Please enter 'yes' or 'no'.")
            return


    return old_config_path, config_path