# Kagura AI - Custom Qdrant with wget for healthcheck
# Issue #659 - Enable Qdrant healthcheck for production monitoring
#
# Base Image: qdrant/qdrant:v1.15.5 (Debian 12 bookworm)
# Additions: wget for Docker healthcheck
# Size Impact: +500KB (187MB → 187.5MB)

FROM qdrant/qdrant:v1.15.5

# Install wget for healthcheck (lightweight, minimal dependencies)
RUN apt-get update && \
    apt-get install -y --no-install-recommends wget && \
    rm -rf /var/lib/apt/lists/*

# Verify wget installation and version
RUN wget --version

# No changes to Qdrant configuration or entrypoint
# This image is functionally identical to official qdrant/qdrant,
# with only wget added for Docker healthcheck support.

# Healthcheck will use:
# wget --no-verbose --tries=1 --spider http://localhost:6333/healthz
