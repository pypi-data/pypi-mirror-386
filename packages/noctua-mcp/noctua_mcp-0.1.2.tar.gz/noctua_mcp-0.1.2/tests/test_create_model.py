"""
Tests for the create_model functionality.
"""

from unittest.mock import Mock, patch
import pytest

from noctua_mcp import mcp_server


@pytest.mark.asyncio
async def test_create_model_with_title():
    """Test creating a model with a title."""

    with patch("noctua_mcp.mcp_server.BaristaClient") as MockClient:
        mock_instance = Mock()
        MockClient.return_value = mock_instance

        from noctua import BaristaResponse
        mock_resp = Mock(spec=BaristaResponse)
        mock_resp.validation_failed = False
        mock_resp.validation_reason = None
        mock_resp.error = None
        mock_resp.success = True
        mock_resp.model_id = "gomodel:new_test_model_123"
        mock_resp.raw = {
            "message-type": "success",
            "signal": "merge",
            "data": {
                "id": "gomodel:new_test_model_123"
            }
        }

        mock_instance.create_model.return_value = mock_resp

        mcp_server._client = None

        # Call the function
        result = await mcp_server.create_model.fn("Test Model Title")

        # Verify calls
        mock_instance.create_model.assert_called_once_with(title="Test Model Title")

        assert result["success"] is True
        assert result["model_id"] == "gomodel:new_test_model_123"
        assert result["created"] is True
        assert "graph_editor_url" in result
        assert "pathway_editor_url" in result


@pytest.mark.asyncio
async def test_create_model_without_title():
    """Test creating a model without a title."""

    with patch("noctua_mcp.mcp_server.BaristaClient") as MockClient:
        mock_instance = Mock()
        MockClient.return_value = mock_instance

        from noctua import BaristaResponse
        mock_resp = Mock(spec=BaristaResponse)
        mock_resp.validation_failed = False
        mock_resp.validation_reason = None
        mock_resp.error = None
        mock_resp.success = True
        mock_resp.model_id = "gomodel:untitled_model_456"
        mock_resp.raw = {
            "message-type": "success",
            "signal": "merge",
            "data": {
                "id": "gomodel:untitled_model_456"
            }
        }

        mock_instance.create_model.return_value = mock_resp

        mcp_server._client = None

        # Call the function with no title
        result = await mcp_server.create_model.fn()

        # Verify calls
        mock_instance.create_model.assert_called_once_with(title=None)

        assert result["success"] is True
        assert result["model_id"] == "gomodel:untitled_model_456"
        assert result["created"] is True


@pytest.mark.asyncio
async def test_create_model_integration():
    """Test create_model integration with MCP client."""
    from fastmcp import Client

    client = Client("src/noctua_mcp/mcp_server.py")
    async with client:
        tools = await client.list_tools()
        tool_names = {t.name for t in tools}

        # Check create_model is available
        assert "create_model" in tool_names

        # Find the create_model tool
        create_tool = next(t for t in tools if t.name == "create_model")

        # Check it has the right parameters
        if hasattr(create_tool, 'parameters') and 'properties' in create_tool.parameters:
            props = create_tool.parameters['properties']
            assert 'title' in props
            assert props['title']['type'] == 'string'

            # title should be optional
            required = create_tool.parameters.get('required', [])
            assert 'title' not in required


@pytest.mark.parametrize("title,expected_id", [
    ("Test Model 1", "gomodel:test1"),
    ("Another Model", "gomodel:test2"),
    (None, "gomodel:untitled"),
    ("", "gomodel:empty_title"),
])
@pytest.mark.asyncio
async def test_create_model_variations(title, expected_id):
    """Test create_model with various titles."""

    with patch("noctua_mcp.mcp_server.BaristaClient") as MockClient:
        mock_instance = Mock()
        MockClient.return_value = mock_instance

        from noctua import BaristaResponse
        mock_resp = Mock(spec=BaristaResponse)
        mock_resp.validation_failed = False
        mock_resp.validation_reason = None
        mock_resp.error = None
        mock_resp.success = True
        mock_resp.model_id = expected_id
        mock_resp.raw = {
            "message-type": "success",
            "data": {"id": expected_id}
        }

        mock_instance.create_model.return_value = mock_resp

        mcp_server._client = None

        result = await mcp_server.create_model.fn(title)

        if title is None:
            mock_instance.create_model.assert_called_once_with(title=None)
        else:
            mock_instance.create_model.assert_called_once_with(title=title)

        assert result["success"] is True
        assert result["model_id"] == expected_id
        assert result["created"] is True


@pytest.mark.asyncio
async def test_create_model_error_handling():
    """Test create_model error handling."""

    with patch("noctua_mcp.mcp_server.BaristaClient") as MockClient:
        mock_instance = Mock()
        MockClient.return_value = mock_instance

        from noctua import BaristaResponse
        mock_resp = Mock(spec=BaristaResponse)
        mock_resp.validation_failed = False
        mock_resp.validation_reason = None
        mock_resp.error = "Failed to create model"
        mock_resp.success = False
        mock_resp.model_id = None
        mock_resp.raw = {
            "message-type": "error",
            "message": "Failed to create model"
        }

        mock_instance.create_model.return_value = mock_resp

        mcp_server._client = None

        result = await mcp_server.create_model.fn("Test Model")

        assert result["success"] is False
        assert result["error"] == "Operation failed"
        assert result["reason"] == "Failed to create model"