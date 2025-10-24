from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel

VARIABLE_TYPE_MAPPING = ((str, "String!"), (int, "Int!"), (float, "Float!"), (bool, "Boolean!"))


def convert_to_graphql_as_string(value: str | bool | list | BaseModel | Enum | Any, convert_enum: bool = False) -> str:  # noqa: PLR0911
    if isinstance(value, str) and value.startswith("$"):
        return value
    if isinstance(value, Enum):
        if convert_enum:
            return convert_to_graphql_as_string(value=value.value, convert_enum=True)
        return value.name
    if isinstance(value, str):
        return f'"{value}"'
    if isinstance(value, bool):
        return repr(value).lower()
    if isinstance(value, list):
        values_as_string = [convert_to_graphql_as_string(value=item, convert_enum=convert_enum) for item in value]
        return "[" + ", ".join(values_as_string) + "]"
    if isinstance(value, BaseModel):
        data = value.model_dump()
        return (
            "{ "
            + ", ".join(
                f"{key}: {convert_to_graphql_as_string(value=val, convert_enum=convert_enum)}"
                for key, val in data.items()
            )
            + " }"
        )

    return str(value)


def render_variables_to_string(data: dict[str, type[str | int | float | bool]]) -> str:
    """Render a dict into a variable string that will be used in a GraphQL Query.

    The $ sign will be automatically added to the name of the query.
    """
    vars_dict = {}
    for key, value in data.items():
        for class_type, var_string in VARIABLE_TYPE_MAPPING:
            if value == class_type:
                vars_dict[f"${key}"] = var_string

    return ", ".join([f"{key}: {value}" for key, value in vars_dict.items()])


def render_query_block(data: dict, offset: int = 4, indentation: int = 4, convert_enum: bool = False) -> list[str]:
    FILTERS_KEY = "@filters"
    ALIAS_KEY = "@alias"
    KEYWORDS_TO_SKIP = [FILTERS_KEY, ALIAS_KEY]

    offset_str = " " * offset
    lines = []
    for key, value in data.items():
        if key in KEYWORDS_TO_SKIP:
            continue
        if value is None:
            lines.append(f"{offset_str}{key}")
        elif isinstance(value, dict) and len(value) == 1 and ALIAS_KEY in value and value[ALIAS_KEY]:
            lines.append(f"{offset_str}{value[ALIAS_KEY]}: {key}")
        elif isinstance(value, dict):
            if value.get(ALIAS_KEY):
                key_str = f"{value[ALIAS_KEY]}: {key}"
            else:
                key_str = key

            if value.get(FILTERS_KEY):
                filters_str = ", ".join(
                    [
                        f"{key2}: {convert_to_graphql_as_string(value=value2, convert_enum=convert_enum)}"
                        for key2, value2 in value[FILTERS_KEY].items()
                    ]
                )
                lines.append(f"{offset_str}{key_str}({filters_str}) " + "{")
            else:
                lines.append(f"{offset_str}{key_str} " + "{")

            lines.extend(
                render_query_block(
                    data=value, offset=offset + indentation, indentation=indentation, convert_enum=convert_enum
                )
            )
            lines.append(offset_str + "}")

    return lines


def render_input_block(data: dict, offset: int = 4, indentation: int = 4, convert_enum: bool = False) -> list[str]:
    offset_str = " " * offset
    lines = []
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"{offset_str}{key}: " + "{")
            lines.extend(
                render_input_block(
                    data=value, offset=offset + indentation, indentation=indentation, convert_enum=convert_enum
                )
            )
            lines.append(offset_str + "}")
        elif isinstance(value, list):
            lines.append(f"{offset_str}{key}: " + "[")
            for item in value:
                if isinstance(item, dict):
                    lines.append(f"{offset_str}{' ' * indentation}" + "{")
                    lines.extend(
                        render_input_block(
                            data=item,
                            offset=offset + indentation + indentation,
                            indentation=indentation,
                            convert_enum=convert_enum,
                        )
                    )
                    lines.append(f"{offset_str}{' ' * indentation}" + "},")
                else:
                    lines.append(
                        f"{offset_str}{' ' * indentation}{convert_to_graphql_as_string(value=item, convert_enum=convert_enum)},"
                    )
            lines.append(offset_str + "]")
        else:
            lines.append(f"{offset_str}{key}: {convert_to_graphql_as_string(value=value, convert_enum=convert_enum)}")
    return lines


class BaseGraphQLQuery:
    query_type: str = "not-defined"
    indentation: int = 4

    def __init__(self, query: dict, variables: dict | None = None, name: str | None = None):
        self.query = query
        self.variables = variables
        self.name = name or ""

    def render_first_line(self) -> str:
        first_line = self.query_type

        if self.name:
            first_line += " " + self.name

        if self.variables:
            first_line += f" ({render_variables_to_string(self.variables)})"

        first_line += " {"

        return first_line


class Query(BaseGraphQLQuery):
    query_type = "query"

    def render(self, convert_enum: bool = False) -> str:
        lines = [self.render_first_line()]
        lines.extend(
            render_query_block(
                data=self.query, indentation=self.indentation, offset=self.indentation, convert_enum=convert_enum
            )
        )
        lines.append("}")

        return "\n" + "\n".join(lines) + "\n"


class Mutation(BaseGraphQLQuery):
    query_type = "mutation"

    def __init__(self, *args: Any, mutation: str, input_data: dict, **kwargs: Any):
        self.input_data = input_data
        self.mutation = mutation
        super().__init__(*args, **kwargs)

    def render(self, convert_enum: bool = False) -> str:
        lines = [self.render_first_line()]
        lines.append(" " * self.indentation + f"{self.mutation}(")
        lines.extend(
            render_input_block(
                data=self.input_data,
                indentation=self.indentation,
                offset=self.indentation * 2,
                convert_enum=convert_enum,
            )
        )
        lines.append(" " * self.indentation + "){")
        lines.extend(
            render_query_block(
                data=self.query,
                indentation=self.indentation,
                offset=self.indentation * 2,
                convert_enum=convert_enum,
            )
        )
        lines.append(" " * self.indentation + "}")
        lines.append("}")

        return "\n" + "\n".join(lines) + "\n"
