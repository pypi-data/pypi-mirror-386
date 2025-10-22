import json
from typing import Any


def orjson_dumps(v: Any, *, default: Any) -> str:
    """
    Utility for dumping a value to JSON using orjson.

    orjson.dumps returns bytes, to match standard json.dumps we need to decode.
    """
    return json.dumps(v, default=default)


def orjson_dumps_extra_compatible(v: Any, *, default: Any) -> str:
    """
    Utility for dumping a value to JSON.
    """
    return json.dumps(v, default=default, ensure_ascii=False)
