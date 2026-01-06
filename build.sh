#!/bin/bash
set -e

echo "🔧 Building Aruba NOC MCP Server with supply chain attestations..."
echo ""

# Use default builder (docker driver) for local builds with attestations
echo "📦 Using default buildx builder (supports local loading with attestations)"
docker buildx use default

echo ""
echo "🏗️  Building image with attestations..."
echo "   - Provenance: true"
echo "   - SBOM: true"
echo ""

# Build with attestations using default builder
# Note: default builder (docker driver) supports --load with basic attestations
docker buildx build \
  --provenance=true \
  --sbom=true \
  --tag aruba-review-aruba-noc-mcp:latest \
  --load \
  .

echo ""
echo "✅ Image built successfully!"
echo ""
echo "📊 Next steps:"
echo "   1. Run security scan: docker scout quickview aruba-review-aruba-noc-mcp:latest"
echo "   2. View CVEs: docker scout cves aruba-review-aruba-noc-mcp:latest"
echo "   3. Start container: docker-compose up -d"
echo ""
