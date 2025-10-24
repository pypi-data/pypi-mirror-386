from __future__ import annotations

import base64
import hashlib
import json
import uuid
from itertools import groupby
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

import httpx
import ujson
from graphql import (
    FieldNode,
    InlineFragmentNode,
    SelectionSetNode,
)

from infrahub_sdk.repository import GitRepoManager

from .exceptions import FileNotValidError, JsonDecodeError, TimestampFormatError
from .timestamp import Timestamp

if TYPE_CHECKING:
    from graphql import GraphQLResolveInfo
    from whenever import TimeDelta


def generate_short_id() -> str:
    """Generate a short unique ID"""
    return base64.urlsafe_b64encode(uuid.uuid4().bytes).rstrip(b"=").decode("ascii").lower()


def base36encode(number: int) -> str:
    if not isinstance(number, (int)):
        raise TypeError("number must be an integer")
    is_negative = number < 0
    number = abs(number)

    alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    base36 = ""

    while number:
        number, i = divmod(number, 36)
        base36 = alphabet[i] + base36
    if is_negative:
        base36 = "-" + base36

    return base36 or alphabet[0]


def base36decode(data: str) -> int:
    return int(data, 36)


def base16decode(data: str) -> int:
    return int(data, 16)


def base16encode(number: int) -> str:
    if not isinstance(number, (int)):
        raise TypeError("number must be an integer")
    is_negative = number < 0
    number = abs(number)

    alphabet = "0123456789abcdef"
    base16 = ""

    while number:
        number, i = divmod(number, 16)
        base16 = alphabet[i] + base16
    if is_negative:
        base16 = "-" + base16

    return base16 or alphabet[0]


def get_fixtures_dir() -> Path:
    """Get the directory which stores fixtures that are common to multiple unit/integration tests."""
    here = Path(__file__).resolve().parent
    return here.parent / "tests" / "fixtures"


def is_valid_uuid(value: Any) -> bool:
    """Check if the input is a valid UUID."""
    try:
        UUID(str(value))
        return True
    except ValueError:
        return False


def decode_json(response: httpx.Response) -> dict:
    try:
        return response.json()
    except json.decoder.JSONDecodeError as exc:
        raise JsonDecodeError(content=response.text, url=str(response.url)) from exc


def generate_uuid() -> str:
    return str(uuid4())


def duplicates(input_list: list) -> list:
    """Identify and return all the duplicates in a list."""

    dups = []

    clean_input_list = [item for item in input_list or [] if item is not None]
    for x, y in groupby(sorted(clean_input_list)):
        #  list(y) returns all the occurences of item x
        if len(list(y)) > 1:
            dups.append(x)

    return dups


def intersection(list1: list[Any], list2: list[Any]) -> list:
    """Calculate the intersection between 2 lists."""
    return list(set(list1) & set(list2))


def compare_lists(list1: list[Any], list2: list[Any]) -> tuple[list[Any], list[Any], list[Any]]:
    """Compare 2 lists and return :
    - the intersection of both
    - the item present only in list1
    - the item present only in list2
    """

    in_both = intersection(list1=list1, list2=list2)
    in_list_1 = list(set(list1) - set(in_both))
    in_list_2 = list(set(list2) - set(in_both))

    return sorted(in_both), sorted(in_list_1), sorted(in_list_2)


def deep_merge_dict(dicta: dict, dictb: dict, path: list | None = None) -> dict:
    """Deep Merge Dictionary B into Dictionary A.
    Code is inspired by https://stackoverflow.com/a/7205107
    """
    if path is None:
        path = []
    for key in dictb:
        b_val = dictb[key]
        if key in dicta:
            a_val = dicta[key]
            if isinstance(a_val, dict) and isinstance(b_val, dict):
                deep_merge_dict(a_val, b_val, path + [str(key)])
            elif isinstance(a_val, list) and isinstance(b_val, list):
                # Merge lists
                # Cannot use compare_list because list of dicts won't work (dict not hashable)
                dicta[key] = [i for i in a_val if i not in b_val] + b_val
            elif a_val is None and b_val is not None:
                dicta[key] = b_val
            elif a_val == b_val or (a_val is not None and b_val is None):
                continue
            else:
                raise ValueError("Conflict at %s" % ".".join(path + [str(key)]))
        else:
            dicta[key] = dictb[key]
    return dicta


def str_to_bool(value: str) -> bool:
    """Convert a String to a Boolean"""

    if isinstance(value, bool):
        return value

    if isinstance(value, int) and value in [0, 1]:
        return bool(value)

    if not isinstance(value, str):
        raise TypeError(f"{value} must be a string")

    MAP = {
        "y": True,
        "yes": True,
        "t": True,
        "true": True,
        "on": True,
        "1": True,
        "n": False,
        "no": False,
        "f": False,
        "false": False,
        "off": False,
        "0": False,
    }
    try:
        return MAP[value.lower()]
    except KeyError as exc:
        raise ValueError(f"{value} can not be converted into a boolean") from exc


def generate_request_filename(request: httpx.Request) -> str:
    """Return a filename for a request sent to the Infrahub API

    This function is used when recording and playing back requests, as Infrahub is using a GraphQL
    API it's not possible to rely on the URL endpoint alone to separate one request from another,
    for this reason a hash of the payload is included in a filename.
    """
    formatted = (
        str(request.url).replace(":", "_").replace("//", "").replace("/", "__").replace("?", "_q_").replace("&", "_a_")
    )
    filename = f"{request.method}_{formatted}"
    if request.content:
        content_hash = hashlib.sha224(request.content)
        filename += f"_{content_hash.hexdigest()}"

    return filename.lower()


def is_valid_url(url: str) -> bool:
    if not isinstance(url, str):
        return False
    if "://" not in url and not url.startswith("/"):
        return False
    if "://" not in url:
        url = "http://localhost" + url

    try:
        parsed = httpx.URL(url)
        return all([parsed.scheme, parsed.netloc])
    except TypeError:
        return False


def get_branch(branch: str | None = None, directory: str | Path = ".") -> str:
    """If branch isn't provide, return the name of the local Git branch."""
    if branch:
        return branch

    repo = GitRepoManager(root_directory=str(directory))
    return str(repo.active_branch)


def dict_hash(dictionary: dict[str, Any]) -> str:
    """MD5 hash of a dictionary."""
    # We need to sort arguments so {'a': 1, 'b': 2} is
    # the same as {'b': 2, 'a': 1}
    encoded = ujson.dumps(dictionary, sort_keys=True).encode()
    dhash = hashlib.md5(encoded, usedforsecurity=False)
    return dhash.hexdigest()


def calculate_dict_depth(data: dict, level: int = 1) -> int:
    """Calculate the depth of a nested Dictionary recursively."""
    if not isinstance(data, dict) or not data:
        return level
    return max(calculate_dict_depth(data=data[key], level=level + 1) for key in data)


def calculate_dict_height(data: dict, cnt: int = 0) -> int:
    """Calculate the number of fields (height) in a nested Dictionary recursively."""
    for key in data:
        if isinstance(data[key], dict):
            cnt = calculate_dict_height(data=data[key], cnt=cnt + 1)
        else:
            cnt += 1
    return cnt


async def extract_fields(selection_set: SelectionSetNode | None) -> dict[str, dict] | None:
    """This function extract all the requested fields in a tree of Dict from a SelectionSetNode

    The goal of this function is to limit the fields that we need to query from the backend.

    Currently the function support Fields and InlineFragments but in a combined tree where the fragments are merged together
    This implementation may seam counter intuitive but in the current implementation
    it's better to have slightly more information at time passed to the query manager.

    In the future we'll probably need to redesign how we read GraphQL queries to generate better Database query.
    """

    if not selection_set:
        return None

    fields = {}
    for node in selection_set.selections:
        sub_selection_set = getattr(node, "selection_set", None)
        if isinstance(node, FieldNode):
            value = await extract_fields(sub_selection_set)
            if node.name.value not in fields:
                fields[node.name.value] = value
            elif isinstance(fields[node.name.value], dict) and isinstance(value, dict):
                fields[node.name.value].update(value)

        elif isinstance(node, InlineFragmentNode):
            for sub_node in node.selection_set.selections:
                sub_sub_selection_set = getattr(sub_node, "selection_set", None)
                value = await extract_fields(sub_sub_selection_set)
                if sub_node.name.value not in fields:
                    fields[sub_node.name.value] = await extract_fields(sub_sub_selection_set)
                elif isinstance(fields[sub_node.name.value], dict) and isinstance(value, dict):
                    fields[sub_node.name.value].update(value)

    return fields


async def extract_fields_first_node(info: GraphQLResolveInfo) -> dict[str, dict]:
    fields = None
    if info.field_nodes:
        fields = await extract_fields(info.field_nodes[0].selection_set)

    return fields or {}


def write_to_file(path: Path, value: Any) -> bool:
    """Write a given value into a file and return if the operation was successful.

    If the file does not exist, the function will attempt to create it."""
    if not path.exists():
        path.touch()

    if path.is_dir():
        raise FileExistsError(f"{path} is a directory")

    to_write = str(value)
    written = path.write_text(to_write)

    return written is not None


def read_file(file_path: Path) -> str:
    if not file_path.is_file():
        raise FileNotValidError(name=str(file_path.name), message=f"{file_path.name}: not found at {file_path.parent}")
    try:
        with Path.open(file_path, encoding="utf-8") as fobj:
            return fobj.read()
    except UnicodeDecodeError as exc:
        raise FileNotValidError(
            name=str(file_path.name), message=f"Unable to read {file_path.name} with utf-8 encoding"
        ) from exc


def get_user_permissions(data: list[dict]) -> dict:
    groups = {}
    for group in data:
        group_name = group["node"]["display_label"]
        permissions = []

        roles = group["node"].get("roles", {}).get("edges", [])
        for role in roles:
            role_permissions = role["node"].get("permissions", {}).get("edges", [])
            for permission in role_permissions:
                permissions.append(permission["node"]["identifier"]["value"])

        groups[group_name] = permissions

    return groups


def calculate_time_diff(value: str) -> str | None:
    """Calculate the time in human format between a timedate in string format and now."""
    try:
        time_value = Timestamp(value)
    except TimestampFormatError:
        return None

    delta: TimeDelta = Timestamp().get_obj().difference(time_value.get_obj())
    (hrs, mins, secs, nanos) = delta.in_hrs_mins_secs_nanos()

    if nanos and nanos > 500_000_000:
        secs += 1

    if hrs and hrs < 24 and mins:
        return f"{hrs}h {mins}m and {secs}s ago"
    if hrs and hrs > 24:
        remaining_hrs = hrs % 24
        days = int((hrs - remaining_hrs) / 24)
        return f"{days}d and {remaining_hrs}h ago"
    if hrs == 0 and mins and secs:
        return f"{mins}m and {secs}s ago"
    if hrs == 0 and mins == 0 and secs:
        return f"{secs}s ago"
    return "now"
