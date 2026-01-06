#!/bin/bash
# Production Test Runner - Execute comprehensive tool test in container

cd "$(dirname "$0")"

# Ensure container is running
echo "Checking container status..."
docker-compose up -d

# Wait for container to be healthy
echo "Waiting for container to be ready..."
sleep 3

# Copy test script to container's /tmp directory (mcp user can read from /tmp)
echo "Copying test script to container..."
docker cp test_all_40_tools.py aruba-noc-mcp-server:/tmp/test_tools.py

# Run test as mcp user
echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║  RUNNING COMPREHENSIVE PRODUCTION TEST (ALL 30 TOOLS)           ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

docker exec -u mcp aruba-noc-mcp-server python3 /tmp/test_tools.py

# Copy report out
echo ""
echo "Retrieving test report..."
docker cp aruba-noc-mcp-server:/tmp/all_40_tools_test_report.json ./test_report.json 2>/dev/null || echo "No report file generated"

echo ""
echo "✅ Test complete! Check test_report.json for details"
