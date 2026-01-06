# Supply Chain Attestations Setup Guide
**Goal**: Enable Docker Scout supply chain attestations (SBOM + Provenance) for your Aruba NOC MCP Server

---

## Overview

Supply chain attestations provide cryptographic proof of:
- **SBOM (Software Bill of Materials)**: Complete list of all dependencies
- **Provenance**: How, when, and where the image was built

This is the final requirement for achieving the best Docker Scout security score.

---

## ✅ What's Already Done

1. ✅ GitHub Actions workflow created: `.github/workflows/docker-build-push.yml`
2. ✅ Workflow configured with:
   - `provenance: mode=max` (maximum provenance detail)
   - `sbom: true` (SBOM generation)
   - Multi-platform build (amd64, arm64)
   - Automatic Docker Scout scanning
3. ✅ Dockerfile optimized with non-root user and security patches

---

## 🔧 Setup Steps

### Step 1: Verify Your Docker Hub Username

First, confirm your Docker Hub username by visiting: https://hub.docker.com/settings/general

**Update the workflow file** if needed:

Edit `.github/workflows/docker-build-push.yml` line 17:
```yaml
IMAGE_NAME: YOUR_DOCKERHUB_USERNAME/aruba-noc-mcp-server
```

**Current setting**: `jgiet001ai/aruba-noc-mcp-server`

If your Docker Hub username is different, update this value.

---

### Step 2: Check GitHub Secrets

You mentioned your Docker Hub credentials are in GitHub Secrets. Verify they exist:

1. Go to: https://github.com/Jgiet001-AI/Aruba-NOC-MCP-Server/settings/secrets/actions

2. Confirm these secrets exist:
   - **`DOCKERHUB_USERNAME`** - Your Docker Hub username
   - **`DOCKERHUB_TOKEN`** - Your Docker Hub Personal Access Token (PAT)

---

### Step 3: Create Docker Hub Access Token (if needed)

If you don't have `DOCKERHUB_TOKEN` secret yet:

1. **Create Token**:
   - Go to: https://hub.docker.com/settings/security
   - Click "New Access Token"
   - Name: `GitHub Actions - Aruba NOC MCP`
   - Permissions: **Read, Write, Delete**
   - Click "Generate"
   - **Copy the token immediately** (you can't see it again!)

2. **Add to GitHub Secrets**:
   - Go to: https://github.com/Jgiet001-AI/Aruba-NOC-MCP-Server/settings/secrets/actions
   - Click "New repository secret"
   - Name: `DOCKERHUB_TOKEN`
   - Value: Paste the token
   - Click "Add secret"

3. **Add Username Secret** (if not exists):
   - Click "New repository secret"
   - Name: `DOCKERHUB_USERNAME`
   - Value: Your Docker Hub username (e.g., `jgiet001ai`)
   - Click "Add secret"

---

### Step 4: Trigger the Workflow

**Option 1: Push to Main/Master** (Automatic)
```bash
git add .github/workflows/docker-build-push.yml
git add Dockerfile requirements.txt
git commit -m "Add supply chain attestations workflow"
git push origin main
```

**Option 2: Manual Trigger**
1. Go to: https://github.com/Jgiet001-AI/Aruba-NOC-MCP-Server/actions
2. Click "Build and Push Docker Image with Attestations"
3. Click "Run workflow"
4. Select branch: `main`
5. Click "Run workflow"

**Option 3: Create a Tag**
```bash
git tag -a v1.0.0 -m "Release v1.0.0 with attestations"
git push origin v1.0.0
```

---

### Step 5: Monitor the Build

1. Go to: https://github.com/Jgiet001-AI/Aruba-NOC-MCP-Server/actions

2. Click on the running workflow

3. Watch the build progress:
   - ✅ Checkout repository
   - ✅ Set up Docker Buildx
   - ✅ Log in to Docker Hub
   - ✅ Build and push (with attestations)
   - ✅ Docker Scout scan
   - ✅ Scout quickview

4. **Expected duration**: 5-10 minutes (multi-platform build)

---

### Step 6: Verify Attestations

Once the workflow completes successfully:

**Check Docker Hub:**
```bash
# Pull the image
docker pull jgiet001ai/aruba-noc-mcp-server:latest

# Verify attestations exist
docker buildx imagetools inspect jgiet001ai/aruba-noc-mcp-server:latest

# You should see:
# - MediaType: application/vnd.oci.image.manifest.v1+json (provenance)
# - MediaType: application/vnd.in-toto+json (SBOM)
```

**Check Docker Scout:**
```bash
docker scout quickview jgiet001ai/aruba-noc-mcp-server:latest
```

**Expected output:**
```
✅ Supply chain attestation(s) found
✅ SBOM attestation
✅ Provenance attestation (mode=max)
```

---

## 🎯 What This Achieves

### Before
- ✗ Missing supply chain attestation(s)
- ⚠️ Cannot verify build provenance
- ⚠️ No SBOM for dependency tracking

### After
- ✅ **SBOM attestation**: Complete dependency manifest
- ✅ **Provenance attestation**: Build verification
- ✅ **Multi-platform**: amd64 + arm64
- ✅ **Automated scanning**: Docker Scout on every build
- ✅ **Cache optimization**: Faster subsequent builds

---

## 🔒 Security Benefits

1. **Supply Chain Verification**:
   - Cryptographically signed proof of build origin
   - Tamper-evident build process
   - Verifiable dependency tree

2. **Compliance**:
   - SLSA Level 3 provenance
   - SBOM for vulnerability tracking
   - Meets enterprise security requirements

3. **Docker Scout Score**:
   - ✅ Checks "Supply chain attestation(s)" requirement
   - Improves overall security grade
   - Better visibility into dependencies

---

## 📊 Workflow Features

### Automatic Triggers
- ✅ Push to `main` or `master` branch
- ✅ Pull requests (build only, no push)
- ✅ Version tags (`v*`)
- ✅ Manual trigger via GitHub UI

### Image Tags Generated
- `latest` - Latest build from main branch
- `main` - Main branch builds
- `v1.0.0` - Semantic version tags
- `main-sha-abc123` - Git commit SHA

### Multi-Platform Support
- ✅ `linux/amd64` (Intel/AMD)
- ✅ `linux/arm64` (Apple Silicon, ARM servers)

### Automated Security Scanning
- ✅ Docker Scout CVE scan after build
- ✅ Reports critical/high vulnerabilities
- ✅ Quickview summary

---

## 🔍 Troubleshooting

### Error: "Invalid credentials"
**Solution**: Check GitHub Secrets
```bash
# Secrets should be:
DOCKERHUB_USERNAME = your_dockerhub_username
DOCKERHUB_TOKEN = dckr_pat_xxxxxxxxxxxxx (not your password!)
```

### Error: "repository does not exist"
**Solution**: Update `IMAGE_NAME` in workflow
```yaml
env:
  IMAGE_NAME: YOUR_USERNAME/aruba-noc-mcp-server
```

### Error: "permission denied"
**Solution**: Ensure Docker Hub token has "Read, Write, Delete" permissions

### Build timeout
**Solution**: Multi-platform builds take longer (5-10 minutes). This is normal.

### Attestations not showing
**Solution**:
1. Wait 1-2 minutes after build completes
2. Check workflow logs for "provenance: mode=max"
3. Verify you pulled the latest image

---

## 📝 Maintenance

### Update Workflow
Edit `.github/workflows/docker-build-push.yml` to:
- Change platforms
- Modify tags
- Add build arguments
- Configure Scout policies

### Rotate Access Token
Every 90 days (recommended):
1. Create new Docker Hub token
2. Update `DOCKERHUB_TOKEN` secret
3. Delete old token from Docker Hub

### Monitor Builds
- GitHub Actions: https://github.com/Jgiet001-AI/Aruba-NOC-MCP-Server/actions
- Docker Hub: https://hub.docker.com/r/jgiet001ai/aruba-noc-mcp-server
- Scout Dashboard: Enable Docker Scout for your repo

---

## 🎉 Success Criteria

After following this guide, you should have:

- ✅ Image pushed to Docker Hub with attestations
- ✅ Docker Scout score improved (attestations requirement met)
- ✅ Automated builds on every push
- ✅ Multi-platform support (amd64 + arm64)
- ✅ Security scanning on every build
- ✅ Public image available: `docker pull jgiet001ai/aruba-noc-mcp-server:latest`

---

## 🔗 Useful Links

- **Workflow runs**: https://github.com/Jgiet001-AI/Aruba-NOC-MCP-Server/actions
- **Docker Hub repo**: https://hub.docker.com/r/jgiet001ai/aruba-noc-mcp-server
- **GitHub Secrets**: https://github.com/Jgiet001-AI/Aruba-NOC-MCP-Server/settings/secrets/actions
- **Docker Hub tokens**: https://hub.docker.com/settings/security
- **SLSA Provenance**: https://slsa.dev/spec/v1.0/provenance
- **Docker Scout**: https://docs.docker.com/scout/

---

## 📞 Next Steps

1. ✅ Verify GitHub Secrets exist (`DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`)
2. ✅ Update `IMAGE_NAME` in workflow if needed
3. ✅ Push workflow to GitHub or trigger manually
4. ✅ Monitor build in GitHub Actions
5. ✅ Verify attestations with Docker Scout
6. ✅ Pull and test image: `docker pull jgiet001ai/aruba-noc-mcp-server:latest`

**Estimated Time**: 10-15 minutes (setup) + 5-10 minutes (first build)

---

**Created**: 2026-01-05
**Status**: Ready to deploy
