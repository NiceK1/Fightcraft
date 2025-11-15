"""Item system for Fightcraft."""
import pygame
from typing import Optional, List
from dataclasses import dataclass, field
from enum import Enum


class ItemType(Enum):
    """Types of items in the game."""
    MATERIAL = "material"
    WEAPON = "weapon"
    ARMOR = "armor"
    CONCOCTION = "concoction"


class Rarity(Enum):
    """Item rarity levels."""
    COMMON = ("common", (200, 200, 200))
    UNCOMMON = ("uncommon", (100, 255, 100))
    RARE = ("rare", (100, 100, 255))
    EPIC = ("epic", (200, 100, 255))
    LEGENDARY = ("legendary", (255, 200, 50))

    def __init__(self, name: str, color: tuple):
        self._name = name
        self.color = color


@dataclass
class ItemStats:
    """Stats for crafted items."""
    damage: int = 0
    armor: int = 0
    speed: float = 1.0
    health: int = 0
    special_effect: str = ""


@dataclass
class Item:
    """Represents an item in the game."""
    name: str
    item_type: ItemType
    sprite: Optional[pygame.Surface] = None
    stats: ItemStats = field(default_factory=ItemStats)
    rarity: Rarity = Rarity.COMMON
    materials: List[str] = field(default_factory=list)
    description: str = ""
    generation_method: str = "Unknown"

    def render(self, surface: pygame.Surface, x: int, y: int, size: int = 64):
        """Render the item sprite at given position."""
        if self.sprite:
            # Scale sprite to fit slot
            scaled_sprite = pygame.transform.scale(self.sprite, (size, size))
            surface.blit(scaled_sprite, (x, y))
        else:
            # Draw placeholder if no sprite
            pygame.draw.rect(surface, (100, 100, 100), (x, y, size, size))
            pygame.draw.rect(surface, (150, 150, 150), (x, y, size, size), 2)

    def get_tooltip_text(self) -> List[str]:
        """Get formatted tooltip text for the item."""
        lines = [
            self.name,
            f"Type: {self.item_type.value.capitalize()}",
            f"Rarity: {self.rarity._name.capitalize()}",
            ""
        ]

        if self.stats.damage > 0:
            lines.append(f"Damage: {self.stats.damage}")
        if self.stats.armor > 0:
            lines.append(f"Armor: {self.stats.armor}")
        if self.stats.health > 0:
            lines.append(f"Health: {self.stats.health}")
        if self.stats.speed != 1.0:
            lines.append(f"Speed: {self.stats.speed:.1f}x")
        if self.stats.special_effect:
            lines.append(f"Effect: {self.stats.special_effect}")

        if self.description:
            lines.append("")
            lines.append(self.description)

        return lines


class Recipe:
    """Crafting recipe defining material combinations."""

    def __init__(self, materials: List[str], result_type: ItemType):
        self.materials = sorted(materials)  # Sort for consistent matching
        self.result_type = result_type

    def matches(self, materials: List[str]) -> bool:
        """Check if given materials match this recipe."""
        return sorted(materials) == self.materials


# Pre-defined base materials
def create_base_materials() -> List[Item]:
    """Create categorized crafting materials."""
    materials = []

    # WEAPON MATERIALS - Metals, sharp, offensive
    weapon_materials = [
        ("Steel Ingot", (180, 180, 190)),
        ("Iron Blade", (140, 140, 150)),
        ("Dragon Shard", (220, 60, 60)),
        ("Obsidian Shard", (50, 50, 60)),
        ("Mithril Bar", (180, 220, 255)),
        ("Dark Crystal", (140, 40, 80)),
    ]

    # ARMOR MATERIALS - Protective, defensive
    armor_materials = [
        ("Thick Leather", (140, 100, 60)),
        ("Steel Plate", (170, 170, 175)),
        ("Dragon Scale", (200, 80, 80)),
        ("Reinforced Wood", (120, 80, 40)),
        ("Titanium Sheet", (200, 200, 210)),
        ("Stone Shield", (100, 100, 110)),
    ]

    # CONCOCTION MATERIALS - Magical, organic, alchemical
    concoction_materials = [
        ("Magic Essence", (200, 100, 255)),
        ("Crystal Powder", (150, 220, 255)),
        ("Phoenix Feather", (255, 180, 80)),
        ("Moonflower", (220, 220, 255)),
        ("Dragon Essence", (180, 20, 20)),
        ("Star Dust", (255, 255, 200)),
    ]

    # Create all materials with visual distinction
    all_categories = [
        (weapon_materials, "⚔"),
        (armor_materials, "🛡"),
        (concoction_materials, "⚗")
    ]

    for material_list, category_symbol in all_categories:
        for name, color in material_list:
            sprite = pygame.Surface((64, 64))
            sprite.fill(color)

            # Add border
            pygame.draw.rect(sprite, (255, 255, 255), (0, 0, 64, 64), 3)

            # Add subtle category indicator (corner dot)
            if "Steel" in name or "Iron" in name or "Blade" in name or "Fang" in name or "Horn" in name or "Obsidian" in name or "Mithril" in name or "Demon" in name:
                pygame.draw.circle(sprite, (255, 100, 100), (10, 10), 5)  # Red dot for weapons
            elif "Leather" in name or "Plate" in name or "Scale" in name or "Wood" in name or "Titanium" in name or "Stone" in name or "Shield" in name:
                pygame.draw.circle(sprite, (100, 100, 255), (10, 10), 5)  # Blue dot for armor
            else:
                pygame.draw.circle(sprite, (255, 255, 100), (10, 10), 5)  # Yellow dot for concoctions

            item = Item(
                name=name,
                item_type=ItemType.MATERIAL,
                sprite=sprite,
                description=f"A crafting material."
            )
            materials.append(item)

    return materials


# Pre-defined recipes (materials needed to craft items)
RECIPES = [
    # Weapons (3 materials)
    Recipe(["Iron Ingot", "Oak Wood", "Crystal Shard"], ItemType.WEAPON),
    Recipe(["Dragon Scale", "Dark Stone", "Magic Essence"], ItemType.WEAPON),
    Recipe(["Iron Ingot", "Iron Ingot", "Oak Wood"], ItemType.WEAPON),

    # Armor (3 materials)
    Recipe(["Iron Ingot", "Leather", "Dark Stone"], ItemType.ARMOR),
    Recipe(["Dragon Scale", "Gold Bar", "Crystal Shard"], ItemType.ARMOR),
    Recipe(["Leather", "Leather", "Iron Ingot"], ItemType.ARMOR),

    # Concoctions (3 materials)
    Recipe(["Magic Essence", "Crystal Shard", "Dragon Scale"], ItemType.CONCOCTION),
    Recipe(["Oak Wood", "Magic Essence", "Leather"], ItemType.CONCOCTION),
    Recipe(["Crystal Shard", "Crystal Shard", "Magic Essence"], ItemType.CONCOCTION),
]
