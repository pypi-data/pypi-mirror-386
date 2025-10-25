"""
Unit tests for the noctua-mcp server components.

These tests do not require the MCP client and test individual functions directly.
"""

import os
from unittest.mock import Mock, patch
import pytest


def test_imports():
    """Test that all modules can be imported."""


def test_barista_compatibility():
    """Test that noctua classes can be imported directly."""
    from noctua import BaristaClient, BaristaResponse, BaristaError

    # These should be imported from noctua
    assert BaristaClient is not None
    assert BaristaResponse is not None
    assert BaristaError is not None


@pytest.mark.asyncio
async def test_get_client_singleton():
    """Test that get_client returns a singleton instance."""
    import noctua_mcp.mcp_server as mcp_server

    with patch("noctua_mcp.mcp_server.BaristaClient") as MockClient:
        mock_instance = Mock()
        MockClient.return_value = mock_instance

        # Reset global client
        mcp_server._client = None

        # First call should create client
        client1 = mcp_server.get_client()
        assert client1 == mock_instance
        MockClient.assert_called_once()

        # Second call should return same instance
        client2 = mcp_server.get_client()
        assert client2 == client1
        MockClient.assert_called_once()  # Still only called once


@pytest.mark.asyncio
async def test_configure_token_resets_client():
    """Test that configure_token resets the client instance."""
    import noctua_mcp.mcp_server as mcp_server

    with patch("noctua_mcp.mcp_server.BaristaClient") as MockClient:
        mock_instance = Mock()
        MockClient.return_value = mock_instance

        # Set initial client
        mcp_server._client = mock_instance

        # Configure new token - access the wrapped function
        result = await mcp_server.configure_token.fn("new-token")

        # Client should be reset to None
        assert mcp_server._client is None
        assert os.environ.get("BARISTA_TOKEN") == "new-token"
        assert result["success"] is True
        assert result["configured"] is True

        # Clean up
        if "BARISTA_TOKEN" in os.environ:
            del os.environ["BARISTA_TOKEN"]


@pytest.mark.asyncio
async def test_add_individual_parameters():
    """Test that add_individual passes correct parameters."""
    import noctua_mcp.mcp_server as mcp_server

    with patch("noctua_mcp.mcp_server.BaristaClient") as MockClient:
        mock_instance = Mock()
        MockClient.return_value = mock_instance

        from noctua import BaristaResponse
        mock_resp = Mock(spec=BaristaResponse)
        mock_resp.raw = {"test": "response"}

        # Update validation properties
        mock_resp.validation_failed = False
        mock_resp.validation_reason = None
        mock_resp.error = None
        mock_resp.success = True
        mock_resp.individual_id = "var1"
        mock_resp.class_curie = "GO:0003674"
        mock_resp.assign_var = "var1"

        # Mock add_individual_validated
        mock_instance.add_individual_validated.return_value = mock_resp

        mcp_server._client = None

        result = await mcp_server.add_individual.fn(
            "model123", "GO:0003674", "molecular_function", "var1"
        )

        # Should use add_individual_validated
        mock_instance.add_individual_validated.assert_called_once_with(
            "model123", "GO:0003674", {"id": "GO:0003674", "label": "molecular_function"}, "var1"
        )
        assert result["success"] is True
        assert result["individual_id"] == "var1"
        assert result["class_curie"] == "GO:0003674"
        assert result["assign_var"] == "var1"


@pytest.mark.asyncio
async def test_add_evidence_to_fact_parameters():
    """Test that add_evidence_to_fact passes correct parameters."""
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
        mock_resp.raw = {"test": "response"}

        mock_reqs = [{"req": "1"}, {"req": "2"}]
        mock_instance.req_add_evidence_to_fact.return_value = mock_reqs
        mock_instance.m3_batch.return_value = mock_resp

        mcp_server._client = None

        result = await mcp_server.add_evidence_to_fact.fn(
            model_id="model123",
            subject_id="subj1",
            object_id="obj1",
            predicate_id="RO:0002333",
            eco_id="ECO:0000353",
            sources=["PMID:12345"],
            with_from=["UniProtKB:P12345"]
        )

        mock_instance.req_add_evidence_to_fact.assert_called_once_with(
            "model123", "subj1", "obj1", "RO:0002333",
            "ECO:0000353", ["PMID:12345"], ["UniProtKB:P12345"]
        )
        mock_instance.m3_batch.assert_called_once_with(mock_reqs)
        assert result["success"] is True


@pytest.mark.asyncio
async def test_model_summary_calculations():
    """Test that model_summary correctly calculates statistics."""
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
            {"id": "i1"}, {"id": "i2"}, {"id": "i3"}, {"id": "i4"}
        ]
        mock_resp.facts = [
            {"property": "RO:0002333"},
            {"property": "RO:0002333"},
            {"property": "RO:0002333"},
            {"property": "RO:0002432"},
            {"property": "RO:0002434"},
        ]
        mock_resp.model_state = "development"

        mock_instance.get_model.return_value = mock_resp

        mcp_server._client = None

        result = await mcp_server.model_summary.fn("model123")

        assert result["model_id"] == "model123"
        assert result["state"] == "development"
        assert result["individual_count"] == 4
        assert result["fact_count"] == 5
        assert result["predicate_distribution"]["RO:0002333"] == 3
        assert result["predicate_distribution"]["RO:0002432"] == 1
        assert result["predicate_distribution"]["RO:0002434"] == 1


@pytest.mark.asyncio
async def test_model_summary_error_handling():
    """Test that model_summary handles errors gracefully."""
    import noctua_mcp.mcp_server as mcp_server

    with patch("noctua_mcp.mcp_server.BaristaClient") as MockClient:
        mock_instance = Mock()
        MockClient.return_value = mock_instance

        from noctua import BaristaResponse
        mock_resp = Mock(spec=BaristaResponse)
        mock_resp.validation_failed = True
        mock_resp.validation_reason = "Model not found"
        mock_resp.error = "not found"
        mock_resp.success = False
        mock_resp.raw = {"error": "not found"}

        mock_instance.get_model.return_value = mock_resp

        mcp_server._client = None

        result = await mcp_server.model_summary.fn("invalid")

        assert "error" in result
        assert result["error"] == "Validation failed"
        assert result["reason"] == "Model not found"


@pytest.mark.asyncio
@pytest.mark.skip(reason="add_activity_unit is deprecated until we solve transaction rollback issues")
async def test_add_activity_unit_request_sequence():
    """Test that add_activity_unit creates the correct sequence of requests."""
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
        mock_resp.raw = {"success": True}

        # Track all calls
        individual_calls = []
        fact_calls = []

        def track_individual(*args):
            individual_calls.append(args)
            return {"entity": "individual", "args": args}

        def track_fact(*args):
            fact_calls.append(args)
            return {"entity": "edge", "args": args}

        mock_instance.req_add_individual.side_effect = track_individual
        mock_instance.req_add_fact.side_effect = track_fact
        mock_instance.m3_batch.return_value = mock_resp

        mcp_server._client = None

        await mcp_server.add_activity_unit.fn(
            model_id="model123",
            pathway_curie="GO:0016055",
            pathway_label="Wnt signaling pathway",
            mf_curie="GO:0003674",
            mf_label="molecular_function",
            gene_product_curie="UniProtKB:P38398",
            gene_product_label="BRCA1",
            cc_curie="GO:0005575",
            cc_label="cellular_component"
        )

        # Check individuals created
        assert len(individual_calls) == 4
        assert ("model123", "GO:0003674", "mf1") in individual_calls
        assert ("model123", "UniProtKB:P38398", "gp1") in individual_calls
        assert ("model123", "GO:0016055", "bp1") in individual_calls
        assert ("model123", "GO:0005575", "cc1") in individual_calls

        # Check facts created
        assert len(fact_calls) == 3
        assert ("model123", "mf1", "gp1", "RO:0002333") in fact_calls  # enabled_by
        assert ("model123", "mf1", "cc1", "BFO:0000066") in fact_calls  # occurs_in
        assert ("model123", "mf1", "bp1", "BFO:0000050") in fact_calls  # part_of


def test_prompts():
    """Test that prompt functions return expected content."""
    import noctua_mcp.mcp_server as mcp_server

    activity_prompt = mcp_server.create_basic_activity.fn()
    assert isinstance(activity_prompt, str)
    assert "add_individual" in activity_prompt
    assert "molecular function" in activity_prompt
    assert "RO:0002333" in activity_prompt

    evidence_prompt = mcp_server.add_evidence_prompt.fn()
    assert isinstance(evidence_prompt, str)
    assert "add_evidence_to_fact" in evidence_prompt
    assert "ECO" in evidence_prompt
    assert "PMID" in evidence_prompt


def test_cli_imports():
    """Test that CLI module can be imported and has expected functions."""
    from noctua_mcp.cli import main, app, serve, version

    assert main is not None
    assert app is not None
    assert serve is not None
    assert version is not None


@pytest.mark.parametrize("model_id,expected", [
    ("gomodel:12345", "gomodel:12345"),
    ("gomodel:abcde", "gomodel:abcde"),
    ("test123", "test123"),
])
@pytest.mark.asyncio
async def test_get_model_with_different_ids(model_id, expected):
    """Test get_model with various model IDs."""
    import noctua_mcp.mcp_server as mcp_server

    with patch("noctua_mcp.mcp_server.BaristaClient") as MockClient:
        mock_instance = Mock()
        MockClient.return_value = mock_instance

        from noctua import BaristaResponse
        mock_resp = Mock(spec=BaristaResponse)
        mock_resp.raw = {"model_id": expected}

        mock_instance.get_model.return_value = mock_resp

        mcp_server._client = None

        result = await mcp_server.get_model.fn(model_id)

        mock_instance.get_model.assert_called_once_with(model_id)
        assert result["model_id"] == expected


@pytest.mark.asyncio
async def test_search_models_basic():
    """Test search_models basic functionality."""
    import noctua_mcp.mcp_server as mcp_server

    with patch("noctua_mcp.mcp_server.BaristaClient") as MockClient:
        mock_instance = Mock()
        MockClient.return_value = mock_instance

        mock_results = {
            "models": [
                {"id": "gomodel:001", "title": "Model 1", "state": "production"},
                {"id": "gomodel:002", "title": "Model 2", "state": "development"}
            ],
            "total": 2
        }
        mock_instance.list_models.return_value = mock_results

        mcp_server._client = None

        result = await mcp_server.search_models.fn()

        mock_instance.list_models.assert_called_once_with(
            title=None,
            state=None,
            contributor=None,
            group=None,
            pmid=None,
            gp=None,
            limit=50,
            offset=0
        )
        assert result == mock_results


@pytest.mark.parametrize("filters,expected_args", [
    (
        {"title": "kinase", "state": "production"},
        {"title": "kinase", "state": "production", "contributor": None, "group": None, "pmid": None, "gp": None}
    ),
    (
        {"gene_product": "UniProtKB:P12345", "limit": 10},
        {"title": None, "state": None, "contributor": None, "group": None, "pmid": None, "gp": "UniProtKB:P12345"}
    ),
    (
        {"contributor": "https://orcid.org/0000-0002-6601-2165", "pmid": "PMID:12345"},
        {"title": None, "state": None, "contributor": "https://orcid.org/0000-0002-6601-2165", "group": None, "pmid": "PMID:12345", "gp": None}
    ),
])
@pytest.mark.asyncio
async def test_search_models_with_filters(filters, expected_args):
    """Test search_models with various filter combinations."""
    import noctua_mcp.mcp_server as mcp_server

    with patch("noctua_mcp.mcp_server.BaristaClient") as MockClient:
        mock_instance = Mock()
        MockClient.return_value = mock_instance

        mock_results = {"models": [], "total": 0}
        mock_instance.list_models.return_value = mock_results

        mcp_server._client = None

        # Set defaults for limit and offset
        call_params = {**filters}
        if "limit" not in call_params:
            call_params["limit"] = 50
        if "offset" not in call_params:
            call_params["offset"] = 0

        result = await mcp_server.search_models.fn(**filters)

        # Build expected call args with defaults
        full_expected_args = {**expected_args}
        full_expected_args["limit"] = call_params.get("limit", 50)
        full_expected_args["offset"] = call_params.get("offset", 0)

        mock_instance.list_models.assert_called_once_with(**full_expected_args)
        assert result == mock_results


@pytest.mark.asyncio
async def test_search_models_exception_handling():
    """Test that search_models handles exceptions gracefully."""
    import noctua_mcp.mcp_server as mcp_server

    with patch("noctua_mcp.mcp_server.BaristaClient") as MockClient:
        mock_instance = Mock()
        MockClient.return_value = mock_instance

        mock_instance.list_models.side_effect = RuntimeError("API connection failed")

        mcp_server._client = None

        result = await mcp_server.search_models.fn(title="test")

        assert "error" in result
        assert result["error"] == "Failed to search models"
        assert "API connection failed" in result["message"]


@pytest.mark.asyncio
async def test_search_bioentities_basic():
    """Test search_bioentities basic functionality."""
    import noctua_mcp.mcp_server as mcp_server

    with patch("noctua_mcp.mcp_server.AmigoClient") as MockAmigoClient:
        mock_client = Mock()
        MockAmigoClient.return_value.__enter__.return_value = mock_client

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
            )
        ]
        mock_client.search_bioentities.return_value = mock_results

        result = await mcp_server.search_bioentities.fn()

        mock_client.search_bioentities.assert_called_once_with(
            text=None,
            taxon=None,
            bioentity_type=None,
            source=None,
            limit=10,
            offset=0
        )
        assert "results" in result
        assert result["count"] == 1


@pytest.mark.parametrize("taxon_input,expected_taxon", [
    ("9606", "NCBITaxon:9606"),
    ("NCBITaxon:9606", "NCBITaxon:9606"),
    ("10090", "NCBITaxon:10090"),
    ("NCBITaxon:10090", "NCBITaxon:10090"),
    (None, None),
])
@pytest.mark.asyncio
async def test_search_bioentities_taxon_normalization_unit(taxon_input, expected_taxon):
    """Test that taxon IDs are normalized correctly."""
    import noctua_mcp.mcp_server as mcp_server

    with patch("noctua_mcp.mcp_server.AmigoClient") as MockAmigoClient:
        mock_client = Mock()
        MockAmigoClient.return_value.__enter__.return_value = mock_client
        mock_client.search_bioentities.return_value = []

        await mcp_server.search_bioentities.fn(taxon=taxon_input)

        mock_client.search_bioentities.assert_called_once_with(
            text=None,
            taxon=expected_taxon,
            bioentity_type=None,
            source=None,
            limit=10,
            offset=0
        )


@pytest.mark.asyncio
async def test_search_bioentities_all_parameters():
    """Test search_bioentities with all parameters."""
    import noctua_mcp.mcp_server as mcp_server

    with patch("noctua_mcp.mcp_server.AmigoClient") as MockAmigoClient:
        mock_client = Mock()
        MockAmigoClient.return_value.__enter__.return_value = mock_client
        mock_client.search_bioentities.return_value = []

        await mcp_server.search_bioentities.fn(
            text="kinase",
            taxon="9606",
            bioentity_type="protein",
            source="UniProtKB",
            limit=20,
            offset=10
        )

        mock_client.search_bioentities.assert_called_once_with(
            text="kinase",
            taxon="NCBITaxon:9606",
            bioentity_type="protein",
            source="UniProtKB",
            limit=20,
            offset=10
        )