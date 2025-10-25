"""
Comprehensive tests for the Noctua MCP server.

These tests verify that the MCP server correctly wraps the gocam-ai library.
"""

from __future__ import annotations

import os
from unittest.mock import Mock, patch

import pytest
from fastmcp import Client

# Path to the MCP server module
SERVER_PATH = "src/noctua_mcp/mcp_server.py"


@pytest.fixture
def mock_barista_client():
    """Create a mock BaristaClient."""
    from noctua import BaristaResponse

    client = Mock()

    # Mock response object
    mock_resp = Mock(spec=BaristaResponse)
    mock_resp.raw = {"message-type": "success", "signal": "merge"}
    mock_resp.ok = True
    mock_resp.individuals = []
    mock_resp.facts = []
    mock_resp.model_state = "development"

    # Setup client methods
    client.m3_batch.return_value = mock_resp
    client.get_model.return_value = mock_resp
    client.remove_individual.return_value = mock_resp
    client.remove_fact.return_value = mock_resp

    # Mock request builders
    client.req_add_individual.return_value = {
        "entity": "individual",
        "operation": "add",
        "arguments": {}
    }
    client.req_add_fact.return_value = {
        "entity": "edge",
        "operation": "add",
        "arguments": {}
    }
    client.req_add_evidence_to_fact.return_value = [
        {"entity": "individual", "operation": "add"},
        {"entity": "individual", "operation": "add-annotation"},
        {"entity": "edge", "operation": "add-annotation"},
    ]

    return client


@pytest.mark.asyncio
async def test_get_model_variables_mock():
    """Test get_model_variables tool."""
    import sys
    sys.path.insert(0, "src")

    import noctua_mcp.mcp_server as mcp_server

    with patch("noctua_mcp.mcp_server.BaristaClient") as MockClient:
        mock_instance = Mock()
        MockClient.return_value = mock_instance

        # Setup mock response
        from noctua import BaristaResponse
        mock_resp = Mock(spec=BaristaResponse)
        mock_resp.error = None
        mock_resp.individuals = [
            {"id": "gomodel:12345/ind1"},
            {"id": "gomodel:12345/ind2"}
        ]
        mock_resp.model_vars = {
            "mf1": "gomodel:12345/ind1",
            "gp1": "gomodel:12345/ind2"
        }

        mock_instance.get_model.return_value = mock_resp
        mock_instance.track_variables = True
        # Variable registry is keyed by (model_id, variable_name) -> actual_id
        mock_instance._variable_registry = {
            ("gomodel:12345", "old_var"): "gomodel:12345/old123"
        }
        # Mock the get_variables method that our code now uses
        mock_instance.get_variables.return_value = {
            "old_var": "gomodel:12345/old123"
        }

        mcp_server._client = None

        result = await mcp_server.get_model_variables.fn("gomodel:12345")

        assert result["success"] is True
        assert result["model_id"] == "gomodel:12345"
        assert "variables" in result
        # Should have both old registry vars and new model_vars
        assert result["variables"]["mf1"] == "gomodel:12345/ind1"
        assert result["variables"]["gp1"] == "gomodel:12345/ind2"
        assert result["variables"]["old_var"] == "gomodel:12345/old123"
        assert result["individual_count"] == 2


@pytest.mark.asyncio
async def test_server_starts_and_lists_tools() -> None:
    """Test that the server starts and lists all expected tools."""
    client = Client(SERVER_PATH)
    async with client:
        tools = await client.list_tools()
        names = {t.name for t in tools}

        # Check all expected tools are present
        expected_tools = {
            "configure_token",
            "create_model",
            "add_individual",
            "add_fact",
            "add_evidence_to_fact",
            "remove_individual",
            "remove_fact",
            "get_model",
            "model_summary",
            "get_model_variables",
            "search_models",
            "search_bioentities",
            "search_annotations",
            "get_annotations_for_bioentity",
        }
        assert expected_tools.issubset(names)


@pytest.mark.asyncio
async def test_configure_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test token configuration."""
    monkeypatch.setenv("BARISTA_TOKEN", "DUMMY")

    client = Client(SERVER_PATH)
    async with client:
        # Set token (no echo)
        res = await client.call_tool("configure_token", {"token": "NEW_TOKEN"})
        assert hasattr(res, "data")
        assert "configured" in str(getattr(res, "data")).lower()


@pytest.mark.asyncio
async def test_add_individual_mock():
    """Test add_individual with a mocked client."""
    import sys
    sys.path.insert(0, "src")

    import noctua_mcp.mcp_server as mcp_server

    with patch("noctua_mcp.mcp_server.BaristaClient") as MockClient:
        mock_instance = Mock()
        MockClient.return_value = mock_instance

        # Setup mock response
        from noctua import BaristaResponse
        mock_resp = Mock(spec=BaristaResponse)
        mock_resp.validation_failed = False
        mock_resp.validation_reason = None
        mock_resp.error = None
        mock_resp.individual_id = "mf1"
        mock_resp.raw = {"message-type": "success", "signal": "merge"}

        mock_instance.req_add_individual.return_value = {
            "entity": "individual",
            "operation": "add"
        }
        mock_instance.m3_batch.return_value = mock_resp

        # Mock add_individual_validated
        mock_instance.add_individual_validated.return_value = mock_resp

        # Reset the client
        mcp_server._client = None

        # Call the function
        result = await mcp_server.add_individual.fn(
            model_id="gomodel:12345",
            class_curie="GO:0003674",
            class_label="molecular_function",
            assign_var="mf1"
        )

        # Verify calls - should use add_individual_validated
        mock_instance.add_individual_validated.assert_called_once_with(
            "gomodel:12345", "GO:0003674", {"id": "GO:0003674", "label": "molecular_function"}, "mf1"
        )

        assert result["success"] is True
        assert result["individual_id"] == "mf1"


@pytest.mark.asyncio
async def test_add_fact_mock():
    """Test add_fact with a mocked client."""
    import sys
    sys.path.insert(0, "src")

    import noctua_mcp.mcp_server as mcp_server

    with patch("noctua_mcp.mcp_server.BaristaClient") as MockClient:
        mock_instance = Mock()
        MockClient.return_value = mock_instance

        from noctua import BaristaResponse
        mock_resp = Mock(spec=BaristaResponse)
        mock_resp.validation_failed = False
        mock_resp.validation_reason = None
        mock_resp.error = None
        mock_resp.validation_failed = False
        mock_resp.validation_reason = None
        mock_resp.error = None
        mock_resp.success = True
        mock_resp.raw = {"message-type": "success"}

        mock_instance.req_add_fact.return_value = {"entity": "edge"}
        mock_instance.m3_batch.return_value = mock_resp

        # Mock _resolve_identifier to return the input unchanged
        mock_instance._resolve_identifier = Mock(side_effect=lambda model_id, identifier: identifier)

        mcp_server._client = None

        result = await mcp_server.add_fact.fn(
            model_id="gomodel:12345",
            subject_id="ind1",
            object_id="ind2",
            predicate_id="RO:0002333"
        )

        # Check that _resolve_identifier was called for both subject and object
        assert mock_instance._resolve_identifier.call_count == 2
        mock_instance._resolve_identifier.assert_any_call("gomodel:12345", "ind1")
        mock_instance._resolve_identifier.assert_any_call("gomodel:12345", "ind2")

        # req_add_fact should be called with resolved identifiers (same in this case)
        mock_instance.req_add_fact.assert_called_once_with(
            "gomodel:12345", "ind1", "ind2", "RO:0002333"
        )
        assert result["success"] is True
        assert result["fact_added"] is True


@pytest.mark.asyncio
async def test_model_summary_mock():
    """Test model_summary with various response scenarios."""
    import sys
    sys.path.insert(0, "src")

    import noctua_mcp.mcp_server as mcp_server

    with patch("noctua_mcp.mcp_server.BaristaClient") as MockClient:
        mock_instance = Mock()
        MockClient.return_value = mock_instance

        from noctua import BaristaResponse
        mock_resp = Mock(spec=BaristaResponse)
        mock_resp.validation_failed = False
        mock_resp.validation_reason = None
        mock_resp.error = None
        mock_resp.success = True
        mock_resp.individuals = [
            {"id": "ind1"}, {"id": "ind2"}, {"id": "ind3"}
        ]
        mock_resp.facts = [
            {"property": "RO:0002333"},
            {"property": "RO:0002333"},
            {"property": "RO:0002432"},
        ]
        mock_resp.model_state = "production"

        mock_instance.get_model.return_value = mock_resp

        mcp_server._client = None

        result = await mcp_server.model_summary.fn("gomodel:12345")

        assert result["model_id"] == "gomodel:12345"
        assert result["state"] == "production"
        assert result["individual_count"] == 3
        assert result["fact_count"] == 3
        assert result["predicate_distribution"]["RO:0002333"] == 2
        assert result["predicate_distribution"]["RO:0002432"] == 1


@pytest.mark.asyncio
@pytest.mark.skip(reason="add_activity_unit is deprecated until we solve transaction rollback issues")
async def test_add_activity_unit_mock():
    """Test add_activity_unit creates correct request sequence."""
    import sys
    sys.path.insert(0, "src")

    import noctua_mcp.mcp_server as mcp_server

    with patch("noctua_mcp.mcp_server.BaristaClient") as MockClient:
        mock_instance = Mock()
        MockClient.return_value = mock_instance

        from noctua import BaristaResponse
        mock_resp = Mock(spec=BaristaResponse)
        mock_resp.validation_failed = False
        mock_resp.validation_reason = None
        mock_resp.error = None
        mock_resp.success = True
        mock_resp.raw = {"message-type": "success"}

        mock_instance.m3_batch.return_value = mock_resp
        mock_instance.req_add_individual.return_value = {"entity": "individual"}
        mock_instance.req_add_fact.return_value = {"entity": "edge"}

        # Mock execute_with_validation
        mock_instance.execute_with_validation.return_value = mock_resp

        mcp_server._client = None

        result = await mcp_server.add_activity_unit.fn(
            model_id="gomodel:12345",
            pathway_curie="GO:0016055",
            pathway_label="Wnt signaling pathway",
            mf_curie="GO:0003674",
            mf_label="molecular_function",
            gene_product_curie="UniProtKB:P38398",
            gene_product_label="BRCA1",
            cc_curie="GO:0005575",
            cc_label="cellular_component"
        )

        # Should call execute_with_validation with the batch requests
        mock_instance.execute_with_validation.assert_called_once()
        # Verify the batch contained expected number of requests
        assert mock_instance.req_add_individual.call_count == 4
        assert mock_instance.req_add_fact.call_count == 3

        assert result["success"] is True


@pytest.mark.asyncio
@pytest.mark.skip(reason="Skipping add_causal_chain test for now")
async def test_add_causal_chain_mock():
    """Test add_causal_chain creates correct request sequence."""
    import sys
    sys.path.insert(0, "src")

    import noctua_mcp.mcp_server as mcp_server

    with patch("noctua_mcp.mcp_server.BaristaClient") as MockClient:
        mock_instance = Mock()
        MockClient.return_value = mock_instance

        from noctua import BaristaResponse
        mock_resp = Mock(spec=BaristaResponse)
        mock_resp.validation_failed = False
        mock_resp.validation_reason = None
        mock_resp.error = None
        mock_resp.success = True
        mock_resp.raw = {"message-type": "success"}

        mock_instance.m3_batch.return_value = mock_resp
        mock_instance.req_add_individual.return_value = {"entity": "individual"}
        mock_instance.req_add_fact.return_value = {"entity": "edge"}

        # Mock execute_with_validation
        mock_instance.execute_with_validation.return_value = mock_resp

        mcp_server._client = None

        result = await mcp_server.add_causal_chain.fn(
            model_id="gomodel:12345",
            mf1_curie="GO:0003674",
            mf1_label="molecular_function 1",
            mf2_curie="GO:0003674",
            mf2_label="molecular_function 2",
            gp1_curie="UniProtKB:P38398",
            gp1_label="protein 1",
            gp2_curie="UniProtKB:Q9BRQ8",
            gp2_label="protein 2"
        )

        # Should call execute_with_validation with the batch requests
        mock_instance.execute_with_validation.assert_called_once()
        # Verify the batch contained expected number of requests
        assert mock_instance.req_add_individual.call_count == 4
        assert mock_instance.req_add_fact.call_count == 3

        assert result["success"] is True


@pytest.mark.live
@pytest.mark.asyncio
async def test_live_mcp_tools_variable_behavior() -> None:
    """Test how variables work through the MCP tools (not bypassing the shim).

    This test properly uses the MCP server tools to demonstrate:
    1. Variables returned from add_individual are actual IDs, not variable names
    2. These IDs can be used across separate MCP tool calls
    3. The get_model_variables tool shows current variable mappings
    """
    token = os.environ.get("BARISTA_TOKEN")
    if not token:
        pytest.skip("BARISTA_TOKEN not set; skipping live test")

    client = Client(SERVER_PATH)
    async with client:
        # Configure token
        await client.call_tool("configure_token", {"token": token})

        # Step 1: Create a model
        print("\n=== Testing MCP tools variable behavior ===")
        create_result = await client.call_tool("create_model", {
            "title": "Test MCP variable behavior"
        })

        if hasattr(create_result, 'data'):
            data = create_result.data
            if "error" in data:
                if "bad token" in str(data).lower():
                    pytest.skip("Invalid BARISTA_TOKEN; skipping live test")
                assert False, f"Failed to create model: {data}"

            assert "model_id" in data
            model_id = data["model_id"]
            print(f"Created model: {model_id}")

            # Step 2: Add individuals with variables
            print("\nAdding individuals with variable names...")

            # Add molecular function
            mf_result = await client.call_tool("add_individual", {
                "model_id": model_id,
                "class_curie": "GO:0003674",
                "class_label": "molecular_function",
                "assign_var": "mf_var"
            })

            mf_data = mf_result.data
            assert mf_data["success"] is True
            mf_id = mf_data["individual_id"]
            print(f"MF individual ID returned: {mf_id}")
            assert mf_id != "mf_var", "Should return actual ID, not variable name"
            # Individual IDs have format gomodel:XXX/YYY - check it starts with model ID base
            assert mf_id.startswith(model_id + "/"), f"ID {mf_id} should start with {model_id}/"

            # Add gene product
            gp_result = await client.call_tool("add_individual", {
                "model_id": model_id,
                "class_curie": "UniProtKB:P12345",
                "class_label": "GOT2 NCBITaxon:9986",  # Actual label for this UniProt entry
                "assign_var": "gp_var"
            })

            gp_data = gp_result.data
            if not gp_data.get("success"):
                print(f"GP addition failed: {gp_data}")
            assert gp_data["success"] is True, f"Failed to add GP: {gp_data}"
            gp_id = gp_data["individual_id"]
            print(f"GP individual ID returned: {gp_id}")
            assert gp_id != "gp_var", "Should return actual ID, not variable name"

            # Step 3: Check variables with get_model_variables
            print("\nChecking model variables...")
            vars_result = await client.call_tool("get_model_variables", {
                "model_id": model_id
            })

            if hasattr(vars_result, 'data'):
                vars_data = vars_result.data
                print(f"Model variables: {vars_data.get('variables', {})}")
                print(f"Individual count: {vars_data.get('individual_count', 0)}")

            # Step 4: Add fact using VARIABLE NAMES (not actual IDs)
            print("\nAdding fact using VARIABLE NAMES...")
            fact_result = await client.call_tool("add_fact", {
                "model_id": model_id,
                "subject_id": "mf_var",  # Using variable name!
                "object_id": "gp_var",   # Using variable name!
                "predicate_id": "RO:0002333"  # enabled_by
            })

            fact_data = fact_result.data
            print(f"Fact addition result: {fact_data}")
            # With proper variable tracking, this should now succeed!
            assert fact_data.get("success") is True, f"Variables should work with persistent client: {fact_data}"
            print("SUCCESS: Variables work across separate MCP tool calls!")

            # Verify that the variables in get_model_variables are populated
            assert vars_data.get("variables", {}), "Should have variables in the registry"
            assert "mf_var" in vars_data["variables"], "Should have mf_var in registry"
            assert "gp_var" in vars_data["variables"], "Should have gp_var in registry"
            print(f"Variables correctly tracked: {vars_data['variables']}")

            # Step 5: Verify the model structure
            print("\nVerifying model structure...")
            summary_result = await client.call_tool("model_summary", {
                "model_id": model_id
            })

            summary_data = summary_result.data
            assert summary_data["individual_count"] >= 2
            assert summary_data["fact_count"] >= 1
            assert "RO:0002333" in summary_data.get("predicate_distribution", {})
            print(f"Model has {summary_data['individual_count']} individuals and {summary_data['fact_count']} facts")

        else:
            assert False, f"Unexpected response type: {type(create_result)}"


@pytest.mark.live
@pytest.mark.asyncio
async def test_live_create_model_with_components() -> None:
    """Live end-to-end test: create model, add GP/MF/CC/BP, and connect with facts."""
    token = os.environ.get("BARISTA_TOKEN")
    if not token:
        pytest.skip("BARISTA_TOKEN not set; skipping live test")

    client = Client(SERVER_PATH)
    async with client:
        # Configure token
        await client.call_tool("configure_token", {"token": token})

        # Step 1: Create a new model
        create_result = await client.call_tool("create_model", {
            "title": "Test model for MCP integration"
        })

        if hasattr(create_result, 'data'):
            data = create_result.data
            if "error" in data:
                if "bad token" in str(data).lower():
                    pytest.skip("Invalid BARISTA_TOKEN; skipping live test")
                assert False, f"Failed to create model: {data}"

            assert "model_id" in data
            model_id = data["model_id"]

            # Step 2: Add molecular function (protein serine/threonine kinase activity)
            mf_result = await client.call_tool("add_individual", {
                "model_id": model_id,
                "assign_var": "torc2_activity",
                "class_curie": "GO:0004674",
                "class_label": "protein serine/threonine kinase activity"
            })

            mf_id = None
            if hasattr(mf_result, 'data'):
                mf_data = mf_result.data
                assert "success" in mf_data
                assert mf_data["success"] is True
                # Get the actual individual ID
                mf_id = mf_data.get("individual_id", "torc2_activity")
                print(f"MF individual created: {mf_id}")

            # Step 3: Add gene product (tor1 from PomBase)
            gp_result = await client.call_tool("add_individual", {
                "model_id": model_id,
                "assign_var": "tor1_gp",
                "class_curie": "PomBase:SPBC30D10.10c",
                "class_label": "tor1 Spom"
            })

            gp_id = None
            if hasattr(gp_result, 'data'):
                gp_data = gp_result.data
                assert "success" in gp_data
                assert gp_data["success"] is True
                # Get the actual individual ID
                gp_id = gp_data.get("individual_id", "tor1_gp")
                print(f"GP individual created: {gp_id}")

            # Step 4: Add cellular component (cytoplasm)
            cc_result = await client.call_tool("add_individual", {
                "model_id": model_id,
                "assign_var": "cytoplasm",
                "class_curie": "GO:0005737",
                "class_label": "cytoplasm"
            })

            cc_id = None
            if hasattr(cc_result, 'data'):
                cc_data = cc_result.data
                assert "success" in cc_data
                assert cc_data["success"] is True
                # Get the actual individual ID
                cc_id = cc_data.get("individual_id", "cytoplasm")
                print(f"CC individual created: {cc_id}")

            # Step 5: Add biological process (TOR signaling)
            bp_result = await client.call_tool("add_individual", {
                "model_id": model_id,
                "assign_var": "tor_signaling",
                "class_curie": "GO:0031929",
                "class_label": "TOR signaling"
            })

            bp_id = None
            if hasattr(bp_result, 'data'):
                bp_data = bp_result.data
                assert "success" in bp_data
                assert bp_data["success"] is True
                # Get the actual individual ID
                bp_id = bp_data.get("individual_id", "tor_signaling")
                print(f"BP individual created: {bp_id}")

            # Step 6: Add enabled_by relationship (MF enabled_by GP)
            # Use the actual individual IDs, not the variable names
            enabled_by_result = await client.call_tool("add_fact", {
                "model_id": model_id,
                "subject_id": mf_id,
                "object_id": gp_id,
                "predicate_id": "RO:0002333"
            })

            if hasattr(enabled_by_result, 'data'):
                eb_data = enabled_by_result.data
                if "error" in eb_data:
                    print(f"Error in add_fact: {eb_data}")
                assert "success" in eb_data, f"add_fact failed: {eb_data}"
                if not eb_data.get("success"):
                    print(f"add_fact returned success=False: {eb_data}")
                assert eb_data["success"] is True

            # Step 7: Add occurs_in relationship (MF occurs_in CC)
            occurs_in_result = await client.call_tool("add_fact", {
                "model_id": model_id,
                "subject_id": mf_id,
                "object_id": cc_id,
                "predicate_id": "BFO:0000066"
            })

            if hasattr(occurs_in_result, 'data'):
                oi_data = occurs_in_result.data
                assert "success" in oi_data
                assert oi_data["success"] is True

            # Step 8: Add part_of relationship (MF part_of BP)
            part_of_result = await client.call_tool("add_fact", {
                "model_id": model_id,
                "subject_id": mf_id,
                "object_id": bp_id,
                "predicate_id": "BFO:0000050"
            })

            if hasattr(part_of_result, 'data'):
                po_data = part_of_result.data
                assert "success" in po_data
                assert po_data["success"] is True

            # Step 9: Verify the model was created correctly
            summary_result = await client.call_tool("model_summary", {"model_id": model_id})

            if hasattr(summary_result, 'data'):
                summary_data = summary_result.data
                assert "individual_count" in summary_data
                assert summary_data["individual_count"] >= 4  # MF, GP, CC, BP
                assert "fact_count" in summary_data
                assert summary_data["fact_count"] >= 3  # enabled_by, occurs_in, part_of

                # Check predicate distribution
                preds = summary_data.get("predicate_distribution", {})
                assert "RO:0002333" in preds  # enabled_by
                assert "BFO:0000066" in preds  # occurs_in
                assert "BFO:0000050" in preds  # part_of
        else:
            assert False, f"Unexpected response type: {type(create_result)}"


# Live tests (require BARISTA_TOKEN and network access)
@pytest.mark.live
@pytest.mark.asyncio
async def test_live_get_model(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test retrieving a model from the live server."""
    model_id = "gomodel:68d5ebd600000096"
    token = os.environ.get("BARISTA_TOKEN")
    if not token:
        pytest.skip("BARISTA_TOKEN not set; skipping live test")

    client = Client(SERVER_PATH)
    async with client:
        await client.call_tool("configure_token", {"token": token})
        out = await client.call_tool("get_model", {"model_id": model_id})

        # The call_tool returns a CallToolResult object, get the data attribute
        if hasattr(out, 'data'):
            data = out.data
            assert isinstance(data, dict)
            # Check for valid response or error
            if "message" in data and "bad token" in data.get("message", "").lower():
                pytest.skip("Invalid BARISTA_TOKEN; skipping live test")
            # Now we expect structured minimal responses with success/error fields
            assert "success" in data or "error" in data
        else:
            assert False, f"Unexpected response type: {type(out)}"


@pytest.mark.live
@pytest.mark.asyncio
async def test_live_model_summary(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test getting a model summary from the live server."""
    model_id = "gomodel:68d5ebd600000096"
    token = os.environ.get("BARISTA_TOKEN")
    if not token:
        pytest.skip("BARISTA_TOKEN not set; skipping live test")

    client = Client(SERVER_PATH)
    async with client:
        await client.call_tool("configure_token", {"token": token})
        out = await client.call_tool("model_summary", {"model_id": model_id})

        # The call_tool returns a CallToolResult object, get the data attribute
        if hasattr(out, 'data'):
            data = out.data
            assert isinstance(data, dict)

            # Check for authentication error
            if "error" in data and "details" in data:
                details = data["details"]
                if isinstance(details, dict) and "message" in details:
                    if "bad token" in details["message"].lower():
                        pytest.skip("Invalid BARISTA_TOKEN; skipping live test")

            # Check for expected fields if no error
            if "error" not in data:
                assert "individual_count" in data
                assert "fact_count" in data
                assert "predicate_distribution" in data
        else:
            assert False, f"Unexpected response type: {type(out)}"


@pytest.mark.asyncio
async def test_prompts_exist() -> None:
    """Test that prompts are available."""
    client = Client(SERVER_PATH)
    async with client:
        prompts = await client.list_prompts()
        prompt_names = {p.name for p in prompts}

        assert "create_basic_activity" in prompt_names
        assert "add_evidence_prompt" in prompt_names


@pytest.mark.asyncio
async def test_prompt_content() -> None:
    """Test that prompts return expected content."""
    client = Client(SERVER_PATH)
    async with client:
        # Get the create_basic_activity prompt
        prompts = await client.list_prompts()
        next(p for p in prompts if p.name == "create_basic_activity")  # Verify it exists

        # Get the prompt content
        content = await client.get_prompt("create_basic_activity")

        # Check content has expected keywords
        assert "add_individual" in str(content)
        assert "RO:0002333" in str(content)


@pytest.mark.asyncio
async def test_search_models_mock():
    """Test search_models with a mocked client."""
    import sys
    sys.path.insert(0, "src")

    import noctua_mcp.mcp_server as mcp_server

    with patch("noctua_mcp.mcp_server.BaristaClient") as MockClient:
        mock_instance = Mock()
        MockClient.return_value = mock_instance

        # Mock search results
        mock_results = {
            "models": [
                {
                    "id": "gomodel:12345",
                    "title": "Test Model 1",
                    "state": "production"
                },
                {
                    "id": "gomodel:67890",
                    "title": "Test Model 2",
                    "state": "development"
                }
            ],
            "total": 2
        }

        mock_instance.list_models.return_value = mock_results

        mcp_server._client = None

        # Test basic search
        result = await mcp_server.search_models.fn(
            title="Test",
            state="production"
        )

        mock_instance.list_models.assert_called_once_with(
            title="Test",
            state="production",
            contributor=None,
            group=None,
            pmid=None,
            gp=None,
            limit=50,
            offset=0
        )
        assert result == mock_results


@pytest.mark.asyncio
async def test_search_models_with_filters_mock():
    """Test search_models with various filter combinations."""
    import sys
    sys.path.insert(0, "src")

    import noctua_mcp.mcp_server as mcp_server

    with patch("noctua_mcp.mcp_server.BaristaClient") as MockClient:
        mock_instance = Mock()
        MockClient.return_value = mock_instance

        mock_results = {"models": [], "total": 0}
        mock_instance.list_models.return_value = mock_results

        mcp_server._client = None

        # Test with gene product and PMID filters
        result = await mcp_server.search_models.fn(
            gene_product="UniProtKB:P38398",
            pmid="PMID:12345678",
            limit=10,
            offset=20
        )

        mock_instance.list_models.assert_called_once_with(
            title=None,
            state=None,
            contributor=None,
            group=None,
            pmid="PMID:12345678",
            gp="UniProtKB:P38398",
            limit=10,
            offset=20
        )
        assert result == mock_results


@pytest.mark.asyncio
async def test_search_models_error_handling_mock():
    """Test search_models error handling."""
    import sys
    sys.path.insert(0, "src")

    import noctua_mcp.mcp_server as mcp_server

    with patch("noctua_mcp.mcp_server.BaristaClient") as MockClient:
        mock_instance = Mock()
        MockClient.return_value = mock_instance

        # Simulate an error
        mock_instance.list_models.side_effect = Exception("Connection error")

        mcp_server._client = None

        result = await mcp_server.search_models.fn()

        assert "error" in result
        assert result["error"] == "Failed to search models"
        assert "Connection error" in result["message"]


@pytest.mark.asyncio
async def test_search_bioentities_mock():
    """Test search_bioentities with a mocked client."""
    import sys
    sys.path.insert(0, "src")

    import noctua_mcp.mcp_server as mcp_server

    with patch("noctua_mcp.mcp_server.AmigoClient") as MockAmigoClient:
        mock_client = Mock()
        MockAmigoClient.return_value.__enter__.return_value = mock_client

        # Mock bioentity results
        from noctua.amigo import BioentityResult
        mock_results = [
            BioentityResult(
                id="UniProtKB:P01308",
                label="INS",
                name="insulin",
                type="protein",
                taxon="NCBITaxon:9606",
                taxon_label="Homo sapiens",
                source="UniProtKB",
                raw={}
            ),
            BioentityResult(
                id="MGI:MGI:96573",
                label="Ins1",
                name="insulin 1",
                type="gene",
                taxon="NCBITaxon:10090",
                taxon_label="Mus musculus",
                source="MGI",
                raw={}
            )
        ]

        mock_client.search_bioentities.return_value = mock_results

        # Test basic search
        result = await mcp_server.search_bioentities.fn(
            text="insulin",
            taxon="9606"
        )

        mock_client.search_bioentities.assert_called_once_with(
            text="insulin",
            taxon="NCBITaxon:9606",  # Should be normalized
            bioentity_type=None,
            source=None,
            limit=10,
            offset=0
        )

        assert "results" in result
        assert len(result["results"]) == 2
        assert result["results"][0]["id"] == "UniProtKB:P01308"
        assert result["results"][0]["label"] == "INS"
        assert result["count"] == 2


@pytest.mark.asyncio
async def test_search_bioentities_taxon_normalization():
    """Test that taxon IDs are properly normalized."""
    import sys
    sys.path.insert(0, "src")

    import noctua_mcp.mcp_server as mcp_server

    with patch("noctua_mcp.mcp_server.AmigoClient") as MockAmigoClient:
        mock_client = Mock()
        MockAmigoClient.return_value.__enter__.return_value = mock_client
        mock_client.search_bioentities.return_value = []

        # Test with just number
        await mcp_server.search_bioentities.fn(taxon="9606")
        mock_client.search_bioentities.assert_called_with(
            text=None,
            taxon="NCBITaxon:9606",
            bioentity_type=None,
            source=None,
            limit=10,
            offset=0
        )

        # Test with already prefixed
        await mcp_server.search_bioentities.fn(taxon="NCBITaxon:10090")
        mock_client.search_bioentities.assert_called_with(
            text=None,
            taxon="NCBITaxon:10090",
            bioentity_type=None,
            source=None,
            limit=10,
            offset=0
        )


@pytest.mark.asyncio
async def test_search_bioentities_error_handling():
    """Test search_bioentities error handling."""
    import sys
    sys.path.insert(0, "src")

    import noctua_mcp.mcp_server as mcp_server

    with patch("noctua_mcp.mcp_server.AmigoClient") as MockAmigoClient:
        mock_client = Mock()
        MockAmigoClient.return_value.__enter__.return_value = mock_client

        # Simulate an error
        mock_client.search_bioentities.side_effect = Exception("Connection error")

        result = await mcp_server.search_bioentities.fn(text="test")

        assert "error" in result
        assert result["error"] == "Failed to search bioentities"
        assert "Connection error" in result["message"]


@pytest.mark.asyncio
async def test_search_annotations_mock():
    """Test search_annotations with mocked AmigoClient"""
    from unittest.mock import Mock, patch
    import noctua_mcp.mcp_server as mcp_server

    # Create mock annotation results
    mock_annotations = [
        Mock(
            bioentity="UniProtKB:P12345",
            bioentity_label="Test Protein",
            bioentity_name="TEST_HUMAN",
            annotation_class="GO:0005634",
            annotation_class_label="nucleus",
            aspect="C",
            evidence_type="IDA",
            evidence="PMID:12345",
            evidence_label="immunofluorescence",
            reference="PMID:12345",
            assigned_by="UniProtKB",
            date="20240101",
            taxon="NCBITaxon:9606",
            taxon_label="Homo sapiens",
            qualifier="",
            annotation_extension=""
        )
    ]

    with patch("noctua_mcp.mcp_server.AmigoClient") as MockAmigoClient:
        mock_client = Mock()
        MockAmigoClient.return_value.__enter__.return_value = mock_client
        mock_client.search_annotations.return_value = mock_annotations

        result = await mcp_server.search_annotations.fn(
            go_term="GO:0005634",
            evidence_types="IDA,IPI",
            taxon="9606",
            limit=50
        )

        assert "annotations" in result
        assert result["total"] == 1
        assert result["annotations"][0]["go_term"] == "GO:0005634"
        assert result["annotations"][0]["evidence_type"] == "IDA"

        # Verify taxon normalization
        mock_client.search_annotations.assert_called_once_with(
            bioentity=None,
            go_term="GO:0005634",
            evidence_types=["IDA", "IPI"],
            taxon="NCBITaxon:9606",  # Should be normalized
            aspect=None,
            assigned_by=None,
            limit=50
        )


@pytest.mark.asyncio
async def test_get_annotations_for_bioentity_mock():
    """Test get_annotations_for_bioentity with mocked AmigoClient"""
    from unittest.mock import Mock, patch
    import noctua_mcp.mcp_server as mcp_server

    mock_annotations = [
        Mock(
            annotation_class="GO:0005634",
            annotation_class_label="nucleus",
            aspect="C",
            evidence_type="IDA",
            evidence="PMID:12345",
            evidence_label="immunofluorescence",
            reference="PMID:12345",
            assigned_by="UniProtKB",
            date="20240101",
            qualifier="",
            annotation_extension=""
        ),
        Mock(
            annotation_class="GO:0008150",
            annotation_class_label="biological_process",
            aspect="P",
            evidence_type="IMP",
            evidence="PMID:67890",
            evidence_label="mutant phenotype",
            reference="PMID:67890",
            assigned_by="MGI",
            date="20240102",
            qualifier="",
            annotation_extension=""
        )
    ]

    with patch("noctua_mcp.mcp_server.AmigoClient") as MockAmigoClient:
        mock_client = Mock()
        MockAmigoClient.return_value.__enter__.return_value = mock_client
        mock_client.get_annotations_for_bioentity.return_value = mock_annotations

        result = await mcp_server.get_annotations_for_bioentity.fn(
            bioentity_id="UniProtKB:P12345",
            evidence_types="IDA,IMP"
        )

        assert result["bioentity_id"] == "UniProtKB:P12345"
        assert "annotations" in result
        assert "summary" in result
        assert result["summary"]["total"] == 2
        assert result["summary"]["by_aspect"] == {"C": 1, "P": 1}
        assert result["summary"]["by_evidence_type"] == {"IDA": 1, "IMP": 1}

        mock_client.get_annotations_for_bioentity.assert_called_once_with(
            bioentity_id="UniProtKB:P12345",
            go_terms_closure=None,
            evidence_types=["IDA", "IMP"],
            aspect=None,
            limit=100
        )


@pytest.mark.asyncio
async def test_search_annotations_with_multiple_filters():
    """Test search_annotations with multiple filter parameters"""
    from unittest.mock import Mock, patch
    import noctua_mcp.mcp_server as mcp_server

    mock_annotations = []

    with patch("noctua_mcp.mcp_server.AmigoClient") as MockAmigoClient:
        mock_client = Mock()
        MockAmigoClient.return_value.__enter__.return_value = mock_client
        mock_client.search_annotations.return_value = mock_annotations

        result = await mcp_server.search_annotations.fn(
            bioentity="UniProtKB:P12345",
            go_term="GO:0005634",
            evidence_types="IDA,IPI,IMP",
            taxon="NCBITaxon:9606",
            aspect="C",
            assigned_by="UniProtKB",
            limit=100
        )

        assert result["total"] == 0
        assert result["annotations"] == []

        # Verify all parameters were passed correctly
        mock_client.search_annotations.assert_called_once_with(
            bioentity="UniProtKB:P12345",
            go_term="GO:0005634",
            evidence_types=["IDA", "IPI", "IMP"],
            taxon="NCBITaxon:9606",
            aspect="C",
            assigned_by="UniProtKB",
            limit=100
        )