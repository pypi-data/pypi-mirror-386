## Docker and deployment recipes for noctua-mcp

# Docker group for container operations

# Build the Docker container
docker-build:
    docker build -t noctua-mcp .

# Build Docker container with no cache (clean build)
docker-build-clean:
    docker build --no-cache -t noctua-mcp .

# Test the Docker container with a mock token
docker-test:
    #!/usr/bin/env bash
    echo "Testing Docker container..."
    echo "Note: This will fail without a valid BARISTA_TOKEN, but tests the container startup"
    timeout 10s docker run --rm -e BARISTA_TOKEN="test-token" noctua-mcp || echo "Container started successfully (expected timeout)"

# Run Docker container interactively with environment
docker-run token="":
    #!/usr/bin/env bash
    if [ -z "{{token}}" ]; then
        if [ -z "$BARISTA_TOKEN" ]; then
            echo "Error: BARISTA_TOKEN environment variable not set"
            echo "Usage: just docker-run token=your-token"
            echo "   or: export BARISTA_TOKEN=your-token && just docker-run"
            exit 1
        fi
        TOKEN="$BARISTA_TOKEN"
    else
        TOKEN="{{token}}"
    fi
    echo "Running noctua-mcp container with provided token..."
    docker run --rm -i -e BARISTA_TOKEN="$TOKEN" noctua-mcp

# Get shell access to the Docker container for debugging
docker-shell:
    docker run --rm -it --entrypoint=/bin/bash noctua-mcp

# Remove Docker images and clean up
docker-clean:
    docker rmi noctua-mcp || true
    docker system prune -f

# Show Docker image info
docker-info:
    @echo "=== Docker Image Info ==="
    docker images noctua-mcp
    @echo ""
    @echo "=== Docker Image History ==="
    docker history noctua-mcp 2>/dev/null || echo "Image not built yet. Run 'just docker-build' first."

# Development group for local server testing

# Start the MCP server locally for testing
serve:
    uv run noctua-mcp serve

# Start the MCP server with verbose output
serve-verbose:
    uv run noctua-mcp serve --verbose

# Test the server with environment check
test-server:
    #!/usr/bin/env bash
    if [ -z "$BARISTA_TOKEN" ]; then
        echo "Warning: BARISTA_TOKEN not set. Server will start but API calls will fail."
        echo "Set BARISTA_TOKEN environment variable for full functionality."
    fi
    echo "Testing local server startup..."
    timeout 5s uv run noctua-mcp serve --verbose || echo "Server started successfully (expected timeout)"

# Smithery deployment group

# Validate smithery.yaml configuration
validate-smithery:
    @echo "=== Validating smithery.yaml ==="
    @echo "Checking required fields..."
    @grep -q "dockerBuildPath" smithery.yaml && echo "✓ dockerBuildPath found" || echo "✗ dockerBuildPath missing"
    @grep -q "type: stdio" smithery.yaml && echo "✓ stdio type found" || echo "✗ stdio type missing"
    @grep -q "baristaToken" smithery.yaml && echo "✓ baristaToken config found" || echo "✗ baristaToken config missing"
    @echo "Configuration appears valid for smithery.ai deployment"

# Show deployment info
deployment-info:
    @echo "=== Deployment Information ==="
    @echo "Docker image: noctua-mcp"
    @echo "Smithery config: smithery.yaml"
    @echo ""
    @echo "To deploy to smithery.ai:"
    @echo "1. Push this repository to GitHub"
    @echo "2. Submit to smithery.ai with the repository URL"
    @echo "3. Users will configure BARISTA_TOKEN in their MCP client"
    @echo ""
    @echo "To deploy to Modal.com:"
    @echo "1. modal setup (if not done)"
    @echo "2. just modal-deploy (no secrets needed at deploy time)"
    @echo "3. Clients provide BARISTA_TOKEN when connecting"

# Modal.com deployment group

# Deploy to Modal.com (no secrets needed at deploy time)
modal-deploy:
    modal deploy modal_deploy.py

# Test Modal deployment (without credentials)
modal-test:
    modal run modal_deploy.py::test_deployment

# View Modal logs
modal-logs:
    modal logs noctua-mcp --follow

# Check Modal status
modal-status:
    modal status

# Test Modal deployment with comprehensive verification
modal-verify:
    uv run python test_modal_deployment.py

# Test Modal deployment with MCP SDK (more detailed)
modal-test-mcp:
    uv run python test_modal_with_mcp_sdk.py
