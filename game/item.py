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
    effect_type: str = ""  # Type of special effect (fire, lifesteal, etc.)
    effect_power: float = 0.0  # Power/magnitude of effect
    special_effect: str = ""  # Human-readable description


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
    """Create categorized crafting materials using real images."""
    materials = []

    # Material lists now contain image paths instead of colors
    weapon_materials = [
        ("Steel Ingot",       "assets/clean_images/Steel_Ignot.png"),
        ("Iron",              "assets/clean_images/Iron.png"),
        ("Dragon Shard",      "assets/clean_images/Dragon_Shard.png"),
        ("Obsidian Shard",    "assets/clean_images/Obsidian_Shard.png"),
        ("Mithril Bar",       "assets/clean_images/Mithril_Bar.png"),
        ("Dark Crystal",      "assets/clean_images/Dark_Crystal.png"),
    ]

    armor_materials = [
        ("Thick Leather",     "assets/clean_images/Thick_Leather.png"),
        ("Steel Plate",       "assets/clean_images/Steel_Plate.png"),
        ("Dragon Scale",      "assets/clean_images/Dragon_Scale.png"),
        ("Reinforced Wood",   "assets/clean_images/Reinforced_Wood.png"),
        ("Titanium Sheet",    "assets/clean_images/Titanium_Sheet.png"),
        ("Stone",             "assets/clean_images/Stone.png"),
    ]

    concoction_materials = [
        ("Magic Essence",     "assets/clean_images/Magic_Essence.png"),
        ("Crystal Powder",    "assets/clean_images/Crystal_Powder.png"),
        ("Phoenix Feather",   "assets/clean_images/Phoenix_Feather.png"),
        ("Moonflower",        "assets/clean_images/Moonflower.png"),
        ("Dragon Essence",    "assets/clean_images/Dragon_Essence.png"),
        ("Star Dust",         "assets/clean_images/Star_Dust.png"),
    ]

    all_categories = [
        (weapon_materials, "⚔"),
        (armor_materials, "🛡"),
        (concoction_materials, "⚗"),
    ]

    for material_list, category_symbol in all_categories:
        for name, path in material_list:

            # 🖼 Загрузка изображения
            try:
                sprite = pygame.image.load(path).convert_alpha()
            except:
                print(f"[ERROR] Missing image: {path}, using placeholder")
                sprite = pygame.Surface((64, 64))
                sprite.fill((150, 0, 0))

            # Добавляем небольшой индикатор категории
            dot_color = (255, 100, 100) if category_symbol == "⚔" else \
                        (100, 100, 255) if category_symbol == "🛡" else \
                        (255, 255, 100)

            pygame.draw.circle(sprite, dot_color, (8, 8), 5)

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
