#!/bin/bash
# =================================================================================
# Script: update_cuda_env.sh
# Purpose: Configure environment for CUDA 12/13 runtime and Triton
# Target: Fix 'Unsupported .target sm_121a' error on Blackwell/GB10 vLLM
# Usage: source update_cuda_env.sh
# =================================================================================

echo "[INFO] Starting CUDA environment configuration..."

# ---------------------------------------------------------------------------------
# Step 1: Detect CUDA installation directory
# Prioritize explicit version directories for CUDA 13.0/12.8 over generic symlinks
# to ensure Blackwell-compatible toolkit is selected in side-by-side installations
# ---------------------------------------------------------------------------------
CUDA_CANDIDATES=(
    "/usr/local/cuda-13.0"
    "/usr/local/cuda-12.9"
    "/usr/local/cuda-12.8"
    "/usr/local/cuda"
)

CUDA_HOME=""
for candidate in "${CUDA_CANDIDATES[@]}"; do
    if [ -d "$candidate" ]; then
        CUDA_HOME="$candidate"
        echo "[INFO] Detected CUDA installation: $CUDA_HOME"
        break
    fi
done

if [ -z "$CUDA_HOME" ]; then
    echo "[ERROR] Could not find a valid CUDA installation in standard locations."
    echo "[ERROR] Ensure CUDA 12.8+ is installed."
    return 1 2>/dev/null || exit 1
fi

# ---------------------------------------------------------------------------------
# Step 2: Update PATH
# Prepend CUDA bin to PATH so system prefers these binaries
# Check if already included to prevent duplicate entries
# ---------------------------------------------------------------------------------
if [[ ":$PATH:" != *":${CUDA_HOME}/bin:"* ]]; then
    export PATH="${CUDA_HOME}/bin:${PATH}"
    echo "[INFO] PATH updated: Added $CUDA_HOME/bin"
else
    echo "[INFO] PATH already includes CUDA bin directory"
fi

# ---------------------------------------------------------------------------------
# Step 3: Update LD_LIBRARY_PATH
# Critical for finding libcudart.so, libcublas.so, etc.
# ---------------------------------------------------------------------------------
LIB_DIR="${CUDA_HOME}/lib64"
if [ ! -d "$LIB_DIR" ]; then
    # Fallback for systems using 'lib' instead of 'lib64' (rare for CUDA)
    LIB_DIR="${CUDA_HOME}/lib"
fi

if [[ ":$LD_LIBRARY_PATH:" != *":${LIB_DIR}:"* ]]; then
    export LD_LIBRARY_PATH="${LIB_DIR}${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
    echo "[INFO] LD_LIBRARY_PATH updated: Added $LIB_DIR"
else
    echo "[INFO] LD_LIBRARY_PATH already includes CUDA lib directory"
fi

# ---------------------------------------------------------------------------------
# Step 4: Configure Triton override (sm_121a fix)
# Locate system ptxas and force Triton to use it
# ---------------------------------------------------------------------------------
SYSTEM_PTXAS="${CUDA_HOME}/bin/ptxas"

if [ -x "$SYSTEM_PTXAS" ]; then
    export TRITON_PTXAS_PATH="$SYSTEM_PTXAS"
    echo "[INFO] TRITON_PTXAS_PATH set to: $SYSTEM_PTXAS"
    
    # Verify ptxas version supports sm_121a logic (version-based heuristic)
    PTXAS_VERSION=$($SYSTEM_PTXAS --version 2>/dev/null | grep -oP 'release \K[0-9]+\.[0-9]+' | head-1)
    echo "[INFO] System ptxas version: ${PTXAS_VERSION:-unknown}"
else
    echo "[ERROR] ptxas binary not found at $SYSTEM_PTXAS"
    echo "[ERROR] Triton compilation for sm_121a will likely fail"
fi

# ---------------------------------------------------------------------------------
# Step 5: Set PyTorch architecture flags
# Explicitly target Blackwell architecture variant
# ---------------------------------------------------------------------------------
# Note: '12.1a' is the specific target requested by the error message
# For multi-GPU configurations with older architectures, can add "9.0 12.1a" etc.
export TORCH_CUDA_ARCH_LIST="12.1a"
echo "[INFO] TORCH_CUDA_ARCH_LIST set to: $TORCH_CUDA_ARCH_LIST"

# ---------------------------------------------------------------------------------
# Step 6: vLLM-specific optimizations (optional but recommended)
# ---------------------------------------------------------------------------------
# Ensure vLLM uses correct compile threads
export NVCC_THREADS=8
# Enable verbose logging for debugging if issues persist
export VLLM_LOGGING_LEVEL=INFO
export VLLM_CONFIGURE_LOGGING=1

echo "[SUCCESS] Environment configuration completed"
echo "[CHECK] Verify with: nvcc --version && echo \$TRITON_PTXAS_PATH"
