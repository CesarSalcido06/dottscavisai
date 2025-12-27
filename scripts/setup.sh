#!/bin/bash
# DottscavisAI Setup Script for M1 Pro Mac
# Part of the BenchAI Multi-Agent System

set -e

echo "=== DottscavisAI Setup ==="
echo "Target: M1 Pro Mac"
echo ""

# Check if running on macOS
if [[ "$(uname)" != "Darwin" ]]; then
    echo "Warning: This script is optimized for macOS. Some features may not work."
fi

# Check for Homebrew
if ! command -v brew &> /dev/null; then
    echo "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Install system dependencies
echo ""
echo "=== Installing System Dependencies ==="
brew install python@3.11 git git-lfs ffmpeg portaudio || true

# Create virtual environment
echo ""
echo "=== Creating Python Environment ==="
cd "$(dirname "$0")/.."
python3.11 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip wheel setuptools

# Install core dependencies
echo ""
echo "=== Installing Core Dependencies ==="
pip install \
    fastapi \
    uvicorn[standard] \
    httpx \
    pydantic \
    python-multipart \
    aiofiles

# Install MLX (Apple's ML framework)
echo ""
echo "=== Installing MLX Framework ==="
pip install mlx mlx-lm

# Install MLX-VLM for vision
echo ""
echo "=== Installing MLX-VLM (Vision) ==="
pip install mlx-vlm || echo "MLX-VLM install failed, will use fallback"

# Install Stable Diffusion
echo ""
echo "=== Installing Stable Diffusion ==="
pip install diffusers transformers accelerate || echo "Diffusers install failed"

# Try MLX Stable Diffusion
pip install mlx-stable-diffusion 2>/dev/null || echo "MLX-SD not available, using diffusers"

# Install Piper TTS
echo ""
echo "=== Installing Piper TTS ==="
pip install piper-tts || {
    echo "Piper Python install failed, trying standalone..."
    brew install piper-tts 2>/dev/null || echo "Will need manual Piper install"
}

# Install audio dependencies
pip install soundfile scipy numpy

# Download default models
echo ""
echo "=== Downloading Models ==="
mkdir -p ~/models

# Download LLaVA (vision model)
echo "Downloading LLaVA 1.5 7B 4-bit..."
python3 -c "
try:
    from mlx_vlm import load
    print('Downloading LLaVA model...')
    load('mlx-community/llava-1.5-7b-4bit')
    print('LLaVA downloaded successfully')
except Exception as e:
    print(f'LLaVA download skipped: {e}')
"

# Download Piper voice
echo "Downloading Piper voice..."
mkdir -p ~/.local/share/piper
cd ~/.local/share/piper
curl -L -o en_US-lessac-medium.onnx \
    "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx" 2>/dev/null || echo "Piper voice download skipped"
curl -L -o en_US-lessac-medium.onnx.json \
    "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json" 2>/dev/null || echo "Piper config download skipped"
cd -

echo ""
echo "=== Setup Complete ==="
echo ""
echo "To start DottscavisAI:"
echo "  cd $(pwd)"
echo "  source venv/bin/activate"
echo "  python router/creative_router.py"
echo ""
echo "Or use the systemd-like service:"
echo "  ./scripts/start.sh"
echo ""
echo "Configure BenchAI connection in config/settings.json"
