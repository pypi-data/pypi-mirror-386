import asyncio
import logging
from unittest.mock import AsyncMock, Mock, patch

import anyio
import pytest

from fastmcp.server.server import FastMCP


class CustomLogFormatterForTest(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return f"TEST_FORMAT::{record.levelname}::{record.name}::{record.getMessage()}"


@pytest.fixture
def mcp_server() -> FastMCP:
    return FastMCP(name="TestLogServer")


@patch("fastmcp.server.server.uvicorn.Server")
@patch("fastmcp.server.server.uvicorn.Config")
async def test_uvicorn_logging_default_level(
    mock_uvicorn_config_constructor: Mock,
    mock_uvicorn_server_constructor: Mock,
    mcp_server: FastMCP,
):
    """Tests that FastMCP passes log_level to uvicorn.Config if no log_config is given."""
    mock_server_instance = AsyncMock()
    mock_uvicorn_server_constructor.return_value = mock_server_instance
    serve_finished_event = anyio.Event()
    mock_server_instance.serve.side_effect = serve_finished_event.wait

    test_log_level = "warning"

    server_task = asyncio.create_task(
        mcp_server.run_http_async(log_level=test_log_level, port=8003)
    )
    await asyncio.sleep(0.01)

    mock_uvicorn_config_constructor.assert_called_once()
    _, kwargs_config = mock_uvicorn_config_constructor.call_args

    assert kwargs_config.get("log_level") == test_log_level.lower()
    assert "log_config" not in kwargs_config

    mock_uvicorn_server_constructor.assert_called_once_with(
        mock_uvicorn_config_constructor.return_value
    )
    mock_server_instance.serve.assert_awaited_once()

    server_task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await server_task


@patch("fastmcp.server.server.uvicorn.Server")
@patch("fastmcp.server.server.uvicorn.Config")
async def test_uvicorn_logging_with_custom_log_config(
    mock_uvicorn_config_constructor: Mock,
    mock_uvicorn_server_constructor: Mock,
    mcp_server: FastMCP,
):
    """Tests that FastMCP passes log_config to uvicorn.Config and not log_level."""
    mock_server_instance = AsyncMock()
    mock_uvicorn_server_constructor.return_value = mock_server_instance
    serve_finished_event = anyio.Event()
    mock_server_instance.serve.side_effect = serve_finished_event.wait

    sample_log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "test_formatter": {
                "()": "tests.server.test_logging.CustomLogFormatterForTest"
            }
        },
        "handlers": {
            "test_handler": {
                "formatter": "test_formatter",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            }
        },
        "loggers": {
            "uvicorn.error": {
                "handlers": ["test_handler"],
                "level": "INFO",
                "propagate": False,
            }
        },
    }

    server_task = asyncio.create_task(
        mcp_server.run_http_async(
            uvicorn_config={"log_config": sample_log_config}, port=8004
        )
    )
    await asyncio.sleep(0.01)

    mock_uvicorn_config_constructor.assert_called_once()
    _, kwargs_config = mock_uvicorn_config_constructor.call_args

    assert kwargs_config.get("log_config") == sample_log_config
    assert "log_level" not in kwargs_config

    mock_uvicorn_server_constructor.assert_called_once_with(
        mock_uvicorn_config_constructor.return_value
    )
    mock_server_instance.serve.assert_awaited_once()

    server_task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await server_task


@patch("fastmcp.server.server.uvicorn.Server")
@patch("fastmcp.server.server.uvicorn.Config")
async def test_uvicorn_logging_custom_log_config_overrides_log_level_param(
    mock_uvicorn_config_constructor: Mock,
    mock_uvicorn_server_constructor: Mock,
    mcp_server: FastMCP,
):
    """Tests log_config precedence if log_level is also passed to run_http_async."""
    mock_server_instance = AsyncMock()
    mock_uvicorn_server_constructor.return_value = mock_server_instance
    serve_finished_event = anyio.Event()
    mock_server_instance.serve.side_effect = serve_finished_event.wait

    sample_log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "test_formatter": {
                "()": "tests.server.test_logging.CustomLogFormatterForTest"
            }
        },
        "handlers": {
            "test_handler": {
                "formatter": "test_formatter",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            }
        },
        "loggers": {
            "uvicorn.error": {
                "handlers": ["test_handler"],
                "level": "INFO",
                "propagate": False,
            }
        },
    }
    explicit_log_level = "debug"

    server_task = asyncio.create_task(
        mcp_server.run_http_async(
            log_level=explicit_log_level,
            uvicorn_config={"log_config": sample_log_config},
            port=8005,
        )
    )
    await asyncio.sleep(0.01)

    mock_uvicorn_config_constructor.assert_called_once()
    _, kwargs_config = mock_uvicorn_config_constructor.call_args

    assert kwargs_config.get("log_config") == sample_log_config
    assert "log_level" not in kwargs_config

    mock_uvicorn_server_constructor.assert_called_once_with(
        mock_uvicorn_config_constructor.return_value
    )
    mock_server_instance.serve.assert_awaited_once()

    server_task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await server_task
