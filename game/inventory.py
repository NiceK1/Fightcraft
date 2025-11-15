"""Inventory system for Fightcraft."""
import pygame
from typing import Optional, List, Tuple
from game.item import Item


class InventorySlot:
    """Represents a single inventory slot."""

    def __init__(self, x: int, y: int, size: int = 64):
        self.x = x
        self.y = y
        self.size = size
        self.item: Optional[Item] = None
        self.rect = pygame.Rect(x, y, size, size)

    def contains_point(self, pos: Tuple[int, int]) -> bool:
        """Check if a position is within this slot."""
        return self.rect.collidepoint(pos)

    def render(self, surface: pygame.Surface, hovered: bool = False):
        """Render the inventory slot."""
        # Draw slot background
        color = (80, 80, 80) if not hovered else (100, 100, 100)
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, (150, 150, 150), self.rect, 2)

        # Draw item if present
        if self.item:
            self.item.render(surface, self.x, self.y, self.size)


class Inventory:
    """Manages player inventory with multiple slots."""

    def __init__(self, x: int, y: int, rows: int = 4, cols: int = 8, slot_size: int = 64, spacing: int = 5):
        self.x = x
        self.y = y
        self.rows = rows
        self.cols = cols
        self.slot_size = slot_size
        self.spacing = spacing
        self.max_slots = rows * cols

        # Create inventory slots
        self.slots: List[InventorySlot] = []
        for row in range(rows):
            for col in range(cols):
                slot_x = x + col * (slot_size + spacing)
                slot_y = y + row * (slot_size + spacing)
                self.slots.append(InventorySlot(slot_x, slot_y, slot_size))

    def add_item(self, item: Item) -> bool:
        """Add an item to the first available slot."""
        for slot in self.slots:
            if slot.item is None:
                slot.item = item
                return True
        return False

    def remove_item(self, slot_index: int) -> Optional[Item]:
        """Remove and return item from a slot."""
        if 0 <= slot_index < len(self.slots):
            item = self.slots[slot_index].item
            self.slots[slot_index].item = None
            return item
        return None

    def get_slot_at_pos(self, pos: Tuple[int, int]) -> Optional[int]:
        """Get slot index at given position."""
        for i, slot in enumerate(self.slots):
            if slot.contains_point(pos):
                return i
        return None

    def get_item_at_pos(self, pos: Tuple[int, int]) -> Optional[Item]:
        """Get item at given position."""
        slot_index = self.get_slot_at_pos(pos)
        if slot_index is not None:
            return self.slots[slot_index].item
        return None

    def get_items(self) -> List[Item]:
        """Get all items in inventory."""
        return [slot.item for slot in self.slots if slot.item is not None]

    def clear_slot(self, slot_index: int):
        """Clear a specific slot."""
        if 0 <= slot_index < len(self.slots):
            self.slots[slot_index].item = None

    def render(self, surface: pygame.Surface, mouse_pos: Optional[Tuple[int, int]] = None):
        """Render the inventory."""
        hovered_slot = self.get_slot_at_pos(mouse_pos) if mouse_pos else None

        for i, slot in enumerate(self.slots):
            slot.render(surface, hovered=(i == hovered_slot))


class EquipmentSlots:
    """Manages equipment slots for weapon, armor, and concoction."""

    def __init__(self, x: int, y: int, slot_size: int = 80, spacing: int = 20):
        self.x = x
        self.y = y
        self.slot_size = slot_size
        self.spacing = spacing

        # Create equipment slots
        self.weapon_slot = InventorySlot(x, y, slot_size)
        self.armor_slot = InventorySlot(x, y + slot_size + spacing, slot_size)
        self.concoction_slot = InventorySlot(x, y + 2 * (slot_size + spacing), slot_size)

        self.slots = {
            "weapon": self.weapon_slot,
            "armor": self.armor_slot,
            "concoction": self.concoction_slot
        }

    def get_slot_at_pos(self, pos: Tuple[int, int]) -> Optional[str]:
        """Get equipment slot name at given position."""
        for name, slot in self.slots.items():
            if slot.contains_point(pos):
                return name
        return None

    def equip_item(self, slot_name: str, item: Item) -> Optional[Item]:
        """Equip an item to a slot, returning previously equipped item."""
        if slot_name in self.slots:
            old_item = self.slots[slot_name].item
            self.slots[slot_name].item = item
            return old_item
        return None

    def get_equipped_item(self, slot_name: str) -> Optional[Item]:
        """Get currently equipped item in a slot."""
        if slot_name in self.slots:
            return self.slots[slot_name].item
        return None

    def render(self, surface: pygame.Surface, font: pygame.font.Font, mouse_pos: Optional[Tuple[int, int]] = None):
        """Render equipment slots with labels."""
        labels = {
            "weapon": "Weapon",
            "armor": "Armor",
            "concoction": "Buff"
        }

        hovered_slot = self.get_slot_at_pos(mouse_pos) if mouse_pos else None

        for name, slot in self.slots.items():
            # Draw label
            label_surf = font.render(labels[name], True, (255, 255, 255))
            surface.blit(label_surf, (slot.x + self.slot_size + 10, slot.y + self.slot_size // 2 - 10))

            # Draw slot
            slot.render(surface, hovered=(name == hovered_slot))
