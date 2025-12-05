#!/bin/bash

# Run vLLM for Qwen3-VL-30B-A3B-Instruct using deepseek-ocr environment
# This model should fit comfortably in 128GB VRAM.

export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/home/sanghyun/miniforge3/envs/deepseek-ocr/lib/python3.12/site-packages/nvidia/cuda_runtime/lib:/home/sanghyun/miniforge3/envs/deepseek-ocr/lib/python3.12/site-packages/nvidia/cu13/lib/
/home/sanghyun/miniforge3/envs/deepseek-ocr/bin/vllm serve Qwen/Qwen3-VL-30B-A3B-Instruct \
  --tensor-parallel-size 1 \
  --gpu-memory-utilization 0.90 \
  --max-model-len 32768 \
  --trust-remote-code
