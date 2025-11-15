"""Sprite generation module with AI integration."""
import io
import random
import os
from PIL import Image, ImageDraw, ImageFont
from typing import List, Optional
import requests


class SpriteGenerator:
    """Generates sprites using AI or fallback methods."""

    def __init__(self, use_ai: bool = True, ai_provider: str = "replicate"):
        """
        Initialize sprite generator.

        Args:
            use_ai: Whether to use AI for generation
            ai_provider: 'replicate', 'openai', or 'comfyui'
        """
        self.use_ai = use_ai
        self.ai_provider = ai_provider
        self.client = None

        if not use_ai:
            return

        # Try Replicate first (easiest)
        if ai_provider == "replicate":
            try:
                import replicate
                api_token = os.getenv("REPLICATE_API_TOKEN")
                if api_token:
                    os.environ["REPLICATE_API_TOKEN"] = api_token
                    self.client = replicate
                    print("[OK] Replicate API initialized for sprite generation")
                else:
                    print("REPLICATE_API_TOKEN not found, using fallback sprite generation")
                    self.use_ai = False
            except ImportError:
                print("Replicate package not installed, using fallback sprite generation")
                self.use_ai = False

        # OpenAI DALL-E
        elif ai_provider == "openai":
            try:
                import openai
                api_key = os.getenv("OPENAI_API_KEY")
                if api_key:
                    self.client = openai.OpenAI(api_key=api_key)
                    print("[OK] OpenAI DALL-E initialized for sprite generation")
                else:
                    print("OPENAI_API_KEY not found, using fallback sprite generation")
                    self.use_ai = False
            except ImportError:
                print("OpenAI package not installed, using fallback sprite generation")
                self.use_ai = False

        # Fallback to ComfyUI
        elif ai_provider == "comfyui":
            comfy_url = "http://localhost:8188"
            try:
                response = requests.get(f"{comfy_url}/system_stats", timeout=2)
                if response.status_code == 200:
                    self.comfy_url = comfy_url
                    print(f"[OK] ComfyUI available at {comfy_url}")
                else:
                    print("ComfyUI not available, using fallback sprite generation")
                    self.use_ai = False
            except:
                print("ComfyUI not available, using fallback sprite generation")
                self.use_ai = False

    def generate(
        self,
        materials: List[str],
        item_type: str,
        seed: Optional[int] = None
    ) -> bytes:
        """Generate sprite image and return as PNG bytes."""

        if self.use_ai and self.client:
            try:
                if self.ai_provider == "replicate":
                    img = self._generate_with_replicate(materials, item_type, seed)
                    img = self.remove_bg_photoroom(img)
                    return img

                elif self.ai_provider == "openai":
                    img = self._generate_with_openai(materials, item_type, seed)
                    img = self.remove_bg_photoroom(img)
                    return img

                elif self.ai_provider == "comfyui":
                    img = self._generate_with_comfy(materials, item_type, seed)
                    img = self.remove_bg_photoroom(img)
                    return img
    except Exception as e:
        print(f"AI sprite generation failed: {e}, using fallback")

        # Fallback to procedural generation
        return self._generate_fallback(materials, item_type, seed)

    def _generate_with_replicate(
        self,
        materials: List[str],
        item_type: str,
        seed: Optional[int] = None
    ) -> bytes:
        """Generate sprite using Replicate SDXL."""

        # Create prompt from materials
        prompt = self._create_prompt(materials, item_type)

        # Use SDXL-Turbo for fast generation
        output = self.client.run(
            "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
            input={
                "prompt": prompt,
                "negative_prompt": "blurry, low quality, text, watermark, signature, multiple items, background clutter",
                "width": 512,
                "height": 512,
                "num_inference_steps": 25,
                "guidance_scale": 7.5,
                "seed": seed if seed else random.randint(0, 1000000)
            }
        )

        # Download the image
        image_url = output[0] if isinstance(output, list) else output
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()

        # Load and resize to 128x128 for game use
        image = Image.open(io.BytesIO(response.content))
        image = image.resize((128, 128), Image.Resampling.LANCZOS)

        # Convert to PNG bytes
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        return buffer.getvalue()
        
    def remove_bg_photoroom(self, image_bytes: bytes) -> bytes:
        """Remove background using PhotoRoom API."""
        api_key = os.getenv("PHOTOROOM_API_KEY")
        if not api_key:
            print("PHOTOROOM_API_KEY not found, skipping background removal")
            return image_bytes

        try:
            response = requests.post(
                "https://sdk.photoroom.com/v1/segment",
                headers={"x-api-key": api_key},
                files={"image_file": ("sprite.png", image_bytes, "image/png")},
                timeout=10
            )

            if response.status_code != 200:
                print("PhotoRoom error:", response.text)
                return image_bytes

            return response.content

        except Exception as e:
            print("PhotoRoom background removal failed:", e)
            return image_bytes

    def _generate_with_openai(
        self,
        materials: List[str],
        item_type: str,
        seed: Optional[int] = None
    ) -> bytes:
        """Generate sprite using OpenAI DALL-E."""

        # Create prompt from materials
        prompt = self._create_prompt(materials, item_type)

        # Add more specific instructions for DALL-E to get game-like sprites
        prompt = f"pixel art game sprite, {prompt}, isolated on white background, top-down view, simple design, video game asset"

        # Use DALL-E 2 for generation (cheaper, no quality parameter)
        response = self.client.images.generate(
            model="dall-e-2",
            prompt=prompt,
            size="1024x1024",
            n=1,
        )

        # Download the image
        image_url = response.data[0].url
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()

        # Load and resize to 128x128 for game use
        image = Image.open(io.BytesIO(response.content))
        image = image.resize((128, 128), Image.Resampling.LANCZOS)

        # Convert to PNG bytes
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        return buffer.getvalue()

    def _generate_with_comfy(
        self,
        materials: List[str],
        item_type: str,
        seed: Optional[int] = None
    ) -> bytes:
        """Generate sprite using ComfyUI with SDXL-Turbo."""

        # Create prompt from materials
        prompt = self._create_prompt(materials, item_type)

        # This is a simplified example. In production, you would:
        # 1. Load a ComfyUI workflow JSON
        # 2. Modify the prompt and seed
        # 3. Queue the workflow
        # 4. Wait for completion
        # 5. Download the result

        workflow = {
            "3": {
                "inputs": {
                    "seed": seed if seed else random.randint(0, 1000000),
                    "steps": 4,
                    "cfg": 1.0,
                    "sampler_name": "lcm",
                    "scheduler": "sgm_uniform",
                    "denoise": 1.0,
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["5", 0]
                },
                "class_type": "KSampler"
            },
            "4": {
                "inputs": {
                    "ckpt_name": "sdxl_turbo.safetensors"
                },
                "class_type": "CheckpointLoaderSimple"
            },
            "5": {
                "inputs": {
                    "width": 512,
                    "height": 512,
                    "batch_size": 1
                },
                "class_type": "EmptyLatentImage"
            },
            "6": {
                "inputs": {
                    "text": prompt,
                    "clip": ["4", 1]
                },
                "class_type": "CLIPTextEncode"
            },
            "7": {
                "inputs": {
                    "text": "blurry, low quality, text, watermark, signature",
                    "clip": ["4", 1]
                },
                "class_type": "CLIPTextEncode"
            },
            "8": {
                "inputs": {
                    "samples": ["3", 0],
                    "vae": ["4", 2]
                },
                "class_type": "VAEDecode"
            },
            "9": {
                "inputs": {
                    "filename_prefix": "fightcraft",
                    "images": ["8", 0]
                },
                "class_type": "SaveImage"
            }
        }

        # Queue the prompt
        response = requests.post(
            f"{self.comfy_url}/prompt",
            json={"prompt": workflow},
            timeout=5
        )
        response.raise_for_status()
        prompt_id = response.json()["prompt_id"]

        # Wait for completion and get image (simplified)
        # In production, you'd poll the history endpoint
        # For now, raise an exception to use fallback
        raise NotImplementedError("ComfyUI workflow needs to be configured")

    def _create_prompt(self, materials: List[str], item_type: str) -> str:
        """Create AI prompt from materials and item type."""
        materials_str = ", ".join(materials).lower()

        prompts = {
            "weapon": f"pixel art game sprite, RPG {item_type}, fantasy weapon made from {materials_str}, "
                     f"centered on white background, isometric view, 64x64 pixels, detailed, clean lines",
            "armor": f"pixel art game sprite, RPG {item_type}, fantasy armor made from {materials_str}, "
                    f"centered on white background, isometric view, 64x64 pixels, detailed, clean lines",
            "concoction": f"pixel art game sprite, fantasy RPG health restore bottle made from {materials_str}, "
                         f"magical glowing flask, video game powerup collectible, cartoon style healing item, "
                         f"centered on white background, isometric view, 64x64 pixels, detailed, clean lines, bright friendly colors"
        }

        return prompts.get(item_type, f"pixel art game sprite, {item_type} made from {materials_str}")

    def _generate_fallback(
        self,
        materials: List[str],
        item_type: str,
        seed: Optional[int] = None
    ) -> bytes:
        """Generate procedural sprite as fallback."""

        if seed:
            random.seed(seed)

        # Create 128x128 image for better quality
        size = 128
        img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)

        # Generate colors from materials
        colors = self._get_material_colors(materials)

        # Draw based on item type
        if item_type == "weapon":
            self._draw_weapon(draw, size, colors)
        elif item_type == "armor":
            self._draw_armor(draw, size, colors)
        elif item_type == "concoction":
            self._draw_concoction(draw, size, colors)
        else:
            self._draw_generic(draw, size, colors)

        # Convert to PNG bytes
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()

    def _get_material_colors(self, materials: List[str]) -> List[tuple]:
        """Get colors based on material names."""
        color_map = {
            "iron": (150, 150, 150),
            "wood": (139, 90, 43),
            "oak": (139, 90, 43),
            "dragon": (200, 50, 50),
            "scale": (180, 60, 60),
            "crystal": (100, 200, 255),
            "shard": (150, 220, 255),
            "dark": (60, 60, 80),
            "stone": (100, 100, 100),
            "gold": (255, 215, 0),
            "bar": (255, 215, 0),
            "leather": (160, 120, 70),
            "magic": (200, 100, 255),
            "essence": (220, 150, 255),
        }

        colors = []
        for material in materials:
            material_lower = material.lower()
            # Find matching color
            color = None
            for key, val in color_map.items():
                if key in material_lower:
                    color = val
                    break
            if color:
                colors.append(color)
            else:
                # Generate random color
                colors.append((random.randint(100, 255), random.randint(100, 255), random.randint(100, 255)))

        return colors if colors else [(150, 150, 150)]

    def _draw_weapon(self, draw: ImageDraw.Draw, size: int, colors: List[tuple]):
        """Draw a stylized weapon."""
        center = size // 2

        # Draw blade (main part)
        blade_points = [
            (center, center - 40),
            (center + 8, center + 10),
            (center - 8, center + 10)
        ]
        draw.polygon(blade_points, fill=colors[0])
        draw.line(blade_points + [blade_points[0]], fill=(0, 0, 0), width=2)

        # Draw handle
        handle_color = colors[1] if len(colors) > 1 else colors[0]
        draw.rectangle([center - 5, center + 10, center + 5, center + 35], fill=handle_color, outline=(0, 0, 0), width=2)

        # Draw guard
        guard_color = colors[2] if len(colors) > 2 else colors[0]
        draw.rectangle([center - 15, center + 8, center + 15, center + 14], fill=guard_color, outline=(0, 0, 0), width=2)

    def _draw_armor(self, draw: ImageDraw.Draw, size: int, colors: List[tuple]):
        """Draw a stylized armor piece."""
        center = size // 2

        # Draw main body (chestplate shape)
        body_points = [
            (center, center - 30),
            (center + 25, center - 10),
            (center + 20, center + 30),
            (center - 20, center + 30),
            (center - 25, center - 10)
        ]
        draw.polygon(body_points, fill=colors[0])
        draw.line(body_points + [body_points[0]], fill=(0, 0, 0), width=2)

        # Draw decorative elements
        if len(colors) > 1:
            draw.ellipse([center - 8, center - 10, center + 8, center + 10], fill=colors[1], outline=(0, 0, 0), width=2)

    def _draw_concoction(self, draw: ImageDraw.Draw, size: int, colors: List[tuple]):
        """Draw a stylized potion/concoction."""
        center = size // 2

        # Draw bottle body
        bottle_points = [
            (center - 15, center + 30),
            (center - 15, center),
            (center - 10, center - 15),
            (center - 8, center - 25),
            (center + 8, center - 25),
            (center + 10, center - 15),
            (center + 15, center),
            (center + 15, center + 30)
        ]
        draw.polygon(bottle_points, fill=colors[0])
        draw.line(bottle_points + [bottle_points[0]], fill=(0, 0, 0), width=2)

        # Draw cork/stopper
        stopper_color = colors[1] if len(colors) > 1 else (100, 70, 50)
        draw.rectangle([center - 5, center - 30, center + 5, center - 24], fill=stopper_color, outline=(0, 0, 0), width=2)

        # Add shine effect
        draw.ellipse([center - 5, center - 10, center + 5, center], fill=(255, 255, 255, 150))

    def _draw_generic(self, draw: ImageDraw.Draw, size: int, colors: List[tuple]):
        """Draw a generic item."""
        center = size // 2
        draw.ellipse([center - 30, center - 30, center + 30, center + 30], fill=colors[0], outline=(0, 0, 0), width=3)
