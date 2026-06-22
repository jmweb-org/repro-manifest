# Capture or diff a manifest from inside a container. Mount the working tree so
# git provenance is available:
#
#   docker build -t repro-manifest .
#   docker run --rm -v "$PWD:/w" -w /w repro-manifest capture
#
FROM python:3.12-slim

LABEL org.opencontainers.image.source="https://github.com/jmweb-org/repro-manifest"
LABEL org.opencontainers.image.description="Capture a reproducibility manifest for a run and diff two manifests."
LABEL org.opencontainers.image.licenses="MIT"

# git lets the manifest record commit and dirty-tree provenance.
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src

RUN pip install --no-cache-dir .

ENTRYPOINT ["repro-manifest"]
CMD ["--help"]
