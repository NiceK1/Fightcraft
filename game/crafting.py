"""Crafting system for Fightcraft."""
import pygame
from typing import Optional, List, Tuple
from game.item import Item, Recipe, ItemType, RECIPES
from game.inventory import InventorySlot


class CraftingGrid:
    """3x3 crafting grid like Minecraft."""

    def __init__(self, x: int, y: int, slot_size: int = 80, spacing: int = 10):
        self.x = x
        self.y = y
        self.slot_size = slot_size
        self.spacing = spacing
        self.grid_size = 3

        # Create 3x3 grid of slots
        self.slots: List[List[InventorySlot]] = []
        for row in range(self.grid_size):
            row_slots = []
            for col in range(self.grid_size):
                slot_x = x + col * (slot_size + spacing)
                slot_y = y + row * (slot_size + spacing)
                row_slots.append(InventorySlot(slot_x, slot_y, slot_size))
            self.slots.append(row_slots)

    def get_slot_at_pos(self, pos: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """Get grid position (row, col) at given screen position."""
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                if self.slots[row][col].contains_point(pos):
                    return (row, col)
        return None

    def get_item_at_pos(self, pos: Tuple[int, int]) -> Optional[Item]:
        """Get item at given position."""
        grid_pos = self.get_slot_at_pos(pos)
        if grid_pos:
            row, col = grid_pos
            return self.slots[row][col].item
        return None

    def place_item(self, row: int, col: int, item: Item):
        """Place an item in a grid slot."""
        if 0 <= row < self.grid_size and 0 <= col < self.grid_size:
            self.slots[row][col].item = item

    def remove_item(self, row: int, col: int) -> Optional[Item]:
        """Remove and return item from a grid slot."""
        if 0 <= row < self.grid_size and 0 <= col < self.grid_size:
            item = self.slots[row][col].item
            self.slots[row][col].item = None
            return item
        return None

    def get_materials(self) -> List[str]:
        """Get list of material names in the grid."""
        materials = []
        for row in self.slots:
            for slot in row:
                if slot.item and slot.item.item_type == ItemType.MATERIAL:
                    materials.append(slot.item.name)
        return materials

    def clear(self):
        """Clear all slots in the grid."""
        for row in self.slots:
            for slot in row:
                slot.item = None

    def render(self, surface: pygame.Surface, mouse_pos: Optional[Tuple[int, int]] = None):
        """Render the crafting grid."""
        hovered_pos = self.get_slot_at_pos(mouse_pos) if mouse_pos else None

        for row in range(self.grid_size):
            for col in range(self.grid_size):
                hovered = (hovered_pos == (row, col)) if hovered_pos else False
                self.slots[row][col].render(surface, hovered)


class CraftingSystem:
    """Manages the crafting system and recipe matching."""

    def __init__(self):
        self.recipes = RECIPES
        self.is_crafting = False
        self.crafting_progress = 0.0
        self.crafting_time = 2.0  # Time in seconds for AI generation

    def find_recipe(self, materials: List[str]) -> Optional[Recipe]:
        """Find a matching recipe for given materials (legacy - not used with AI)."""
        if len(materials) < 1:
            return None

        for recipe in self.recipes:
            if recipe.matches(materials):
                return recipe

        return None

    def can_craft(self, materials: List[str]) -> bool:
        """Check if materials can be crafted."""
        return self.find_recipe(materials) is not None

    def start_crafting(self):
        """Start the crafting process (AI generation)."""
        self.is_crafting = True
        self.crafting_progress = 0.0

    def update_crafting(self, dt: float) -> bool:
        """Update crafting progress. Returns True when complete."""
        if self.is_crafting:
            self.crafting_progress += dt / self.crafting_time
            if self.crafting_progress >= 1.0:
                self.is_crafting = False
                self.crafting_progress = 0.0
                return True
        return False


class CraftingButton:
    """Button to initiate crafting."""

    def __init__(self, x: int, y: int, width: int = 200, height: int = 50):
        self.rect = pygame.Rect(x, y, width, height)
        self.enabled = False
        self.hovered = False

    def contains_point(self, pos: Tuple[int, int]) -> bool:
        """Check if position is within button."""
        return self.rect.collidepoint(pos)

    def render(self, surface: pygame.Surface, font: pygame.font.Font):
        """Render the crafting button."""
        # Determine button color
        if not self.enabled:
            color = (60, 60, 60)
            text_color = (100, 100, 100)
        elif self.hovered:
            color = (80, 150, 80)
            text_color = (255, 255, 255)
        else:
            color = (60, 120, 60)
            text_color = (255, 255, 255)

        # Draw button
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, (200, 200, 200), self.rect, 2)

        # Draw text
        text = "Craft Item"
        text_surf = font.render(text, True, text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)


class ResultSlot:
    """Slot to display crafted item result."""

    def __init__(self, x: int, y: int, size: int = 100):
        self.slot = InventorySlot(x, y, size)

    def set_item(self, item: Optional[Item]):
        """Set the result item."""
        self.slot.item = item

    def get_item(self) -> Optional[Item]:
        """Get and clear the result item."""
        item = self.slot.item
        self.slot.item = None
        return item

    def contains_point(self, pos: Tuple[int, int]) -> bool:
        """Check if position is within result slot."""
        return self.slot.contains_point(pos)

    def render(self, surface: pygame.Surface, font: pygame.font.Font, mouse_pos: Optional[Tuple[int, int]] = None):
        """Render the result slot with label."""
        # Draw label
        label = font.render("Result", True, (255, 255, 255))
        surface.blit(label, (self.slot.x, self.slot.y - 30))

        # Draw slot
        hovered = self.contains_point(mouse_pos) if mouse_pos else False
        self.slot.render(surface, hovered)


class WeaponTypeSelector:
    """UI element for selecting weapon subtype (sword, axe, spear)."""

    def __init__(self, x: int, y: int, width: int = 120, height: int = 40):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.weapon_types = ["sword", "axe", "spear"]
        self.selected_type = "sword"  # Default
        self.spacing = 10

        # Calculate button positions
        self.buttons = []
        button_height = (height - 2 * self.spacing) // 3
        for i, weapon_type in enumerate(self.weapon_types):
            button_y = y + i * (button_height + self.spacing)
            self.buttons.append({
                "type": weapon_type,
                "rect": pygame.Rect(x, button_y, width, button_height),
                "color": (100, 100, 150),
                "hover_color": (130, 130, 180),
                "selected_color": (150, 150, 220)
            })

    def handle_click(self, pos: Tuple[int, int]) -> bool:
        """Handle click on weapon type buttons. Returns True if selection changed."""
        for button in self.buttons:
            if button["rect"].collidepoint(pos):
                old_type = self.selected_type
                self.selected_type = button["type"]
                return old_type != self.selected_type
        return False

    def get_selected_type(self) -> str:
        """Get currently selected weapon type."""
        return self.selected_type

    def render(self, surface: pygame.Surface, font: pygame.font.Font, mouse_pos: Optional[Tuple[int, int]] = None):
        """Render weapon type selector buttons."""
        # Draw title
        title = font.render("Weapon Type", True, (255, 255, 255))
        surface.blit(title, (self.x, self.y - 30))

        # Draw buttons
        for button in self.buttons:
            # Determine button color
            if button["type"] == self.selected_type:
                color = button["selected_color"]
            elif mouse_pos and button["rect"].collidepoint(mouse_pos):
                color = button["hover_color"]
            else:
                color = button["color"]

            # Draw button background
            pygame.draw.rect(surface, color, button["rect"])
            pygame.draw.rect(surface, (255, 255, 255), button["rect"], 2)

            # Draw button text
            text = font.render(button["type"].capitalize(), True, (255, 255, 255))
            text_rect = text.get_rect(center=button["rect"].center)
            surface.blit(text, text_rect)
