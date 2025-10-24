"""
Component saving functionality for the JITX parts database.

This module provides functions to save component data from JSON to Python files.
"""

import json
import sys

from jitx._websocket import set_websocket_uri
from .convert import create_component
from .commands import PartJSON


def save_component_command(json_arg: str | None, port_arg: int) -> None:
    """CLI wrapper for the save-component command."""
    try:
        # Get JSON input - either from --json argument or stdin
        if json_arg:
            json_input = json_arg
        else:
            # Read from stdin
            json_input = sys.stdin.read().strip()
            if not json_input:
                raise ValueError(
                    "No JSON input provided. Use --json argument or provide JSON via stdin."
                )

        # Call the clean API function
        result = save_component(port_arg, json_input)

        # Output the results
        print(json.dumps(result, indent=2))

    except Exception as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)


def save_component(port: int, json_input: str) -> dict[str, str]:
    """Save a component from JSON data to a Python file.

    Creates a new Python file containing a jitx.Component class definition based on the
    provided part JSON data. The file is saved at ``components/<manufacturer>/Component<mpn>.py``
    and any referenced 3D models are downloaded to the same directory.

    Args:
        port: Port number for websocket connection to JITX server.
        json_input: JSON string containing component data.

    Returns:
        Dictionary with 'package' (import statement) and 'path' (file location).

    Raises:
        json.JSONDecodeError: If the provided JSON is invalid.
        RuntimeError: If component creation or file writing fails.

    Example:
        >>> result = save_component(7681, '{"mpn": "LM317LM", "manufacturer": "ON Semiconductor"}')
        >>> print(result['path'])
        ./components/ON_Semiconductor/ComponentLM317LM.py
    """
    # Set websocket URI for 3D model downloads
    set_websocket_uri(host="localhost", port=port)

    # Parse JSON and create component
    part_json: PartJSON = json.loads(json_input)
    package_reference, path = create_component(part_json)

    return {"package": package_reference, "path": path}
