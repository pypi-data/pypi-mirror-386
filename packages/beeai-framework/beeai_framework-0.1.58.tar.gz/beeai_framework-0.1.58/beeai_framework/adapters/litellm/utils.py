# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Any

import litellm
from openai.lib._pydantic import _ensure_strict_json_schema
from pydantic import BaseModel

from beeai_framework.backend import ChatModelError
from beeai_framework.backend.utils import parse_broken_json
from beeai_framework.utils.dicts import traverse
from beeai_framework.utils.models import is_pydantic_model


def parse_extra_headers(
    settings_headers: dict[str, Any] | None = None,
    env_headers: str | None = None,
) -> dict[str, str]:
    """
    Parses extra headers from settings and/or environment variables.

    Args:
        settings_headers: Extra headers provided in settings.
        env_headers: Extra headers from the environment variable.

    Returns:
        A dictionary of extra headers or {} if no headers are found.

    """
    extra_headers: dict[str, str] = {}

    # Priority 2: Environment variable (provider-specific)
    if env_headers:
        extra_headers = _parse_header_string(env_headers)

    # Priority 1: Settings (highest priority)
    if settings_headers is None:
        pass
    elif isinstance(settings_headers, dict):
        extra_headers = settings_headers
    else:
        # Should be unreachable. protect against not passing dict/None
        raise ValueError(
            f"Invalid settings_headers format. Expected a dictionary or None, received {type(settings_headers)}"
        )

    return extra_headers


def _parse_header_string(header_string: str) -> dict[str, str]:
    """Parses a comma-separated string of headers into a dictionary."""
    from beeai_framework.logger import Logger

    logger = Logger(__name__)

    headers: dict[str, str] = {}
    if not header_string:
        return headers
    header_string = header_string.strip()
    for pair in header_string.split(","):
        pair = pair.strip()
        if "=" in pair:
            key, value = pair.split("=", 1)
            headers[key.strip()] = value.strip()
        else:
            logger.warning(f"Malformed header string detected. Will ignore it: {pair}")
    return headers


def litellm_debug(enable: bool = True) -> None:
    litellm.set_verbose = enable  # type: ignore
    litellm.suppress_debug_info = not enable

    litellm.suppress_debug_info = not enable
    litellm.logging = enable

    litellm_logger = logging.getLogger("LiteLLM")
    litellm_logger.setLevel(logging.DEBUG if enable else logging.CRITICAL + 1)


def to_strict_json_schema(model: type[BaseModel] | dict[str, Any]) -> dict[str, Any]:
    json_schema = model if isinstance(model, dict) else model.model_json_schema()

    if json_schema.get("type") == "object":
        json_schema["additionalProperties"] = False

    strict_schema = _ensure_strict_json_schema(json_schema, path=(), root=json_schema)
    for obj, _ in traverse(strict_schema):
        if obj.get("type") == "object" and "additionalProperties" in obj:
            obj["additionalProperties"] = False
    return strict_schema


def process_structured_output(schema: dict[str, Any] | type[BaseModel] | None, text: str) -> Any:
    try:
        data = parse_broken_json(text)
        if schema and is_pydantic_model(schema):
            return schema.model_validate(data, strict=False)
        else:
            return data
    except Exception as e:
        raise ChatModelError(
            "The model failed to satisfy the schema given in the response format.", context={"input": text}
        ) from e
