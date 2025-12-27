#!/usr/bin/env python3
"""
DottscavisAI - Creative Agent Router
Part of the BenchAI Multi-Agent System

Specializes in:
- Vision Analysis (MLX-VLM / LLaVA)
- Image Generation (Stable Diffusion)
- Text-to-Speech (Piper)
- Audio Generation (MusicGen)
"""

import asyncio
import base64
import hashlib
import json
import os
import subprocess
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel

# --- Configuration ---

BENCHAI_URL = os.getenv("BENCHAI_URL", "http://benchai.local:8085")
AGENT_ID = "dottscavisAI"
AGENT_PORT = 8766

# Model paths (adjust for your setup)
MODELS_DIR = Path.home() / "models"
OUTPUT_DIR = Path.home() / "dottscavisai_output"
OUTPUT_DIR.mkdir(exist_ok=True)

# --- FastAPI App ---

app = FastAPI(
    title="DottscavisAI",
    description="Creative Agent - Vision, Image Gen, TTS",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Data Models ---

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: Optional[str] = "auto"
    messages: List[ChatMessage]
    max_tokens: Optional[int] = 1000
    temperature: Optional[float] = 0.7
    stream: Optional[bool] = False

class ImageGenRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = ""
    width: Optional[int] = 512
    height: Optional[int] = 512
    steps: Optional[int] = 20
    cfg_scale: Optional[float] = 7.5
    seed: Optional[int] = None

class VisionRequest(BaseModel):
    image: str  # base64 encoded
    prompt: str
    max_tokens: Optional[int] = 500

class TTSRequest(BaseModel):
    text: str
    voice: Optional[str] = "en_US-lessac-medium"
    speed: Optional[float] = 1.0

class A2ATaskRequest(BaseModel):
    from_agent: str
    task_type: str
    task_description: str
    context: Optional[Dict] = {}
    priority: Optional[str] = "normal"
    trace_id: Optional[str] = None

class SyncRequest(BaseModel):
    from_agent: str
    sync_type: str  # experience, knowledge, pattern
    items: List[Dict]

# --- State ---

class AgentState:
    def __init__(self):
        self.status = "initializing"
        self.load = 0.0
        self.capabilities = ["vision", "image_gen", "tts", "audio_gen"]
        self.current_task = None
        self.task_history = []
        self.synced_knowledge = []
        self.models_loaded = {
            "vision": False,
            "image_gen": False,
            "tts": False,
            "llm": False
        }

state = AgentState()

# --- Model Loaders (Lazy) ---

vision_model = None
vision_processor = None
sd_pipe = None
tts_engine = None
llm_model = None

async def load_vision_model():
    """Load MLX-VLM model."""
    global vision_model, vision_processor
    if vision_model is not None:
        return True

    try:
        from mlx_vlm import load
        print("[VISION] Loading LLaVA 1.5 7B...")
        vision_model, vision_processor = load("mlx-community/llava-1.5-7b-4bit")
        state.models_loaded["vision"] = True
        print("[VISION] Model loaded successfully")
        return True
    except ImportError:
        print("[VISION] MLX-VLM not installed, trying fallback...")
        return False
    except Exception as e:
        print(f"[VISION] Load error: {e}")
        return False

async def load_sd_model():
    """Load Stable Diffusion model."""
    global sd_pipe
    if sd_pipe is not None:
        return True

    try:
        # Try MLX Stable Diffusion first
        from mlx_stable_diffusion import StableDiffusion
        print("[SD] Loading Stable Diffusion 2.1...")
        sd_pipe = StableDiffusion()
        state.models_loaded["image_gen"] = True
        print("[SD] Model loaded successfully")
        return True
    except ImportError:
        try:
            # Fallback to diffusers
            from diffusers import StableDiffusionPipeline
            import torch
            print("[SD] Loading via diffusers...")
            sd_pipe = StableDiffusionPipeline.from_pretrained(
                "stabilityai/stable-diffusion-2-1",
                torch_dtype=torch.float16
            )
            sd_pipe = sd_pipe.to("mps")  # Apple Metal
            state.models_loaded["image_gen"] = True
            return True
        except Exception as e:
            print(f"[SD] Load error: {e}")
            return False

async def load_tts_engine():
    """Load Piper TTS."""
    global tts_engine
    if tts_engine is not None:
        return True

    # Check if piper is available
    try:
        result = subprocess.run(["which", "piper"], capture_output=True, text=True)
        if result.returncode == 0:
            state.models_loaded["tts"] = True
            tts_engine = "piper"
            print("[TTS] Piper available")
            return True
    except Exception:
        pass

    # Try Python piper-tts
    try:
        import piper
        state.models_loaded["tts"] = True
        tts_engine = "piper-python"
        print("[TTS] Piper (Python) loaded")
        return True
    except ImportError:
        print("[TTS] Piper not available")
        return False

# --- Core Functions ---

async def analyze_image(image_b64: str, prompt: str) -> str:
    """Analyze image using vision model."""
    if not await load_vision_model():
        return "Vision model not available. Please install mlx-vlm."

    try:
        from mlx_vlm import generate
        import tempfile

        # Decode image
        image_data = base64.b64decode(image_b64)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(image_data)
            image_path = f.name

        # Generate response
        output = generate(vision_model, vision_processor, image_path, prompt)

        # Cleanup
        os.unlink(image_path)

        return output
    except Exception as e:
        return f"Vision analysis error: {e}"

async def generate_image(request: ImageGenRequest) -> str:
    """Generate image using Stable Diffusion."""
    if not await load_sd_model():
        return None

    try:
        seed = request.seed or int(time.time())

        # Generate
        image = sd_pipe(
            prompt=request.prompt,
            negative_prompt=request.negative_prompt,
            width=request.width,
            height=request.height,
            num_inference_steps=request.steps,
            guidance_scale=request.cfg_scale,
            generator=seed
        ).images[0]

        # Save
        filename = f"gen_{int(time.time())}_{seed}.png"
        filepath = OUTPUT_DIR / filename
        image.save(filepath)

        return str(filepath)
    except Exception as e:
        print(f"[SD] Generation error: {e}")
        return None

async def text_to_speech(text: str, voice: str = "en_US-lessac-medium") -> str:
    """Convert text to speech using Piper."""
    if not await load_tts_engine():
        return None

    try:
        filename = f"tts_{int(time.time())}.wav"
        filepath = OUTPUT_DIR / filename

        # Use piper CLI
        result = subprocess.run(
            ["piper", "--model", voice, "--output_file", str(filepath)],
            input=text,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0 and filepath.exists():
            return str(filepath)
        else:
            print(f"[TTS] Error: {result.stderr}")
            return None
    except Exception as e:
        print(f"[TTS] Error: {e}")
        return None

# --- A2A Communication ---

async def report_to_benchai(task_id: str, result: Any, success: bool):
    """Report task completion to BenchAI."""
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{BENCHAI_URL}/v1/learning/collective/contribute",
                json={
                    "from_agent": AGENT_ID,
                    "task_id": task_id,
                    "result": str(result)[:1000] if result else "",
                    "success": success,
                    "timestamp": datetime.utcnow().isoformat()
                },
                timeout=10
            )
    except Exception as e:
        print(f"[A2A] Failed to report to BenchAI: {e}")

async def send_heartbeat():
    """Send heartbeat to BenchAI."""
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{BENCHAI_URL}/v1/learning/a2a/heartbeat",
                json={
                    "agent_id": AGENT_ID,
                    "status": state.status,
                    "load": state.load,
                    "capabilities": state.capabilities,
                    "models_loaded": state.models_loaded
                },
                timeout=5
            )
    except Exception:
        pass  # Heartbeat failures are not critical

# --- API Endpoints ---

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "dottscavisai",
        "version": "1.0.0",
        "models": state.models_loaded,
        "load": state.load
    }

@app.get("/.well-known/agent.json")
async def agent_card():
    """A2A Agent Discovery Card."""
    return {
        "name": "DottscavisAI",
        "description": "Creative AI Agent - Vision, Image Generation, TTS",
        "version": "1.0.0",
        "url": f"http://dottscavisai.local:{AGENT_PORT}",
        "capabilities": {
            "vision": {
                "models": ["llava-1.5-7b"],
                "formats": ["png", "jpg", "webp"]
            },
            "image_gen": {
                "models": ["stable-diffusion-2.1"],
                "max_resolution": "1024x1024"
            },
            "tts": {
                "models": ["piper"],
                "languages": ["en", "es", "fr", "de"]
            },
            "streaming": True
        },
        "endpoints": {
            "chat": "/v1/chat/completions",
            "vision": "/v1/vision/analyze",
            "image_gen": "/v1/images/generate",
            "tts": "/v1/audio/speech",
            "a2a_task": "/v1/a2a/task",
            "sync": "/v1/sync/receive"
        },
        "authentication": None,
        "rate_limits": {
            "requests_per_minute": 30,
            "concurrent_tasks": 2
        }
    }

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    """OpenAI-compatible chat endpoint."""
    last_message = request.messages[-1].content if request.messages else ""

    # Detect intent
    intent = detect_creative_intent(last_message)

    response_content = ""

    if intent == "vision":
        # Extract image from message if present
        response_content = "Please provide an image for analysis. Use the /v1/vision/analyze endpoint."
    elif intent == "image_gen":
        response_content = "To generate an image, use the /v1/images/generate endpoint with your prompt."
    elif intent == "tts":
        response_content = "To convert text to speech, use the /v1/audio/speech endpoint."
    else:
        # General creative response
        response_content = "I'm DottscavisAI, the creative agent. I can help with:\n" \
                          "- Image analysis and understanding\n" \
                          "- Image generation (Stable Diffusion)\n" \
                          "- Text-to-speech\n" \
                          "- Audio generation\n\n" \
                          "What would you like to create?"

    return {
        "id": f"chatcmpl-{int(time.time())}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": "dottscavisai",
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": response_content},
            "finish_reason": "stop"
        }]
    }

@app.post("/v1/vision/analyze")
async def vision_analyze(request: VisionRequest):
    """Analyze an image with vision model."""
    state.load = 0.8
    state.current_task = "vision_analysis"

    try:
        result = await analyze_image(request.image, request.prompt)
        state.load = 0.0
        state.current_task = None

        return {
            "status": "success",
            "analysis": result
        }
    except Exception as e:
        state.load = 0.0
        state.current_task = None
        raise HTTPException(500, f"Vision analysis failed: {e}")

@app.post("/v1/images/generate")
async def images_generate(request: ImageGenRequest):
    """Generate an image with Stable Diffusion."""
    state.load = 0.9
    state.current_task = "image_generation"

    try:
        filepath = await generate_image(request)
        state.load = 0.0
        state.current_task = None

        if filepath:
            # Return as base64
            with open(filepath, "rb") as f:
                image_b64 = base64.b64encode(f.read()).decode()

            return {
                "status": "success",
                "image": image_b64,
                "path": filepath,
                "seed": request.seed
            }
        else:
            raise HTTPException(500, "Image generation failed")
    except Exception as e:
        state.load = 0.0
        state.current_task = None
        raise HTTPException(500, f"Image generation failed: {e}")

@app.post("/v1/audio/speech")
async def audio_speech(request: TTSRequest):
    """Convert text to speech."""
    state.load = 0.5
    state.current_task = "tts"

    try:
        filepath = await text_to_speech(request.text, request.voice)
        state.load = 0.0
        state.current_task = None

        if filepath:
            return FileResponse(
                filepath,
                media_type="audio/wav",
                filename=Path(filepath).name
            )
        else:
            raise HTTPException(500, "TTS failed")
    except Exception as e:
        state.load = 0.0
        state.current_task = None
        raise HTTPException(500, f"TTS failed: {e}")

@app.post("/v1/a2a/task")
async def receive_a2a_task(request: A2ATaskRequest):
    """Receive task from BenchAI or other agents."""
    task_id = request.trace_id or str(uuid.uuid4())

    print(f"[A2A] Received task from {request.from_agent}: {request.task_type}")
    print(f"[A2A] Description: {request.task_description[:100]}...")

    state.current_task = request.task_type
    state.load = 0.7

    result = None
    success = False

    try:
        if request.task_type == "vision" or request.task_type == "image_analysis":
            # Extract image from context
            image_b64 = request.context.get("image", "")
            if image_b64:
                result = await analyze_image(image_b64, request.task_description)
                success = True
            else:
                result = "No image provided in context"

        elif request.task_type == "image_gen":
            img_request = ImageGenRequest(
                prompt=request.task_description,
                negative_prompt=request.context.get("negative_prompt", "")
            )
            filepath = await generate_image(img_request)
            if filepath:
                result = filepath
                success = True
            else:
                result = "Image generation failed"

        elif request.task_type == "tts":
            filepath = await text_to_speech(
                request.task_description,
                request.context.get("voice", "en_US-lessac-medium")
            )
            if filepath:
                result = filepath
                success = True
            else:
                result = "TTS failed"

        else:
            result = f"Unknown task type: {request.task_type}"

        state.task_history.append({
            "task_id": task_id,
            "from": request.from_agent,
            "type": request.task_type,
            "success": success,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Report back to BenchAI
        await report_to_benchai(task_id, result, success)

    except Exception as e:
        result = str(e)
        success = False
    finally:
        state.load = 0.0
        state.current_task = None

    return {
        "task_id": task_id,
        "status": "completed" if success else "failed",
        "result": result
    }

@app.post("/v1/sync/receive")
async def receive_sync(request: SyncRequest):
    """Receive knowledge sync from BenchAI."""
    print(f"[SYNC] Received {len(request.items)} items from {request.from_agent}")

    for item in request.items:
        state.synced_knowledge.append({
            "from": request.from_agent,
            "type": request.sync_type,
            "content": item.get("content", ""),
            "timestamp": datetime.utcnow().isoformat()
        })

    # Keep only last 100 items
    state.synced_knowledge = state.synced_knowledge[-100:]

    return {
        "status": "received",
        "items_stored": len(request.items)
    }

@app.get("/v1/sync/share")
async def share_sync(requester: str, sync_type: str = "experience"):
    """Share knowledge with requesting agent."""
    # Filter relevant items
    items = [
        item for item in state.synced_knowledge
        if item["type"] == sync_type
    ][-20:]  # Last 20 items

    return {
        "from_agent": AGENT_ID,
        "sync_type": sync_type,
        "items": items
    }

# --- Helpers ---

def detect_creative_intent(text: str) -> str:
    """Detect the creative intent from text."""
    text_lower = text.lower()

    if any(w in text_lower for w in ["analyze", "describe", "what is in", "look at", "see"]):
        return "vision"
    if any(w in text_lower for w in ["generate", "create", "draw", "paint", "make image"]):
        return "image_gen"
    if any(w in text_lower for w in ["speak", "say", "read aloud", "tts", "voice"]):
        return "tts"

    return "general"

# --- Startup ---

@app.on_event("startup")
async def startup():
    state.status = "online"
    print(f"[DOTTSCAVISAI] Creative Agent started on port {AGENT_PORT}")
    print(f"[DOTTSCAVISAI] BenchAI URL: {BENCHAI_URL}")

    # Send initial heartbeat
    await send_heartbeat()

    # Start heartbeat loop
    asyncio.create_task(heartbeat_loop())

async def heartbeat_loop():
    """Send periodic heartbeats to BenchAI."""
    while True:
        await asyncio.sleep(30)
        await send_heartbeat()

# --- Main ---

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=AGENT_PORT)
