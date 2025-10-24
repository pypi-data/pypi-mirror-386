# Docker Operations for mcp-orchestration

**Purpose**: Docker containerization guide for deployment and development.

**Parent**: See [../AGENTS.md](../AGENTS.md) for project overview and other topics.

---

## Quick Reference

- **Build image**: `just docker-build`
- **Verify image**: `just docker-verify`
- **Start services**: `just docker-compose-up`
- **View logs**: `just docker-logs`

---

## Docker Operations

**When enabled** (`include_docker: true`), mcp-orchestration includes production-ready Docker support with ergonomic commands.

### Discovery

```bash
# List all Docker commands
just --list | grep docker

# Available commands:
# - docker-build [TAG]          Build production image
# - docker-build-multi [TAG]    Build for amd64 + arm64
# - docker-verify [TAG]          Smoke test image health
# - docker-shell [TAG]           Interactive debugging shell
# - docker-test                  Run tests in isolated container
# - docker-compose-up            Start all services
# - docker-compose-down          Stop all services
# - docker-logs                  View service logs
# - docker-clean                 Remove images and containers
# - docker-push REGISTRY TAG     Push to container registry
# - docker-release VERSION REG   Full release workflow
```

### Common Workflows

```bash
# Build and verify image
just docker-build
just docker-verify

# Run services locally
just docker-compose-up
just docker-logs

# Stop services
just docker-compose-down

# Clean up
just docker-clean
```

---

## Detailed Documentation

**For comprehensive Docker workflows:** See project documentation
---

## Adopter Responsibilities (Wiring Required)

- [ ] Ensure `mcp_orchestration.__version__` is defined
- [ ] Test import-based health check works
- [ ] Configure project-specific environment variables in `.env`
- [ ] Set service dependencies in `docker-compose.yml` (if using multiple services)
- [ ] Configure registry credentials for `docker-push` (if publishing)
- [ ] Test multi-architecture builds (if deploying to ARM64)
---

## Image Optimization Results

**Expected metrics (wheel builds):**
- **Size**: 150-250MB (40% smaller than naive builds)
- **Build time**: ~2-3 minutes (first build), ~30 seconds (cached)
- **Health check**: <100ms (import-based validation)
- **Multi-arch**: Native ARM64 support (Apple Silicon)

---

## Related Documentation

- **[Main AGENTS.md](../AGENTS.md)** - Project overview, architecture, common tasks
- **[Testing AGENTS.md](../tests/AGENTS.md)** - Testing instructions
- **[Memory System AGENTS.md](../.chora/memory/AGENTS.md)** - Cross-session learning
- **[scripts/AGENTS.md](../scripts/AGENTS.md)** - Automation scripts reference

---

**End of Docker Operations Guide**

For questions or issues not covered here, see the main [AGENTS.md](../AGENTS.md) or [DOCKER_BEST_PRACTICES.md](../DOCKER_BEST_PRACTICES.md).
