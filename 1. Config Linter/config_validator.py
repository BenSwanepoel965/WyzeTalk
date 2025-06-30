# config_validator.py
import yaml
from jinja2 import Environment, meta
import os

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


def validate_config(config_path):
    errors = [] # maybe make this a key-value pair to aid in counting errors at which line as well as printing them out again
    params = {}

    # Load YAML
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
    except Exception as e:
        return False, [f"YAML parsing error: {e}"]

    sql_template_name, params = get_sql_template_and_params(config)
    print("===")
    print(params)
    print("===")
    sql_template = load_sql_template(sql_template_name[4:])

    vars = extract_jinja_variables(sql_template)

    print(vars)

    return
