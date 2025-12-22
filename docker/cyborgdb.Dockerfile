FROM niledb/cyborgdb:latest

# CyborgDB with persistent storage support
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Use the image's default CMD

