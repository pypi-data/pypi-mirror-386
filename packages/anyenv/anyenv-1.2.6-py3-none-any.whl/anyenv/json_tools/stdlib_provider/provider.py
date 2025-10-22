"""Standard library JSON provider implementation."""

from __future__ import annotations

import datetime
from io import TextIOWrapper
from typing import Any

from anyenv.json_tools.base import JsonDumpError, JsonLoadError, JsonProviderBase
from anyenv.json_tools.utils import handle_datetimes, prepare_numpy_arrays


class StdLibProvider(JsonProviderBase):
    """Standard library implementation of the JSON provider interface."""

    @staticmethod
    def load_json(data: str | bytes | TextIOWrapper) -> Any:
        """Load JSON using stdlib json."""
        import json

        try:
            match data:
                case TextIOWrapper():
                    data = data.read()
                case bytes():
                    data = data.decode()
            return json.loads(data)
        except json.JSONDecodeError as exc:
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
        """Dump data to JSON string using stdlib json."""
        import json

        try:
            # Handle datetime objects first
            data = handle_datetimes(data, naive_utc)

            # Then process numpy arrays if requested
            if serialize_numpy:
                data = prepare_numpy_arrays(data)

            # Standard library's json can't handle datetime objects directly
            # So we need a custom encoder
            class CustomEncoder(json.JSONEncoder):
                def default(self, obj: Any) -> Any:
                    if isinstance(obj, datetime.datetime):
                        return obj.isoformat()
                    return super().default(obj)

            return json.dumps(
                data,
                indent=2 if indent else None,
                cls=CustomEncoder,
                sort_keys=sort_keys,
            )
        except (TypeError, ValueError) as exc:
            error_msg = f"Cannot serialize to JSON: {exc}"
            raise JsonDumpError(error_msg) from exc
