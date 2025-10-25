"""
Noctua MCP Server
=================

Thin MCP wrapper around gocam-ai library for GO-CAM model manipulation.
This server exposes GO-CAM editing capabilities through the Model Context Protocol.

Security & credentials
----------------------
- Set BARISTA_TOKEN in environment before launch
- The token is used by the underlying gocam-ai BaristaClient

Transport
---------
- Runs via stdio transport by default
- Launch with: uvx noctua-mcp
"""

from typing import Any, Dict, List, Optional
from pathlib import Path

from fastmcp import FastMCP
from noctua import BaristaClient
from noctua.amigo import AmigoClient

# Path to guidelines directory
GUIDELINES_DIR = Path(__file__).parent / "guidelines"

mcp = FastMCP(
    "noctua-mcp",
    instructions="""
Noctua MCP Server provides tools for editing GO-CAM models via the Barista API.
Use these tools to create and edit GO-CAM models with individuals, facts, and evidence.
This also provides tools for finding relevant genes and gene products (entities) for use in the model.

Available operations:
- Create new empty GO-CAM models
- Add individuals (instances) of GO/ECO terms
- Add facts (edges) between individuals
- Add evidence to facts
- Remove individuals and facts
- Query model structure
- Create common GO-CAM patterns (e.g., basic pathway units)

"""
)


# Create a module-level client instance (will be lazily initialized)
_client: Optional[BaristaClient] = None


def get_client() -> BaristaClient:
    """Get or create the Barista client instance."""
    global _client
    if _client is None:
        _client = BaristaClient()
    return _client


@mcp.tool()
async def configure_token(token: str) -> Dict[str, Any]:
    """
    Configure the Barista authentication token.

    Args:
        token: The Barista authentication token

    Returns:
        Success status
    """
    import os
    global _client

    # Set environment variable
    os.environ["BARISTA_TOKEN"] = token

    # Reset client to pick up new token
    _client = None

    return {
        "success": True,
        "configured": True
    }



@mcp.tool()
async def create_model(
    title: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new empty GO-CAM model.

    Args:
        title: Optional title for the model

    Returns:
        Barista API response containing the new model ID and editor URLs

    Examples:
        # Create a new model with a title
        response = create_model("RAS-RAF signaling pathway")
        model_id = response["data"]["id"]
        print(f"Graph editor: {response['graph_editor_url']}")
        print(f"Pathway editor: {response['pathway_editor_url']}")

        # Create a model with a descriptive title
        response = create_model("Human Wnt signaling pathway")

        # Create an unnamed model
        response = create_model()

        # Extract the model ID from response
        if response["message-type"] == "success":
            model_id = response["data"]["id"]
            print(f"Created model: {model_id}")

    Notes:
        - The returned model_id can be used with other tools like add_individual
        - Models are created in "development" state by default
        - To add taxon information, use add_individual after creating the model
    """
    client = get_client()
    resp = client.create_model(title=title)

    if resp.validation_failed:
        return {
            "success": False,
            "error": "Validation failed",
            "reason": resp.validation_reason,
            "rolled_back": True
        }

    if resp.error:
        return {
            "success": False,
            "error": "Operation failed",
            "reason": resp.error
        }

    # Build minimal response
    result = {
        "success": True,
        "model_id": resp.model_id,
        "created": True
    }

    # Add editor URLs if we have a model ID
    if resp.model_id:
        import os
        token = os.environ.get("BARISTA_TOKEN", "")

        # Graph editor with token
        result["graph_editor_url"] = f"http://noctua-dev.berkeleybop.org/editor/graph/{resp.model_id}?barista_token={token}"

        # Pathway editor without token (URL encoded model ID)
        from urllib.parse import quote
        encoded_id = quote(resp.model_id, safe="")
        result["pathway_editor_url"] = f"http://noctua-dev.berkeleybop.org/workbench/noctua-visual-pathway-editor/?model_id={encoded_id}"

    return result


@mcp.tool()
async def add_individual(
    model_id: str,
    class_curie: str,
    class_label: str,
    assign_var: str = "x1"
) -> Dict[str, Any]:
    """
    Add an individual (instance) of a class to a GO-CAM model with label validation.

    This tool requires providing the expected label for the class to prevent
    accidental use of wrong IDs (e.g., GO:0003924 vs GO:0003925). The operation
    will automatically rollback if the created individual doesn't match the
    expected label.

    Args:
        model_id: The GO-CAM model identifier (e.g., "gomodel:12345")
        class_curie: The class to instantiate (e.g., "GO:0003674")
        class_label: The expected rdfs:label of the class (e.g., "molecular_function")
        assign_var: Variable name for referencing in the same batch

    Returns:
        Barista API response with message-type and signal fields.
        If validation fails, includes rolled_back=true and validation error.

    Examples:
        # Add a molecular function activity with validation
        add_individual("gomodel:12345", "GO:0004672", "protein kinase activity", "mf1")

        # Add a protein/gene product with validation
        add_individual("gomodel:12345", "UniProtKB:P38398", "BRCA1", "gp1")

        # Add a cellular component with validation
        add_individual("gomodel:12345", "GO:0005737", "cytoplasm", "cc1")

        # Add a biological process with validation
        add_individual("gomodel:12345", "GO:0016055", "Wnt signaling pathway", "bp1")

        # Add an evidence instance with validation
        add_individual("gomodel:12345", "ECO:0000353", "physical interaction evidence", "ev1")

        # Variables like "mf1", "gp1" can be referenced in subsequent
        # add_fact calls within the same batch operation

    Notes:
        - The label acts as a checksum to prevent ID hallucination
        - If the label doesn't match, the operation is automatically rolled back
        - This prevents corrupt models from incorrect IDs
    """
    client = get_client()
    expected_type = {"id": class_curie, "label": class_label}
    resp = client.add_individual_validated(model_id, class_curie, expected_type, assign_var)

    if resp.validation_failed:
        return {
            "success": False,
            "error": "Validation failed",
            "reason": resp.validation_reason,
            "rolled_back": True,
            "expected_label": class_label,
            "class_curie": class_curie
        }

    if resp.error:
        return {
            "success": False,
            "error": resp.error,
            "model_id": model_id,
            "class_curie": class_curie
        }

    # Get the actual individual ID from model_vars
    individual_id = assign_var  # Default to the variable name
    if hasattr(resp, 'model_vars') and resp.model_vars:
        individual_id = resp.model_vars.get(assign_var, assign_var)

    # Return minimal success response
    return {
        "success": True,
        "individual_id": individual_id,
        "class_curie": class_curie,
        "assign_var": assign_var
    }


@mcp.tool()
async def add_fact(
    model_id: str,
    subject_id: str,
    object_id: str,
    predicate_id: str
) -> Dict[str, Any]:
    """
    Add a fact (edge/relation) between two individuals in a model.

    Args:
        model_id: The GO-CAM model identifier
        subject_id: Subject individual ID or variable
        object_id: Object individual ID or variable
        predicate_id: Relation predicate (e.g., "RO:0002333" for enabled_by)

    Returns:
        Barista API response

    Examples:
        # Connect molecular function to gene product (enabled_by)
        add_fact("gomodel:12345", "mf1", "gp1", "RO:0002333")

        # Connect molecular function to cellular component (occurs_in)
        add_fact("gomodel:12345", "mf1", "cc1", "BFO:0000066")

        # Connect molecular function to biological process (part_of)
        add_fact("gomodel:12345", "mf1", "bp1", "BFO:0000050")

        # Add causal relationship between activities
        add_fact("gomodel:12345", "mf1", "mf2", "RO:0002411")  # causally upstream of
        add_fact("gomodel:12345", "mf1", "mf2", "RO:0002629")  # directly positively regulates
        add_fact("gomodel:12345", "mf1", "mf2", "RO:0002630")  # directly negatively regulates
        add_fact("gomodel:12345", "mf1", "mf2", "RO:0002413")  # provides input for

        # Add regulates relationships
        add_fact("gomodel:12345", "mf1", "bp1", "RO:0002211")  # regulates
        add_fact("gomodel:12345", "mf1", "bp1", "RO:0002213")  # positively regulates
        add_fact("gomodel:12345", "mf1", "bp1", "RO:0002212")  # negatively regulates

        # Add indirect regulation relationships
        add_fact("gomodel:12345", "mf1", "mf2", "RO:0002407")  # indirectly positively regulates
        add_fact("gomodel:12345", "mf1", "mf2", "RO:0002409")  # indirectly negatively regulates

        # Add causal relationships with effects
        add_fact("gomodel:12345", "mf1", "mf2", "RO:0002304")  # causally upstream of, positive effect
        add_fact("gomodel:12345", "mf1", "mf2", "RO:0002305")  # causally upstream of, negative effect

        # Add small molecule regulation relationships
        add_fact("gomodel:12345", "sm1", "mf1", "RO:0012005")  # is small molecule activator of
        add_fact("gomodel:12345", "sm1", "mf1", "RO:0012006")  # is small molecule inhibitor of

        # Use with existing individual IDs from model
        add_fact("gomodel:12345", "gomodel:12345/abc123", "gomodel:12345/def456", "RO:0002333")
    """
    client = get_client()

    # Resolve any variables to actual IDs
    resolved_subject = client._resolve_identifier(model_id, subject_id)
    resolved_object = client._resolve_identifier(model_id, object_id)

    req = client.req_add_fact(model_id, resolved_subject, resolved_object, predicate_id)
    resp = client.m3_batch([req])

    if resp.validation_failed:
        return {
            "success": False,
            "error": "Validation failed",
            "reason": resp.validation_reason,
            "rolled_back": True,
            "fact": {
                "subject": subject_id,
                "predicate": predicate_id,
                "object": object_id
            }
        }

    if resp.error:
        return {
            "success": False,
            "error": resp.error,
            "model_id": model_id,
            "fact": {
                "subject": subject_id,
                "predicate": predicate_id,
                "object": object_id
            }
        }

    # Return minimal success response
    return {
        "success": True,
        "fact_added": True
    }


@mcp.tool()
async def add_evidence_to_fact(
    model_id: str,
    subject_id: str,
    object_id: str,
    predicate_id: str,
    eco_id: str,
    sources: List[str],
    with_from: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Add evidence to an existing fact in a GO-CAM model.

    Args:
        model_id: The GO-CAM model identifier
        subject_id: Subject of the fact
        object_id: Object of the fact
        predicate_id: Predicate of the fact
        eco_id: Evidence code (e.g., "ECO:0000353")
        sources: List of source references (e.g., ["PMID:12345"])
        with_from: Optional list of with/from references

    Returns:
        Barista API response

    Examples:
        # Add experimental evidence from a paper
        add_evidence_to_fact(
            "gomodel:12345", "mf1", "gp1", "RO:0002333",
            "ECO:0000353",  # physical interaction evidence
            ["PMID:12345678"]
        )

        # Add multiple sources
        add_evidence_to_fact(
            "gomodel:12345", "mf1", "gp1", "RO:0002333",
            "ECO:0000314",  # direct assay evidence
            ["PMID:12345678", "PMID:87654321", "doi:10.1234/example"]
        )

        # Add evidence with with/from (e.g., for IPI)
        add_evidence_to_fact(
            "gomodel:12345", "mf1", "gp1", "RO:0002333",
            "ECO:0000353",  # IPI
            ["PMID:12345678"],  
            ["UniProtKB:Q9Y6K9", "UniProtKB:P38398"]  # interacting partners
        )

        # Common evidence codes:
        # ECO:0000314 - direct assay evidence
        # ECO:0000353 - physical interaction evidence (IPI)
        # ECO:0000315 - mutant phenotype evidence (IMP)
        # ECO:0000316 - genetic interaction evidence (IGI)
        # ECO:0000318 - biological aspect of ancestor evidence (IBA)
        # ECO:0000269 - experimental evidence
    """
    client = get_client()
    reqs = client.req_add_evidence_to_fact(
        model_id, subject_id, object_id, predicate_id,
        eco_id, sources, with_from
    )
    resp = client.m3_batch(reqs)

    if resp.validation_failed:
        return {
            "success": False,
            "error": "Validation failed",
            "reason": resp.validation_reason,
            "rolled_back": True,
            "fact": {
                "subject": subject_id,
                "predicate": predicate_id,
                "object": object_id
            },
            "evidence": {
                "eco_id": eco_id,
                "sources": sources,
                "with_from": with_from
            }
        }

    if resp.error:
        return {
            "success": False,
            "error": resp.error,
            "model_id": model_id,
            "fact": {
                "subject": subject_id,
                "predicate": predicate_id,
                "object": object_id
            }
        }

    # Return minimal success response
    return {
        "success": True,
        "evidence_added": True,
        "eco_id": eco_id
    }


@mcp.tool()
async def remove_individual(
    model_id: str,
    individual_id: str
) -> Dict[str, Any]:
    """
    Remove an individual from a GO-CAM model.

    Note: This will also remove all facts (edges) connected to this individual.

    Args:
        model_id: The GO-CAM model identifier
        individual_id: The individual to remove

    Returns:
        Barista API response

    Examples:
        # Remove using a variable reference (within same batch)
        remove_individual("gomodel:12345", "mf1")

        # Remove using full individual ID
        remove_individual("gomodel:12345", "gomodel:12345/5fce9b7300001215")

        # Remove an evidence individual
        remove_individual("gomodel:12345", "gomodel:12345/evidence_123")

        # Clean up after testing
        for ind_id in ["test1", "test2", "test3"]:
            remove_individual("gomodel:12345", ind_id)
    """
    client = get_client()
    resp = client.remove_individual(model_id, individual_id)

    if resp.validation_failed:
        return {
            "success": False,
            "error": "Validation failed",
            "reason": resp.validation_reason,
            "rolled_back": True,
            "individual_id": individual_id,
            "model_id": model_id
        }

    if resp.error:
        return {
            "success": False,
            "error": resp.error,
            "individual_id": individual_id,
            "model_id": model_id
        }

    # Return minimal success response
    return {
        "success": True,
        "removed": True,
        "individual_id": individual_id
    }


@mcp.tool()
async def remove_fact(
    model_id: str,
    subject_id: str,
    object_id: str,
    predicate_id: str
) -> Dict[str, Any]:
    """
    Remove a fact from a GO-CAM model.

    You must specify the exact triple (subject, predicate, object) to remove.

    Args:
        model_id: The GO-CAM model identifier
        subject_id: Subject of the fact
        object_id: Object of the fact
        predicate_id: Predicate of the fact

    Returns:
        Barista API response

    Examples:
        # Remove an enabled_by relationship
        remove_fact(
            "gomodel:12345",
            "gomodel:12345/mf_123",
            "gomodel:12345/gp_456",
            "RO:0002333"
        )

        # Remove a causal relationship
        remove_fact(
            "gomodel:12345",
            "gomodel:12345/activity1",
            "gomodel:12345/activity2",
            "RO:0002413"  # provides input for
        )

        # Remove occurs_in relationship
        remove_fact(
            "gomodel:12345",
            "gomodel:12345/mf_123",
            "gomodel:12345/cc_789",
            "BFO:0000066"  # occurs_in
        )

        # Remove using variable references (within same batch)
        remove_fact("gomodel:12345", "mf1", "gp1", "RO:0002333")
    """
    client = get_client()
    resp = client.remove_fact(model_id, subject_id, object_id, predicate_id)

    if resp.validation_failed:
        return {
            "success": False,
            "error": "Validation failed",
            "reason": resp.validation_reason,
            "rolled_back": True,
            "fact": {
                "subject": subject_id,
                "predicate": predicate_id,
                "object": object_id
            },
            "model_id": model_id
        }

    if resp.error:
        return {
            "success": False,
            "error": resp.error,
            "fact": {
                "subject": subject_id,
                "predicate": predicate_id,
                "object": object_id
            },
            "model_id": model_id
        }

    # Return minimal success response
    return {
        "success": True,
        "removed": True
    }


@mcp.tool()
async def get_model(model_id: str) -> Dict[str, Any]:
    """
    Retrieve the full JSON representation of a GO-CAM model.

    Args:
        model_id: The GO-CAM model identifier

    Returns:
        Full model data including individuals and facts

    Examples:
        # Get a production model
        model = get_model("gomodel:5fce9b7300001215")
        # Returns complete model with:
        # - data.id: model ID
        # - data.individuals: list of all individuals
        # - data.facts: list of all relationships
        # - data.annotations: model-level annotations

        # Extract specific information
        model = get_model("gomodel:12345")
        individuals = model["data"]["individuals"]
        facts = model["data"]["facts"]

        # Find all molecular functions
        mfs = [i for i in individuals
               if any("GO:0003674" in str(e) for e in i.get("expressions", []))]

        # Find all enabled_by relationships
        enabled_by = [f for f in facts if f["property"] == "RO:0002333"]

        # Check model state
        annotations = model["data"].get("annotations", [])
        state = next((a["value"] for a in annotations if a["key"] == "state"), None)
    """
    client = get_client()
    resp = client.get_model(model_id)

    if resp.error:
        return {
            "success": False,
            "error": resp.error,
            "model_id": model_id
        }

    # Return structured response with model data
    return {
        "success": True,
        "model_id": model_id,
        "data": {
            "individuals": resp.individuals,
            "facts": resp.facts,
            "annotations": resp.annotations if hasattr(resp, 'annotations') else [],
            "state": resp.model_state if hasattr(resp, 'model_state') else None
        },
        "raw": resp.raw  # Include raw for backward compatibility
    }


# NOTE: The following function is intentionally commented out and preserved for future reference.
# BUG DESCRIPTION:
# The add_activity_unit tool is currently buggy: it can create duplicate activity units in the GO-CAM model
# due to incomplete rollback logic when an error occurs during multi-step model updates.
# Specifically, if any part of the pathway unit creation fails, partial changes may remain,
# resulting in duplicate molecular function (MF), gene product (GP), or cellular component (CC) individuals or facts.
# 
# FUTURE PLANS:
# - Refactor the function to ensure atomicity: either all steps succeed, or all changes are rolled back.
# - Add checks to prevent duplicate individuals and relationships.
# - Consider using transactions or temporary model states if supported by the Barista API.
# 
# Until these issues are resolved, this function should not be enabled.
#@mcp.tool()
async def add_activity_unit(
    model_id: str,
    pathway_curie: str,
    pathway_label: str,
    mf_curie: str,
    mf_label: str,
    gene_product_curie: str,
    gene_product_label: str,
    cc_curie: str,
    cc_label: str
) -> Dict[str, Any]:
    """
    Add a basic GO-CAM pathway unit: MF enabled_by GP, occurs_in CC, part_of BP.

    Creates a complete activity unit with all standard relationships, with
    label validation to prevent ID errors.

    Args:
        model_id: The GO-CAM model identifier
        pathway_curie: Biological process term ID
        pathway_label: Biological process term label
        mf_curie: Molecular function term ID
        mf_label: Molecular function term label
        gene_product_curie: Gene product/protein identifier
        gene_product_label: Gene product/protein name
        cc_curie: Cellular component term ID
        cc_label: Cellular component term label

    Returns:
        Barista API response. If validation fails, includes error details.

    Examples:
        # Add a kinase activity in Wnt signaling
        add_basic_pathway(
            "gomodel:12345",
            "GO:0016055", "Wnt signaling pathway",
            "GO:0004672", "protein kinase activity",
            "UniProtKB:P68400", "CSNK1A1",
            "GO:0005737", "cytoplasm"
        )

        # Add a transcription factor activity
        add_basic_pathway(
            "gomodel:12345",
            "GO:0006355", "regulation of transcription, DNA-templated",
            "GO:0003700", "DNA-binding transcription factor activity",
            "UniProtKB:Q01094", "E2F1",
            "GO:0005634", "nucleus"
        )

        # Add a receptor activity at membrane
        add_basic_pathway(
            "gomodel:12345",
            "GO:0007165", "signal transduction",
            "GO:0004888", "transmembrane signaling receptor activity",
            "UniProtKB:P04626", "ERBB2",
            "GO:0005886", "plasma membrane"
        )

    Notes:
        - All labels are required to prevent ID hallucination
        - Operations are executed with validation and automatic rollback
        - If any validation fails, all changes are rolled back
    """
    client = get_client()

    # Build the batch of requests for the pathway unit
    reqs: List[Dict[str, Any]] = []

    # Create MF individual
    reqs.append(client.req_add_individual(model_id, mf_curie, "mf1"))

    # Create GP individual
    reqs.append(client.req_add_individual(model_id, gene_product_curie, "gp1"))

    # Create BP individual
    reqs.append(client.req_add_individual(model_id, pathway_curie, "bp1"))

    # Create CC individual
    reqs.append(client.req_add_individual(model_id, cc_curie, "cc1"))

    # Add relationships
    reqs.append(client.req_add_fact(model_id, "mf1", "gp1", "RO:0002333"))  # enabled_by
    reqs.append(client.req_add_fact(model_id, "mf1", "cc1", "BFO:0000066"))  # occurs_in
    reqs.append(client.req_add_fact(model_id, "mf1", "bp1", "BFO:0000050"))  # part_of

    # Execute with validation
    expected_individuals = [
        {"id": mf_curie, "label": mf_label},
        {"id": gene_product_curie, "label": gene_product_label},
        {"id": pathway_curie, "label": pathway_label},
        {"id": cc_curie, "label": cc_label}
    ]

    resp = client.execute_with_validation(reqs, expected_individuals=expected_individuals)

    if resp.validation_failed:
        return {
            "success": False,
            "error": "Validation failed",
            "reason": resp.validation_reason,
            "rolled_back": True,
            "model_id": model_id,
            "entities": {
                "pathway": {"curie": pathway_curie, "label": pathway_label},
                "molecular_function": {"curie": mf_curie, "label": mf_label},
                "gene_product": {"curie": gene_product_curie, "label": gene_product_label},
                "cellular_component": {"curie": cc_curie, "label": cc_label}
            }
        }

    if resp.error:
        return {
            "success": False,
            "error": resp.error,
            "model_id": model_id
        }

    # Return minimal success response
    return {
        "success": True,
        "pathway_created": True,
        "individuals_added": 4,
        "facts_added": 3
    }


# NOTE: This function is currently commented out and not registered as an MCP tool due to a known bug.
# BUG DESCRIPTION:
#   - The function can create duplicate molecular function and gene product individuals in the GO-CAM model.
#   - This occurs when a partial rollback happens after a validation failure or error during the multi-step creation process.
#   - Not all changes are reliably reverted, so some individuals or facts may remain, leading to duplicate entries if the function is retried.
#   - The bug is most likely to occur when the model is in a partially valid state or when network/database errors interrupt the process.
#   - This function is retained in the codebase for future debugging and as a reference for the intended causal chain creation logic.
#   - Do NOT uncomment or register this function as a tool until the rollback logic is fixed and thoroughly tested.
#   - See issue tracker #<insert-issue-number-if-applicable> for more details and progress on resolving this bug.
#@mcp.tool()
async def add_causal_chain(
    model_id: str,
    mf1_curie: str,
    mf1_label: str,
    mf2_curie: str,
    mf2_label: str,
    gp1_curie: str,
    gp1_label: str,
    gp2_curie: str,
    gp2_label: str,
    causal_relation: str = "RO:0002411"
) -> Dict[str, Any]:
    """
    Add two molecular functions connected by a causal relationship.

    Creates two complete activities and links them causally, with label
    validation to prevent ID errors.

    Args:
        model_id: The GO-CAM model identifier
        mf1_curie: First molecular function ID
        mf1_label: First molecular function label
        mf2_curie: Second molecular function ID
        mf2_label: Second molecular function label
        gp1_curie: Gene product for first MF
        gp1_label: Gene product name for first MF
        gp2_curie: Gene product for second MF
        gp2_label: Gene product name for second MF
        causal_relation: Causal relation (default: RO:0002411 - causally upstream of)

    Returns:
        Barista API response. If validation fails, includes error details.

    Examples:
        # Kinase activating another kinase
        add_causal_chain(
            "gomodel:12345",
            "GO:0004674", "protein serine/threonine kinase activity",
            "GO:0004674", "protein serine/threonine kinase activity",
            "UniProtKB:P31749", "AKT1",
            "UniProtKB:P31751", "AKT2",
            "RO:0002629"  # directly positively regulates
        )

        # Receptor activating kinase cascade
        add_causal_chain(
            "gomodel:12345",
            "GO:0004888", "transmembrane signaling receptor activity",
            "GO:0004674", "protein serine/threonine kinase activity",
            "UniProtKB:P04626", "ERBB2",
            "UniProtKB:P31749", "AKT1",
            "RO:0002411"  # causally upstream of
        )

        # Transcription factor inhibiting another
        add_causal_chain(
            "gomodel:12345",
            "GO:0003700", "DNA-binding transcription factor activity",
            "GO:0003700", "DNA-binding transcription factor activity",
            "UniProtKB:P01106", "MYC",
            "UniProtKB:Q01094", "E2F1",
            "RO:0002630"  # directly negatively regulates
        )

        # Common causal relations:
        # RO:0002411 - causally upstream of (general)
        # RO:0002629 - directly positively regulates
        # RO:0002630 - directly negatively regulates
        # RO:0002413 - provides input for
        # RO:0002407 - indirectly positively regulates
        # RO:0002409 - indirectly negatively regulates
        # RO:0002304 - causally upstream of, positive effect
        # RO:0002305 - causally upstream of, negative effect

    Notes:
        - All labels are required to prevent ID hallucination
        - Operations are executed with validation and automatic rollback
        - If any validation fails, all changes are rolled back
    """
    client = get_client()

    reqs: List[Dict[str, Any]] = []

    # First activity
    reqs.append(client.req_add_individual(model_id, mf1_curie, "mf1"))
    reqs.append(client.req_add_individual(model_id, gp1_curie, "gp1"))
    reqs.append(client.req_add_fact(model_id, "mf1", "gp1", "RO:0002333"))

    # Second activity
    reqs.append(client.req_add_individual(model_id, mf2_curie, "mf2"))
    reqs.append(client.req_add_individual(model_id, gp2_curie, "gp2"))
    reqs.append(client.req_add_fact(model_id, "mf2", "gp2", "RO:0002333"))

    # Causal connection
    reqs.append(client.req_add_fact(model_id, "mf1", "mf2", causal_relation))

    # Execute with validation
    expected_individuals = [
        {"id": mf1_curie, "label": mf1_label},
        {"id": gp1_curie, "label": gp1_label},
        {"id": mf2_curie, "label": mf2_label},
        {"id": gp2_curie, "label": gp2_label}
    ]

    resp = client.execute_with_validation(reqs, expected_individuals=expected_individuals)

    if resp.validation_failed:
        return {
            "success": False,
            "error": "Validation failed",
            "reason": resp.validation_reason,
            "rolled_back": True,
            "model_id": model_id,
            "entities": {
                "activity1": {
                    "molecular_function": {"curie": mf1_curie, "label": mf1_label},
                    "gene_product": {"curie": gp1_curie, "label": gp1_label}
                },
                "activity2": {
                    "molecular_function": {"curie": mf2_curie, "label": mf2_label},
                    "gene_product": {"curie": gp2_curie, "label": gp2_label}
                }
            }
        }

    if resp.error:
        return {
            "success": False,
            "error": resp.error,
            "model_id": model_id
        }

    # Return minimal success response
    return {
        "success": True,
        "causal_chain_created": True,
        "activities_added": 2,
        "causal_relationship": causal_relation
    }


@mcp.tool()
async def model_summary(model_id: str) -> Dict[str, Any]:
    """
    Get a summary of a GO-CAM model including counts and key information.

    Args:
        model_id: The GO-CAM model identifier

    Returns:
        Summary with individual count, fact count, and predicate distribution

    Examples:
        # Get summary of a model
        result = model_summary("gomodel:5fce9b7300001215")
        # Returns:
        # {
        #   "model_id": "gomodel:5fce9b7300001215",
        #   "state": "production",
        #   "individual_count": 42,
        #   "fact_count": 67,
        #   "predicate_distribution": {
        #     "RO:0002333": 15,  # enabled_by (note: not in vetted list)
        #     "RO:0002411": 8,   # causally upstream of
        #     "BFO:0000066": 12,  # occurs_in
        #     "BFO:0000050": 5    # part_of
        #   }
        # }

        # Check if a model is empty
        result = model_summary("gomodel:new_empty_model")
        if result["individual_count"] == 0:
            print("Model is empty")

        # Analyze model complexity
        result = model_summary("gomodel:12345")
        causal_edges = result["predicate_distribution"].get("RO:0002411", 0)
        causal_edges += result["predicate_distribution"].get("RO:0002413", 0)  # provides input for
        causal_edges += result["predicate_distribution"].get("RO:0002629", 0)  # directly positively regulates
        causal_edges += result["predicate_distribution"].get("RO:0002630", 0)  # directly negatively regulates
        print(f"Model has {causal_edges} causal relationships")
    """
    client = get_client()
    resp = client.get_model(model_id)

    if resp.validation_failed:
        return {
            "success": False,
            "error": "Validation failed",
            "reason": resp.validation_reason,
            "model_id": model_id
        }

    if resp.error:
        return {
            "success": False,
            "error": "Failed to retrieve model",
            "reason": resp.error,
            "model_id": model_id
        }

    # Extract summary information
    individuals = resp.individuals
    facts = resp.facts

    # Count predicates
    predicate_counts: Dict[str, int] = {}
    for fact in facts:
        pred = fact.get("property", "unknown")
        predicate_counts[pred] = predicate_counts.get(pred, 0) + 1

    # Get model state if available
    model_state = resp.model_state

    return {
        "success": True,
        "model_id": model_id,
        "state": model_state,
        "individual_count": len(individuals),
        "fact_count": len(facts),
        "predicate_distribution": predicate_counts,
    }


@mcp.tool()
async def get_model_variables(model_id: str) -> Dict[str, Any]:
    """
    Get the currently bound variables for a GO-CAM model.

    Returns a mapping of variable names to their actual individual IDs.
    This is useful for understanding what variables are available in the
    current model context, especially after batch operations.

    Args:
        model_id: The GO-CAM model identifier

    Returns:
        Dictionary with variable mappings and model information

    Examples:
        # Get variables after creating individuals
        vars = get_model_variables("gomodel:12345")
        # Returns:
        # {
        #   "model_id": "gomodel:12345",
        #   "variables": {
        #     "mf1": "gomodel:12345/68dee4d300000481",
        #     "gp1": "gomodel:12345/68dee4d300000482",
        #     "cc1": "gomodel:12345/68dee4d300000483"
        #   },
        #   "individual_count": 3
        # }

        # Use the variables in subsequent operations
        vars = get_model_variables("gomodel:12345")
        mf_id = vars["variables"]["mf1"]
        add_fact("gomodel:12345", mf_id, vars["variables"]["gp1"], "RO:0002333")

    Notes:
        - Variables are only valid within the same batch operation
        - This tool helps identify actual IDs for cross-batch operations
        - If the model has no tracked variables, returns empty dict
    """
    client = get_client()

    # Check if the client has variable tracking enabled
    if not hasattr(client, 'track_variables') or not client.track_variables:
        client.track_variables = True

    # Get the model to see current state
    resp = client.get_model(model_id)

    if resp.error:
        return {
            "success": False,
            "error": resp.error,
            "model_id": model_id
        }

    # Get variables from the client's registry
    variables = {}
    if hasattr(client, '_variable_registry') and client._variable_registry:
        # The registry is keyed by (model_id, variable_name) -> actual_id
        # We need to extract variables for this specific model
        variables = client.get_variables(model_id)

    # Also check if the last response has model_vars
    if hasattr(resp, 'model_vars') and resp.model_vars:
        variables.update(resp.model_vars)

    # Count individuals
    individual_count = len(resp.individuals) if resp.individuals else 0

    return {
        "success": True,
        "model_id": model_id,
        "variables": variables,
        "individual_count": individual_count,
    }


@mcp.tool()
async def search_models(
    title: Optional[str] = None,
    state: Optional[str] = None,
    contributor: Optional[str] = None,
    group: Optional[str] = None,
    pmid: Optional[str] = None,
    gene_product: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Search for GO-CAM models based on various criteria.

    Allows searching models by title, state, contributor, group, publication, or gene product.
    Returns a list of matching models with their metadata.

    Args:
        title: Search for models containing this text in their title
        state: Filter by model state (production, development, internal_test)
        contributor: Filter by contributor ORCID (e.g., 'https://orcid.org/0000-0002-6601-2165')
        group: Filter by group/provider (e.g., 'http://www.wormbase.org')
        pmid: Filter by PubMed ID (e.g., 'PMID:12345678')
        gene_product: Filter by gene product (e.g., 'UniProtKB:Q9BRQ8', 'MGI:MGI:97490')
        limit: Maximum number of results to return (default: 50)
        offset: Offset for pagination (default: 0)

    Returns:
        Dictionary containing search results with model metadata

    Examples:
        # Search for all production models
        results = search_models(state="production")

        # Find models containing "Wnt signaling" in title
        results = search_models(title="Wnt signaling")

        # Find models for a specific gene product
        results = search_models(gene_product="UniProtKB:P38398")

        # Find models from a specific paper
        results = search_models(pmid="PMID:30194302")

        # Find models by a specific contributor
        results = search_models(
            contributor="https://orcid.org/0000-0002-6601-2165"
        )

        # Combine filters
        results = search_models(
            state="production",
            title="kinase",
            limit=10
        )

        # Pagination example
        page1 = search_models(limit=50, offset=0)
        page2 = search_models(limit=50, offset=50)

        # Find models from specific research group
        results = search_models(group="http://www.wormbase.org")

        # Search for development models with specific gene
        results = search_models(
            state="development",
            gene_product="MGI:MGI:97490"
        )

    Notes:
        - Results include model ID, title, state, contributors, and dates
        - Use pagination (offset/limit) for large result sets
        - Filters can be combined for more specific searches
        - Gene products can be from various databases (UniProt, MGI, RGD, etc.)
    """
    client = get_client()

    try:
        results = client.list_models(
            title=title,
            state=state,
            contributor=contributor,
            group=group,
            pmid=pmid,
            gp=gene_product,
            limit=limit,
            offset=offset
        )
        return results
    except Exception as e:
        return {
            "error": "Failed to search models",
            "message": str(e)
        }


@mcp.tool()
async def search_bioentities(
    text: Optional[str] = None,
    taxon: Optional[str] = None,
    bioentity_type: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = 10,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Search for bioentities (genes/proteins) using Gene Ontology data.

    Searches across gene and protein names/labels with optional taxonomic filtering.
    Provides access to comprehensive bioentity information from GOlr.

    Args:
        text: Text search across names and labels (e.g., "insulin", "kinase")
        taxon: Organism filter - accepts NCBI Taxon ID with or without prefix
               (e.g., "9606", "NCBITaxon:9606" for human)
        bioentity_type: Type filter (e.g., "protein", "gene")
        source: Source database filter (e.g., "UniProtKB", "MGI", "RGD")
        limit: Maximum number of results to return (default: 10)
        offset: Starting offset for pagination (default: 0)

    Returns:
        Dictionary containing search results with bioentity information

    Examples:
        # Search for human insulin proteins
        results = search_bioentities(
            text="insulin",
            taxon="9606",
            bioentity_type="protein"
        )

        # Find mouse kinases from MGI
        results = search_bioentities(
            text="kinase",
            taxon="NCBITaxon:10090",
            source="MGI",
            limit=20
        )

        # Search for any human genes/proteins
        results = search_bioentities(
            taxon="9606",
            limit=50
        )

        # Find specific protein types
        results = search_bioentities(
            text="receptor",
            bioentity_type="protein",
            limit=25
        )

        # Search across all organisms
        results = search_bioentities(text="p53")

        # Pagination example
        page1 = search_bioentities(text="kinase", limit=10, offset=0)
        page2 = search_bioentities(text="kinase", limit=10, offset=10)

        # Common organisms:
        # Human: "9606" or "NCBITaxon:9606"
        # Mouse: "10090" or "NCBITaxon:10090"
        # Rat: "10116" or "NCBITaxon:10116"
        # Fly: "7227" or "NCBITaxon:7227"
        # Worm: "6239" or "NCBITaxon:6239"
        # Yeast: "559292" or "NCBITaxon:559292"

    Notes:
        - Results include ID, name, type, organism, and source information
        - Text search covers both short names/symbols and full descriptions
        - Taxon IDs automatically handle NCBITaxon: prefix normalization
        - Use pagination for large result sets
        - Sources include UniProtKB, MGI, RGD, ZFIN, SGD, and others
    """

    # Normalize taxon ID - add NCBITaxon prefix if just a number
    if taxon and not taxon.startswith("NCBITaxon:"):
        if taxon.isdigit():
            taxon = f"NCBITaxon:{taxon}"

    try:
        with AmigoClient() as client:
            results = client.search_bioentities(
                text=text,
                taxon=taxon,
                bioentity_type=bioentity_type,
                source=source,
                limit=limit,
                offset=offset
            )

            return {
                "results": [
                    {
                        "id": result.id,
                        "label": result.label,
                        "name": result.name,
                        "type": result.type,
                        "taxon": result.taxon,
                        "taxon_label": result.taxon_label,
                        "source": result.source
                    }
                    for result in results
                ],
                "count": len(results),
                "limit": limit,
                "offset": offset
            }

    except Exception as e:
        return {
            "error": "Failed to search bioentities",
            "message": str(e)
        }


@mcp.tool()
async def search_annotations(
    bioentity: Optional[str] = None,
    go_term: Optional[str] = None,
    evidence_types: Optional[str] = None,
    taxon: Optional[str] = None,
    aspect: Optional[str] = None,
    assigned_by: Optional[str] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Search for GO annotations (evidence) with filtering.

    Args:
        bioentity: Specific bioentity ID to filter by (e.g., "UniProtKB:P12345")
        go_term: Specific GO term ID to filter by (e.g., "GO:0008150")
        evidence_types: Comma-separated evidence codes (e.g., "IDA,IPI,IMP")
        taxon: Organism filter - accepts numeric (9606) or full ID (NCBITaxon:9606)
        aspect: GO aspect filter - "C" (cellular component), "F" (molecular function), or "P" (biological process)
        assigned_by: Annotation source filter (e.g., "GOC", "UniProtKB", "MGI")
        limit: Maximum number of results (default: 10, max: 1000)

    Returns:
        Dictionary containing:
        - annotations: List of annotation results with evidence details
        - total: Number of results returned

    Examples:
        # Find all evidence for a specific protein
        search_annotations(bioentity="UniProtKB:P53762")

        # Find proteins with experimental evidence for a GO term
        search_annotations(go_term="GO:0005634", evidence_types="IDA,IPI")

        # Find human proteins in nucleus with experimental evidence
        search_annotations(
            go_term="GO:0005634",
            taxon="9606",
            evidence_types="IDA,IPI,IMP",
            aspect="C"
        )

        # Find all UniProt annotations for apoptosis
        search_annotations(
            go_term="GO:0006915",
            assigned_by="UniProtKB"
        )
    """
    # Normalize taxon ID
    if taxon and not taxon.startswith("NCBITaxon:"):
        if taxon.isdigit():
            taxon = f"NCBITaxon:{taxon}"

    # Parse evidence types
    evidence_list = None
    if evidence_types:
        evidence_list = [e.strip() for e in evidence_types.split(",")]

    # Limit bounds
    limit = min(max(1, limit), 1000)

    try:
        with AmigoClient() as client:
            results = client.search_annotations(
                bioentity=bioentity,
                go_term=go_term,
                evidence_types=evidence_list,
                taxon=taxon,
                aspect=aspect,
                assigned_by=assigned_by,
                limit=limit
            )

            return {
                "annotations": [
                    {
                        "bioentity": r.bioentity,
                        "bioentity_label": r.bioentity_label,
                        "bioentity_name": r.bioentity_name,
                        "go_term": r.annotation_class,
                        "go_term_label": r.annotation_class_label,
                        "aspect": r.aspect,
                        "evidence_type": r.evidence_type,
                        "evidence": r.evidence,
                        "evidence_label": r.evidence_label,
                        "reference": r.reference,
                        "assigned_by": r.assigned_by,
                        "date": r.date,
                        "taxon": r.taxon,
                        "taxon_label": r.taxon_label,
                        "qualifier": r.qualifier,
                        "annotation_extension": r.annotation_extension
                    }
                    for r in results
                ],
                "total": len(results)
            }

    except Exception as e:
        return {
            "error": "Failed to search annotations",
            "message": str(e)
        }


@mcp.tool()
async def get_annotations_for_bioentity(
    bioentity_id: str,
    go_terms: Optional[str] = None,
    evidence_types: Optional[str] = None,
    aspect: Optional[str] = None,
    limit: int = 100
) -> Dict[str, Any]:
    """
    Get all GO annotations (evidence) for a specific bioentity.

    Args:
        bioentity_id: The bioentity ID (e.g., "UniProtKB:P12345")
        go_terms: Comma-separated GO terms to filter (includes child terms)
        evidence_types: Comma-separated evidence codes to filter (e.g., "IDA,IPI")
        aspect: GO aspect filter - "C", "F", or "P"
        limit: Maximum number of results (default: 100)

    Returns:
        Dictionary containing:
        - bioentity_id: The queried bioentity
        - annotations: List of annotation results
        - summary: Count by aspect and evidence type

    Examples:
        # Get all annotations for a protein
        get_annotations_for_bioentity("UniProtKB:P53762")

        # Get only experimental evidence
        get_annotations_for_bioentity(
            "UniProtKB:P53762",
            evidence_types="IDA,IPI,IMP"
        )

        # Get annotations for specific GO terms
        get_annotations_for_bioentity(
            "UniProtKB:P53762",
            go_terms="GO:0005634,GO:0005737"
        )

        # Get only molecular function annotations
        get_annotations_for_bioentity(
            "UniProtKB:P53762",
            aspect="F"
        )
    """
    # Parse comma-separated lists
    go_terms_list = None
    if go_terms:
        go_terms_list = [t.strip() for t in go_terms.split(",")]

    evidence_list = None
    if evidence_types:
        evidence_list = [e.strip() for e in evidence_types.split(",")]

    try:
        with AmigoClient() as client:
            results = client.get_annotations_for_bioentity(
                bioentity_id=bioentity_id,
                go_terms_closure=go_terms_list,
                evidence_types=evidence_list,
                aspect=aspect,
                limit=limit
            )

            # Calculate summary statistics
            aspect_counts: Dict[str, int] = {}
            evidence_counts: Dict[str, int] = {}
            for r in results:
                aspect_counts[r.aspect] = aspect_counts.get(r.aspect, 0) + 1
                evidence_counts[r.evidence_type] = evidence_counts.get(r.evidence_type, 0) + 1

            return {
                "bioentity_id": bioentity_id,
                "annotations": [
                    {
                        "go_term": r.annotation_class,
                        "go_term_label": r.annotation_class_label,
                        "aspect": r.aspect,
                        "evidence_type": r.evidence_type,
                        "evidence": r.evidence,
                        "evidence_label": r.evidence_label,
                        "reference": r.reference,
                        "assigned_by": r.assigned_by,
                        "date": r.date,
                        "qualifier": r.qualifier,
                        "annotation_extension": r.annotation_extension
                    }
                    for r in results
                ],
                "summary": {
                    "total": len(results),
                    "by_aspect": aspect_counts,
                    "by_evidence_type": evidence_counts
                }
            }

    except Exception as e:
        return {
            "error": "Failed to get annotations",
            "message": str(e)
        }


# Prompts to help users construct common patterns
@mcp.prompt()
def create_basic_activity() -> str:
    """Generate a prompt for creating a basic GO-CAM activity."""
    return """To create a basic GO-CAM activity, use:
1. add_individual to create a molecular function instance
2. add_individual to create a gene product instance
3. add_fact with RO:0002333 (enabled_by) to connect them
"""


@mcp.prompt()
def add_evidence_prompt() -> str:
    """Generate a prompt for adding evidence to facts."""
    return """To add evidence to a fact:
1. Use add_evidence_to_fact with the fact coordinates
2. Provide an ECO code (e.g., ECO:0000353 for IPI)
3. Include source references (e.g., PMID:12345)
"""


# Resources for GO-CAM guidelines
def _get_available_guidelines() -> List[str]:
    """Get list of available guideline files."""
    if not GUIDELINES_DIR.exists():
        return []
    return sorted([f.stem for f in GUIDELINES_DIR.glob("*.md")])


def _inject_guideline_list(content: str, title: str) -> str:
    """Inject list of available guidelines at the end of content."""
    guidelines = _get_available_guidelines()
    if not guidelines:
        return content

    # Create formatted list
    guideline_section = "\n\n## Available GO-CAM Guidelines\n\n"
    guideline_section += f"This is the '{title}' guideline. Other available guidelines include:\n\n"

    for guide in guidelines:
        # Skip the current one
        if guide == title:
            continue
        # Make the filename more readable
        readable_name = guide.replace("_", " ").replace("-", " ")
        guideline_section += f"- {readable_name}\n"

    guideline_section += "\nUse the `get_guideline_content` tool to access any specific guideline."

    return content + guideline_section


@mcp.resource("guidelines://modeling-best-practices")
async def get_modeling_guidelines() -> str:
    """GO-CAM modeling best practices and general guidelines."""
    # Try multiple possible filenames
    possible_files = [
        "GO-CAM_annotation_guidelines_README.md",
        "GO-CAM_modelling_guidelines_TO_DO.md",
        "WIP_-_Regulation_and_Regulatory_Processes_in_GO-CAM.md"
    ]

    for filename in possible_files:
        file_path = GUIDELINES_DIR / filename
        if file_path.exists():
            with open(file_path) as f:
                content = f.read()
            return _inject_guideline_list(content, file_path.stem)

    # If none found, return a generic message with list
    return _inject_guideline_list(
        "# GO-CAM Modeling Guidelines\n\nNo main guideline file found.",
        "modeling-best-practices"
    )


@mcp.resource("guidelines://evidence-requirements")
async def get_evidence_guidelines() -> str:
    """Evidence code usage and requirements for GO-CAM."""
    # Look for E3 ubiquitin ligases as it contains evidence info
    file_path = GUIDELINES_DIR / "E3_ubiquitin_ligases.md"
    if file_path.exists():
        with open(file_path) as f:
            content = f.read()
        return _inject_guideline_list(content, file_path.stem)

    # Fallback with list
    return _inject_guideline_list(
        "# Evidence Requirements\n\nNo evidence guideline file found.",
        "evidence-requirements"
    )


@mcp.resource("guidelines://complex-annotations")
async def get_complex_guidelines() -> str:
    """Guidelines for annotating protein complexes in GO-CAM."""
    file_path = GUIDELINES_DIR / "How_to_annotate_complexes_in_GO-CAM.md"
    if file_path.exists():
        with open(file_path) as f:
            content = f.read()
        return _inject_guideline_list(content, file_path.stem)

    return _inject_guideline_list(
        "# Complex Annotation Guidelines\n\nNo complex guideline file found.",
        "complex-annotations"
    )


@mcp.tool()
async def list_guidelines() -> Dict[str, Any]:
    """List all available GO-CAM guideline documents.

    Returns a list of available guideline names that can be accessed
    using the get_guideline_content tool.

    Returns:
        Dictionary with 'guidelines' key containing list of available guidelines

    Examples:
        # List all available guidelines
        result = list_guidelines()
        for guide in result['guidelines']:
            print(guide)
    """
    guidelines = _get_available_guidelines()

    return {
        "guidelines": guidelines,
        "count": len(guidelines),
        "note": "Use get_guideline_content(guideline_name) to fetch any guideline"
    }


@mcp.tool()
async def get_guideline_content(guideline_name: str) -> Dict[str, Any]:
    """Fetch specific GO-CAM guideline content.

    Args:
        guideline_name: Name of guideline file (without .md extension).
                       Use list_guidelines() to see available options.

    Returns:
        Dictionary with guideline content or error message

    Examples:
        # Get a specific guideline
        content = get_guideline_content("E3_ubiquitin_ligases")

        # Get transcription factor guidelines
        content = get_guideline_content("DNA-binding_transcription_factor_activity_annotation_guidelines")
    """
    file_path = GUIDELINES_DIR / f"{guideline_name}.md"

    if not file_path.exists():
        available = _get_available_guidelines()
        return {
            "success": False,
            "error": f"Guideline '{guideline_name}' not found",
            "available_guidelines": available,
            "hint": "Use one of the available guideline names listed above"
        }

    try:
        with open(file_path) as f:
            content = f.read()

        # Extract first heading as description
        lines = content.split('\n')
        description = ""
        for line in lines:
            if line.strip():
                description = line.strip('#').strip()
                break

        return {
            "success": True,
            "guideline_name": guideline_name,
            "description": description,
            "content": content,
            "length": len(content)
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to read guideline: {str(e)}",
            "guideline_name": guideline_name
        }


if __name__ == "__main__":
    mcp.run()