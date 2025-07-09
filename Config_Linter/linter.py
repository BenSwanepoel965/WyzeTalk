# linter.py

import argparse
import os
from syntax_validator import validate_syntax
from semantic_validator import validate_semantics

def find_config_path(filename, base_dir="Configs"):
    for root, _, files in os.walk(base_dir):
        
        if filename in files:
            return os.path.join(root, filename)
    return None


def main():
    parser = argparse.ArgumentParser(description="Lint YAML config files for templated SQL reports.")
    parser.add_argument("config_path", help="Path to the YAML config file")

    args = parser.parse_args()
    config_file = args.config_path
    print(config_file)

    #path_to_config = config_file
    path_to_config = find_config_path(config_file)

    print("found file at: ", path_to_config)

    path_to_config = validate_syntax(path_to_config)

    path_to_config = validate_semantics(path_to_config)


if __name__ == "__main__":
    main()