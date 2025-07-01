# config_validator.py
import yaml
from jinja2 import Environment, meta
import subprocess

def get_sql_template_and_params(yaml_file):
    inputs = yaml_file.get("inputs", [])

    if not inputs or not isinstance(inputs[0], dict):
        return None, None
    
    input_entry = inputs[0]  # assumes only one input block — or just using the first
    sql_template = input_entry.get("sql_template")
    sql_params = input_entry.get("sql_params", {})

    return sql_template, sql_params
        
def load_sql_template(template_name, folder="sql_templates"):
    path = f"{folder}/{template_name}"
    with open(path, "r") as f:
        return f.read()

def extract_jinja_variables(sql_text):
    env = Environment()
    ast = env.parse(sql_text)
    return meta.find_undeclared_variables(ast)

def yamllint_check(filepath, lint_path=".yamllint"):
    result = subprocess.run(['yamllint', '-c', lint_path, filepath], capture_output=True, text=True)
    return result.returncode == 0, result.stdout


def validate_config(config_path):
    errors = [] # maybe make this a key-value pair to aid in counting errors at which line as well as printing them out again
    params = {}

    ok, output = yamllint_check(config_path)

    if ok:
        print("\nThe provided .yaml file has no formatting errors.\n")
    else:
        print('The provided .yaml file has formatting errors listed below:\n', output)
        yes_no = input('Would you like to auto-repair the file? A new file will be created rather than modifying the provided one.\nyes/no\n').lower().strip()

        if yes_no in ['yes', 'y']:
            print('making new corrected file') 
            # start function to fix errors made and create new fixed file
            return
        elif yes_no in ['no', 'n']:
            print('No corrected file will be made. The linting cannot continue, however, without a syntactically correct .yaml file.')
            return
        else:
            print("Invalid input. Please enter 'yes' or 'no'.")
            return
    
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

    except Exception as e:
        return False, [f"YAML parsing error: {e}"]
    

    sql_template_name, params = get_sql_template_and_params(config)
    print("=== Here are the params found in the .yaml file to be rendered into the SQL template by Jinja ===\n")
    print(params)
    print("===")
    sql_template = load_sql_template(sql_template_name[4:])

    vars = extract_jinja_variables(sql_template)

    print("\n=== Here are the params found in the SQL template to be rendered by Jinja ===\n")
    print(vars)
    print("===")

    return
