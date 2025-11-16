"""Inventory system for Fightcraft."""
import pygame
from typing import Optional, List, Tuple
from game.item import Item, ItemType


def _draw_item_silhouette(surface: pygame.Surface, rect: pygame.Rect, item_type: ItemType):
    """Draw a subtle silhouette of an item type in the slot background."""
    center_x = rect.centerx
    center_y = rect.centery
    size = min(rect.width, rect.height)
    
    # Very subtle color for silhouette (dark grey, almost invisible)
    silhouette_color = (50, 50, 50)
    
    if item_type == ItemType.WEAPON:
        # Draw sword silhouette - simple sword shape
        # Blade (vertical line)
        blade_width = size // 8
        blade_height = size // 2
        blade_rect = pygame.Rect(
            center_x - blade_width // 2,
            center_y - blade_height // 2,
            blade_width,
            blade_height
        )
        pygame.draw.rect(surface, silhouette_color, blade_rect)
        
        # Crossguard (horizontal line)
        guard_width = size // 2
        guard_height = size // 12
        guard_rect = pygame.Rect(
            center_x - guard_width // 2,
            center_y - guard_height // 2,
            guard_width,
            guard_height
        )
        pygame.draw.rect(surface, silhouette_color, guard_rect)
        
        # Handle (small vertical rectangle at bottom)
        handle_width = size // 10
        handle_height = size // 4
        handle_rect = pygame.Rect(
            center_x - handle_width // 2,
            center_y + blade_height // 2 - handle_height // 4,
            handle_width,
            handle_height
        )
        pygame.draw.rect(surface, silhouette_color, handle_rect)
    
    elif item_type == ItemType.ARMOR:
        # Draw armor silhouette - chest plate shape
        # Main body (rounded rectangle)
        body_width = size // 1.5
        body_height = size // 1.2
        body_rect = pygame.Rect(
            center_x - body_width // 2,
            center_y - body_height // 2,
            body_width,
            body_height
        )
        # Draw rounded rectangle approximation
        pygame.draw.ellipse(surface, silhouette_color, body_rect)
        
        # Shoulder pads (small circles at top)
        shoulder_size = size // 4
        left_shoulder = pygame.Rect(
            center_x - body_width // 2 - shoulder_size // 4,
            center_y - body_height // 2,
            shoulder_size,
            shoulder_size
        )
        right_shoulder = pygame.Rect(
            center_x + body_width // 2 - shoulder_size * 3 // 4,
            center_y - body_height // 2,
            shoulder_size,
            shoulder_size
        )
        pygame.draw.ellipse(surface, silhouette_color, left_shoulder)
        pygame.draw.ellipse(surface, silhouette_color, right_shoulder)
    
    elif item_type == ItemType.CONCOCTION:
        # Draw potion bottle silhouette
        # Bottle body (rounded bottom, straight sides)
        bottle_width = size // 2.5
        bottle_height = size // 1.3
        bottle_x = center_x - bottle_width // 2
        bottle_y = center_y - bottle_height // 2
        
        # Draw bottle body (ellipse for rounded bottom)
        body_rect = pygame.Rect(
            bottle_x,
            bottle_y + bottle_height // 3,
            bottle_width,
            bottle_height * 2 // 3
        )
        pygame.draw.ellipse(surface, silhouette_color, body_rect)
        
        # Draw bottle neck (rectangle)
        neck_width = bottle_width // 2
        neck_height = bottle_height // 3
        neck_rect = pygame.Rect(
            center_x - neck_width // 2,
            bottle_y,
            neck_width,
            neck_height
        )
        pygame.draw.rect(surface, silhouette_color, neck_rect)
        
        # Draw cork/stopper (small rectangle at top)
        cork_width = neck_width * 1.2
        cork_height = neck_height // 2
        cork_rect = pygame.Rect(
            center_x - cork_width // 2,
            bottle_y - cork_height // 2,
            cork_width,
            cork_height
        )
        pygame.draw.rect(surface, silhouette_color, cork_rect)


class InventorySlot:
    """Represents a single inventory slot."""

    def __init__(self, x: int, y: int, size: int = 64, item_type_hint: Optional[ItemType] = None):
        self.x = x
        self.y = y
        self.size = size
        self.item: Optional[Item] = None
        self.item_type_hint: Optional[ItemType] = None  # Hint for silhouette when empty
        self.rect = pygame.Rect(x, y, size, size)

    def contains_point(self, pos: Tuple[int, int]) -> bool:
        """Check if a position is within this slot."""
        return self.rect.collidepoint(pos)

    def render(self, surface: pygame.Surface, hovered: bool = False, item_type_hint: Optional[ItemType] = None):
        """Render the inventory slot."""
        # Draw slot background
        color = (80, 80, 80) if not hovered else (100, 100, 100)
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, (150, 150, 150), self.rect, 2)

        # Draw silhouette if slot is empty and we have a type hint
        if not self.item:
            hint_type = item_type_hint or self.item_type_hint
            if hint_type:
                _draw_item_silhouette(surface, self.rect, hint_type)

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

    def __init__(self, x: int, y: int, slot_size: int = 80, spacing: int = 40):
        self.x = x
        self.y = y
        self.slot_size = slot_size
        self.spacing = spacing

        # Create equipment slots - horizontally arranged
        self.weapon_slot = InventorySlot(x, y, slot_size)
        self.armor_slot = InventorySlot(x + slot_size + spacing, y, slot_size)
        self.concoction_slot = InventorySlot(x + 2 * (slot_size + spacing), y, slot_size)

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
        
        # Map slot names to item types for silhouette hints
        type_map = {
            "weapon": ItemType.WEAPON,
            "armor": ItemType.ARMOR,
            "concoction": ItemType.CONCOCTION
        }

        hovered_slot = self.get_slot_at_pos(mouse_pos) if mouse_pos else None

        for name, slot in self.slots.items():
            # Draw slot with silhouette hint based on slot type
            item_type_hint = type_map.get(name)
            slot.render(surface, hovered=(name == hovered_slot), item_type_hint=item_type_hint)
            
            # Draw label below the slot, centered
            label_surf = font.render(labels[name], True, (255, 255, 255))
            label_rect = label_surf.get_rect()
            label_x = slot.x + (self.slot_size - label_rect.width) // 2
            label_y = slot.y + self.slot_size + 5
            surface.blit(label_surf, (label_x, label_y))
