# Visual AOI Server — Docker Image
#
# Build:  docker compose build
# Run:    docker compose up -d
#
# GPU:  Requires NVIDIA Container Toolkit on the host.
#       RTX 5080 (compute capability 12.0) uses PTX JIT compilation
#       enabled via CUDA_FORCE_PTX_JIT=1.
#
# Shared folder:
#   The container exposes /app/shared as a bind-mount point.
#   The host Samba server shares the SAME physical directory so the
#   client can reach session images via CIFS at /mnt/visual-aoi-shared/.

FROM python:3.11-slim-bookworm

# ---------------------------------------------------------------------------
# System packages required by OpenCV, EasyOCR, Pillow, and Dynamsoft
# ---------------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    ffmpeg \
    curl \
    ca-certificates \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

# ---------------------------------------------------------------------------
# pip configuration — bypass SSL certificate inspection on corporate networks.
# Lists all hosts pip or its CDN redirects may contact.
# ---------------------------------------------------------------------------
RUN mkdir -p /root/.config/pip && \
    printf '[global]\ntrusted-host =\n    pypi.org\n    pypi.python.org\n    files.pythonhosted.org\n    download.pytorch.org\n    download-r2.pytorch.org\n' \
    > /root/.config/pip/pip.conf

# ---------------------------------------------------------------------------
# Python dependencies
# Install PyTorch (CUDA 12.4 wheel) first, then the rest of requirements.txt.
# ---------------------------------------------------------------------------
RUN pip install --no-cache-dir --timeout 300 \
    torch torchvision \
    --index-url https://download.pytorch.org/whl/cu124 && \
    pip install --no-cache-dir --timeout 300 \
    -r requirements.txt

# ---------------------------------------------------------------------------
# Application code
# Copy in layers that change least → most to maximise cache hits.
# ---------------------------------------------------------------------------
COPY src/    ./src/
COPY server/ ./server/

# ---------------------------------------------------------------------------
# Shared folder and config mount points.
# Overridden by bind-mounts at runtime (see docker-compose.yml).
# Created here so the server starts even without mounts.
# ---------------------------------------------------------------------------
RUN mkdir -p \
    /app/shared/sessions \
    /app/shared/roi_editor \
    /app/config/products \
    /app/config/system

# ---------------------------------------------------------------------------
# Runtime environment
# ---------------------------------------------------------------------------
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    CUDA_FORCE_PTX_JIT=1

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

CMD ["python", "server/simple_api_server.py", "--host", "0.0.0.0", "--port", "5000"]
