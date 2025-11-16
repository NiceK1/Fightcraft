"""FastAPI server for AI generation backend."""
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import List, Optional
import random
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_backend.sprite_gen import SpriteGenerator
from ai_backend.stats_gen import StatsGenerator
from ai_backend.cache import SpriteCache, StatsCache


app = FastAPI(title="Fightcraft AI Backend")

# Initialize generators and caches with AI enabled
# Will auto-fall back to procedural generation if API keys are not found
sprite_gen = SpriteGenerator(use_ai=True, ai_provider="openai")  # or "replicate" or "comfyui"
stats_gen = StatsGenerator(use_ai=True, ai_provider="openai")  # or "anthropic"
sprite_cache = SpriteCache()
stats_cache = StatsCache()


class SpriteRequest(BaseModel):
    """Request model for sprite generation."""
    materials: List[str]
    item_type: str
    seed: Optional[int] = None
    weapon_subtype: Optional[str] = None


class StatsRequest(BaseModel):
    """Request model for stats generation."""
    materials: List[str]
    item_type: Optional[str] = None
    weapon_subtype: Optional[str] = None


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Fightcraft AI Backend",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/generate_sprite")
async def generate_sprite(request: SpriteRequest):
    """Generate a sprite for an item."""
    try:
        # Validate materials
        if not request.materials:
            raise HTTPException(status_code=400, detail="Materials list cannot be empty")

        # Generate new sprite (no caching - each craft is unique)
        print(f"Generating sprite: {request.materials} -> {request.item_type} (subtype: {request.weapon_subtype})")
        sprite_data = sprite_gen.generate(
            request.materials,
            request.item_type,
            request.seed,
            request.weapon_subtype
        )

        return Response(content=sprite_data, media_type="image/png")

    except Exception as e:
        print(f"Error generating sprite: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate_stats")
async def generate_stats(request: StatsRequest):
    """Generate stats for an item."""
    try:
        # Validate materials
        if not request.materials:
            raise HTTPException(status_code=400, detail="Materials list cannot be empty")

        # Generate new stats (no caching - each craft is unique)
        print(f"Generating stats: {request.materials} -> {request.item_type} (subtype: {request.weapon_subtype})")
        stats = stats_gen.generate(request.materials, request.item_type, request.weapon_subtype)

        return stats

    except Exception as e:
        print(f"Error generating stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    print("Starting Fightcraft AI Backend Server...")
    print("Server will be available at http://localhost:8000")
    print("API docs available at http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
