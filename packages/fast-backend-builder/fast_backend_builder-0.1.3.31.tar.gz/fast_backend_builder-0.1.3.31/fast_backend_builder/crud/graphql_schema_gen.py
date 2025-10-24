import os
import ast
from pathlib import Path

import strawberry
from tortoise import fields
from typing import List
import importlib.resources

from fast_backend_builder.utils.file import get_file_content

models_package = 'fast_backend_builder.muarms.models'  # This should be a Python package, not a directory


# Step 1: Traverse the folder and collect all Python files
def get_python_files(package_name: str) -> List[str]:
    """
    Returns a list of Python file paths (as strings) in the given package,
    excluding __init__.py files. Works for both installed packages and local folders.
    """
    try:
        # Try to import the package
        package = importlib.import_module(package_name)
        package_dir = Path(package.__file__).parent
    except ModuleNotFoundError:
        # Fallback: assume it's a local folder relative to cwd
        package_dir = Path.cwd() / Path(*package_name.split("."))
        if not package_dir.exists():
            raise ModuleNotFoundError(f"Cannot find package '{package_name}'")

    # Recursively collect all .py files, excluding __init__.py
    py_files = [str(p) for p in package_dir.rglob("*.py") if p.name != "__init__.py"]

    return py_files


# Step 2: Parse files to look for class definitions and Tortoise fields
def get_class_fields_from_file(file_path: str):
    file_content = get_file_content(
        file_path)  # Assuming this is a function that retrieves the file content as a string

    # Parse the file using AST
    tree = ast.parse(file_content)
    class_fields = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # Step 3: Check for Tortoise ORM fields in the class body
            fields_in_class = {}
            for stmt in node.body:
                if isinstance(stmt, ast.Assign):
                    for target in stmt.targets:
                        if isinstance(target, ast.Name) and isinstance(stmt.value, ast.Call):
                            field_name = target.id
                            # Check if stmt.value.func is an instance of ast.Name (simple field call)
                            if isinstance(stmt.value.func, ast.Name):
                                field_type = stmt.value.func.id
                                if hasattr(fields, field_type):  # Check if it's a Tortoise field
                                    fields_in_class[field_name] = field_type
                            # Handle more complex cases where stmt.value.func might be an attribute
                            elif isinstance(stmt.value.func, ast.Attribute):
                                # You can extend this if necessary to capture more complex expressions
                                field_type = stmt.value.func.attr  # This captures something like "fields.CharField"
                                if hasattr(fields, field_type):
                                    fields_in_class[field_name] = field_type
            if fields_in_class:
                class_fields[node.name] = fields_in_class

    return class_fields


# Step 4: Convert Tortoise fields to GraphQL input types
def create_graphql_input_fields(class_fields: dict):
    field_definitions = {}
    for field_name, field_type in class_fields.items():
        if field_type == 'CharField':
            field_definitions[field_name] = 'str'
        elif field_type == 'JSONField':
            field_definitions[field_name] = 'str'
        elif field_type == 'TextField':
            field_definitions[field_name] = 'str'
        elif field_type == 'IntField':
            field_definitions[field_name] = 'int'
        elif field_type == 'DecimalField':
            field_definitions[field_name] = 'float'
        elif field_type == 'FloatField':
            field_definitions[field_name] = 'float'
        elif field_type == 'BooleanField':
            field_definitions[field_name] = 'bool'
        elif field_type == 'DateField':
            field_definitions[field_name] = 'str'
        elif field_type == 'DateTimeField':
            field_definitions[field_name] = 'str'
        elif field_type == 'ForeignKeyField':
            field_definitions[f"{field_name}_id"] = 'str'
    return field_definitions


def create_graphql_type_fields(class_fields: dict):
    field_definitions = {}
    for field_name, field_type in class_fields.items():
        if field_type == 'CharField':
            field_definitions[field_name] = 'str'
        elif field_type == 'JSONField':
            field_definitions[field_name] = 'str'
        elif field_type == 'TextField':
            field_definitions[field_name] = 'str'
        elif field_type == 'IntField':
            field_definitions[field_name] = 'int'
        elif field_type == 'DecimalField':
            field_definitions[field_name] = 'float'
        elif field_type == 'FloatField':
            field_definitions[field_name] = 'float'
        elif field_type == 'BooleanField':
            field_definitions[field_name] = 'bool'
        elif field_type == 'DateField':
            field_definitions[field_name] = 'str'
        elif field_type == 'DateTimeField':
            field_definitions[field_name] = 'str'
        elif field_type == 'ForeignKeyField':
            field_definitions[f"{field_name}_id"] = 'str'
    return field_definitions


# Main function to process the entire folder
def generate_schemas(module_package: str, model_name: str, is_response: bool = False):
    current_directory = os.getcwd()
    python_files = get_python_files(module_package)

    schemas = dict()

    for file_path in python_files:
        class_fields = get_class_fields_from_file(file_path)
        if class_fields:

            for class_name, fields in class_fields.items():
                graphql_input_fields = create_graphql_input_fields(fields)
                if model_name == class_name:
                    schema = dict()
                    schema[class_name] = graphql_input_fields
                    return schema
                else:
                    schemas[class_name] = graphql_input_fields
    if model_name is None:
        return schemas
    else:
        return False


# Example usage
if __name__ == "__main__":
    generate_schemas('Country')
