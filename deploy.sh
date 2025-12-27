#!/bin/bash
#
# deploy.sh - Deploy Aruba NOC MCP Server to Docker
#
# Usage: ./deploy.sh
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}       Aruba NOC MCP Server - Docker Deployment${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Step 1: Check prerequisites
echo -e "${YELLOW}[1/5]${NC} Checking prerequisites..."
if ! command -v docker &> /dev/null; then
    echo -e "${RED}ERROR: Docker is not installed${NC}"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo -e "${RED}ERROR: Docker daemon is not running${NC}"
    exit 1
fi
echo "  ✓ Docker is available"

# Step 2: Check for .env file
echo -e "${YELLOW}[2/5]${NC} Checking environment configuration..."
if [ ! -f .env ]; then
    echo -e "${YELLOW}  WARNING: .env file not found${NC}"
    echo "  Creating .env from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${YELLOW}  Please edit .env with your Aruba Central credentials${NC}"
    else
        cat > .env << 'EOF'
# Aruba Central API Configuration
ARUBA_BASE_URL=https://us1.api.central.arubanetworks.com
ARUBA_CLIENT_ID=your_client_id_here
ARUBA_CLIENT_SECRET=your_client_secret_here
ARUBA_ACCESS_TOKEN=your_access_token_here
EOF
        echo -e "${YELLOW}  Created .env template - please configure before use${NC}"
    fi
else
    echo "  ✓ .env file exists"
fi

# Step 3: Stop existing container if running
echo -e "${YELLOW}[3/5]${NC} Stopping existing container..."
if docker ps -q --filter "name=aruba-noc-mcp-server" | grep -q .; then
    docker compose down
    echo "  ✓ Stopped existing container"
else
    echo "  ✓ No existing container running"
fi

# Step 4: Build and start container
echo -e "${YELLOW}[4/5]${NC} Building and starting container..."
docker compose build --no-cache
docker compose up -d

# Step 5: Verify deployment
echo -e "${YELLOW}[5/5]${NC} Verifying deployment..."
sleep 3  # Wait for container to start

# Check container health
CONTAINER_STATUS=$(docker ps --filter "name=aruba-noc-mcp-server" --format "{{.Status}}")
if echo "$CONTAINER_STATUS" | grep -q "healthy\|Up"; then
    echo -e "  ✓ Container is ${GREEN}healthy${NC}"
else
    echo -e "  ${RED}Container status: $CONTAINER_STATUS${NC}"
    echo "  Checking logs..."
    docker logs aruba-noc-mcp-server --tail 20
    exit 1
fi

# Run a quick test to verify the server responds
echo "  Testing MCP server..."
TEST_OUTPUT=$(docker exec aruba-noc-mcp-server python -c "from src.server import main; print('OK')" 2>&1)
if echo "$TEST_OUTPUT" | grep -q "OK"; then
    echo -e "  ✓ MCP server module loads correctly"
else
    echo -e "  ${YELLOW}Warning: Could not verify server module${NC}"
fi

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ Deployment Complete!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Container: aruba-noc-mcp-server"
echo "Status: $(docker ps --filter 'name=aruba-noc-mcp-server' --format '{{.Status}}')"
echo ""
echo "To use with MCP client, add to mcp_config.json:"
echo '  "aruba-noc": {'
echo '    "command": "docker",'
echo '    "args": ["exec", "-i", "aruba-noc-mcp-server", "python", "-m", "src.server"]'
echo '  }'
echo ""
echo "Useful commands:"
echo "  - View logs:    docker logs aruba-noc-mcp-server -f"
echo "  - Stop:         docker compose down"
echo "  - Restart:      docker compose restart"
