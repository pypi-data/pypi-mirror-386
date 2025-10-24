"""
Commands for interacting with the JITX parts database.

This module provides functions for communicating with the JITX parts database.
"""

import asyncio
import json
import logging
from collections.abc import Sequence, Mapping
from typing import Any, TypeAlias, Callable, Awaitable
from jitx._websocket import set_websocket_uri, on_websocket_message
from jitx._instantiation import InstantiationStructureException
from jitx.design import DesignContext, name
from jitx.units import PlainQuantity

JSON: TypeAlias = (
    Mapping[str, "JSON"] | Sequence["JSON"] | str | int | float | bool | None
)
# PartJSON must be 'dict', not 'Mapping' in order to match the input type of `from_dict` in dataclasses_json/api.py
# so that type checking passes for the `from_dict` calls.
PartJSON = dict[str, JSON]
QueryParamValue: TypeAlias = float | int | str | Sequence[float | int | str]

# Configure logging
logging = logging.getLogger(__name__)


async def _dbquery_async(
    args: Mapping[str, QueryParamValue],
    limit: int,
    skip_cache: bool = False,
) -> Sequence[PartJSON]:
    """Internal async function to send a dbquery request to the JITX server.

    Args:
        args: The query parameters
        limit: Maximum number of results to return
        skip_cache: Whether to skip cached results

    Returns:
        A list of results
    """

    # Categorize args by type according to the dbquery-schema
    int_args = []
    double_args = []
    string_args = []
    tuple_string_args = []
    tuple_double_args = []

    for key, value in args.items():
        if isinstance(value, str):
            string_args.append([key, value])
        elif isinstance(value, int):
            int_args.append([key, value])
        elif isinstance(value, float):
            double_args.append([key, value])
        elif isinstance(value, PlainQuantity):
            scalar = value.to_base_units().magnitude
            double_args.append([key, scalar])
        elif isinstance(value, Sequence):
            if all(isinstance(x, str) for x in value):
                tuple_string_args.append([key, list(value)])
            elif all(isinstance(x, int | float) for x in value):
                tuple_double_args.append(
                    [key, [float(x) for x in value]]
                )  # Convert all numeric values to float
            else:
                raise ValueError(f"Mixed type tuples not supported for key: {key}")
        else:
            raise ValueError(f"Unsupported value type for key {key}: {type(value)}")

    query = {
        "design-name": get_design_name(),
        "int-args": int_args,
        "string-args": string_args,
        "double-args": double_args,
        "tuple-string-args": tuple_string_args,
        "tuple-double-args": tuple_double_args,
        "limit": limit,
        "skipCache": skip_cache,
    }

    async def on_response_in_progress(message: dict[str, Any], send_message):
        # Check if message is a prompt for input.
        match message.get("type"):
            # Forward stdout line by line from server.
            case "stdout":
                print(message["body"]["message"])
            case _:
                raise RuntimeError(f"Unhandled response in progress type: {message}")

    def on_error(body: dict[str, Any]):
        if "message" in body:
            error_msg = body["message"]
            raise RuntimeError(error_msg)
        else:
            raise RuntimeError(f"Unknown error format. Received: {body}")

    def on_success(body: dict[str, Any]):
        return body["message"]

    def on_connection_closed(e):
        raise RuntimeError("dbquery connection closed.") from e

    return await on_websocket_message(
        "dbquery",
        query,
        on_response_in_progress,
        on_error,
        on_success,
        on_connection_closed,
        "parts-db",
    )


# Used in tests, disables per-design part locking.
ALLOW_NO_DESIGN_CONTEXT = False


def get_design_name() -> str | None:
    try:
        ctx = DesignContext.get()
        if ctx is None:
            if ALLOW_NO_DESIGN_CONTEXT:
                return None
            raise RuntimeError(
                "The Parts Database cannot be queried outside of the context of a Design."
            )
        return name(ctx.design)
    except InstantiationStructureException as e:
        raise RuntimeError(
            "The parts database can only be queried during the instantiation of a JITX Design, typically in the __init__ method of a Circuit subclass.\n"
            "You may be trying to use it to define a class attribute?"
        ) from e


def dbquery(
    args: Mapping[str, QueryParamValue], limit: int = 1000, skip_cache: bool = False
) -> Sequence[PartJSON]:
    """Query the JITX parts database.

    The function automatically categorizes arguments by their type to be sent to the server:
        - int-args: tuple[tuple[str, int], ...]
        - double-args: tuple[tuple[str, float], ...]
        - string-args: tuple[tuple[str, str], ...]
        - tuple-double-args: tuple[tuple[str, tuple[float, ...]], ...]
        - tuple-string-args: tuple[tuple[str, tuple[str, ...]], ...]

    The function also passes the following parameters along to the server:
        - limit: int
        - skip_cache: bool

    Args:
        args: The query parameters
        limit: Maximum number of results to return
        skip_cache: Whether to skip cached results

    Returns:
        A list of matching components
    """
    try:
        return asyncio.run(_dbquery_async(args, limit, skip_cache))
    except Exception as e:
        logging.error(f"dbquery failed: {e}")
        raise


def download_model3d(filepath: str) -> None:
    """Download a model 3D file from the JITX parts database.

    Args:
        filepath: The path to the model 3D file
    """
    try:
        asyncio.run(_download_model3d(filepath))
    except Exception as e:
        logging.debug(f"download_model_3d failed: {e}")
        raise


async def _download_model3d(filepath: str):
    """Download a model 3D file from the JITX parts database.

    Args:
        filepath: The path to the model 3D file
    """

    async def on_response_in_progress(
        message: dict[str, Any],
        send_message: Callable[[str, dict[str, Any]], Awaitable[None]],
    ):
        match message.get("type"):
            # Prompt user for input.
            case "stdin":
                answer = input()
                # Send user answer back to server.
                await send_message("stdin", {"message": answer})
            # Forward stdout line by line from server.
            case "stdout":
                logging.info(message["body"]["message"])
            case _:
                raise RuntimeError(f"Unhandled response in progress type: {message}")

    def on_error(body: dict[str, Any]):
        if "message" in body:
            error_msg = body["message"]
            raise RuntimeError(error_msg)
        else:
            raise RuntimeError(f"Error. Received: {body}")

    def on_success(body: dict[str, Any]):
        if "message" in body:
            logging.info(body["message"])
            return body["message"]
        return None

    def on_connection_closed(e: Exception):
        raise RuntimeError("Connection closed while running design") from e

    return await on_websocket_message(
        "download-model3d",
        {"filepath": filepath},
        on_response_in_progress,
        on_error,
        on_success,
        on_connection_closed,
        "client",
    )


if __name__ == "__main__":
    try:
        # Simple test query with minimal data
        set_websocket_uri(host="localhost", port=7681)
        result = dbquery({"category": "resistor", "resistance": 10000.0}, limit=1)
        print("Result content:")
        # del result[0]["sellers"]
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error running query: {e}")
