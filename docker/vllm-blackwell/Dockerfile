# =================================================================================
# Dockerfile for vLLM on Blackwell GPU (GB10/B200)
# Resolves: ptxas fatal: Unsupported .target 'sm_121a'
# Architecture: aarch64 (Grace CPU + Blackwell GPU)
# =================================================================================

# Use official vLLM image as base
# We will mount host CUDA 13.0 at runtime for Blackwell (sm_121a) support
FROM vllm/vllm-openai:latest

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive

# Prepend host CUDA path to LD_LIBRARY_PATH to support Blackwell runtime
# This preserves the base image's paths (including PyTorch libs)
ENV LD_LIBRARY_PATH=/usr/local/cuda-13.0/lib64:${LD_LIBRARY_PATH}

# Bypass NVIDIA entrypoint check for unsupported GPUs (GB10)
ENTRYPOINT []

# Install analysis dependencies
RUN pip install --no-cache-dir \
    PyYAML \
    tqdm \
    "numpy<2.0" \
    langchain \
    langchain-community \
    langchain-core \
    openai

# Create model cache directory
RUN mkdir -p /root/.cache/huggingface

# Set working directory

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5m --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose vLLM API port
EXPOSE 8000

# Default command
CMD ["vllm", "serve", "--help"]
