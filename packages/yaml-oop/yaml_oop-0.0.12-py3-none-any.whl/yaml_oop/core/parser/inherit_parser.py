import sys
import os
from typing import Dict, Any, Set, Optional
from yaml_oop.core.custom_errors import (
    KeySealedError,
    ConflictingDeclarationError,
    NoOverrideError,
    InvalidVariableError,
    InvalidInstantiationError,
    InvalidDeclarationError,
)

import yaml_oop.core.parser.config_parser as config_parser
import yaml_oop.core.parser.next_parser as next_parser
from ..declarations import DeclarationType
from .context import ProcessingContext
from .parse_functions import remove_all_key_declarations


def process_inherit(
    sub_data: dict,
    base_data: dict,
    context: ProcessingContext
) -> None:

    if DeclarationType.BASE_CONFIG in base_data:
        config_parser.process_base_config_declaration(yaml_data=base_data,
                                                      context=context)

    # Map matches the base_data keys to the sub keys with their declarations.
    # sub_key_map Key = parsed key (no declaration)
    # sub_key_map Value = Full key
    sub_key_map = _map_parsed_sub_keys(sub_data)

    # List containing:
    # [base_key (without declarations), full_key (with_declaratios), list of declarations]
    base_key_list = _list_parsed_base_keys(base_data)

    # Iterate through parsed base keys and perform inheritance logic
    for parsed_base_key, full_base_key in base_key_list:

        # Initialize base declaration logic
        full_base_key, base_key_declarations = context.extract_base_declarations(base_data, full_base_key)
        if DeclarationType.PRIVATE in base_key_declarations:
            continue  # Do no inherit private keys

        # Matching sub_key does not exist. Apply full inheritance logic.
        if parsed_base_key not in sub_key_map:
            if DeclarationType.ABSTRACT in context.base_declarations or DeclarationType.ABSTRACT in base_key_declarations:
                raise NotImplementedError(f"Base YAML declares abstract, but base key: '{parsed_base_key}' is not implemented in sub YAML: '{sub_data}'.")
            if DeclarationType.OVERRIDE in context.sub_declarations:
                # If override was declared for a key.
                # New keys are not inherited.
                continue
            next_parser.process_next(
                yaml_data=base_data[full_base_key],
                context=ProcessingContext(
                    directory=context.directory,
                    loader=context.loader,
                    variables=context.variables,
                    sub_files=context.sub_files.copy(),
                )
            )
            remove_all_key_declarations(base_data[full_base_key], "key", DeclarationType.PRIVATE)
            sub_data[full_base_key] = base_data[full_base_key]
            continue

        # Matching sub_key exists. Apply standard inheritance logic.
        sub_key = sub_key_map.pop(parsed_base_key)
        sub_key, sub_key_declarations = context.extract_sub_declarations(sub_data, sub_key)
        # Catch case where type mismatch between base and sub occurs
        if sub_key in sub_data and is_type_mismatch(sub_data[sub_key], base_data[full_base_key]):
            raise TypeError(f"Type mismatch for base YAML key: '{full_base_key}': {type(base_data[full_base_key])}, and sub YAML key: '{sub_key}': {type(sub_data[sub_key])}.")
        # Cannot inherit from sealed base keys
        if DeclarationType.SEALED in context.base_declarations or DeclarationType.SEALED in base_key_declarations:
            raise KeySealedError(f"Cannot override base key: '{full_base_key}' when base key is sealed.")
        if type(base_data[full_base_key]) is dict:
            process_inherit(
                sub_data=sub_data[sub_key],
                base_data=base_data[full_base_key],
                context=ProcessingContext(
                    directory=context.directory,
                    loader=context.loader,
                    variables=context.variables,
                    sub_files=context.sub_files.copy(),
                    sub_declarations=context.sub_declarations.copy() | sub_key_declarations,
                    base_declarations=context.base_declarations.copy() | base_key_declarations
                )
            )
        elif type(base_data[full_base_key]) is list:
            if DeclarationType.APPEND in sub_key_declarations:
                sub_data[sub_key] = _process_append_prepend(sub_data[sub_key], base_data[full_base_key], "append", context)
                continue
            if DeclarationType.PREPEND in sub_key_declarations:
                sub_data[sub_key] = _process_append_prepend(sub_data[sub_key], base_data[full_base_key], "prepend", context)
                continue
            if DeclarationType.MERGE in sub_key_declarations:
                sub_data[sub_key] = _process_merge(sub_data[sub_key], base_data[full_base_key], context)
                continue
            if DeclarationType.OVERRIDE not in sub_key_declarations | context.sub_declarations and \
               DeclarationType.ABSTRACT not in base_key_declarations | context.base_declarations:
                raise NoOverrideError(f"No override declared for '{sub_key}' list despite having matching key in base_config.")
        elif base_data[full_base_key] is not None:  # Data is scalar
            if DeclarationType.OVERRIDE in sub_key_declarations | context.sub_declarations:
                continue  # Maintain sub_data's values.
            raise NoOverrideError(f"No override declared for '{sub_key}' scalar despite having matching key in base_config.")
        else:  # Data is None
            continue  # Maintain sub_data's values.

    # Process remaining sub_data keys that did not match base_data keys
    for sub_key in sub_key_map.values():
        sub_key, sub_key_declarations = context.extract_sub_declarations(sub_data, sub_key)
        if DeclarationType.APPEND in sub_key_declarations or DeclarationType.PREPEND in sub_key_declarations or DeclarationType.MERGE in sub_key_declarations:
            raise InvalidDeclarationError(f"Key: '{sub_key}' cannot declare append, prepend, or merge without an immediate base key to inherit from.")
        next_data = next_parser.process_next(
            yaml_data=sub_data[sub_key],
            context=ProcessingContext(
                directory=context.directory,
                loader=context.loader,
                variables=context.variables,
                sub_files=context.sub_files.copy(),
                sub_declarations=context.sub_declarations.copy() | sub_key_declarations,
            )
        )
        sub_data[sub_key] = next_data if next_data is not None else sub_data[sub_key]


def _process_append_prepend(sub_data, base_data, mode: str, context: ProcessingContext):
    """Append sub_data's values to base_data's values and return new list."""

    remove_all_key_declarations(base_data, "key", DeclarationType.PRIVATE)
    next_parser.process_next(
        yaml_data=base_data,
        context=ProcessingContext(
            directory=context.directory,
            loader=context.loader,
            variables=context.variables,
            sub_files=context.sub_files.copy(),
        )
    )

    # Catch case where appending into empty key
    base_data = base_data if base_data is not None else []
    sub_data = sub_data if sub_data is not None else []
    
    # Append or prepend
    if mode == "append":
        return base_data + sub_data
    elif mode == "prepend":
        return sub_data + base_data
    else:
        # Should not reach this point
        raise Exception("Incorrect mode arg in process_append_prepend function call. Please open a Github issue with your given input.")


def _process_merge(sub_data, base_data, context: ProcessingContext):
    """Merge base_data's list values into sub_data's list values and return new list.
       Merging involving applying inheritance rules to each item of matching index in sub and base lists."""

    total_length = max(len(sub_data), len(base_data))
    for i in range(total_length):
        if i >= len(sub_data):
            sub_data.append(base_data[i])
        elif i >= len(base_data):
            pass
        elif sub_data[i] is None:
            sub_data[i] = base_data[i]
        elif base_data[i] is None:
            pass
        else:
            # Sub and base both have values, so apply inheritance rules
            # Apply inheritance rules only if both sub and base are dicts
            if (type(sub_data[i]) is not dict and base_data[i] is not None) or \
               (type(base_data[i]) is not dict and sub_data[i] is not None):
                raise TypeError(f"Cannot merge list items at index {i} because one or both items are not dictionaries.")
            process_inherit(
                sub_data=sub_data[i],
                base_data=base_data[i],
                context=ProcessingContext(
                    directory=context.directory,
                    loader=context.loader,
                    variables=context.variables,
                    sub_files=context.sub_files.copy(),
                )
            )
    return sub_data


def _map_parsed_sub_keys(sub_data: dict) -> dict:
    """Map parsed sub keys to their declaration and full key.
       Key = parsed key (no declaration)
       Value = full key."""
    key_map = {}
    for full_key in sub_data:
        parsed_key = _key_without_declaration(full_key)
        key_map[parsed_key] = full_key
    return key_map


def _list_parsed_base_keys(base_data: dict) -> list:
    """List parsed base keys to their declaration and full key.
       Value = parsed key, full key."""
    key_list = []
    for full_key in base_data:
        parsed_key = _key_without_declaration(full_key)
        key_list.append((parsed_key, full_key))
    return key_list


def _key_without_declaration(key: str) -> str:
    """Returns the key without any declarations."""
    if key == "" or key is None:
        return ""
    return " ".join([
        item for item in key.split()
        if item not in DeclarationType.BASE_KEY_DECLARATIONS and item not in DeclarationType.SUB_KEY_DECLARATIONS
    ])


def is_type_mismatch(sub_data, base_data) -> bool:
    """Returns true if types of base and sub prevent inheritance."""
    if sub_data is None or base_data is None:
        return False
    # Empty dicts or lists are essentially None
    elif not sub_data or not base_data:
        return False
    elif type(base_data) is not type(sub_data):
        return True
    # sub and base are both non-empty dicts or non-empty lists
    return False
