from typing import Annotated, Literal
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from fastapi import FastAPI, Query

from fastmcp import Client, FastMCP
from fastmcp.server.openapi import MCPType, OpenAPITool, RouteMap
from fastmcp.utilities.openapi import HTTPRoute, ParameterInfo


@pytest.fixture
def array_path_spec():
    """Load a minimal OpenAPI spec with an array path parameter."""
    return {
        "openapi": "3.1.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/select/{days}": {
                "put": {
                    "operationId": "test-operation",
                    "parameters": [
                        {
                            "name": "days",
                            "in": "path",
                            "required": True,
                            "style": "simple",
                            "explode": False,
                            "schema": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": [
                                        "monday",
                                        "tuesday",
                                        "wednesday",
                                        "thursday",
                                        "friday",
                                        "saturday",
                                        "sunday",
                                    ],
                                },
                            },
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {"result": {"type": "string"}},
                                        "required": ["result"],
                                    }
                                }
                            },
                        }
                    },
                }
            }
        },
    }


@pytest.fixture
def mock_client():
    """Create a mock httpx.AsyncClient."""
    client = AsyncMock(spec=httpx.AsyncClient)
    # Set up a mock response
    mock_response = MagicMock()
    mock_response.json.return_value = {"result": "success"}
    mock_response.raise_for_status.return_value = None
    client.request.return_value = mock_response
    return client


async def test_fastmcp_from_openapi(array_path_spec, mock_client):
    """Test creating FastMCP from OpenAPI spec with array path parameter."""
    # Create FastMCP from the spec
    mcp = FastMCP.from_openapi(array_path_spec, client=mock_client)

    # Verify the tool was created using the MCP protocol method
    tools_result = await mcp.get_tools()
    tool_names = [tool.name for tool in tools_result.values()]
    assert "test_operation" in tool_names


async def test_array_path_parameter_handling(mock_client):
    """Test how array path parameters are handled."""
    # Create a simple route with array path parameter
    route = HTTPRoute(
        path="/select/{days}",
        method="PUT",
        operation_id="test_operation",
        parameters=[
            ParameterInfo(
                name="days",
                location="path",
                required=True,
                schema={
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": [
                            "monday",
                            "tuesday",
                            "wednesday",
                            "thursday",
                            "friday",
                            "saturday",
                            "sunday",
                        ],
                    },
                },
            )
        ],
    )

    # Create the tool
    tool = OpenAPITool(
        client=mock_client,
        route=route,
        name="test_operation",
        description="Test operation",
        parameters={},
    )

    # Test with a single value
    await tool.run({"days": ["monday"]})

    # Check that the path parameter is formatted correctly
    # This is where the bug is: it should be '/select/monday' not '/select/[\'monday\']'
    mock_client.request.assert_called_with(
        method="PUT",
        url="/select/monday",  # This is the expected format
        params={},
        headers={},
        json=None,
        timeout=None,
    )
    mock_client.request.reset_mock()

    # Test with multiple values
    await tool.run({"days": ["monday", "tuesday"]})

    # Check that the path parameter is formatted correctly
    # It should be '/select/monday,tuesday' not '/select/[\'monday\', \'tuesday\']'
    mock_client.request.assert_called_with(
        method="PUT",
        url="/select/monday,tuesday",  # This is the expected format
        params={},
        headers={},
        json=None,
        timeout=None,
    )


async def test_integration_array_path_parameter(array_path_spec, mock_client):
    """Integration test for array path parameters."""
    # Create FastMCP from the spec
    mcp = FastMCP.from_openapi(array_path_spec, client=mock_client)

    # Call the tool with a single value
    await mcp._call_tool_mcp("test_operation", {"days": ["monday"]})

    # Check the request was made correctly
    mock_client.request.assert_called_with(
        method="PUT",
        url="/select/monday",
        params={},
        headers={},
        json=None,
        timeout=None,
    )
    mock_client.request.reset_mock()

    # Call the tool with multiple values
    await mcp._call_tool_mcp("test_operation", {"days": ["monday", "tuesday"]})

    # Check the request was made correctly
    mock_client.request.assert_called_with(
        method="PUT",
        url="/select/monday,tuesday",
        params={},
        headers={},
        json=None,
        timeout=None,
    )


async def test_complex_nested_array_path_parameter(mock_client):
    """Test handling of complex nested array path parameters."""
    # Create a route with a path parameter that contains nested objects in an array
    route = HTTPRoute(
        path="/report/{filters}",
        method="GET",
        operation_id="test-complex-filters",
        parameters=[
            ParameterInfo(
                name="filters",
                location="path",
                required=True,
                schema={
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "field": {"type": "string"},
                            "value": {"type": "string"},
                        },
                    },
                },
            )
        ],
    )

    # Create the tool
    tool = OpenAPITool(
        client=mock_client,
        route=route,
        name="test-complex-filters",
        description="Test operation with complex filters",
        parameters={},
    )

    # Test with a more complex path parameter
    # This would typically be serialized as JSON or a more complex format
    # But for path parameters with style=simple, it should be comma-separated
    complex_filters = [
        {"field": "status", "value": "active"},
        {"field": "type", "value": "user"},
    ]

    # Execute the request with complex filters
    await tool.run({"filters": complex_filters})

    # The complex object should be properly serialized in the URL
    # For path parameters, this would typically need a custom serialization strategy
    # but our implementation should handle it safely
    call_args = mock_client.request.call_args

    # Verify the request was made
    assert call_args is not None, "The request was not made"

    # Get the called URL and verify it contains the serialized path parameter
    called_url = call_args[1].get("url")

    # Check that the path parameter is handled (we don't expect perfect serialization,
    # but it should not cause errors and should maintain the array structure)
    assert "/report/" in called_url, "The URL should contain the path prefix"

    # Check that it didn't just convert the objects to string representations
    # that include the Python object syntax
    assert "status" in called_url, "The URL should contain filter field names"
    assert "active" in called_url, "The URL should contain filter values"
    assert "}" not in called_url, "The URL should not contain Python object syntax"
    assert "{" not in called_url, "The URL should not contain Python object syntax"


async def test_array_query_param_with_fastapi():
    """Test array query parameters using FastAPI and FastMCP.from_fastapi integration."""
    # Create a FastAPI app with a route that has an array query parameter
    app = FastAPI()

    @app.get("/select")
    async def select_days(
        days: Annotated[
            list[
                Literal[
                    "monday",
                    "tuesday",
                    "wednesday",
                    "thursday",
                    "friday",
                    "saturday",
                    "sunday",
                ]
            ],
            Query(explode=True),
        ],
    ):  # Using explode=True to get days=monday&days=tuesday format
        return {"selected": days}

    # Create a FastMCP server from the FastAPI app
    mcp = FastMCP.from_fastapi(
        app,
        route_maps=[RouteMap(methods=["GET"], pattern=r".*", mcp_type=MCPType.TOOL)],
    )

    # Test with the client
    async with Client(mcp) as client:
        # Get the actual tool name first
        tools = await client.list_tools()
        tool_names = [tool.name for tool in tools]
        assert len(tool_names) == 1, (
            f"Expected one tool, got {len(tool_names)}: {tool_names}"
        )
        tool_name = tool_names[0]

        # Single day
        result = await client.call_tool(tool_name, {"days": ["monday"]})
        assert result.data == {"selected": ["monday"]}

        # Multiple days
        result = await client.call_tool(tool_name, {"days": ["monday", "tuesday"]})
        assert result.data == {"selected": ["monday", "tuesday"]}


async def test_array_query_parameter_format(mock_client):
    """Test that array query parameters are formatted as comma-separated values when explode=False."""
    # Create a route with array query parameter
    route = HTTPRoute(
        path="/select",
        method="GET",
        operation_id="test-operation",
        parameters=[
            ParameterInfo(
                name="days",
                location="query",  # This is a query parameter
                required=True,
                explode=False,  # Set explode=False to test comma-separated formatting
                schema={
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": [
                            "monday",
                            "tuesday",
                            "wednesday",
                            "thursday",
                            "friday",
                            "saturday",
                            "sunday",
                        ],
                    },
                },
            )
        ],
    )

    # Create the tool
    tool = OpenAPITool(
        client=mock_client,
        route=route,
        name="test-operation",
        description="Test operation",
        parameters={},
    )

    # Test with a single value
    await tool.run({"days": ["monday"]})

    # Check that the query parameter is formatted correctly
    mock_client.request.assert_called_with(
        method="GET",
        url="/select",
        params={"days": "monday"},  # Should be formatted as a string, not a list
        headers={},
        json=None,
        timeout=None,
    )
    mock_client.request.reset_mock()

    # Test with multiple values
    await tool.run({"days": ["monday", "tuesday"]})

    # Check that the query parameter is formatted correctly
    # It should be 'days=monday,tuesday' not 'days=["monday","tuesday"]'
    mock_client.request.assert_called_with(
        method="GET",
        url="/select",
        params={"days": "monday,tuesday"},  # Should be comma-separated
        headers={},
        json=None,
        timeout=None,
    )


async def test_array_query_parameter_exploded_format(mock_client):
    """Test that array query parameters are formatted as separate parameters when explode=True."""
    # Create a route with array query parameter with explode=True (default)
    route = HTTPRoute(
        path="/select-exploded",
        method="GET",
        operation_id="test-exploded-operation",
        parameters=[
            ParameterInfo(
                name="days",
                location="query",  # This is a query parameter
                required=True,
                explode=True,  # Set explode=True for separate parameter serialization
                schema={
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": [
                            "monday",
                            "tuesday",
                            "wednesday",
                            "thursday",
                            "friday",
                            "saturday",
                            "sunday",
                        ],
                    },
                },
            )
        ],
    )

    # Create the tool
    tool = OpenAPITool(
        client=mock_client,
        route=route,
        name="test-exploded-operation",
        description="Test operation with exploded arrays",
        parameters={},
    )

    # Test with a single value
    await tool.run({"days": ["monday"]})

    # Check that the query parameter is formatted correctly
    mock_client.request.assert_called_with(
        method="GET",
        url="/select-exploded",
        params={"days": ["monday"]},  # Should be passed as a list for explode=True
        headers={},
        json=None,
        timeout=None,
    )
    mock_client.request.reset_mock()

    # Test with multiple values
    await tool.run({"days": ["monday", "tuesday"]})

    # Check that the query parameter is formatted correctly
    # It should be passed as an array, which httpx will serialize as days=monday&days=tuesday
    mock_client.request.assert_called_with(
        method="GET",
        url="/select-exploded",
        params={"days": ["monday", "tuesday"]},  # Should be passed as a list
        headers={},
        json=None,
        timeout=None,
    )


async def test_empty_array_parameter_exclusion(mock_client):
    """Test that empty array parameters are excluded from requests."""
    # Create a route with array query parameter
    route = HTTPRoute(
        path="/search",
        method="GET",
        operation_id="search-operation",
        parameters=[
            ParameterInfo(
                name="tags",
                location="query",
                required=False,
                schema={
                    "type": "array",
                    "items": {"type": "string"},
                },
            ),
            ParameterInfo(
                name="categories",
                location="query",
                required=False,
                schema={
                    "type": "array",
                    "items": {"type": "string"},
                },
            ),
            ParameterInfo(
                name="limit",
                location="query",
                required=False,
                schema={"type": "integer"},
            ),
        ],
    )

    # Create the tool
    tool = OpenAPITool(
        client=mock_client,
        route=route,
        name="search-operation",
        description="Search operation",
        parameters={},
    )

    # Test with empty array - should be excluded
    await tool.run(
        {
            "tags": [],  # Empty array should be excluded
            "categories": ["tech", "news"],  # Non-empty array should be included
            "limit": 10,  # Non-array param should be included
        }
    )

    # Check that empty array is excluded, but others are included
    mock_client.request.assert_called_with(
        method="GET",
        url="/search",
        params={
            "categories": ["tech", "news"],  # Only non-empty array included
            "limit": 10,
        },
        headers={},
        json=None,
        timeout=None,
    )


async def test_empty_deep_object_parameter_exclusion(mock_client):
    """Test that empty dict parameters with deepObject style are excluded from requests."""
    # Create a route with deepObject query parameter
    route = HTTPRoute(
        path="/filter",
        method="GET",
        operation_id="filter-operation",
        parameters=[
            ParameterInfo(
                name="filters",
                location="query",
                required=False,
                style="deepObject",
                explode=True,
                schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "age": {"type": "integer"},
                    },
                },
            ),
            ParameterInfo(
                name="options",
                location="query",
                required=False,
                style="deepObject",
                explode=True,
                schema={
                    "type": "object",
                    "properties": {
                        "sort": {"type": "string"},
                        "order": {"type": "string"},
                    },
                },
            ),
            ParameterInfo(
                name="page",
                location="query",
                required=False,
                schema={"type": "integer"},
            ),
        ],
    )

    # Create the tool
    tool = OpenAPITool(
        client=mock_client,
        route=route,
        name="filter-operation",
        description="Filter operation",
        parameters={},
    )

    # Test with empty dict - should be excluded
    await tool.run(
        {
            "filters": {},  # Empty dict should be excluded
            "options": {
                "sort": "name",
                "order": "asc",
            },  # Non-empty dict should be included
            "page": 1,  # Non-dict param should be included
        }
    )

    # Check that empty dict is excluded, but others are included
    mock_client.request.assert_called_with(
        method="GET",
        url="/filter",
        params={
            "options[sort]": "name",  # Deep object style for non-empty dict
            "options[order]": "asc",
            "page": 1,
        },
        headers={},
        json=None,
        timeout=None,
    )


def test_parameter_location_enum_handling():
    """Test that ParameterLocation enum values are handled correctly (issue #950)."""
    from enum import Enum

    # Create a mock ParameterLocation enum like the one from openapi_pydantic
    class MockParameterLocation(Enum):
        PATH = "path"
        QUERY = "query"
        HEADER = "header"
        COOKIE = "cookie"

    # Test the enum handling logic directly (reproduces the fix in openapi.py)
    test_cases = [
        (MockParameterLocation.PATH, "path"),
        (MockParameterLocation.QUERY, "query"),
        (MockParameterLocation.HEADER, "header"),
        (MockParameterLocation.COOKIE, "cookie"),
        ("path", "path"),  # Also test that strings work
        ("query", "query"),
    ]

    for param_in, expected_str in test_cases:
        # This is the enum handling logic from the fix
        param_in_str = param_in.value if isinstance(param_in, Enum) else param_in
        assert param_in_str == expected_str
        assert isinstance(param_in_str, str)
