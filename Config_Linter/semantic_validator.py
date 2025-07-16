# semantic_validator.py

import yaml
from ruamel.yaml import YAML
from jinja2 import Environment, meta
from datetime import date
from pathlib import Path

ruamel_yaml = YAML()
ruamel_yaml.preserve_quotes = True

type_map = {
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "list": list,
    "dict": dict,
    "null": type(None),
    "none": type(None),
    "date": date, 
    "datetime": str
}

def get_sql_template_and_params(inputs):

    if not inputs or not isinstance(inputs[0], dict):
        return None, None
    
    input_entry = inputs[0] 
    sql_schema_path = "Schemas/" + input_entry.get("sql_template")[4:-4] + "_schema.yaml"
    #print(sql_schema_path)
    sql_params = input_entry.get("sql_params", {})

    current_file = Path(__file__)
    workspace_dir = current_file.parent
    sql_schema_path = workspace_dir / sql_schema_path

    with open(sql_schema_path) as f:
        sql_schema = yaml.safe_load(f)

    return sql_params, sql_schema
        
def load_sql_template(template_name, folder="sql_templates"):
    path = f"{folder}/{template_name}"
    with open(path, "r") as f:
        return f.read()

def extract_jinja_variables(sql_text):
    env = Environment()
    ast = env.parse(sql_text)
    return meta.find_undeclared_variables(ast)

def validate_dags(data, config_path, yaml_data) -> list:
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
    filename = Path(config_path).name
    section_line = yaml_data.lc.key('dag')[0]
    section_line = (section_line + 1) if section_line is not None else 0

    if not isinstance(data, dict):
        errors.append(f"{filename}:{section_line}:0: [error] dag should be a dict, got {type(data).__name__}")
        return errors
    
    node = yaml_data['dag']
    for key, expected_type in dag_schema.items():
        if key not in data:
            errors.append(f"{filename}:{section_line}:0: [error] Missing field 'dag.{key}'")
        elif not isinstance(data[key], expected_type):
            actual_type = type(data[key]).__name__
            expected_name = expected_type.__name__
            key_line = node.lc.key(key)[0]
            key_line = (key_line + 1) if key_line is not None else section_line
            errors.append(
                    f"{filename}:{key_line}:0: [error] Field 'dag.{key}' should be {expected_name}, got {actual_type}"
            )

    if not errors:
        errors.append(f"No errors in dag section.")
    return errors

def parse_type(val):
    if isinstance(val, list):
        return tuple(type_map[v] for v in val)
    return type_map[val]

def validate_inputs(inputs, config_path, yaml_data) -> list:
    errors = []
    filename = Path(config_path).name

    #print(inputs)

    input_schema = {
        'operation': str,
        'redis_conn_id': str,
        'jdbc_conn_id': str,
        'pre_sql_template': str,
        'sql_template': str,
        'sql_params': dict,
        'id': str
    }

    if not isinstance(inputs, list):
        errors.append(f"{filename}:0:0: [error] inputs should be a list, got {type(inputs).__name__}")
        return errors
    
    for i, item in enumerate(inputs):
        node = yaml_data['inputs'][i]
        node_line = node.lc.line + 1
        for key, expected_type in input_schema.items():
            #print("key: ", key)
            #print("expected type: ", expected_type)
            if key not in item:
                errors.append(f"{filename}:{node_line}:0: [error] Missing field 'inputs[{i}].{key}'")
            elif not isinstance(item[key], expected_type):
                if not isinstance(item[key], type(None)):
                    actual_type = type(item[key]).__name__
                    expected_name = expected_type.__name__
                    key_line = node.lc.key(key)
                    key_line = (key_line + 1) if key_line is not None else node_line
                    errors.append(
                        f"{filename}:{key_line}:0: [error] Field 'inputs[{i}].{key}' should be {expected_name}, got {actual_type}"
                    )

    params, expected_schema = get_sql_template_and_params(inputs)
    #print("params: ", params)
    #print("sql schema: ", expected_schema)

    # Check for missing fields
    for key in expected_schema:
        schema_type = parse_type(expected_schema[key])
        node_line += 1
        if key not in params:
            errors.append(f"{filename}:{node_line}:0: [info] sql_params.{key} was found in the SQL template but not in the config file.")
        elif not isinstance(params[key], schema_type):
            expected_name = (
                ", ".join([t.__name__ for t in schema_type])
                if isinstance(schema_type, tuple)
                else schema_type.__name__
            )
            actual_type = type(params[key]).__name__
            errors.append(
                f"{filename}:{node_line}:0: [error] sql_params.{key} should be {expected_name}, got {actual_type}."
            )

    return errors

def validate_output(outputs, config_path) -> list:
    errors = []
    return errors

def report_issue(file_path, line, column, message, level="error"):
    print(f"{file_path}:{line}:{column}: [{level}] {message}")


def validate_semantics(config_path):
    try:
        #with open(config_path, "r") as f:
        with open(config_path) as f:
            #data = yaml.safe_load(f)
            data = ruamel_yaml.load(f)

    except Exception as e:
        print("File could not be opened for semantical analysis.")
        return False, [f"YAML parsing error: {e}"]
    
    #print(data)

    errors = []
    if "dag" not in data:
        errors.append("Missing 'dag' section.")
    else:
        dag_errors = validate_dags(data["dag"], config_path, data)
        errors.extend(dag_errors)
    
    if "inputs" not in data:
        errors.append("Missing input section.")
    else:
        input_errors = validate_inputs(data["inputs"], config_path, data)
        errors.extend(input_errors)

    if "ouputs" not in data:
        errors.append("Missing output sections.")
    else:
        output_errors = validate_output(data['ouputs'], config_path)
        errors.extend(output_errors)
    

    # add functionality for the outputs section in the file

    if not errors:
        print("No type-checking errors.")
    else:
        for error in errors:
            print(error)

    return config_path