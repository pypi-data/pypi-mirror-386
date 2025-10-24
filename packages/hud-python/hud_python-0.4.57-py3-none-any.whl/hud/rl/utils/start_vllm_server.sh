#!/bin/bash
# Start vLLM server with OpenAI-compatible API

echo "Starting vLLM server for Qwen2.5-VL-3B-Instruct..."

# Enable runtime LoRA adapter loading
export VLLM_ALLOW_RUNTIME_LORA_UPDATING=True

export TOKENIZERS_PARALLELISM=false
export VLLM_LOGGING_LEVEL=DEBUG
export CUDA_LAUNCH_BLOCKING=1  # Better error messages for CUDA errors

# Common vLLM server command
# Using CUDA_VISIBLE_DEVICES to put vLLM on GPU 1
CUDA_VISIBLE_DEVICES=1 uv run vllm serve \
    Qwen/Qwen2.5-VL-3B-Instruct \
    --api-key token-abc123 \
    --host 0.0.0.0 \
    --port 8000 \
    --tensor-parallel-size 1 \
    --trust-remote-code \
    --max-model-len 16384 \
    --enable-lora \
    --max-lora-rank 64 \
    --max-cpu-loras 4 \
    --enable-auto-tool-choice \
    --tool-call-parser hermes \
    --chat-template chat_template.jinja \
    --enable-log-requests \
    --uvicorn-log-level=debug 2>&1 | tee vllm_debug.log