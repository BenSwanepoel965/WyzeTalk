# semantic_validator.py

import yaml
from ruamel.yaml import YAML
from jinja2 import Environment, meta
from datetime import date
from pathlib import Path
from collections import defaultdict

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
    """
    Loads the SQL template schema and parameter values based on the input entry.

    Args:
        inputs (list[dict]): List of input dictionaries from the YAML file.

    Returns:
        tuple[dict or None, dict or None]: 
            - The 'sql_params' dict from the input entry.
            - The expected schema loaded from the corresponding SQL schema YAML file.
    """


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
    """
    Loads the raw SQL template text from a file.

    Args:
        template_name (str): Filename of the SQL template.
        folder (str): Directory where SQL templates are stored.

    Returns:
        str: Raw contents of the SQL template file.
    """

    path = f"{folder}/{template_name}"
    with open(path, "r") as f:
        return f.read()

def extract_jinja_variables(sql_text):
    """
    Parses the SQL template using Jinja2 and extracts all undeclared variables.

    Args:
        sql_text (str): Jinja-enabled SQL template string.

    Returns:
        set[str]: A set of variable names used in the template.
    """

    env = Environment()
    ast = env.parse(sql_text)
    return meta.find_undeclared_variables(ast)

def validate_dags(data, config_path, yaml_data) -> list:
    """
    Validates the 'dag' section of the YAML file against a predefined schema.

    Args:
        data (dict): Parsed 'dag' section from YAML.
        config_path (str): Path to the YAML file (used for error messages).
        yaml_data (ruamel.yaml object): Full parsed YAML content with line number metadata.

    Returns:
        list[str]: List of formatted error/info messages for the dag section.
    """

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
        key_line = node.lc.key(key)[0]
        key_line = (key_line + 1) if key_line is not None else section_line
        if key not in data:
            errors.append(f"{filename}:{key_line}:0: [info] dag.{key} was found in the schema but not in the config file.")
        elif not isinstance(data[key], expected_type):
            actual_type = type(data[key]).__name__
            expected_name = expected_type.__name__
            errors.append(
                    f"{filename}:{key_line}:0: [error] Field 'dag.{key}' should be {expected_name}, got {actual_type}"
            )

    return errors

def parse_type(val):
    """
    Maps a YAML schema type string (or list of strings) to Python type(s) using the global type_map.

    Args:
        val (str or list): Type name(s) from the SQL parameter schema.

    Returns:
        type or tuple[type]: Corresponding Python type or tuple of types.
    """

    if isinstance(val, list):
        return tuple(type_map[v] for v in val)
    return type_map[val]

def validate_inputs(inputs, config_path, yaml_data) -> list:
    """
    Validates the 'inputs' section against a predefined schema and cross-checks with the SQL template schema.

    Args:
        inputs (list[dict]): List of input entries from YAML.
        config_path (str): Path to the config YAML file.
        yaml_data (ruamel.yaml object): Full parsed YAML with line metadata.

    Returns:
        list[str]: List of errors and info messages for the 'inputs' and 'sql_params' sections.
    """

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
                errors.append(f"{filename}:{node_line}:0: [info] inputs.{key} was found in the schema but not in the config file.")
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

def validate_output(data, config_path, yaml_data) -> list:
    """
    Validates the 'outputs' section and its nested 'operations' fields using hierarchical schema checks.

    Args:
        data (list[dict]): List of output entries from YAML.
        config_path (str): Path to the YAML config file.
        yaml_data (ruamel.yaml object): Full parsed YAML data with line metadata.

    Returns:
        list[str]: List of errors and info messages for the 'outputs' section and its operations.
    """


    output_schema = {
        'process': str,
        'operations': dict,
        'id': str
    }

    operations_schema = {
        'UploadToAzureStorageFromRedis': dict,
        'GenerateSasLink': dict,
        'Email': dict,
    }

    upload_schema = {
        'redis_conn_id': str,
        'container_name': str,
        'folder_path': str,
        'filename': str,
        'file_type': str,
        'password': str
    }

    email_schema  = {
        'recipients': list,
        'bcc_recipients': list,
        'subject': str,
        'body': str
    }


    errors = []
    filename = Path(config_path).name

    section_line = yaml_data.lc.key('ouputs')[0]
    section_line = (section_line + 1) if section_line is not None else 0

    if not isinstance(data, list):
        errors.append(f"{filename}:{section_line}:0: [error] outputs should be a list, got {type(data).__name__}")
        return errors
    
    node = yaml_data['ouputs']

    for i, entry in enumerate(data):
        if not isinstance(entry, dict):
            errors.append(f"{filename}:{section_line}:0: [error] outputs should be a dict, got {type(entry).__name__}")
            continue

        for key, expected_type in output_schema.items():
            key_line = node[i].lc.key(key)[0] if node[i].lc.key(key) is not None else section_line
            key_line = (key_line + 1) if key_line is not None else section_line

            if key not in entry:
                errors.append(f"{filename}:{key_line}:0: [info] outputs.{key} was found in the schema but not in the config file.")
            elif not isinstance(entry[key], expected_type):
                actual_type = type(entry[key]).__name__
                expected_name = expected_type.__name__
                errors.append(f"{filename}:{key_line}:0: [error] Field 'outputs.{key}' should be {expected_name}, got {actual_type}")

        if 'operations' in entry:
            if isinstance(entry['operations'], dict):
                ops = entry['operations']
                for op_key, expected_type in operations_schema.items():
                    op_line = node[i]['operations'].lc.key(op_key)[0] if node[i]['operations'].lc.key(op_key) else section_line
                    op_line = (op_line + 1) if op_line is not None else section_line

                    if op_key not in ops:
                        errors.append(f"{filename}:{op_line}:0: [info] outputs.operations.{op_key} was found in the schema but not in the config file.")
                        continue
                    elif not isinstance(ops[op_key], expected_type) and ops[op_key] is not None:
                        actual_type = type(ops[op_key]).__name__
                        expected_name = expected_type.__name__
                        errors.append(f"{filename}:{op_line}:0: [error] outputs.operations.{op_key} should be {expected_name}, got {actual_type}")
                        continue

                    # Validate inner structures
                    if op_key == 'UploadToAzureStorageFromRedis':
                        if isinstance(ops[op_key], dict):
                            for field, expected_type in upload_schema.items():
                                if field not in ops[op_key]:
                                    errors.append(f"{filename}:{op_line}:0: [info] outputs.operations.{op_key}.{field} was found in the schema but not in the config file.")
                                elif not isinstance(ops[op_key][field], expected_type):
                                    actual = type(ops[op_key][field]).__name__
                                    expected = expected_type.__name__
                                    errors.append(f"{filename}:{op_line}:0: [error] outputs.operations.{op_key}.{field} should be {expected}, got {actual}")
                        else:
                            errors.append(f"{filename}:{section_line}:0: [error] outputs.operations.UploadToAzureStorageFromRedis should be dict, got {type(ops[op_key]).__name__}.")

                    elif op_key == 'GenerateSasLink':
                        if isinstance(ops[op_key], dict):
                            for k, v in ops[op_key].items():
                                if not isinstance(v, str):
                                    val_type = type(v).__name__
                                    errors.append(f"{filename}:{op_line}:0: [error] outputs.operations.GenerateSasLink.{k} should be str, got {val_type}")
                        else:
                            errors.append(f"{filename}:{section_line}:0: [error] outputs.operations.GenerateSasLink should be dict, got {type(ops[op_key]).__name__}.")

                    elif op_key == 'Email':
                        if isinstance(ops[op_key], dict):
                            for field, expected_type in email_schema.items():
                                if field not in ops[op_key]:
                                    errors.append(f"{filename}:{op_line}:0: [info] outputs.operations.Email.{field} was found in the schema but not in the config file.")
                                elif not isinstance(ops[op_key][field], expected_type):
                                    actual = type(ops[op_key][field]).__name__
                                    expected = expected_type.__name__
                                    errors.append(f"{filename}:{op_line}:0: [error] outputs.operations.Email.{field} should be {expected}, got {actual}")
                        else:
                            errors.append(f"{filename}:{section_line}:0: [error] outputs.operations.Email should be dict, got {type(ops[op_key]).__name__}.")

            else:
                errors.append(f"{filename}:{section_line}:0: [error] outputs.operations should be dict, got {type(entry['operations']).__name__}.")
        else:
            errors.append(f"{filename}:{section_line}:0: [error] outputs.operations was found in the schema but is missing in the config file.")


    return errors

def validate_semantics(config_path):
    """
    Loads a YAML file and performs semantic validation on its 'dag', 'inputs', and 'outputs' sections.

    Args:
        config_path (str): Path to the YAML file.

    Returns:
        str: Path to the YAML file (for consistency with syntax validator).
    """


    #print("\n===== ", config_path, " =====\n")
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
        output_errors = validate_output(data['ouputs'], config_path, data)
        errors.extend(output_errors)
    

    # add functionality for the outputs section in the file

    if not errors:
        print("No type-checking errors.")
    else:
        grouped = defaultdict(list)
        for error in errors:
            if "]" in error:
                tag_start = error.find("[")
                tag_end = error.find("]", tag_start) + 1
                tag = error[tag_start:tag_end]
                grouped[tag].append(error)
            else:
                grouped["[misc]"].append(error)

        tag_labels = {
            "[error]": "Errors",
            "[info]": "Info"
        }

        for tag in sorted(grouped):
            print(f"\n{tag_labels.get(tag, tag)}:")
            for error in grouped[tag]:
                print(f"  {error}")

    

    return config_path
