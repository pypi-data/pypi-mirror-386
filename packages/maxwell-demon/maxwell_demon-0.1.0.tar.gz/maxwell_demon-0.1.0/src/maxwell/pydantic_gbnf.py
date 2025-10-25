"""Generic Pydantic to GBNF Grammar Converter.

This module provides utilities to convert Pydantic models to GBNF (Generalized Backus-Naur Form)
grammar for structured LLM output parsing with llama.cpp.

Key Features:
- Automatic grammar generation from Pydantic models
- Support for nested models, lists, unions, enums
- Markdown code block and triple-quoted string handling
- Compatible with llama.cpp grammar constraints

Usage:
    from pydantic import BaseModel
    from maxwell.pydantic_gbnf import generate_gbnf_grammar_and_documentation

    class MyModel(BaseModel):
        name: str
        count: int
        tags: List[str]

__all__ = ["generate_gbnf_grammar_and_documentation", "format_model_and_field_name"]

    grammar, docs = generate_gbnf_grammar_and_documentation([MyModel])

    # Use grammar with llama.cpp
    llm.generate(prompt, grammar=grammar)
"""

from __future__ import annotations

import inspect
import re
from enum import Enum
from inspect import isclass
from typing import TYPE_CHECKING, Any, Optional, Union, get_args, get_origin

from pydantic import BaseModel

if TYPE_CHECKING:
    from types import GenericAlias
else:
    # python 3.8 compat
    from typing import _GenericAlias as GenericAlias


class PydanticDataType(Enum):
    """Defines the data types supported by the grammar_generator."""

    STRING = "string"
    TRIPLE_QUOTED_STRING = "triple_quoted_string"
    MARKDOWN_CODE_BLOCK = "markdown_code_block"
    BOOLEAN = "boolean"
    INTEGER = "integer"
    FLOAT = "float"
    OBJECT = "object"
    ARRAY = "array"
    ENUM = "enum"
    ANY = "any"
    NULL = "null"
    CUSTOM_CLASS = "custom-class"
    CUSTOM_DICT = "custom-dict"
    SET = "set"


def map_pydantic_type_to_gbnf(pydantic_type: type[Any]) -> str:
    """Map a Pydantic type to its GBNF grammar rule name."""
    if isclass(pydantic_type) and issubclass(pydantic_type, str):
        return PydanticDataType.STRING.value
    elif isclass(pydantic_type) and issubclass(pydantic_type, bool):
        return PydanticDataType.BOOLEAN.value
    elif isclass(pydantic_type) and issubclass(pydantic_type, int):
        return PydanticDataType.INTEGER.value
    elif isclass(pydantic_type) and issubclass(pydantic_type, float):
        return PydanticDataType.FLOAT.value
    elif isclass(pydantic_type) and issubclass(pydantic_type, Enum):
        return PydanticDataType.ENUM.value
    elif isclass(pydantic_type) and issubclass(pydantic_type, BaseModel):
        return format_model_and_field_name(pydantic_type.__name__)
    elif get_origin(pydantic_type) is list:
        element_type = get_args(pydantic_type)[0]
        return f"{map_pydantic_type_to_gbnf(element_type)}-list"
    elif get_origin(pydantic_type) is set:
        element_type = get_args(pydantic_type)[0]
        return f"{map_pydantic_type_to_gbnf(element_type)}-set"
    elif get_origin(pydantic_type) is Union:
        union_types = get_args(pydantic_type)
        union_rules = [map_pydantic_type_to_gbnf(ut) for ut in union_types]
        return f"union-{'-or-'.join(union_rules)}"
    elif get_origin(pydantic_type) is Optional:
        element_type = get_args(pydantic_type)[0]
        return f"optional-{map_pydantic_type_to_gbnf(element_type)}"
    elif isclass(pydantic_type):
        return f"{PydanticDataType.CUSTOM_CLASS.value}-{format_model_and_field_name(pydantic_type.__name__)}"
    elif get_origin(pydantic_type) is dict:
        key_type, value_type = get_args(pydantic_type)
        return f"custom-dict-key-type-{format_model_and_field_name(map_pydantic_type_to_gbnf(key_type))}-value-type-{format_model_and_field_name(map_pydantic_type_to_gbnf(value_type))}"
    else:
        return "unknown"


def format_model_and_field_name(model_name: str) -> str:
    """Format model/field names for GBNF rules (CamelCase -> kebab-case)."""
    parts = re.findall("[A-Z][^A-Z]*", model_name)
    if not parts:
        return model_name.lower().replace("_", "-")
    return "-".join(part.lower().replace("_", "-") for part in parts)


def generate_list_rule(element_type):
    """Generate a GBNF rule for a list of a given element type."""
    rule_name = f"{map_pydantic_type_to_gbnf(element_type)}-list"
    element_rule = map_pydantic_type_to_gbnf(element_type)
    list_rule = rf'{rule_name} ::= "["  {element_rule} (","  {element_rule})* "]"'
    return list_rule


def generate_gbnf_rule_for_type(
    model_name,
    field_name,
    field_type,
    is_optional,
    processed_models,
    created_rules,
    field_info=None,
) -> tuple[str, list[str]]:
    """Generate GBNF rule for a given field type."""
    rules = []
    field_name = format_model_and_field_name(field_name)
    gbnf_type = map_pydantic_type_to_gbnf(field_type)

    if isclass(field_type) and issubclass(field_type, BaseModel):
        nested_model_name = format_model_and_field_name(field_type.__name__)
        nested_model_rules, _ = generate_gbnf_grammar(field_type, processed_models, created_rules)
        rules.extend(nested_model_rules)
        gbnf_type, rules = nested_model_name, rules
    elif isclass(field_type) and issubclass(field_type, Enum):
        enum_values = [f'"\\"{e.value}\\""' for e in field_type]
        enum_rule = f"{model_name}-{field_name} ::= {' | '.join(enum_values)}"
        rules.append(enum_rule)
        gbnf_type, rules = model_name + "-" + field_name, rules
    elif get_origin(field_type) is list:
        element_type = get_args(field_type)[0]
        element_rule_name, additional_rules = generate_gbnf_rule_for_type(
            model_name,
            f"{field_name}-element",
            element_type,
            is_optional,
            processed_models,
            created_rules,
        )
        rules.extend(additional_rules)
        array_rule = f"""{model_name}-{field_name} ::= "[" ws {element_rule_name} ("," ws {element_rule_name})*  "]" """
        rules.append(array_rule)
        gbnf_type, rules = model_name + "-" + field_name, rules
    elif get_origin(field_type) is set:
        element_type = get_args(field_type)[0]
        element_rule_name, additional_rules = generate_gbnf_rule_for_type(
            model_name,
            f"{field_name}-element",
            element_type,
            is_optional,
            processed_models,
            created_rules,
        )
        rules.extend(additional_rules)
        array_rule = f"""{model_name}-{field_name} ::= "[" ws {element_rule_name} ("," ws {element_rule_name})*  "]" """
        rules.append(array_rule)
        gbnf_type, rules = model_name + "-" + field_name, rules
    elif gbnf_type.startswith("union-"):
        union_types = get_args(field_type)
        union_rules = []

        for union_type in union_types:
            if isinstance(union_type, GenericAlias):
                union_gbnf_type, union_rules_list = generate_gbnf_rule_for_type(
                    model_name, field_name, union_type, False, processed_models, created_rules
                )
                union_rules.append(union_gbnf_type)
                rules.extend(union_rules_list)
            elif not issubclass(union_type, type(None)):
                union_gbnf_type, union_rules_list = generate_gbnf_rule_for_type(
                    model_name, field_name, union_type, False, processed_models, created_rules
                )
                union_rules.append(union_gbnf_type)
                rules.extend(union_rules_list)

        if len(union_rules) == 1:
            union_grammar_rule = (
                f"{model_name}-{field_name}-optional ::= {' | '.join(union_rules)} | null"
            )
        else:
            union_grammar_rule = f"{model_name}-{field_name}-union ::= {' | '.join(union_rules)}"
        rules.append(union_grammar_rule)
        gbnf_type = (
            f"{model_name}-{field_name}-optional"
            if len(union_rules) == 1
            else f"{model_name}-{field_name}-union"
        )
    else:
        gbnf_type, rules = gbnf_type, []

    return gbnf_type, rules


def generate_gbnf_grammar(
    model: type[BaseModel],
    processed_models: set[type[BaseModel]],
    created_rules: dict[str, list[str]],
) -> tuple[list[str], bool]:
    """Generate GBNF grammar for a given Pydantic model."""
    if model in processed_models:
        return [], False

    processed_models.add(model)
    model_name = format_model_and_field_name(model.__name__)

    if not issubclass(model, BaseModel):
        if hasattr(model, "__annotations__") and model.__annotations__:
            model_fields = {name: (typ, ...) for name, typ in model.__annotations__.items()}
        else:
            init_signature = inspect.signature(model.__init__)
            parameters = init_signature.parameters
            model_fields = {
                name: (param.annotation, param.default)
                for name, param in parameters.items()
                if name != "self"
            }
    else:
        model_fields = model.__annotations__

    model_rule_parts = []
    nested_rules = []

    for field_name, field_info in model_fields.items():
        if not issubclass(model, BaseModel):
            field_type, default_value = field_info
            is_optional = (default_value is not inspect.Parameter.empty) and (
                default_value is not Ellipsis
            )
        else:
            field_type = field_info
            field_info = model.model_fields[field_name]
            is_optional = field_info.is_required is False and get_origin(field_type) is Optional

        rule_name, additional_rules = generate_gbnf_rule_for_type(
            model_name,
            format_model_and_field_name(field_name),
            field_type,
            is_optional,
            processed_models,
            created_rules,
            field_info,
        )

        if rule_name not in created_rules:
            created_rules[rule_name] = additional_rules
        model_rule_parts.append(f' ws "\\"{field_name}\\"" ":" ws {rule_name}')
        nested_rules.extend(additional_rules)

    fields_joined = r' "," "\n" '.join(model_rule_parts)
    model_rule = rf'{model_name} ::= "{{" "\n" {fields_joined} "\n" ws "}}"'

    all_rules = [model_rule] + nested_rules
    return all_rules, False


def generate_gbnf_grammar_from_pydantic_models(
    models: list[type[BaseModel]],
    outer_object_name: str | None = None,
    outer_object_content: str | None = None,
    list_of_outputs: bool = False,
) -> str:
    """Generate GBNF Grammar from Pydantic Models."""
    processed_models: set[type[BaseModel]] = set()
    all_rules = []
    created_rules: dict[str, list[str]] = {}

    if outer_object_name is None:
        for model in models:
            model_rules, _ = generate_gbnf_grammar(model, processed_models, created_rules)
            all_rules.extend(model_rules)

        if list_of_outputs:
            root_rule = (
                r'root ::= (" "| "\n") "[" ws grammar-models ("," ws grammar-models)* ws "]"' + "\n"
            )
        else:
            root_rule = r'root ::= (" "| "\n") grammar-models' + "\n"
        root_rule += "grammar-models ::= " + " | ".join(
            [format_model_and_field_name(model.__name__) for model in models]
        )
        all_rules.insert(0, root_rule)
        return "\n".join(all_rules)
    elif outer_object_name is not None:
        if list_of_outputs:
            root_rule = (
                rf'root ::= (" "| "\n") "[" ws {format_model_and_field_name(outer_object_name)} ("," ws {format_model_and_field_name(outer_object_name)})* ws "]"'
                + "\n"
            )
        else:
            root_rule = f"root ::= {format_model_and_field_name(outer_object_name)}\n"

        model_rule = rf'{format_model_and_field_name(outer_object_name)} ::= (" "| "\n") "{{" ws "\"{outer_object_name}\""  ":" ws grammar-models'

        fields_joined = " | ".join(
            [rf"{format_model_and_field_name(model.__name__)}-grammar-model" for model in models]
        )

        grammar_model_rules = f"\ngrammar-models ::= {fields_joined}"
        mod_rules = []
        for model in models:
            mod_rule = rf"{format_model_and_field_name(model.__name__)}-grammar-model ::= "
            mod_rule += (
                rf'"\"{model.__name__}\"" "," ws "\"{outer_object_content}\"" ":" ws {format_model_and_field_name(model.__name__)}'
                + "\n"
            )
            mod_rules.append(mod_rule)
        grammar_model_rules += "\n" + "\n".join(mod_rules)

        for model in models:
            model_rules, has_special_string = generate_gbnf_grammar(
                model, processed_models, created_rules
            )

            if not has_special_string:
                model_rules[0] += r'"\n" ws "}"'

            all_rules.extend(model_rules)

        all_rules.insert(0, root_rule + model_rule + grammar_model_rules)
        return "\n".join(all_rules)


def get_primitive_grammar(grammar):
    """Returns the needed GBNF primitive grammar for a given GBNF grammar string."""
    type_list: list[type[object]] = []
    if "string-list" in grammar:
        type_list.append(str)
    if "boolean-list" in grammar:
        type_list.append(bool)
    if "integer-list" in grammar:
        type_list.append(int)
    if "float-list" in grammar:
        type_list.append(float)
    additional_grammar = [generate_list_rule(t) for t in type_list]
    primitive_grammar = r"""
boolean ::= "true" | "false"
null ::= "null"
string ::= "\"" (
        [^"\\] |
        "\\" (["\\/bfnrt] | "u" [0-9a-fA-F] [0-9a-fA-F] [0-9a-fA-F] [0-9a-fA-F])
      )* "\"" ws
ws ::= ([ \t\n] ws)?
float ::= ("-"? ([0-9] | [1-9] [0-9]*)) ("." [0-9]+)? ([eE] [-+]? [0-9]+)? ws

integer ::= [0-9]+"""

    return "\n" + "\n".join(additional_grammar) + primitive_grammar


def remove_empty_lines(string):
    """Remove empty lines from a string."""
    lines = string.splitlines()
    non_empty_lines = [line for line in lines if line.strip() != ""]
    string_no_empty_lines = "\n".join(non_empty_lines)
    return string_no_empty_lines


def generate_gbnf_grammar_and_documentation(
    pydantic_model_list,
    outer_object_name: str | None = None,
    outer_object_content: str | None = None,
    model_prefix: str = "Output Model",
    fields_prefix: str = "Output Fields",
    list_of_outputs: bool = False,
    documentation_with_field_description=True,
):
    """Generate GBNF grammar and documentation for a list of Pydantic models.

    Args:
        pydantic_model_list: List of Pydantic model classes.
        outer_object_name: Outer object name for the GBNF grammar.
        outer_object_content: Content for the outer rule in the GBNF grammar.
        model_prefix: Prefix for the model section in the documentation.
        fields_prefix: Prefix for the fields section in the documentation.
        list_of_outputs: Whether the output is a list of items.
        documentation_with_field_description: Include field descriptions in the documentation.

    Returns:
        tuple: GBNF grammar string, documentation string.

    """
    grammar = generate_gbnf_grammar_from_pydantic_models(
        pydantic_model_list, outer_object_name, outer_object_content, list_of_outputs
    )
    grammar = remove_empty_lines(grammar + get_primitive_grammar(grammar))

    # Generate simple documentation
    documentation = f"# {model_prefix}\n\n"
    for model in pydantic_model_list:
        documentation += f"## {model.__name__}\n\n"
        documentation += f"{fields_prefix}:\n"
        for field_name, field_type in model.__annotations__.items():
            documentation += f"- {field_name}: {field_type}\n"
        documentation += "\n"

    return grammar, documentation
