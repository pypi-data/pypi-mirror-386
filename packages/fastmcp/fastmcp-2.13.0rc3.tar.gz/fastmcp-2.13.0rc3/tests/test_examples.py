"""Tests for example servers"""

from pydantic import AnyUrl

from fastmcp import Client


async def test_simple_echo():
    """Test the simple echo server"""
    from examples.simple_echo import mcp

    async with Client(mcp) as client:
        result = await client.call_tool_mcp("echo", {"text": "hello"})
        assert len(result.content) == 1
        assert result.content[0].text == "hello"


async def test_complex_inputs():
    """Test the complex inputs server"""
    from examples.complex_inputs import mcp

    async with Client(mcp) as client:
        tank = {"shrimp": [{"name": "bob"}, {"name": "alice"}]}
        result = await client.call_tool_mcp(
            "name_shrimp", {"tank": tank, "extra_names": ["charlie"]}
        )
        # Adjacent non-MCP list items are combined into single content
        assert len(result.content) == 1
        assert result.content[0].text == '["bob","alice","charlie"]'


async def test_desktop(monkeypatch):
    """Test the desktop server"""
    from examples.desktop import mcp

    async with Client(mcp) as client:
        # Test the add function
        result = await client.call_tool_mcp("add", {"a": 1, "b": 2})
        assert len(result.content) == 1
        assert result.content[0].text == "3"

    async with Client(mcp) as client:
        result = await client.read_resource(AnyUrl("greeting://rooter12"))
        assert len(result) == 1
        assert result[0].text == "Hello, rooter12!"


async def test_echo():
    """Test the echo server"""
    from examples.echo import mcp

    async with Client(mcp) as client:
        result = await client.call_tool_mcp("echo_tool", {"text": "hello"})
        assert len(result.content) == 1
        assert result.content[0].text == "hello"

    async with Client(mcp) as client:
        result = await client.read_resource(AnyUrl("echo://static"))
        assert len(result) == 1
        assert result[0].text == "Echo!"

    async with Client(mcp) as client:
        result = await client.read_resource(AnyUrl("echo://server42"))
        assert len(result) == 1
        assert result[0].text == "Echo: server42"

    async with Client(mcp) as client:
        result = await client.get_prompt("echo", {"text": "hello"})
        assert len(result.messages) == 1
        assert result.messages[0].content.text == "hello"
