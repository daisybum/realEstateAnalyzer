#!/bin/bash

# Run vLLM for Qwen3-VL-235B-A22B-Instruct-FP8
# Note: FP8 weights for 235B might require > 128GB VRAM.
# We use aggressive memory utilization and reduced context length to try and fit it.

/home/sanghyun/miniforge3/envs/deepseek-ocr/bin/vllm serve Qwen/Qwen3-VL-235B-A22B-Instruct-FP8 \
  --tensor-parallel-size 1 \
  --gpu-memory-utilization 0.92 \
  --max-model-len 4096 \
  --trust-remote-code
