# semantic_validator.py

import yaml
from jinja2 import Environment, meta
from datetime import date

type_map = {
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "list": list,
    "dict": dict,
    "null": type(None),
    "none": type(None),
    "date": str, 
    "datetime": str
}

def get_sql_template_and_params(inputs):

    if not inputs or not isinstance(inputs[0], dict):
        return None, None
    
    input_entry = inputs[0]  # assumes only one input block — or just using the first
    sql_template = input_entry.get("sql_template")
    sql_params = input_entry.get("sql_params", {})

    with open(sql_template) as f:
        raw = yaml.safe_load(f)
    sql_schema =  {k: parse_type(v) for k, v in raw.items()}

    return sql_template, sql_params, sql_schema
        
def load_sql_template(template_name, folder="sql_templates"):
    path = f"{folder}/{template_name}"
    with open(path, "r") as f:
        return f.read()

def extract_jinja_variables(sql_text):
    env = Environment()
    ast = env.parse(sql_text)
    return meta.find_undeclared_variables(ast)

def validate_dags(data) -> list:
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

    if not isinstance(data, dict):
        errors.append(f"dag should be of type dict but got {type(data).__name__}")
        return errors

    for key, expected_type in dag_schema.items():
        if key not in data:
            errors.append(f"dag.{key} is missing.")
        elif not isinstance(data[key], expected_type):
            errors.append(
                f"dag.{key} should be of type {expected_type.__name__}, "
                f"but got {type(data[key]).__name__}."
            )

    return errors

def parse_type(val):
    if isinstance(val, list):
        return tuple(type_map[v] for v in val)
    return type_map[val]

def validate_inputs(inputs) -> list:
    errors = []

    input_schema = {
        'operation': str,
        'redis_conn_id': str,
        'jdbc_conn_id': str,
        'pre_sql_template': str,
        'sql_template': str,
        'sql_params': list,
        'id': str
    }

    if not isinstance(inputs, dict):
        errors.append(f"inputs should be of type dict but got {type(inputs).__name__}")
        return errors
    
    for key, expected_type in input_schema.items():
        if key not in inputs:
            errors.append(f"inputs.{key} is missing.")
        elif not isinstance(inputs[key], expected_type):
            errors.append(
                f"inputs.{key} should be of type {expected_type.__name__}, "
                f"but got {type(inputs[key]).__name__}."
            )

    sql_template, params, expected_schema = get_sql_template_and_params(inputs)
    print("Sql template: ", sql_template)
    print("params: ", params)
    print("sql schema: ", expected_schema)

    # Check for missing fields
    for key in expected_schema:
        if key not in params:
            errors.append(f"sql_params.{key} is missing.")
        elif not isinstance(params[key], expected_schema[key]):
            expected_name = (
                ", ".join([t.__name__ for t in expected_schema[key]])
                if isinstance(expected_schema[key], tuple)
                else expected_schema[key].__name__
            )
            errors.append(
                f"sql_params.{key} should be {expected_name}, "
                f"got {type(params[key]).__name__}."
            )

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

    # add functionality for the outputs section in the file

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