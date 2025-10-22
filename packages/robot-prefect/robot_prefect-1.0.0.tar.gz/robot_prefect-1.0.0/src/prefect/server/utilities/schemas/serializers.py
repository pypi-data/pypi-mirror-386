import json
from typing import Any, TypeVar

from pydantic import BaseModel

T = TypeVar("T")
B = TypeVar("B", bound=BaseModel)


def orjson_dumps(v: Any, *, default: Any) -> str:
    """
    Utility for dumping a value to JSON using orjson.

    orjson.dumps returns bytes, to match standard json.dumps we need to decode.
    """
    return json.dumps(v, default=default)


def orjson_dumps_extra_compatible(v: Any, *, default: Any) -> str:
    """
    Utility for dumping a value to JSON using orjson
    """
    return json.dumps(v, default=default)
