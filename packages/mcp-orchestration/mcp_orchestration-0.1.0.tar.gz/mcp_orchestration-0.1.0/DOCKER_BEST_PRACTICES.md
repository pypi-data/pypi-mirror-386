# Docker Best Practices for mcp-orchestration

This guide covers Docker best practices specific to this project, based on production-proven patterns from the chora-base template.

## Quick Reference

```bash
# Build and verify
just docker-build
just docker-verify

# Run locally
just docker-compose-up
just docker-logs

# Stop
just docker-compose-down
```

## Image Optimization

### Current Configuration

This project uses **multi-stage builds** with wheel distribution for optimal image size:

- **Builder stage:** Compiles dependencies, builds wheel
- **Runtime stage:** Minimal image with only runtime dependencies
- **Expected size:** 150-250MB (vs 500MB+ with editable install)

### Why Wheel Builds?

```dockerfile
# Builder stage
RUN python -m build --wheel --outdir /dist

# Runtime stage
COPY --from=builder /dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl
```

**Benefits:**
- ✅ 40% smaller images (no build tools in runtime)
- ✅ Eliminates import path conflicts
- ✅ Standard distribution method (matches PyPI)
- ✅ Faster deployments (smaller transfer size)

## Health Checks

### Import-Based Validation

This project uses **import-based health checks** (not CLI-based):

```dockerfile
HEALTHCHECK CMD python -c "import mcp_orchestration; assert mcp_orchestration.__version__"
```

**Why this matters for MCP servers:**
- MCP servers use STDIO transport (not HTTP)
- CLI health checks add 100-500ms overhead
- Import validation is <100ms and validates Python environment

**What it validates:**
- Python interpreter is functional
- Package is correctly installed
- Dependencies are available
- Version resolution works

## CI/CD Integration

### GitHub Actions Cache

For **6x faster builds**, use Docker layer caching:

```yaml
- name: Set up Docker Buildx
  uses: docker/setup-buildx-action@v3

- name: Build test image
  uses: docker/build-push-action@v5
  with:
    file: ./Dockerfile.test
    tags: mcp-orchestration:test
    cache-from: type=gha              # Read from cache
    cache-to: type=gha,mode=max       # Write all layers
    load: true
```

**Performance:**
- First build: ~2-3 minutes (populates cache)
- Cached builds: ~30 seconds (6x faster)

### Coverage Extraction

Get coverage reports from Docker tests:

```bash
# Run tests in container
docker run --rm mcp-orchestration:test

# Extract coverage report
container_id=$(docker create mcp-orchestration:test)
docker cp $container_id:/app/coverage.xml ./
docker rm $container_id
```

**Why not volume mounts?**
- Works across all CI systems (no permission issues)
- Atomic operation (file copies or fails cleanly)
- No sudo required
## Multi-Architecture Builds

### Building for ARM64

Support Apple Silicon (M1/M2) and AWS Graviton:

```bash
# Build for amd64 + arm64
just docker-build-multi latest

# Verify platforms
docker buildx imagetools inspect mcp-orchestration:latest
```

**Setup buildx (one-time):**
```bash
docker buildx create --use
docker buildx inspect --bootstrap
```

## Development Workflows

### Local Development

**Option 1: Use venv locally (recommended)**
```bash
# Fast iteration with local venv
./scripts/setup.sh
just test
just lint
```

**Option 2: Docker for integration testing**
```bash
# Test with Docker (matches production)
just docker-test
just docker-compose-up
```

### Hot-Reload Configuration

For configuration hot-reload without rebuilds:

```yaml
# docker-compose.yml
volumes:
  - ./configs:/app/configs:ro  # Read-only configs
```

Edit `configs/` files on your host → changes immediately reflected in container.
## Security Best Practices

### Current Configuration

✅ **Non-root user** (UID 1000)
```dockerfile
USER appuser  # Not root
```

✅ **Minimal base image** (`python:3.12-slim`)
```dockerfile
FROM python:3.12-slim  # Not full image
```

✅ **No secrets in image**
```yaml
env_file:
  - .env  # Secrets via environment, not baked in
```

✅ **Build context optimization**
```
# .dockerignore excludes:
.env          # Secrets never sent to build context
.git/         # No version control history
__pycache__/  # No cache artifacts
```

### Vulnerability Scanning

Add to your CI workflow:

```yaml
- name: Scan image for vulnerabilities
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: mcp-orchestration:latest
    severity: HIGH,CRITICAL
```

## Production Deployment

### Registry Publishing

Push to container registry:

```bash
# Tag and push specific version
just docker-push ghcr.io/liminalcommons/mcp-orchestration 1.0.0

# Full release workflow (build, verify, tag, push)
just docker-release 1.0.0 ghcr.io/liminalcommons
```

### Environment Configuration

Use **environment-based configuration** (12-factor app):

```yaml
# docker-compose.yml
environment:
  - MCP_ORCHESTRATION_LOG_LEVEL=${MCP_ORCHESTRATION_LOG_LEVEL:-INFO}
  - DATABASE_URL=${DATABASE_URL}
```

**Pattern:** `${VAR:-default}` for sensible defaults

### MCP Server Deployment

**STDIO transport (Claude Desktop):**
- No port exposure needed
- Run as daemon: `just docker-run`

**SSE transport (n8n, web clients):**
```yaml
environment:
  - MCP_TRANSPORT=sse
  - MCP_SERVER_HOST=0.0.0.0
  - MCP_SERVER_PORT=8000
ports:
  - "8000:8000"
```

## Troubleshooting

### Issue: Image larger than expected

**Check build context size:**
```bash
docker build --no-cache -t test . 2>&1 | grep "Sending build context"
```

**Solution:** Review `.dockerignore` and ensure large directories are excluded.

### Issue: "Module not found" error

**Cause:** Wheel build changed package installation

**Solution:**
```bash
# Rebuild from scratch
docker system prune -f
just docker-build
```

### Issue: Health check failing

**Verify manually:**
```bash
# Test health check command
docker run --rm mcp-orchestration:latest python -c "import mcp_orchestration; assert mcp_orchestration.__version__"
```

**Common causes:**
- Missing `__version__` attribute in `__init__.py`
- Import-time errors in package
- Missing runtime dependencies

### Issue: Slow builds in CI

**Check cache configuration:**
```yaml
# Ensure both cache-from and cache-to
cache-from: type=gha
cache-to: type=gha,mode=max  # mode=max is important
```

**Verify layers are cached:**
```bash
# Check CI logs for "CACHED" indicators
```

## Volume Management

### Data Persistence

```yaml
volumes:
  # Logs (persistent, safe to commit)
  - ./logs:/app/logs

  # Data (persistent, backup regularly)
  - ./data:/app/data

# Agent memory (persistent, version controlled)
  - ./.chora/memory:/app/.chora/memory
```

### Cleanup

```bash
# Remove containers and images
just docker-clean

# Full cleanup (including volumes)
just docker-clean-all  # WARNING: Deletes data!
```

## Performance Tuning

### Build Cache Optimization

**Layer ordering** (from least to most frequently changed):
1. System dependencies (`apt-get install`)
2. Python dependencies (`pyproject.toml`)
3. Application code (`src/`)

```dockerfile
# Good: Dependencies before code
COPY pyproject.toml ./
RUN pip install --no-cache-dir .
COPY src/ ./src/

# Bad: Code before dependencies (cache bust)
COPY src/ ./src/
COPY pyproject.toml ./
RUN pip install --no-cache-dir .
```

### Runtime Optimization

**Environment variables:**
```dockerfile
ENV PYTHONUNBUFFERED=1            # Real-time logs
ENV PYTHONDONTWRITEBYTECODE=1     # No .pyc files (reduces I/O)
```

## Monitoring and Observability

### Container Logs

```bash
# Follow logs
just docker-logs

# Or directly
docker-compose logs -f mcp-orchestration
```

### Health Status

```bash
# Check health
docker inspect --format='{{.State.Health.Status}}' mcp-orchestration

# View health check logs
docker inspect --format='{{json .State.Health}}' mcp-orchestration | jq
```

### Resource Usage

```bash
# Monitor resource usage
docker stats mcp-orchestration

# Set limits in docker-compose.yml
resources:
  limits:
    cpus: '1.0'
    memory: 512M
```

## Chora-base Template Patterns

This project follows chora-base Docker patterns:

- ✅ Multi-stage builds (size optimization)
- ✅ Wheel distribution (import path safety)
- ✅ Import-based health checks (low overhead)
- ✅ Non-root execution (security)
- ✅ Environment-based config (12-factor)
- ✅ GitHub Actions cache (build speed)

**Learn more:** [chora-base Docker documentation](https://github.com/liminalcommons/chora-base)

## Additional Resources

- **Dockerfile** - Production multi-stage build
- **Dockerfile.test** - CI/test build with coverage
- **docker-compose.yml** - Service orchestration
- **.dockerignore** - Build context optimization
- **justfile** - Docker command shortcuts

**Questions?** Open an issue or consult the chora-base documentation.
