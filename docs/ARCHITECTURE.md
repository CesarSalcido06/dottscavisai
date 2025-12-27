# DottscavisAI Architecture

## Overview

DottscavisAI is the **Creative Agent** in the BenchAI multi-agent ecosystem, running on M1 Pro Mac hardware.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        USER / OPEN WEB UI                                │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            BENCHAI                                       │
│                    (Orchestrator / Big Brain)                            │
│                      Linux Server - RTX 3060                             │
│                                                                          │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────────┐  │
│   │ Task Router  │  │   Memory     │  │      Semantic Routing        │  │
│   │              │──│   System     │──│  "generate image" → Dotts    │  │
│   │              │  │              │  │  "analyze photo" → Dotts     │  │
│   └──────────────┘  └──────────────┘  │  "debug code" → Marunochi    │  │
│          │                            └──────────────────────────────┘  │
└──────────┼──────────────────────────────────────────────────────────────┘
           │
           │ A2A Protocol
           │
     ┌─────┴─────┬─────────────────────┐
     │           │                     │
     ▼           ▼                     ▼
┌─────────┐ ┌─────────┐        ┌─────────────────┐
│Marunochi│ │ Dotts-  │        │   Future        │
│   AI    │ │ cavisAI │        │   Agents        │
│  (Code) │ │(Creative│        │                 │
│ M4 Pro  │ │ M1 Pro  │        │                 │
└─────────┘ └─────────┘        └─────────────────┘
```

## System Components

### 1. Creative Router (`creative_router.py`)

FastAPI-based router handling:
- OpenAI-compatible `/v1/chat/completions`
- Vision analysis `/v1/vision/analyze`
- Image generation `/v1/images/generate`
- Text-to-speech `/v1/audio/speech`
- A2A task handling `/v1/a2a/task`
- Knowledge sync `/v1/sync/receive`

### 2. Model Management

Models are loaded lazily (on-demand) to conserve memory:

```python
# Vision loaded when needed
if not vision_model:
    vision_model = load("mlx-community/llava-1.5-7b-4bit")

# SD loaded when needed
if not sd_pipe:
    sd_pipe = StableDiffusionPipeline.from_pretrained(...)
```

### 3. A2A Protocol Integration

#### Receiving Tasks from BenchAI

```json
POST /v1/a2a/task
{
    "from_agent": "benchai",
    "task_type": "image_gen",
    "task_description": "A cyberpunk cityscape at night",
    "context": {
        "style": "detailed",
        "negative_prompt": "blurry, low quality"
    }
}
```

#### Reporting Results

```json
POST benchai:8085/v1/learning/collective/contribute
{
    "from_agent": "dottscavisAI",
    "task_id": "abc123",
    "result": "/path/to/generated/image.png",
    "success": true
}
```

## Memory Budget (16GB M1 Pro)

| Component | Memory | Notes |
|-----------|--------|-------|
| System + macOS | ~4GB | Always reserved |
| LLaVA 7B 4-bit | ~4GB | Vision model |
| Stable Diffusion | ~4GB | When generating |
| Piper TTS | ~0.5GB | Very light |
| **Buffer** | ~3.5GB | For flexibility |

**Strategy**: Run one large model at a time, swap as needed.

## API Reference

### Health Check
```
GET /health
```

### Agent Discovery (A2A)
```
GET /.well-known/agent.json
```

### Vision Analysis
```
POST /v1/vision/analyze
{
    "image": "<base64>",
    "prompt": "Describe this image"
}
```

### Image Generation
```
POST /v1/images/generate
{
    "prompt": "A beautiful sunset over mountains",
    "width": 512,
    "height": 512,
    "steps": 20
}
```

### Text-to-Speech
```
POST /v1/audio/speech
{
    "text": "Hello, this is DottscavisAI speaking.",
    "voice": "en_US-lessac-medium"
}
```

## Deployment

### On M1 Pro Mac

```bash
# Clone
git clone https://github.com/CesarSalcido06/dottscavisai.git
cd dottscavisai

# Setup (installs dependencies, downloads models)
./scripts/setup.sh

# Configure BenchAI URL
vim config/settings.json

# Start
./scripts/start.sh
```

### As LaunchAgent (Auto-start)

```xml
<!-- ~/Library/LaunchAgents/com.dottscavisai.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.dottscavisai</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/yourname/dottscavisai/scripts/start.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>/Users/yourname/dottscavisai</string>
</dict>
</plist>
```

## Network Configuration

For BenchAI to reach DottscavisAI across the network:

1. **Static IP or mDNS**: Set up `dottscavisai.local` or static IP
2. **Firewall**: Allow port 8766
3. **BenchAI Config**: Update MODELS in `llm_router.py`:

```python
EXTERNAL_AGENTS = {
    "dottscavisAI": {
        "url": "http://dottscavisai.local:8766",
        "capabilities": ["vision", "image_gen", "tts"]
    }
}
```

---

*Part of the BenchAI Multi-Agent System*
