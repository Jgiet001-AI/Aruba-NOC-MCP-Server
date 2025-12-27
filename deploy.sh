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
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}       Aruba NOC MCP Server - Docker Deployment${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Step 1: Check prerequisites
echo -e "${YELLOW}[1/6]${NC} Checking prerequisites..."
if ! command -v docker &> /dev/null; then
    echo -e "${RED}ERROR: Docker is not installed${NC}"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo -e "${RED}ERROR: Docker daemon is not running${NC}"
    exit 1
fi
echo "  ✓ Docker is available"

# Step 2: Check/Configure credentials
echo -e "${YELLOW}[2/6]${NC} Checking credentials configuration..."

configure_credentials() {
    echo ""
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║           Aruba Central API Configuration                     ║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "  You need to provide your Aruba Central API credentials."
    echo "  These can be found in your Aruba Central account under:"
    echo "  Account Home > API Gateway > My Apps & Tokens"
    echo ""
    
    # Base URL selection
    echo -e "${YELLOW}Select your Aruba Central region:${NC}"
    echo ""
    echo "  ── Americas ──"
    echo "   1) US-1 (prod)           us1.api.central.arubanetworks.com"
    echo "   2) US-2 (central-prod2)  us2.api.central.arubanetworks.com"
    echo "   3) US-WEST-4 (uswest4)   us4.api.central.arubanetworks.com"
    echo "   4) US-WEST-5 (uswest5)   us5.api.central.arubanetworks.com"
    echo "   5) US-East1 (us-east-1)  us6.api.central.arubanetworks.com"
    echo "   6) Canada-1 (starman)    ca1.api.central.arubanetworks.com"
    echo ""
    echo "  ── Europe ──"
    echo "   7) EU-1 (eu)             de1.api.central.arubanetworks.com"
    echo "   8) EU-Central2           de2.api.central.arubanetworks.com"
    echo "   9) EU-Central3           de3.api.central.arubanetworks.com"
    echo ""
    echo "  ── Asia Pacific ──"
    echo "  10) APAC-1 (apac)         in.api.central.arubanetworks.com"
    echo "  11) APAC-EAST1 (apaceast) jp1.api.central.arubanetworks.com"
    echo "  12) APAC-SOUTH1           au1.api.central.arubanetworks.com"
    echo ""
    echo "  ── Other ──"
    echo "  13) Internal              internal.api.central.arubanetworks.com"
    echo "  14) Custom (enter your own URL)"
    echo ""
    read -p "  Enter choice [1-14]: " region_choice
    
    case $region_choice in
        1)  ARUBA_BASE_URL="https://us1.api.central.arubanetworks.com" ;;
        2)  ARUBA_BASE_URL="https://us2.api.central.arubanetworks.com" ;;
        3)  ARUBA_BASE_URL="https://us4.api.central.arubanetworks.com" ;;
        4)  ARUBA_BASE_URL="https://us5.api.central.arubanetworks.com" ;;
        5)  ARUBA_BASE_URL="https://us6.api.central.arubanetworks.com" ;;
        6)  ARUBA_BASE_URL="https://ca1.api.central.arubanetworks.com" ;;
        7)  ARUBA_BASE_URL="https://de1.api.central.arubanetworks.com" ;;
        8)  ARUBA_BASE_URL="https://de2.api.central.arubanetworks.com" ;;
        9)  ARUBA_BASE_URL="https://de3.api.central.arubanetworks.com" ;;
        10) ARUBA_BASE_URL="https://in.api.central.arubanetworks.com" ;;
        11) ARUBA_BASE_URL="https://jp1.api.central.arubanetworks.com" ;;
        12) ARUBA_BASE_URL="https://au1.api.central.arubanetworks.com" ;;
        13) ARUBA_BASE_URL="https://internal.api.central.arubanetworks.com" ;;
        14) 
            read -p "  Enter custom base URL (e.g., https://your-server.com): " ARUBA_BASE_URL
            ;;
        *)
            echo -e "${RED}Invalid choice. Please run the script again.${NC}"
            exit 1
            ;;
    esac
    echo -e "  ✓ Region: ${GREEN}$ARUBA_BASE_URL${NC}"
    echo ""
    
    # Client ID
    read -p "  Enter Client ID: " ARUBA_CLIENT_ID
    if [ -z "$ARUBA_CLIENT_ID" ]; then
        echo -e "${RED}ERROR: Client ID cannot be empty${NC}"
        exit 1
    fi
    echo -e "  ✓ Client ID configured"
    
    # Client Secret (hidden input)
    echo -n "  Enter Client Secret: "
    read -s ARUBA_CLIENT_SECRET
    echo ""
    if [ -z "$ARUBA_CLIENT_SECRET" ]; then
        echo -e "${RED}ERROR: Client Secret cannot be empty${NC}"
        exit 1
    fi
    echo -e "  ✓ Client Secret configured"
    
    # Access Token (optional)
    echo ""
    echo -e "${CYAN}  Note: Access Token is optional - it will be generated automatically${NC}"
    echo -e "${CYAN}        from Client ID/Secret using OAuth2 client credentials flow.${NC}"
    read -p "  Enter Access Token (press Enter to skip): " ARUBA_ACCESS_TOKEN
    if [ -z "$ARUBA_ACCESS_TOKEN" ]; then
        ARUBA_ACCESS_TOKEN="auto_generated"
    fi
    echo ""
    
    # Write .env file
    cat > .env << EOF
# Aruba Central API Configuration
# Generated by deploy.sh on $(date)
ARUBA_BASE_URL=$ARUBA_BASE_URL
ARUBA_CLIENT_ID=$ARUBA_CLIENT_ID
ARUBA_CLIENT_SECRET=$ARUBA_CLIENT_SECRET
ARUBA_ACCESS_TOKEN=$ARUBA_ACCESS_TOKEN
EOF
    
    echo -e "  ${GREEN}✓ Credentials saved to .env${NC}"
}

# Check if .env exists and has valid credentials
NEEDS_CONFIG=false
if [ ! -f .env ]; then
    NEEDS_CONFIG=true
    echo "  .env file not found"
elif grep -q "your_client_id\|your_client_secret\|your_access_token" .env 2>/dev/null; then
    NEEDS_CONFIG=true
    echo "  .env has placeholder values"
elif [ -z "$(grep ARUBA_CLIENT_ID .env | cut -d= -f2)" ]; then
    NEEDS_CONFIG=true
    echo "  .env is missing Client ID"
else
    echo "  ✓ .env file exists with credentials"
    
    # Ask if user wants to reconfigure
    read -p "  Do you want to reconfigure credentials? [y/N]: " reconfigure
    if [[ "$reconfigure" =~ ^[Yy]$ ]]; then
        NEEDS_CONFIG=true
    fi
fi

if [ "$NEEDS_CONFIG" = true ]; then
    configure_credentials
fi

# Step 3: Validate credentials format
echo -e "${YELLOW}[3/6]${NC} Validating credentials..."
source .env
if [ -z "$ARUBA_BASE_URL" ] || [ -z "$ARUBA_CLIENT_ID" ] || [ -z "$ARUBA_CLIENT_SECRET" ]; then
    echo -e "${RED}ERROR: Missing required credentials in .env${NC}"
    exit 1
fi
echo "  ✓ Base URL: $ARUBA_BASE_URL"
echo "  ✓ Client ID: ${ARUBA_CLIENT_ID:0:8}..."
echo "  ✓ Client Secret: ****"

# Step 4: Stop existing container if running
echo -e "${YELLOW}[4/6]${NC} Stopping existing container..."
if docker ps -q --filter "name=aruba-noc-mcp-server" | grep -q .; then
    docker compose down
    echo "  ✓ Stopped existing container"
else
    echo "  ✓ No existing container running"
fi

# Step 5: Build and start container
echo -e "${YELLOW}[5/6]${NC} Building and starting container..."
docker compose build --no-cache
docker compose up -d

# Step 6: Verify deployment
echo -e "${YELLOW}[6/6]${NC} Verifying deployment..."
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
echo "  - Reconfigure:  ./deploy.sh  (and select 'y' to reconfigure)"
