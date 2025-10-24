"""OrJSON provider implementation."""

from __future__ import annotations

from io import TextIOWrapper
from typing import Any

from anyenv.json_tools.base import JsonDumpError, JsonLoadError, JsonProviderBase


class OrJsonProvider(JsonProviderBase):
    """OrJSON implementation of the JSON provider interface."""

    @staticmethod
    def load_json(data: str | bytes | TextIOWrapper) -> Any:
        """Load JSON using orjson."""
        import orjson

        try:
            match data:
                case TextIOWrapper():
                    data = data.read()
                case str():
                    data = data.encode()
            return orjson.loads(data)
        except orjson.JSONDecodeError as exc:
            error_msg = f"Invalid JSON: {exc}"
            raise JsonLoadError(error_msg) from exc

    @staticmethod
    def dump_json(
        data: Any,
        indent: bool = False,
        naive_utc: bool = False,
        serialize_numpy: bool = False,
        sort_keys: bool = False,
    ) -> str:
        """Dump data to JSON string using orjson."""
        import orjson

        try:
            options = 0
            if indent:
                options = orjson.OPT_INDENT_2
            if naive_utc:
                options |= orjson.OPT_NAIVE_UTC
            if serialize_numpy:
                options |= orjson.OPT_SERIALIZE_NUMPY
            if sort_keys:
                options |= orjson.OPT_SORT_KEYS
            result = orjson.dumps(data, option=options)
            return result.decode()
        except (TypeError, ValueError) as exc:
            error_msg = f"Cannot serialize to JSON: {exc}"
            raise JsonDumpError(error_msg) from exc
