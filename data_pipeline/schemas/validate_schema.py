#!/usr/bin/env python3
"""
JSON Schema validation utility for Telemetra message types.

Usage:
    python validate_schema.py <schema_file> <message_json>

Example:
    python validate_schema.py chat_message.json '{"message_id": "...", ...}'
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any

try:
    from jsonschema import validate, ValidationError, Draft7Validator
except ImportError:
    print("Error: jsonschema package not installed")
    print("Install with: pip install jsonschema")
    sys.exit(1)


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load JSON schema from file"""
    with open(schema_path, 'r') as f:
        return json.load(f)


def validate_message(schema: Dict[str, Any], message: Dict[str, Any]) -> bool:
    """
    Validate a message against a schema.

    Returns True if valid, False otherwise.
    Prints validation errors to stderr.
    """
    try:
        validator = Draft7Validator(schema)
        validator.validate(message)
        return True
    except ValidationError as e:
        print(f"Validation Error: {e.message}", file=sys.stderr)
        print(f"Failed at path: {' -> '.join(str(p) for p in e.path)}", file=sys.stderr)
        return False


def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <schema_file> <message_json>")
        print(f"\nExample:")
        print(f"  {sys.argv[0]} chat_message.json '{{'\"message_id\": \"test\"}}'\n")
        sys.exit(1)

    schema_file = Path(sys.argv[1])
    message_json = sys.argv[2]

    # Load schema
    if not schema_file.exists():
        print(f"Error: Schema file not found: {schema_file}", file=sys.stderr)
        sys.exit(1)

    try:
        schema = load_schema(schema_file)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in schema file: {e}", file=sys.stderr)
        sys.exit(1)

    # Parse message
    try:
        message = json.loads(message_json)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in message: {e}", file=sys.stderr)
        sys.exit(1)

    # Validate
    if validate_message(schema, message):
        print(f"✓ Message is valid according to {schema_file.name}")
        sys.exit(0)
    else:
        print(f"✗ Message is invalid according to {schema_file.name}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
