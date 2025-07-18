# linter.py

import argparse
import os
from syntax_validator import validate_syntax
from semantic_validator import validate_semantics

def find_config_path(filename, base_dir="Configs"):
    """
    Recursively searches for a given filename within a base directory (default: 'Configs').

    Args:
        filename (str): Name of the YAML config file to locate.
        base_dir (str): Root directory to begin the search.

    Returns:
        str or None: Full path to the file if found, otherwise None.
    """

    for root, _, files in os.walk(base_dir):
        
        if filename in files:
            return os.path.join(root, filename)
    return None


def main():
    """
    Main entry point for the YAML linter.

    Parses command-line arguments, runs syntax validation using yamllint,
    and then runs semantic validation using custom schema checks.
    """
    
    parser = argparse.ArgumentParser(description="Lint YAML config files for templated SQL reports.")
    parser.add_argument("config_path", help="Path to the YAML config file")

    args = parser.parse_args()
    config_file = args.config_path

    path_to_config = config_file
    #path_to_config = find_config_path(config_file)

    #print("found file at: ", path_to_config)
    print("=== Starting syntax analysis. ===\n")
    path_to_config = validate_syntax(path_to_config)
    print("\n=== Starting semantic analysis. ===\n")
    path_to_config = validate_semantics(path_to_config)


if __name__ == "__main__":
    main()