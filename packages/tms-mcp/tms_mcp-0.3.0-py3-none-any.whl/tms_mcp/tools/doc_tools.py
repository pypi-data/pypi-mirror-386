"""
Documentation tools for the Omelet Routing Engine MCP server.
"""

import json
import os
from pathlib import Path
from typing import Annotated, Any

from tms_mcp.config import settings
from tms_mcp.pipeline.utils import load_markdown_with_front_matter
from tms_mcp.server import mcp

provider_configs = settings.pipeline_config.provider_configs


def _get_docs_dir() -> Path:
    """Get the docs directory path."""
    return Path(__file__).parent.parent / "docs"


def _get_integration_patterns_dir() -> Path:
    """Get the integration patterns directory path."""
    return _get_docs_dir() / "integration_patterns"


def _get_troubleshooting_dir() -> Path:
    """Get the troubleshooting guides directory path."""
    return _get_docs_dir() / "troubleshooting"


def _get_provider_from_path(path: str) -> str:
    """
    Determine the provider based on the API path using configuration.

    Args:
        path: API endpoint path

    Returns:
        Provider name ("omelet" or "inavi")
    """
    # Check each provider's path prefix from configuration
    for provider_name, provider_config in provider_configs.items():
        prefix = provider_config.path_prefix
        if path.startswith(prefix):
            return provider_name

    # Default to omelet for non-matching paths
    return "omelet"


def _path_to_path_id(path: str, provider: str | None = None) -> str:
    """
    Convert API path to path_id format based on provider configuration.

    Args:
        path: API path (e.g., "/api/foo/bar" or "/maps/v3.0/appkeys/{appkey}/coordinates")
        provider: Optional provider name to determine conversion logic

    Returns:
        Path ID (e.g., "foo_bar" for Omelet, "coordinates" for iNavi)
    """
    # Auto-detect provider if not specified
    if provider is None:
        provider = _get_provider_from_path(path)

    # Get provider configuration
    provider_config = provider_configs.get(provider)
    if not provider_config:
        # Fallback to default behavior
        return "_".join(path.strip("/").split("/"))

    # Remove the provider's path prefix
    prefix = provider_config.path_prefix
    if path.startswith(prefix):
        endpoint_name = path[len(prefix) :].strip("/")
    else:
        endpoint_name = path.strip("/")

    return endpoint_name.replace("/", "_")


def _read_text_file(file_path: Path) -> str:
    """
    Helper function to read a text file with error handling.

    Args:
        file_path: Path to the file to read

    Returns:
        Content of the file or error message if file cannot be read
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        return f"Error: {file_path.name} file not found."
    except Exception as e:
        return f"Error reading {file_path.name}: {str(e)}"


def _read_json_file(file_path: Path, file_type: str, path: str, path_id: str) -> str:
    """
    Helper function to read a JSON file and return formatted content.

    Args:
        file_path: Path to the JSON file
        file_type: Type of file for error messages (e.g., "overview", "schema")
        path: Original API path for error messages
        path_id: Converted path ID for error messages

    Returns:
        Formatted JSON content or error message if file cannot be read
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            json_data = json.load(file)
            return json.dumps(json_data, indent=2, ensure_ascii=False)
    except FileNotFoundError:
        return f"Error: {file_type.capitalize()} file for '{path}' (path_id: {path_id}) not found."
    except json.JSONDecodeError as e:
        return f"Error: Invalid JSON in {file_type} file for '{path}': {str(e)}"
    except Exception as e:
        return f"Error reading {file_type} for '{path}': {str(e)}"


def _resolve_provider_and_path_id(path: str, provider: str | None) -> tuple[str, str]:
    """
    Resolve provider and convert path to path_id.

    Args:
        path: API endpoint path
        provider: Optional provider name

    Returns:
        Tuple of (resolved_provider, path_id)
    """
    resolved_provider = provider.lower() if provider is not None else _get_provider_from_path(path)
    path_id = _path_to_path_id(path, resolved_provider)
    return resolved_provider, path_id


def _get_json_file_content(path: str, provider: str | None, file_subpath: str, file_type: str) -> str:
    """
    Generic function to get JSON file content for an endpoint.

    Args:
        path: API endpoint path
        provider: Optional provider name
        file_subpath: Subpath within the provider directory (e.g., "overviews", "schemas/request_body")
        file_type: Type of file for error messages

    Returns:
        JSON content or error message
    """
    resolved_provider, path_id = _resolve_provider_and_path_id(path, provider)
    file_path = _get_docs_dir() / resolved_provider / file_subpath / f"{path_id}.json"
    return _read_json_file(file_path, file_type, path, path_id)


def _sanitize_document_id(document_id: str) -> list[str] | None:
    """Validate and normalize a nested document identifier."""

    if not document_id:
        return None

    parts = [part for part in document_id.strip().split("/") if part]
    if not parts:
        return None

    for part in parts:
        if part in {".", ".."}:
            return None

    return parts


def _read_integration_pattern(pattern_id: str) -> tuple[str, Path | None]:
    """Resolve an integration pattern and return its content with the path."""

    docs_dir = _get_integration_patterns_dir()
    parts = _sanitize_document_id(pattern_id)
    if not parts:
        return ("Error: Invalid pattern_id provided.", None)

    pattern_path = docs_dir.joinpath(*parts).with_suffix(".md")

    try:
        docs_root = docs_dir.resolve(strict=False)
        resolved_path = pattern_path.resolve(strict=False)
        if not resolved_path.is_relative_to(docs_root):
            return ("Error: Invalid pattern_id provided.", None)
    except Exception:
        # Fallback to existence check below if resolution fails
        pass

    if not pattern_path.exists():
        return (f"Error: Integration pattern '{pattern_id}' not found. Please run 'update-docs'.", None)

    try:
        _, body = load_markdown_with_front_matter(pattern_path)
    except Exception:
        return (_read_text_file(pattern_path), pattern_path)

    if body:
        return (body, pattern_path)

    return (_read_text_file(pattern_path), pattern_path)


def _read_troubleshooting_guide(guide_id: str) -> tuple[str, Path | None]:
    """Resolve a troubleshooting guide and return its content with the path."""

    docs_dir = _get_troubleshooting_dir()
    parts = _sanitize_document_id(guide_id)
    if not parts:
        return ("Error: Invalid guide_id provided.", None)

    guide_path = docs_dir.joinpath(*parts).with_suffix(".md")

    try:
        docs_root = docs_dir.resolve(strict=False)
        resolved_path = guide_path.resolve(strict=False)
        if not resolved_path.is_relative_to(docs_root):
            return ("Error: Invalid guide_id provided.", None)
    except Exception:
        pass

    if not guide_path.exists():
        return (f"Error: Troubleshooting guide '{guide_id}' not found. Please run 'update-docs'.", None)

    try:
        _, body = load_markdown_with_front_matter(guide_path)
    except Exception:
        return (_read_text_file(guide_path), guide_path)

    if body:
        return (body, guide_path)

    return (_read_text_file(guide_path), guide_path)


@mcp.tool
def get_basic_info() -> str:
    """
    Get basic information about Omelet Routing Engine API and iNavi Maps API.
    Includes user-provided API keys.
    """
    file_path = _get_docs_dir() / "basic_info.md"
    content = _read_text_file(file_path)
    if os.getenv("INAVI_API_KEY"):
        content += f"\n\nINAVI_API_KEY: {os.getenv('INAVI_API_KEY')}"
    if os.getenv("OMELET_API_KEY"):
        content += f"\n\nOMELET_API_KEY: {os.getenv('OMELET_API_KEY')}"
    return content


@mcp.tool
def list_integration_patterns() -> str:
    """
    Return a table of all available integration patterns, which are guidelines for integrating different API endpoints for specific use cases.
    """

    list_path = _get_integration_patterns_dir() / "list.md"
    if not list_path.exists():
        return "Error: Integration pattern list not found. Please run 'update-docs'."

    return _read_text_file(list_path)


@mcp.tool
def get_integration_pattern(
    pattern_id: Annotated[str, "Integration pattern identifier in the format 'category/pattern'"],
    simple: Annotated[
        bool,
        "If True, return only the standalone document. If False, provide additional guidelines for agentic coding tips, to enhance tool usage and autonomous agentic development. Refer to these tips for creating or revising TO DO lists.",
    ] = False,
) -> str:
    """
    Retrieve the specified integration pattern document.
    These integration patterns serve as starting points for further API exploration and development.

    It is **STRONGLY** advised that the user provide or setup API keys in advance for autonomous agentic development.
    """
    content, _ = _read_integration_pattern(pattern_id)
    if content.startswith("Error:"):
        return content

    if simple:
        return content

    guidelines_path = _get_integration_patterns_dir() / "agentic_coding_guidelines.md"
    guidelines_content = _read_text_file(guidelines_path)

    if guidelines_content.startswith("Error:"):
        return f"{content.rstrip()}\n\n{guidelines_content.strip()}\n"

    return f"{content.rstrip()}\n\n---\n\n{guidelines_content.strip()}\n"


@mcp.tool
def list_troubleshooting_guides() -> str:
    """
    Return a table of all available troubleshooting guides, covering common errors and recommended fixes.
    """

    list_path = _get_troubleshooting_dir() / "list.md"
    if not list_path.exists():
        return "Error: Troubleshooting guide list not found. Please run 'update-docs'."

    return _read_text_file(list_path)


@mcp.tool
def get_troubleshooting_guide(
    guide_id: Annotated[str, "Troubleshooting guide identifier in the format 'category/guide'"],
) -> str:
    """
    Retrieve the specified troubleshooting guide.
    These guides outline steps to diagnose and resolve recurring integration or runtime issues.
    """
    content, _ = _read_troubleshooting_guide(guide_id)
    if content.startswith("Error:"):
        return content

    return content


@mcp.tool
def list_endpoints(
    provider: Annotated[
        str | None, "Optional provider filter ('omelet' or 'inavi'). If None, returns combined list."
    ] = None,
) -> str:
    """
    Get a list of available API endpoints with their summaries and descriptions.

    Returns:
        Markdown table of endpoints
    """
    docs_dir = _get_docs_dir()

    if provider:
        # Return provider-specific endpoints
        file_path = docs_dir / provider / "endpoints_summary.md"
        if file_path.exists():
            return _read_text_file(file_path)

    # Return combined endpoints from both providers
    content_parts = []

    for provider_name in provider_configs.keys():
        file_path = docs_dir / provider_name / "endpoints_summary.md"
        if file_path.exists():
            content = _read_text_file(file_path)
            if not content.startswith("Error:"):
                content_parts.append(content)

    if not content_parts:
        return "Error: No endpoints found. Please run 'update-docs' first."

    return "\n\n---\n\n".join(content_parts)


@mcp.tool
def get_endpoint_overview(
    path: Annotated[str, "API endpoint path (e.g., '/api/fsmvrp', '/api/cost-matrix')"],
    provider: Annotated[str | None, "Optional provider name. If None, auto-detects from path."] = None,
) -> str:
    """
    Get detailed overview information for a specific API endpoint.

    Returns:
        JSON content of the endpoint overview
    """
    return _get_json_file_content(path, provider, "overviews", "overview")


@mcp.tool
def get_request_body_schema(
    path: Annotated[str, "API endpoint path (e.g., '/api/fsmvrp', '/api/cost-matrix')"],
    provider: Annotated[str | None, "Optional provider name. If None, auto-detects from path."] = None,
) -> str:
    """
    Get the request body schema for a specific API endpoint (only works for endpoints that require a request body, typically POST/PUT methods).

    Returns:
        JSON schema content for the request body
    """
    return _get_json_file_content(path, provider, "schemas/request_body", "schema")


@mcp.tool
def get_response_schema(
    path: Annotated[str, "API endpoint path (e.g., '/api/fsmvrp', '/api/cost-matrix')"],
    response_code: Annotated[str, "HTTP response code (e.g., '200', '201', '400', '404')"],
    provider: Annotated[str | None, "Optional provider name. If None, auto-detects from path."] = None,
) -> str:
    """
    Get the response schema for a specific API endpoint and response code.
    Most successful response codes are 200, however endpoints with "-long" in their name
    return a 201 code when successful. This tool should be used when trying to design
    post-processes for handling the API response.

    Returns:
        JSON schema content for the response
    """
    resolved_provider, path_id = _resolve_provider_and_path_id(path, provider)
    file_path = _get_docs_dir() / resolved_provider / "schemas" / "response" / path_id / f"{response_code}.json"
    return _read_json_file(file_path, f"response schema (code: {response_code})", path, path_id)


@mcp.tool
def list_examples(
    path: Annotated[str, "API endpoint path (e.g., '/api/vrp', '/api/cost-matrix')"],
    example_type: Annotated[
        str | None, "Type of examples to list: 'request', 'response', or 'both' (default: 'both')"
    ] = "both",
    provider: Annotated[str | None, "Optional provider name. If None, auto-detects from path."] = None,
) -> str:
    """
    List available request and response examples for a specific API endpoint.
    Currently, only usable for "omelet" provider endpoints.

    Returns:
        JSON containing available example names for request and/or response bodies
    """
    resolved_provider, path_id = _resolve_provider_and_path_id(path, provider)
    docs_dir = _get_docs_dir() / resolved_provider / "examples"

    result: dict[str, Any] = {"endpoint": path, "path_id": path_id}

    # List request examples
    if example_type in ["request", "both"]:
        request_dir = docs_dir / "request_body" / path_id
        if request_dir.exists() and request_dir.is_dir():
            request_examples = [f.stem for f in request_dir.glob("*.json")]
            request_examples.sort()
            result["request_examples"] = request_examples
        else:
            result["request_examples"] = []

    # List response examples
    if example_type in ["response", "both"]:
        response_dir = docs_dir / "response_body" / path_id
        if response_dir.exists() and response_dir.is_dir():
            response_examples = {}
            # Check for subdirectories named by response codes
            for code_dir in response_dir.iterdir():
                if code_dir.is_dir() and code_dir.name.isdigit():
                    code_examples = [f.stem for f in code_dir.glob("*.json")]
                    if code_examples:
                        code_examples.sort()
                        response_examples[code_dir.name] = code_examples
            result["response_examples"] = response_examples
        else:
            result["response_examples"] = {}

    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool
def get_example(
    path: Annotated[str, "API endpoint path (e.g., '/api/vrp', '/api/cost-matrix')"],
    example_name: Annotated[str, "Name of the example"],
    example_type: Annotated[str, "Type of example: 'request' or 'response'"],
    response_code: Annotated[
        str | None, "HTTP response code (required if example_type is 'response', e.g., '200', '201')"
    ] = None,
    provider: Annotated[str | None, "Optional provider name. If None, auto-detects from path."] = None,
) -> str:
    """
    Get a specific example for an API endpoint.
    Check the list of examples using the list_examples tool first for the `example_name`.
    Currently, only usable for "omelet" provider endpoints.

    Note: Saved examples may be truncated, so the returned example may not be complete.

    Returns:
        JSON content of the example
    """
    resolved_provider, path_id = _resolve_provider_and_path_id(path, provider)
    docs_dir = _get_docs_dir() / resolved_provider / "examples"

    if example_type == "request":
        file_path = docs_dir / "request_body" / path_id / f"{example_name}.json"
    elif example_type == "response":
        if response_code is None:
            return "Error: response_code is required when example_type is 'response'"
        file_path = docs_dir / "response_body" / path_id / response_code / f"{example_name}.json"
    else:
        return f"Error: Invalid example_type '{example_type}'. Must be 'request' or 'response'"

    if not file_path.exists():
        return f"Error: Example '{example_name}' not found for {example_type} at path '{path}' (path_id: {path_id})"

    return _read_json_file(file_path, f"{example_type} example", path, path_id)
