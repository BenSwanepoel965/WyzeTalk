# semantic_validator.py

import yaml
from jinja2 import Environment, meta
from datetime import date

def get_sql_template_and_params(inputs):

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

def validate_dags(data: dict) -> list:
    dag_schema = {
        'owner': str,
        'domain_id': int,
        'name': str,
        'cron_interval': str,
        'start_date': date,
        'retries': int,
        'tags': list,
        'template': str
    }

    errors = []

    for key, expected_type in dag_schema.items():
        if key not in data:
            errors.append(f"dag.{key} is missing.")
        elif not isinstance(data[key], expected_type):
            errors.append(
                f"dag.{key} should be of type {expected_type.__name__}, "
                f"but got {type(data[key]).__name__}."
            )

    return errors

def validate_inputs(data:dict) -> list:

    sql_template, params = get_sql_template_and_params(data)
    print("Sql template: ", sql_template)
    print("params: ", params)

    errors = []
    return errors

def validate_semantics(config_path):
    try:
        with open(config_path, "r") as f:
            data = yaml.safe_load(f)

    except Exception as e:
        return False, [f"YAML parsing error: {e}"]
    
    #print(data)

    errors = []
    if "dag" not in data:
        errors.append("Missing 'dag' section.")
    else:
        dag_errors = validate_dags(data["dag"])
        errors.extend(dag_errors)
    
    if "inputs" not in data:
        errors.append("Missing input section.")
    else:
        input_errors = validate_inputs(data["inputs"])
        errors.extend(input_errors)

    if not errors:
        print("No type-checking errors.")
    else:
        for error in errors:
            print(error)

    return config_path
    

    sql_template_name, params = get_sql_template_and_params(config)
    print("\n=== Here are the params found in the .yaml file to be rendered into the SQL template by Jinja ===\n")
    print(params)
    print("===")
    sql_template = load_sql_template(sql_template_name[4:])

    vars = extract_jinja_variables(sql_template)

    print("\n=== Here are the params found in the SQL template to be rendered by Jinja ===\n")
    print(vars)
    print("===")



    return config_path