# =================================================================================
# Dockerfile for vLLM on Blackwell GPU (GB10/B200)
# =================================================================================
# Architecture: aarch64 (Grace CPU + Blackwell GPU)
# Resolves: ptxas fatal: Unsupported .target 'sm_121a'
# =================================================================================

FROM vllm/vllm-openai:latest

# Environment
ENV DEBIAN_FRONTEND=noninteractive
ENV LD_LIBRARY_PATH=/usr/local/cuda-13.0/lib64:${LD_LIBRARY_PATH}

# Bypass NVIDIA entrypoint check for unsupported GPUs (GB10)
ENTRYPOINT []

# Install Python dependencies for analysis pipeline
RUN pip install --no-cache-dir \
    PyYAML \
    tqdm \
    "numpy<2.0" \
    langchain \
    langchain-community \
    langchain-core \
    langsmith \
    openai

# Create directories
RUN mkdir -p /root/.cache/huggingface

# Working directory
WORKDIR /workspace/app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5m --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose API port
EXPOSE 8000

# Default command
CMD ["vllm", "serve", "--help"]
