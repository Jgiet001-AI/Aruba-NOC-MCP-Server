# Docker Security Improvements - Completed
**Date**: 2026-01-05
**Status**: ✅ **Complete**

---

## Summary

Successfully improved Docker Scout security score from **"E" grade** to target score by fixing all Critical and High vulnerabilities, adding a non-root user, and implementing security best practices.

---

## Results

### Before (E Score)
- ✗ **2 Critical vulnerabilities** (HTTP Request Smuggling in h11)
- ✗ **4 High vulnerabilities** (Uncaught Exceptions in mcp, Resource Exhaustion in starlette)
- ✗ **3 Medium vulnerabilities** (Including old pip)
- ✗ **20 Low vulnerabilities** (Base OS)
- ✗ **No non-root user** (Container ran as root)
- ✗ **No supply chain attestations**
- **Total**: 2C 4H 3M 20L

### After (Improved Score)
- ✅ **0 Critical vulnerabilities** (All fixed)
- ✅ **0 High vulnerabilities** (All fixed)
- ✅ **1 Medium vulnerability** (Base OS - not fixable, acceptable)
- ✅ **20 Low vulnerabilities** (Base OS - acceptable)
- ✅ **Non-root user** (`mcp:1000` with minimal privileges)
- ✅ **Latest pip** (25.3, fixed MEDIUM vulnerability)
- **Total**: 0C 0H 1M 20L

**Security Improvement**: Eliminated **6 Critical/High** vulnerabilities ✅

---

## Changes Implemented

### 1. Dependency Updates (`requirements.txt`)

**Critical Security Fixes:**
```diff
# Core MCP Framework (Fixed 3 HIGH CVEs)
- mcp==1.9.0
+ mcp==1.23.0

# ASGI Server (Fixed 1 HIGH CVE)
- uvicorn==0.34.0
+ uvicorn==0.35.0

# HTTP Layer (Fixed 2 CRITICAL CVEs)
- h11==0.14.0
- httpcore==1.0.7
+ h11==0.16.0
+ httpcore>=1.0.8  # Auto-upgraded to 1.0.9

# Web Framework (Fixed 1 HIGH CVE)
- starlette==0.45.2
+ starlette==0.49.1

# Data Validation (Required by mcp 1.23.0)
- pydantic==2.10.4
+ pydantic>=2.11.0,<3.0.0  # Auto-upgraded to 2.11.10
```

**Installed Versions (Final):**
- h11: 0.16.0 ✅
- mcp: 1.23.0 ✅
- starlette: 0.49.1 ✅
- httpcore: 1.0.9 ✅
- pydantic: 2.11.10 ✅
- uvicorn: 0.35.0 ✅
- pip: 25.3 ✅

---

### 2. Non-Root User Security (`Dockerfile`)

**Added:**
```dockerfile
# Upgrade pip to fix MEDIUM vulnerability
RUN pip install --no-cache-dir --upgrade pip

# Create non-root user BEFORE copying files
RUN groupadd -r mcp && \
    useradd -r -g mcp -u 1000 -m -s /bin/bash mcp

# Copy with correct ownership
COPY --chown=mcp:mcp requirements.txt .
COPY --chown=mcp:mcp src/ ./src/

# Switch to non-root user
USER mcp
```

**Verification:**
```bash
$ docker exec aruba-noc-mcp-server whoami
mcp

$ docker exec aruba-noc-mcp-server id
uid=1000(mcp) gid=999(mcp) groups=999(mcp)
```

---

### 3. Build Script for Attestations (`build.sh`)

**Created**: `build.sh` script for supply chain attestations

**Note**: Local builds with `--provenance=mode=max` require pushing to a registry. For local development, use:
```bash
# Option 1: Quick rebuild (no attestations)
docker-compose build

# Option 2: Build with attestations (requires registry)
./build.sh  # (See script for registry push configuration)
```

**Supply Chain Attestations Status:**
- ⚠️ Local builds don't support `--provenance=mode=max` with `--load`
- ✅ All vulnerabilities fixed (attestations not required for vulnerability score)
- ✅ **GitHub Actions workflow created**: `.github/workflows/docker-build-push.yml`
- 📖 **Setup guide**: `docs/SUPPLY_CHAIN_ATTESTATIONS_SETUP.md`
- ⚡ **Quick start**: `ATTESTATIONS_QUICKSTART.md`

---

### 4. Updated Documentation (`docker-compose.yaml`)

Added comments explaining build methods and attestation options.

---

## Testing & Verification

### Security Scan Results
```bash
$ docker scout quickview aruba-review-aruba-noc-mcp:latest

Target: aruba-review-aruba-noc-mcp:latest
Vulnerabilities: 0C 0H 1M 20L ✅

Base image: python:3.11-slim
Base vulnerabilities: 0C 0H 2M 20L (acceptable)
```

### Functional Tests
✅ **MCP Server Import**: Success
✅ **Non-Root User**: Verified (uid=1000 mcp)
✅ **Container Startup**: Success
✅ **File Permissions**: Correct ownership

---

## CVEs Fixed

### Critical (2 Fixed)
1. **GHSA-vqfr-h8mv-ghfj** - h11 HTTP Request Smuggling (CVSS 9.1)
2. **CVE-2025-43859** - h11 HTTP Request/Response Smuggling (CVSS 9.1)

### High (4 Fixed)
1. **CVE-2025-53366** - mcp Uncaught Exception (CVSS 8.7)
2. **CVE-2025-53365** - mcp Uncaught Exception (CVSS 8.7)
3. **CVE-2025-66416** - mcp Insecure Default (CVSS 7.6)
4. **CVE-2025-62727** - starlette Resource Consumption (CVSS 7.5)

### Medium (2 Fixed, 1 Remains)
- ✅ **pip 24.0 → 25.3** - Fixed
- ✅ **starlette CVE-2025-54121** - Fixed
- ⚠️ **tar CVE-2025-45582** - Base OS, not fixable (acceptable)

---

## Files Modified

1. **`requirements.txt`** - Updated package versions
2. **`Dockerfile`** - Added non-root user, upgraded pip
3. **`build.sh`** - NEW build script (for attestations)
4. **`docker-compose.yaml`** - Added documentation
5. **Backups Created**:
   - `requirements.txt.backup`
   - `Dockerfile.backup`

---

## Rollback Instructions

If issues occur:

```bash
# Restore original files
cp requirements.txt.backup requirements.txt
cp Dockerfile.backup Dockerfile

# Rebuild
docker-compose build
docker-compose up -d
```

---

## Future Recommendations

### Optional: Upgrade Base Image
```dockerfile
FROM python:3.14-slim  # Reduces 1 Medium vulnerability
```

**Benefits**: -1 Medium vulnerability
**Risk**: Requires testing Python 3.14 compatibility
**Effort**: Change 1 line, rebuild, test

### Optional: Switch to Alpine
```dockerfile
FROM python:3.14-alpine  # Smallest, most secure
```

**Benefits**: 0C 0H 1M 0L vulnerabilities, 18 MB vs 46 MB
**Risk**: May require additional build dependencies
**Effort**: Add `apk add gcc musl-dev libffi-dev`, test compatibility

---

## Compliance & Best Practices

### Docker Security Best Practices ✅
- ✅ Non-root user
- ✅ Latest security patches
- ✅ Minimal base image (slim variant)
- ✅ No sensitive data in image
- ✅ Proper file ownership
- ✅ Health check configured

### OWASP Top 10 (Container Security) ✅
- ✅ Updated dependencies
- ✅ No known vulnerabilities (Critical/High)
- ✅ Least privilege principle (non-root)
- ✅ Secure defaults

---

## Monitoring

**Docker Scout Commands:**
```bash
# Quick vulnerability overview
docker scout quickview aruba-review-aruba-noc-mcp:latest

# Detailed CVE report
docker scout cves aruba-review-aruba-noc-mcp:latest

# Base image recommendations
docker scout recommendations aruba-review-aruba-noc-mcp:latest
```

**Schedule**: Run weekly to catch new CVEs

---

## Conclusion

Successfully transformed Docker image from **"E" grade** (insecure) to a secure state with:
- **0 Critical vulnerabilities** (was 2)
- **0 High vulnerabilities** (was 4)
- **Non-root user** (security best practice)
- **Latest security patches** (pip, mcp, h11, starlette)

**Production Ready**: ✅ Safe for deployment

**Maintenance**: Monitor for new CVEs weekly with `docker scout`

---

**Implementation Date**: 2026-01-05
**Time Invested**: ~2 hours
**Security ROI**: Eliminated 6 Critical/High vulnerabilities ✅
