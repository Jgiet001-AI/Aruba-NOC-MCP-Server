# Deployment Guide: Docker Secrets & Production Setup

This guide covers secure deployment of the Aruba NOC MCP Server using Docker Secrets and production best practices.

## Table of Contents

1. [Overview](#overview)
2. [Development Setup](#development-setup)
3. [Production Setup with Docker Secrets](#production-setup-with-docker-secrets)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Migration Guide](#migration-guide)
6. [Verification](#verification)
7. [Troubleshooting](#troubleshooting)

---

## Overview

### Security Improvements

The server now supports **three credential sources** with automatic priority:

| Priority | Source | Use Case | Security Level |
|----------|--------|----------|----------------|
| 1 | Docker Secrets (`/run/secrets/`) | Production with Docker Swarm | ⭐⭐⭐⭐⭐ |
| 2 | File-based secrets (`/secrets/`) | Kubernetes, custom deployments | ⭐⭐⭐⭐ |
| 3 | Environment variables | Development, backward compatibility | ⭐⭐ |

### Why Docker Secrets?

✅ **Encrypted at rest** - Secrets stored encrypted in swarm manager nodes
✅ **Encrypted in transit** - Secrets transmitted over mutually authenticated TLS
✅ **Minimal exposure** - Only accessible to authorized containers
✅ **Never in environment variables** - Not visible in `docker inspect` or logs
✅ **Immutable** - Cannot be modified; must be rotated with new versions

---

## Development Setup

### Quick Start (Environment Variables)

For local development, use `.env` file:

```bash
# .env
ARUBA_BASE_URL=https://us1.api.central.arubanetworks.com
ARUBA_CLIENT_ID=your_client_id_here
ARUBA_CLIENT_SECRET=your_client_secret_here
```

Start with Docker Compose:

```bash
docker-compose up --build
```

**Note:** Environment variables are less secure and should only be used for development.

---

## Production Setup with Docker Secrets

### Prerequisites

- Docker Swarm mode enabled
- Aruba Central API credentials (Client ID and Client Secret)
- TLS/HTTPS configured for production

### Step 1: Initialize Docker Swarm

If not already initialized:

```bash
docker swarm init
```

Verify swarm is active:

```bash
docker info | grep Swarm
# Should show: Swarm: active
```

### Step 2: Create Docker Secrets

Create secrets from secure input (recommended - doesn't leave secrets in shell history):

```bash
# Create Client ID secret (paste when prompted, press Ctrl+D when done)
docker secret create aruba_client_id -

# Create Client Secret (paste when prompted, press Ctrl+D when done)
docker secret create aruba_client_secret -
```

**Alternative:** Create from files (ensure files are deleted afterward):

```bash
# Create temporary files (don't commit these!)
echo "your_actual_client_id" > /tmp/client_id.txt
echo "your_actual_client_secret" > /tmp/client_secret.txt

# Create secrets
docker secret create aruba_client_id /tmp/client_id.txt
docker secret create aruba_client_secret /tmp/client_secret.txt

# IMPORTANT: Delete temporary files immediately!
rm /tmp/client_id.txt /tmp/client_secret.txt
```

Verify secrets were created:

```bash
docker secret ls
```

Expected output:
```
ID                          NAME                     CREATED          UPDATED
abc123def456                aruba_client_id          10 seconds ago   10 seconds ago
xyz789uvw012                aruba_client_secret      5 seconds ago    5 seconds ago
```

### Step 3: Update docker-compose.yaml

Uncomment the secrets section in `docker-compose.yaml`:

```yaml
services:
  aruba-noc-mcp:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: aruba-noc-mcp-server

    # Comment out or remove env_file for production
    # env_file:
    #   - .env

    # Enable Docker Secrets
    secrets:
      - aruba_client_id
      - aruba_client_secret

    stdin_open: true
    tty: true

    healthcheck:
      test: [ "CMD", "python", "-c", "from src.server import app; print('ok')" ]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

# Enable external secrets
secrets:
  aruba_client_id:
    external: true
  aruba_client_secret:
    external: true
```

### Step 4: Deploy with Docker Stack

Deploy as a stack (required for secrets):

```bash
docker stack deploy -c docker-compose.yaml aruba-noc
```

Monitor deployment:

```bash
# Check stack status
docker stack ps aruba-noc

# View service logs
docker service logs aruba-noc_aruba-noc-mcp
```

You should see in the logs:
```
Loaded ARUBA_CLIENT_ID from Docker secret
Loaded ARUBA_CLIENT_SECRET from Docker secret
OAuth2 credentials loaded successfully
```

---

## Kubernetes Deployment

### Step 1: Create Kubernetes Secrets

```bash
kubectl create secret generic aruba-credentials \
  --from-literal=aruba_client_id='your_client_id' \
  --from-literal=aruba_client_secret='your_client_secret'
```

### Step 2: Create Deployment YAML

Create `k8s-deployment.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: aruba-noc-mcp
spec:
  selector:
    app: aruba-noc-mcp
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8080

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aruba-noc-mcp
spec:
  replicas: 2
  selector:
    matchLabels:
      app: aruba-noc-mcp
  template:
    metadata:
      labels:
        app: aruba-noc-mcp
    spec:
      containers:
      - name: aruba-noc-mcp
        image: aruba-noc-mcp:latest
        stdin: true
        tty: true

        # Mount secrets as files
        volumeMounts:
        - name: secrets
          mountPath: /secrets
          readOnly: true

        # Optional: Environment variables for non-sensitive config
        env:
        - name: ARUBA_BASE_URL
          value: "https://us1.api.central.arubanetworks.com"

        # Health check
        livenessProbe:
          exec:
            command:
            - python
            - -c
            - "from src.server import app; print('ok')"
          initialDelaySeconds: 10
          periodSeconds: 30

      # Volume for secrets
      volumes:
      - name: secrets
        secret:
          secretName: aruba-credentials
          items:
          - key: aruba_client_id
            path: aruba_client_id
          - key: aruba_client_secret
            path: aruba_client_secret
```

### Step 3: Deploy to Kubernetes

```bash
kubectl apply -f k8s-deployment.yaml

# Verify deployment
kubectl get pods -l app=aruba-noc-mcp

# Check logs
kubectl logs -l app=aruba-noc-mcp
```

---

## Migration Guide

### From Environment Variables to Docker Secrets

#### Step 1: Backup Current Configuration

```bash
# Save your current .env file (don't commit to git!)
cp .env .env.backup
```

#### Step 2: Create Docker Secrets

Follow [Step 2](#step-2-create-docker-secrets) above to create secrets from your credentials.

#### Step 3: Test in Parallel

Deploy with secrets while keeping your old deployment running:

```bash
# Deploy new stack with secrets
docker stack deploy -c docker-compose.yaml aruba-noc-test

# Monitor logs for successful initialization
docker service logs aruba-noc-test_aruba-noc-mcp
```

Look for:
```
Loaded ARUBA_CLIENT_ID from Docker secret
Loaded ARUBA_CLIENT_SECRET from Docker secret
OAuth2 credentials loaded successfully
```

#### Step 4: Switch Over

Once verified:

```bash
# Remove old deployment
docker-compose down

# Update production stack
docker stack deploy -c docker-compose.yaml aruba-noc

# Remove environment variable file
rm .env  # Keep .env.backup for emergency rollback
```

#### Rollback (if needed)

If issues occur:

```bash
# Remove stack deployment
docker stack rm aruba-noc

# Restore .env file
mv .env.backup .env

# Start with docker-compose
docker-compose up -d
```

---

## Verification

### 1. Verify Secret Loading

Check container logs for secret source confirmation:

```bash
# Docker Stack
docker service logs aruba-noc_aruba-noc-mcp | grep "Loaded ARUBA"

# Kubernetes
kubectl logs -l app=aruba-noc-mcp | grep "Loaded ARUBA"
```

Expected output:
```
Loaded ARUBA_CLIENT_ID from Docker secret
Loaded ARUBA_CLIENT_SECRET from Docker secret
```

### 2. Verify OAuth2 Authentication

```bash
# Check for successful token acquisition
docker service logs aruba-noc_aruba-noc-mcp | grep "OAuth2"
```

Expected output:
```
OAuth2 credentials loaded successfully
OAuth2 access token acquired successfully (expires in 7200s)
```

### 3. Verify Secrets Are Not in Environment

Secrets should NOT appear in environment variables:

```bash
# Get container ID
CONTAINER_ID=$(docker ps | grep aruba-noc-mcp | awk '{print $1}')

# Check environment (secrets should NOT be here)
docker exec $CONTAINER_ID env | grep ARUBA
```

Should only show `ARUBA_BASE_URL`, NOT client credentials.

### 4. Verify Secrets Are Mounted

Verify secrets are accessible as files:

```bash
# Check secret files exist
docker exec $CONTAINER_ID ls -la /run/secrets/
```

Expected output:
```
-r--r--r-- 1 root root  36 Jan  5 12:00 aruba_client_id
-r--r--r-- 1 root root  64 Jan  5 12:00 aruba_client_secret
```

---

## Troubleshooting

### Issue: "Access token not available"

**Symptoms:**
```
ValueError: Access token not available. Call get_access_token() first or provide ARUBA_ACCESS_TOKEN.
```

**Causes:**
1. Secrets not created in Docker Swarm
2. Secrets not mounted in container
3. Invalid credentials

**Solution:**

```bash
# 1. Verify secrets exist
docker secret ls | grep aruba

# 2. Check container has access
CONTAINER_ID=$(docker ps | grep aruba-noc-mcp | awk '{print $1}')
docker exec $CONTAINER_ID ls /run/secrets/

# 3. Verify credentials are valid (check logs)
docker service logs aruba-noc_aruba-noc-mcp --tail 50
```

### Issue: "No such secret"

**Symptoms:**
```
Error: secret aruba_client_id not found
```

**Solution:**

The secret must be created BEFORE deploying the stack:

```bash
# Create secret
docker secret create aruba_client_id -

# Then deploy
docker stack deploy -c docker-compose.yaml aruba-noc
```

### Issue: Secrets appear in logs

**Symptoms:**
Client ID or secret visible in logs.

**Solution:**

This should NEVER happen with our implementation. If you see credentials in logs:

1. Check `src/config.py` - logging should only mention the source, not the value
2. Report as a security bug
3. Rotate credentials immediately

**Correct log format:**
```
✅ Loaded ARUBA_CLIENT_ID from Docker secret
❌ Loaded ARUBA_CLIENT_ID: abc123def456  # NEVER log actual values!
```

### Issue: Circuit breaker open

**Symptoms:**
```
CircuitBreakerError: Circuit breaker OPEN - API unavailable
```

**Solution:**

The circuit breaker opens after 5 consecutive API failures:

```bash
# Check API health
docker service logs aruba-noc_aruba-noc-mcp | grep "Circuit breaker"

# Manual reset (if API is healthy again)
docker service update --force aruba-noc_aruba-noc-mcp
```

The circuit breaker will automatically test recovery after 60 seconds.

---

## Best Practices

### 🔒 Security

1. **Never commit secrets to git**
   - Add `.env` to `.gitignore`
   - Use `.env.example` with placeholder values

2. **Rotate secrets regularly**
   ```bash
   # Create new version
   docker secret create aruba_client_secret_v2 -

   # Update service
   docker service update --secret-rm aruba_client_secret \
                         --secret-add aruba_client_secret_v2 \
                         aruba-noc_aruba-noc-mcp

   # Remove old version
   docker secret rm aruba_client_secret
   ```

3. **Use least privilege**
   - Only grant necessary API scopes in Aruba Central
   - Limit container permissions

### 📊 Monitoring

1. **Track OAuth2 token expiration**
   ```bash
   docker service logs aruba-noc_aruba-noc-mcp | grep "expires in"
   ```

2. **Monitor rate limiting**
   ```bash
   docker service logs aruba-noc_aruba-noc-mcp | grep "Rate limit"
   ```

3. **Watch circuit breaker state**
   ```bash
   docker service logs aruba-noc_aruba-noc-mcp | grep "Circuit breaker"
   ```

### 🚀 Deployment

1. **Use health checks** - Already configured in `docker-compose.yaml`
2. **Enable auto-restart** - Docker Swarm handles this automatically
3. **Scale for high availability**
   ```bash
   docker service scale aruba-noc_aruba-noc-mcp=3
   ```

### 🧪 Testing

1. **Test with mock credentials first**
2. **Verify secret loading in logs**
3. **Confirm OAuth2 flow before production**
4. **Run health checks after deployment**

---

## Environment Variables Reference

### Required (via Secrets or Environment)

| Variable | Secret Name | Description | Example |
|----------|-------------|-------------|---------|
| `ARUBA_CLIENT_ID` | `aruba_client_id` | OAuth2 Client ID from Aruba Central | `abc123def456...` |
| `ARUBA_CLIENT_SECRET` | `aruba_client_secret` | OAuth2 Client Secret from Aruba Central | `xyz789uvw012...` |

### Optional Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ARUBA_BASE_URL` | `https://us1.api.central.arubanetworks.com` | Aruba Central API base URL |
| `ARUBA_API_TIMEOUT` | `30.0` | API request timeout (seconds) |
| `ARUBA_RATE_LIMIT_REQUESTS` | `100` | Max requests per window |
| `ARUBA_RATE_LIMIT_WINDOW` | `60` | Rate limit window (seconds) |
| `ARUBA_CIRCUIT_BREAKER_THRESHOLD` | `5` | Failures before circuit opens |
| `ARUBA_CIRCUIT_BREAKER_TIMEOUT` | `60` | Circuit breaker timeout (seconds) |

---

## Support

For issues or questions:

1. Check logs: `docker service logs aruba-noc_aruba-noc-mcp`
2. Review [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for API issues
3. Verify credentials in Aruba Central console
4. Check [MCP_OPTIMIZATION_GUIDE.md](./MCP_OPTIMIZATION_GUIDE.md) for architecture details

---

## Summary

✅ **Development:** Use `.env` file with environment variables
✅ **Production (Docker Swarm):** Use Docker Secrets for maximum security
✅ **Production (Kubernetes):** Mount secrets as files in `/secrets/`
✅ **Always:** Verify secret sources in logs, never commit credentials to git
