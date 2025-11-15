"""AI client for communicating with the backend server."""
import pygame
import requests
import io
import threading
from typing import Optional, Callable, List
from game.item import Item, ItemStats, ItemType, Rarity


class AIClient:
    """Client for requesting AI-generated sprites and stats."""

    def __init__(self, backend_url: str = "http://localhost:8000"):
        self.backend_url = backend_url
        self.session = requests.Session()

    def generate_item_async(
        self,
        materials: List[str],
        item_type: Optional[ItemType],
        callback: Callable[[Item], None],
        seed: Optional[int] = None
    ):
        """Generate item with AI (sprites and stats) asynchronously."""

        def generate():
            try:
                item = self.generate_item(materials, item_type, seed)
                callback(item)
            except Exception as e:
                print(f"Error generating item: {e}")
                # Create fallback item on error
                fallback_item = self._create_fallback_item(materials, item_type)
                callback(fallback_item)

        thread = threading.Thread(target=generate, daemon=True)
        thread.start()

    def generate_item(
        self,
        materials: List[str],
        item_type: Optional[ItemType],
        seed: Optional[int] = None
    ) -> Item:
        """Generate item with AI (sprites and stats) synchronously."""
        try:
            # Request stats generation first (backend will determine item type)
            stats_data = self._request_stats(materials, item_type)

            # Get item type from stats response (backend decides)
            determined_type_str = stats_data.get("item_type", "weapon")
            determined_type = self._parse_item_type(determined_type_str)

            # Request sprite generation with determined type
            sprite = self._request_sprite(materials, determined_type, seed)

            # Create item from AI-generated data
            item = Item(
                name=stats_data.get("name", "Unknown Item"),
                item_type=determined_type,
                sprite=sprite,
                stats=ItemStats(
                    damage=stats_data.get("damage", 0),
                    armor=stats_data.get("armor", 0),
                    speed=stats_data.get("speed", 1.0),
                    health=stats_data.get("health", 0),
                    special_effect=stats_data.get("special_effect", "")
                ),
                rarity=self._parse_rarity(stats_data.get("rarity", "common")),
                materials=materials,
                description=stats_data.get("description", ""),
                generation_method=stats_data.get("generation_method", "Unknown")
            )
            return item

        except Exception as e:
            print(f"Error in generate_item: {e}")
            import traceback
            traceback.print_exc()
            return self._create_fallback_item(materials, item_type or ItemType.WEAPON)

    def _request_sprite(
        self,
        materials: List[str],
        item_type: ItemType,
        seed: Optional[int] = None
    ) -> pygame.Surface:
        """Request sprite generation from backend."""
        try:
            response = self.session.post(
                f"{self.backend_url}/generate_sprite",
                json={
                    "materials": materials,
                    "item_type": item_type.value,
                    "seed": seed
                },
                timeout=30
            )
            response.raise_for_status()

            # Load image from response
            image_data = response.content
            image = pygame.image.load(io.BytesIO(image_data))
            return image

        except Exception as e:
            print(f"Error requesting sprite: {e}")
            # Return placeholder sprite
            return self._create_placeholder_sprite()

    def _request_stats(
        self,
        materials: List[str],
        item_type: Optional[ItemType]
    ) -> dict:
        """Request stats generation from backend."""
        try:
            response = self.session.post(
                f"{self.backend_url}/generate_stats",
                json={
                    "materials": materials,
                    "item_type": item_type.value if item_type else None
                },
                timeout=10
            )
            response.raise_for_status()
            return response.json()

        except Exception as e:
            print(f"Error requesting stats: {e}")
            # Return default stats
            return self._create_default_stats(materials, item_type or ItemType.WEAPON)

    def _create_placeholder_sprite(self) -> pygame.Surface:
        """Create a placeholder sprite when AI generation fails."""
        sprite = pygame.Surface((64, 64))
        sprite.fill((100, 100, 150))
        pygame.draw.rect(sprite, (200, 200, 200), (0, 0, 64, 64), 3)
        # Draw question mark
        font = pygame.font.Font(None, 48)
        text = font.render("?", True, (255, 255, 255))
        text_rect = text.get_rect(center=(32, 32))
        sprite.blit(text, text_rect)
        return sprite

    def _create_default_stats(self, materials: List[str], item_type: ItemType) -> dict:
        """Create default stats when AI generation fails."""
        material_str = " + ".join(materials)

        base_stats = {
            ItemType.WEAPON: {"damage": 10, "armor": 0, "speed": 1.0},
            ItemType.ARMOR: {"damage": 0, "armor": 10, "speed": 0.9},
            ItemType.CONCOCTION: {"damage": 0, "armor": 0, "health": 20, "speed": 1.0}
        }

        stats = base_stats.get(item_type, {"damage": 5, "armor": 5, "speed": 1.0})

        return {
            "name": f"{material_str} {item_type.value.capitalize()}",
            "damage": stats.get("damage", 0),
            "armor": stats.get("armor", 0),
            "speed": stats.get("speed", 1.0),
            "health": stats.get("health", 0),
            "special_effect": "",
            "rarity": "common",
            "description": f"Crafted from {material_str}"
        }

    def _create_fallback_item(self, materials: List[str], item_type: ItemType) -> Item:
        """Create fallback item when AI generation fails."""
        stats_data = self._create_default_stats(materials, item_type)
        sprite = self._create_placeholder_sprite()

        return Item(
            name=stats_data["name"],
            item_type=item_type,
            sprite=sprite,
            stats=ItemStats(
                damage=stats_data["damage"],
                armor=stats_data["armor"],
                speed=stats_data["speed"],
                health=stats_data["health"],
                special_effect=stats_data["special_effect"]
            ),
            rarity=Rarity.COMMON,
            materials=materials,
            description=stats_data["description"],
            generation_method="Fallback (Error)"
        )

    def _parse_rarity(self, rarity_str: str) -> Rarity:
        """Parse rarity string to Rarity enum."""
        rarity_map = {
            "common": Rarity.COMMON,
            "uncommon": Rarity.UNCOMMON,
            "rare": Rarity.RARE,
            "epic": Rarity.EPIC,
            "legendary": Rarity.LEGENDARY
        }
        return rarity_map.get(rarity_str.lower(), Rarity.COMMON)

    def _parse_item_type(self, type_str: str) -> ItemType:
        """Parse item type string to ItemType enum."""
        type_map = {
            "weapon": ItemType.WEAPON,
            "armor": ItemType.ARMOR,
            "concoction": ItemType.CONCOCTION,
            "material": ItemType.MATERIAL
        }
        return type_map.get(type_str.lower(), ItemType.WEAPON)

    def check_backend_health(self) -> bool:
        """Check if backend server is running."""
        try:
            response = self.session.get(f"{self.backend_url}/health", timeout=2)
            return response.status_code == 200
        except:
            return False
