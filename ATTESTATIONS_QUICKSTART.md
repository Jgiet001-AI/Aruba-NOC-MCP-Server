# Supply Chain Attestations - Quick Start

**Goal**: Enable Docker Scout attestations by pushing to Docker Hub

---

## ⚡ Fast Track (5 Minutes)

### 1. Verify GitHub Secrets
Go to: https://github.com/Jgiet001-AI/Aruba-NOC-MCP-Server/settings/secrets/actions

**Required secrets:**
- `DOCKERHUB_USERNAME` - Your Docker Hub username
- `DOCKERHUB_TOKEN` - Your Docker Hub Personal Access Token

**Missing a secret?** See "Create Docker Hub Token" below.

---

### 2. Update Docker Hub Username (if needed)

Edit `.github/workflows/docker-build-push.yml` line 17:
```yaml
IMAGE_NAME: YOUR_USERNAME/aruba-noc-mcp-server
```

**Current**: `jgiet001ai/aruba-noc-mcp-server`

---

### 3. Push to GitHub

```bash
git add .
git commit -m "Add supply chain attestations workflow"
git push origin main
```

**Or trigger manually**: https://github.com/Jgiet001-AI/Aruba-NOC-MCP-Server/actions → "Run workflow"

---

### 4. Monitor Build

Watch at: https://github.com/Jgiet001-AI/Aruba-NOC-MCP-Server/actions

**Expected**: 5-10 minutes for multi-platform build

---

### 5. Verify Success

```bash
docker pull jgiet001ai/aruba-noc-mcp-server:latest
docker scout quickview jgiet001ai/aruba-noc-mcp-server:latest
```

**Expected output:**
```
✅ Supply chain attestation(s) found
✅ SBOM attestation
✅ Provenance attestation (mode=max)
```

---

## 🔑 Create Docker Hub Token (if needed)

1. **Generate token**: https://hub.docker.com/settings/security
   - Name: `GitHub Actions`
   - Permissions: Read, Write, Delete
   - Copy token immediately

2. **Add to GitHub**:
   - Go to: https://github.com/Jgiet001-AI/Aruba-NOC-MCP-Server/settings/secrets/actions
   - New secret: `DOCKERHUB_TOKEN`
   - Value: Paste token
   - Add secret: `DOCKERHUB_USERNAME` (your Docker Hub username)

---

## 🎯 What You Get

- ✅ **SBOM** - Complete dependency list
- ✅ **Provenance** - Build verification (SLSA Level 3)
- ✅ **Multi-platform** - amd64 + arm64
- ✅ **Auto-scan** - Docker Scout on every build
- ✅ **Docker Scout score** - Attestations requirement met

---

## 🔗 Links

- **Workflow**: `.github/workflows/docker-build-push.yml`
- **Full docs**: `docs/SUPPLY_CHAIN_ATTESTATIONS_SETUP.md`
- **Actions**: https://github.com/Jgiet001-AI/Aruba-NOC-MCP-Server/actions
- **Docker Hub**: https://hub.docker.com/r/jgiet001ai/aruba-noc-mcp-server

---

**Ready?** Push to GitHub and watch the magic happen! 🚀
