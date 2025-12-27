# DottscavisAI

**The Creative Agent** - Part of the BenchAI Multi-Agent System

DottscavisAI is a specialized creative AI agent running on M1 Pro Mac, designed for:
- 🎨 Image Generation & Manipulation
- 🎬 Video Generation
- 🎵 Audio/Music Generation
- 🗣️ Text-to-Speech
- 👁️ Vision Analysis & OCR

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    BENCHAI MULTI-AGENT SYSTEM               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │  BenchAI    │◄──►│ MarunochiAI  │    │ DottscavisAI │   │
│  │ (Big Brain) │    │ (Code Expert)│    │ (Creative)   │   │
│  │ Linux/3060  │    │ M4 Pro Mac   │    │ M1 Pro Mac   │   │
│  └─────────────┘    └──────────────┘    └──────────────┘   │
│        │                   │                   │           │
│        └───────────────────┴───────────────────┘           │
│                    A2A Protocol                             │
└─────────────────────────────────────────────────────────────┘
```

## Capabilities

| Capability | Model | Status |
|------------|-------|--------|
| Image Gen | Stable Diffusion XL | 🔄 Planned |
| Vision | Qwen2-VL / LLaVA | 🔄 Planned |
| TTS | Piper / Coqui | 🔄 Planned |
| Audio Gen | MusicGen | 🔄 Planned |

## A2A Integration

DottscavisAI communicates with BenchAI using the Agent-to-Agent (A2A) protocol:

- **Receives**: Creative tasks from BenchAI
- **Reports**: Task completions back to BenchAI
- **Syncs**: Learns from collective knowledge

## Setup

```bash
# On M1 Pro Mac
./scripts/setup.sh
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `/health` | Health check |
| `/.well-known/agent.json` | Agent discovery card |
| `/v1/chat/completions` | OpenAI-compatible chat |
| `/v1/images/generate` | Image generation |
| `/v1/audio/speech` | Text-to-speech |
| `/v1/vision/analyze` | Vision analysis |
| `/v1/a2a/task` | Receive tasks from BenchAI |
| `/v1/sync/receive` | Receive knowledge sync |

---

*Part of the BenchAI Multi-Agent System*
