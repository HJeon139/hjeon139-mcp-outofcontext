"""FastMCP prompts for common context operations."""

import json

from hjeon139_mcp_outofcontext.fastmcp_server import mcp


@mcp.prompt()
def create_context_prompt(name: str, text: str, metadata: dict | None = None) -> str:
    """Create a new context with the specified name and content.

    This prompt template helps create a new context entry. The name must be
    filename-safe (alphanumeric, hyphens, underscores). The text should be
    markdown content, and optional metadata can be provided as a dictionary.

    Args:
        name: The context name (filename-safe)
        text: The markdown content for the context
        metadata: Optional metadata dictionary to store with the context
    """
    metadata_str = ""
    if metadata:
        metadata_str = f"\n\nMetadata: {json.dumps(metadata, indent=2)}"

    return f"""Create a new context named '{name}' with the following content:

{text}{metadata_str}

Use the put_context tool to save this context."""


@mcp.prompt()
def update_context_prompt(name: str, text: str, metadata: dict | None = None) -> str:
    """Update an existing context with new content.

    This prompt template helps update an existing context. If the context
    doesn't exist, it will be created. The text should be markdown content,
    and optional metadata can be provided to update the context's metadata.

    Args:
        name: The context name to update
        text: The new markdown content for the context
        metadata: Optional metadata dictionary to update
    """
    metadata_str = ""
    if metadata:
        metadata_str = f"\n\nUpdated metadata: {json.dumps(metadata, indent=2)}"

    return f"""Update the context named '{name}' with the following content:

{text}{metadata_str}

Use the put_context tool to save the updated context."""


@mcp.prompt()
def get_context_prompt(name: str) -> str:
    """Retrieve a context by name.

    This prompt template helps retrieve a specific context by its name.
    The context will be returned with its text content and metadata.

    Args:
        name: The name of the context to retrieve
    """
    return f"""Retrieve the context named '{name}'.

Use the get_context tool to fetch the context content and metadata."""


@mcp.prompt()
def search_context_prompt(query: str, limit: int | None = None) -> str:
    """Search for contexts matching a query string.

    This prompt template helps search for contexts that match a query.
    The search looks in both metadata (YAML frontmatter) and text content.
    You can optionally limit the number of results.

    Args:
        query: The search query string
        limit: Optional limit on the number of results to return
    """
    limit_str = f" (limit to {limit} results)" if limit else ""
    return f"""Search for contexts matching: '{query}'{limit_str}

Use the search_context tool to find matching contexts. The search will look
in both metadata and content."""


@mcp.prompt()
def list_contexts_prompt(limit: int | None = None) -> str:
    """List all available contexts.

    This prompt template helps list all contexts, sorted by creation date
    (newest first). You can optionally limit the number of results.

    Args:
        limit: Optional limit on the number of contexts to list
    """
    limit_str = f" (limit to {limit} results)" if limit else ""
    return f"""List all available contexts{limit_str}.

Use the list_context tool to get a list of all contexts with their names,
creation dates, and previews."""


@mcp.prompt()
def delete_context_prompt(name: str) -> str:
    """Delete a context by name.

    This prompt template helps delete a specific context. This operation
    permanently removes the context and cannot be undone.

    Args:
        name: The name of the context to delete
    """
    return f"""Delete the context named '{name}'.

Use the delete_context tool to permanently remove this context.
Warning: This operation cannot be undone."""


@mcp.prompt()
def bulk_create_contexts_prompt(contexts: list[dict]) -> str:
    """Create multiple contexts at once.

    This prompt template helps create multiple contexts in a single operation.
    Each context in the list should have 'name' and 'text' fields, and
    optionally a 'metadata' field.

    Args:
        contexts: List of context dictionaries, each with 'name', 'text', and optional 'metadata'
    """
    contexts_str = json.dumps(contexts, indent=2)
    return f"""Create multiple contexts in bulk:

{contexts_str}

Use the put_context tool with the 'contexts' parameter to save all contexts at once."""


@mcp.prompt()
def bulk_get_contexts_prompt(names: list[str]) -> str:
    """Retrieve multiple contexts by name.

    This prompt template helps retrieve multiple contexts in a single operation.
    Returns results for all requested contexts, with errors for any that are not found.

    Args:
        names: List of context names to retrieve
    """
    names_str = ", ".join(f"'{name}'" for name in names)
    return f"""Retrieve multiple contexts: {names_str}

Use the get_context tool with the 'names' parameter to fetch all contexts at once."""


@mcp.prompt()
def bulk_delete_contexts_prompt(names: list[str]) -> str:
    """Delete multiple contexts by name.

    This prompt template helps delete multiple contexts in a single operation.
    This operation permanently removes the contexts and cannot be undone.

    Args:
        names: List of context names to delete
    """
    names_str = ", ".join(f"'{name}'" for name in names)
    return f"""Delete multiple contexts: {names_str}

Use the delete_context tool with the 'names' parameter to remove all contexts at once.
Warning: This operation cannot be undone."""
