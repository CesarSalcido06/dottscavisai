# DottscavisAI Research: Creative AI on M1 Pro Mac

**Date**: December 27, 2025
**Target Hardware**: M1 Pro Mac (16GB+ RAM)

---

## Executive Summary

DottscavisAI will be the **creative agent** in the BenchAI multi-agent system, specializing in:
- Vision/Image Understanding
- Image Generation
- Text-to-Speech
- Audio Generation

This document analyzes the best models and frameworks for M1 Pro Mac.

---

## Framework Comparison

| Framework | Optimization | Best For | Notes |
|-----------|--------------|----------|-------|
| **MLX** | Native Apple Silicon | LLMs, VLMs, Diffusion | Apple's official ML framework |
| **Core ML** | Native | Stable Diffusion | Apple's model format |
| **GGUF** | Cross-platform | Fallback | Works but not optimal |
| **MPS** | Metal backend | PyTorch models | Good compatibility |

**Recommendation**: Use **MLX** where possible for best M1 Pro performance.

---

## Vision Language Models (VLMs)

### Best Options for M1 Pro

| Model | Size | Quantization | Framework | Speed |
|-------|------|--------------|-----------|-------|
| **LLaVA 1.5 7B** | ~4GB | 4-bit | MLX-VLM | Good |
| **LLaVA 1.6 Mistral** | ~4GB | 4-bit | MLX-VLM | Good |
| **Qwen-VL 7B** | ~4GB | 4-bit | MLX-VLM | Good |
| **FastVLM** (Apple) | TBD | Native | Core ML | 85x faster |

### MLX-VLM Library

```bash
pip install mlx-vlm
```

**Available Models:**
- `mlx-community/llava-1.5-7b-4bit`
- `mlx-community/llava-v1.6-mistral-7b-4bit`
- `mlx-community/llava-llama-3-8b-v1_1-4bit`
- `mlx-community/llava-interleave-qwen-7b-4bit`

**Usage:**
```python
from mlx_vlm import load, generate
model, processor = load("mlx-community/llava-1.5-7b-4bit")
output = generate(model, processor, image, prompt)
```

### Known Issues
- Some M1 Pro users reported issues in Jan 2025 (likely resolved)
- GGUF versions work as fallback

**Sources:**
- [vllm-mlx GitHub](https://github.com/waybarrios/vllm-mlx)
- [MLX-VLM Guide](https://dzone.com/articles/vision-ai-apple-silicon-guide-mlx-vlm)
- [Apple FastVLM](https://machinelearning.apple.com/research/fast-vision-language-models)

---

## Image Generation

### Stable Diffusion on M1 Pro

| Method | Speed (512x512) | Ease of Use |
|--------|-----------------|-------------|
| **DiffusionBee** | ~35s | One-click install |
| **Core ML SD** | ~35s | Need conversion |
| **MLX Diffusion** | ~30s | Native MLX |
| **ComfyUI** | ~40s | Full features |

### Performance by Chip

| Chip | Time for 512x512 |
|------|------------------|
| M1 | ~35 seconds |
| M1 Pro | ~25 seconds |
| M2 | ~23 seconds |
| M3 Max | ~12 seconds |

### Recommended: MLX Stable Diffusion

```bash
pip install mlx-stable-diffusion
# or
git clone https://github.com/ml-explore/mlx-examples
cd mlx-examples/stable_diffusion
```

**Models:**
- Stable Diffusion 1.5
- Stable Diffusion 2.1
- Stable Diffusion XL (requires 16GB+ RAM)

**Sources:**
- [Apple Core ML SD](https://github.com/apple/ml-stable-diffusion)
- [DiffusionBee](https://github.com/divamgupta/diffusionbee-stable-diffusion-ui)
- [MLX Examples](https://github.com/ml-explore/mlx-examples)

---

## Text-to-Speech (TTS)

### Options for M1 Pro

| Model | Latency | Quality | Languages |
|-------|---------|---------|-----------|
| **Piper** | <50ms | Good | 20+ |
| **XTTS v2** | <200ms | Excellent | 17 |
| **Coqui TTS** | ~500ms | Good | Many |
| **Bark** | ~2s | Excellent | Multi |

### Recommended: Piper

Fast, local neural TTS with excellent M1 support.

```bash
# Install
pip install piper-tts

# Download voices
piper --download en_US-lessac-medium
```

**Voice Quality Tiers:**
- `x_low`: Fastest, lowest quality
- `low`: Fast, acceptable quality
- `medium`: Balanced (recommended)
- `high`: Best quality, slower

### Alternative: XTTS v2 (Coqui)

Better voice cloning, 17 languages, but requires more setup.

```bash
pip install coqui-tts
```

**Note**: GPU acceleration not available on M1, but CPU is sufficient.

**Sources:**
- [Piper GitHub](https://github.com/rhasspy/piper)
- [Coqui TTS](https://github.com/idiap/coqui-ai-TTS)
- [TTS on Mac Guide](https://www.thoughtasylum.com/2025/08/25/text-to-speech-on-macos-with-piper/)

---

## Audio/Music Generation

### MusicGen

Short musical composition generation via transformers.

```bash
pip install transformers torch
```

**Models:**
- `facebook/musicgen-small` (300M) - Fast
- `facebook/musicgen-medium` (1.5B) - Balanced
- `facebook/musicgen-large` (3.3B) - Best quality

### Bark

Text-to-audio with music, sound effects, and speech.

```bash
pip install bark
```

**Sources:**
- [LocalAI TTS](https://localai.io/features/text-to-audio/)

---

## Recommended Stack for DottscavisAI

### Primary (MLX-Native)

| Capability | Tool | Model |
|------------|------|-------|
| Vision | MLX-VLM | LLaVA 1.5 7B 4-bit |
| Image Gen | MLX SD | Stable Diffusion 2.1 |
| TTS | Piper | en_US-lessac-medium |
| General LLM | MLX-LM | Qwen2.5 7B |

### Fallback (Cross-Platform)

| Capability | Tool | Model |
|------------|------|-------|
| Vision | llama.cpp | Qwen2-VL GGUF |
| Image Gen | ComfyUI | SDXL |
| TTS | Coqui | XTTS v2 |

---

## Memory Considerations

**M1 Pro 16GB RAM Budget:**

| Component | Memory |
|-----------|--------|
| LLaVA 7B 4-bit | ~4GB |
| Stable Diffusion | ~4GB |
| Piper TTS | ~0.5GB |
| System | ~2GB |
| **Available** | ~5GB buffer |

**Recommendation**: Run one large model at a time, swap as needed.

---

## Integration with BenchAI

### A2A Protocol Endpoints

```python
# Receive tasks from BenchAI
POST /v1/a2a/task
{
    "from_agent": "benchai",
    "task_type": "image_gen",
    "task_description": "Generate a cyberpunk city",
    "context": {...}
}

# Report completion
POST http://benchai:8085/v1/learning/collective/contribute
{
    "from_agent": "dottscavisAI",
    "result": "...",
    "success": true
}
```

### Routing Matrix

| Task Keyword | Routes To | Capability |
|--------------|-----------|------------|
| "generate image" | DottscavisAI | Image Gen |
| "analyze image" | DottscavisAI | Vision |
| "describe photo" | DottscavisAI | Vision |
| "speak" / "read aloud" | DottscavisAI | TTS |
| "create music" | DottscavisAI | MusicGen |

---

## Next Steps

1. **Setup Script**: Install MLX, MLX-VLM, Piper, SD
2. **Core Router**: FastAPI with A2A endpoints
3. **Model Downloads**: LLaVA, SD 2.1, Piper voices
4. **Integration Test**: BenchAI → DottscavisAI flow
5. **Performance Tuning**: Memory management, model swapping

---

*Research compiled by BenchAI (Claude Opus 4.5) - December 27, 2025*
