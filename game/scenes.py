"""Game scenes for Fightcraft."""
import pygame
from typing import Optional, Tuple
from game.engine import Scene
from game.item import create_base_materials, Item, ItemType
from game.inventory import Inventory, EquipmentSlots
from game.crafting import CraftingGrid, CraftingSystem, CraftingButton, ResultSlot, FightButton
from game.combat import Fighter, CombatSystem, CombatRenderer
from game.ai_client import AIClient


class MainMenuScene(Scene):
    """Main menu scene."""

    def __init__(self, game):
        super().__init__(game)
        self.title_font = pygame.font.Font(None, 72)
        self.menu_font = pygame.font.Font(None, 48)

        self.options = ["Start Game", "Quit"]
        self.selected = 0
        self.pressed_option = None  # Track which option is being pressed
        self.press_timer = 0.0  # Timer for press animation

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % len(self.options)
            elif event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % len(self.options)
            elif event.key == pygame.K_RETURN:
                self._execute_option(self.selected)
        
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Handle mouse click on menu options
            mouse_pos = event.pos
            for i, option in enumerate(self.options):
                text = self.menu_font.render(option, True, (200, 200, 200))
                text_rect = text.get_rect(center=(self.game.width // 2, 350 + i * 60))
                # Use inflated rect for easier clicking
                click_rect = text_rect.inflate(20, 10)
                if click_rect.collidepoint(mouse_pos):
                    self.pressed_option = i
                    self.press_timer = 0.15  # 150ms press animation
                    break
        
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            # Handle mouse release
            if self.pressed_option is not None:
                mouse_pos = event.pos
                i = self.pressed_option
                text = self.menu_font.render(self.options[i], True, (200, 200, 200))
                text_rect = text.get_rect(center=(self.game.width // 2, 350 + i * 60))
                click_rect = text_rect.inflate(20, 10)
                if click_rect.collidepoint(mouse_pos):
                    self._execute_option(i)
                self.pressed_option = None
                self.press_timer = 0.0

    def _execute_option(self, index: int):
        """Execute the action for the selected menu option."""
        if index == 0:
            # Start game - go to crafting scene
            self.game.change_scene(CraftingScene(self.game))
        elif index == 1:
            # Quit
            self.game.quit()

    def update(self, dt: float):
        # Update selected option based on mouse hover
        mouse_pos = pygame.mouse.get_pos()
        hover_found = False
        for i, option in enumerate(self.options):
            text = self.menu_font.render(option, True, (200, 200, 200))
            text_rect = text.get_rect(center=(self.game.width // 2, 350 + i * 60))
            hover_rect = text_rect.inflate(20, 10)
            if hover_rect.collidepoint(mouse_pos):
                self.selected = i
                hover_found = True
                break
        
        # If mouse is not over any option, keep current selection (for keyboard navigation)
        
        # Update press timer
        if self.press_timer > 0:
            self.press_timer = max(0, self.press_timer - dt)

    def render(self):
        # Draw title
        title = self.title_font.render("FIGHTCRAFT", True, (255, 200, 50))
        title_rect = title.get_rect(center=(self.game.width // 2, 150))
        self.screen.blit(title, title_rect)

        # Draw subtitle
        subtitle = self.game.small_font.render(
            "AI-Powered Crafting & Combat", True, (200, 200, 200)
        )
        subtitle_rect = subtitle.get_rect(center=(self.game.width // 2, 220))
        self.screen.blit(subtitle, subtitle_rect)

        # Draw menu options with interactive states
        mouse_pos = pygame.mouse.get_pos()
        for i, option in enumerate(self.options):
            text = self.menu_font.render(option, True, (200, 200, 200))
            text_rect = text.get_rect(center=(self.game.width // 2, 350 + i * 60))
            hover_rect = text_rect.inflate(20, 10)
            is_hovered = hover_rect.collidepoint(mouse_pos) and self.pressed_option is None
            is_pressed = (self.pressed_option == i) and self.press_timer > 0
            
            # Determine colors and effects based on state
            if is_pressed:
                # Pressed state - darker, slightly smaller
                text_color = (150, 150, 150)
                border_color = (200, 200, 100)
                border_width = 2
                scale = 0.95
                offset_y = 1  # Slight downward shift
            elif is_hovered or i == self.selected:
                # Hover/selected state - bright yellow, glowing effect
                text_color = (255, 255, 100)
                border_color = (255, 255, 150)
                border_width = 3
                scale = 1.0
                offset_y = 0
            else:
                # Normal state
                text_color = (200, 200, 200)
                border_color = None
                border_width = 0
                scale = 1.0
                offset_y = 0
            
            # Draw glow effect for hover/selected
            if (is_hovered or (i == self.selected and not is_pressed)) and border_color:
                glow_color = border_color if isinstance(border_color, tuple) else (255, 255, 150)
                glow_rect = text_rect.inflate(30, 15)
                # Draw multiple layers for glow effect
                for glow_offset in [15, 10, 5]:
                    glow_alpha = max(0, 25 - glow_offset * 2)
                    glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
                    inner_rect = pygame.Rect(glow_offset, glow_offset, 
                                           glow_rect.width - glow_offset * 2, 
                                           glow_rect.height - glow_offset * 2)
                    pygame.draw.rect(
                        glow_surf,
                        (*glow_color[:3], glow_alpha),
                        inner_rect
                    )
                    glow_pos = (glow_rect.x, glow_rect.y)
                    self.screen.blit(glow_surf, glow_pos)
            
            # Draw border/selector
            if border_color:
                border_rect = text_rect.inflate(20, 10)
                border_rect.y += offset_y
                pygame.draw.rect(
                    self.screen,
                    border_color,
                    border_rect,
                    border_width
                )
            
            # Draw text with scale effect
            if scale != 1.0:
                scaled_text = pygame.transform.scale(
                    self.menu_font.render(option, True, text_color),
                    (int(text_rect.width * scale), int(text_rect.height * scale))
                )
                scaled_rect = scaled_text.get_rect(center=(text_rect.centerx, text_rect.centery + offset_y))
                self.screen.blit(scaled_text, scaled_rect)
            else:
                text_surf = self.menu_font.render(option, True, text_color)
                text_pos = (text_rect.x, text_rect.y + offset_y)
                self.screen.blit(text_surf, text_pos)


class CraftingScene(Scene):
    """Crafting scene where players create items."""

    def __init__(self, game):
        super().__init__(game)

        # Initialize systems
        self.ai_client = AIClient()
        self.crafting_system = CraftingSystem()

        # Tab system - separate crafting stations
        self.current_tab = "weapon"  # weapon, armor, concoction
        self.tabs = ["weapon", "armor", "concoction"]
        self.tab_colors = {
            "weapon": (255, 100, 100),
            "armor": (100, 100, 255),
            "concoction": (180, 150, 0)  # Dark yellow for better contrast
        }

        # Create UI elements - positioned according to layout
        # Fight button at top center
        fight_button_width = 150
        fight_button_x = (self.game.width - fight_button_width) // 2  # Centered
        fight_button_y = 10
        self.fight_button = FightButton(fight_button_x, fight_button_y, width=fight_button_width, height=40)
        
        # Shift all elements down by 60px to make room for Fight button
        offset_y = 60
        
        # Instructions end at ~160, so crafting grid starts below them (shifted down)
        self.crafting_grid = CraftingGrid(150, 170 + offset_y)
        # Result slot on the right, same height as crafting grid
        # Result slot: label (30px) + slot (100px) = 130px total
        self.result_slot = ResultSlot(810, 230 + offset_y)
        # Craft button below result slot
        # Result slot ends at 170 + 130 = 300, add 10px spacing = 310
        self.craft_button = CraftingButton(760, 390 + offset_y)
        # Inventory will be positioned dynamically below materials label in render()
        # Using approximate position for initialization
        self.inventory = Inventory(80, 470 + offset_y, rows=2, cols=6)
        # Equipment slots on the right, bottom - horizontally arranged
        # Position: right side, below craft button
        # Craft button: y=310, height=50, ends at 360, add 20px spacing = 380
        equipment_x = 700  # Align with result slot
        equipment_y = 465 + offset_y  # Below craft button with spacing
        self.equipment_slots = EquipmentSlots(equipment_x, equipment_y)

        # Store all materials by category
        all_materials = create_base_materials()
        self.weapon_materials = all_materials[0:6]
        self.armor_materials = all_materials[6:12]
        self.concoction_materials = all_materials[12:18]

        # Populate inventory based on current tab
        self._update_inventory_for_tab()

        # Drag and drop state
        self.dragging_item: Optional[Item] = None
        self.drag_source: Optional[str] = None
        self.drag_source_index: Optional[int] = None

        # AI generation state
        self.generating = False
        self.generation_message = ""

        # Check backend
        backend_available = self.ai_client.check_backend_health()
        if backend_available:
            self.status_message = "AI Backend connected!"
        else:
            self.status_message = "AI Backend offline - using fallback generation"

    def _update_inventory_for_tab(self):
        """Update inventory to show only materials for current tab."""
        # Clear inventory
        for slot in self.inventory.slots:
            slot.item = None

        # Get materials for current tab
        if self.current_tab == "weapon":
            materials = self.weapon_materials
        elif self.current_tab == "armor":
            materials = self.armor_materials
        else:  # concoction
            materials = self.concoction_materials

        # Add to inventory
        for material in materials:
            self.inventory.add_item(material)

    def _switch_tab(self, tab_name: str):
        """Switch to a different crafting tab."""
        if tab_name in self.tabs:
            self.current_tab = tab_name
            self._update_inventory_for_tab()
            # Clear crafting grid when switching tabs
            self.crafting_grid.clear()
            self.result_slot.set_item(None)

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # Go to combat with current equipment
                self.game.change_scene(CombatScene(self.game, self.equipment_slots))
            elif event.key == pygame.K_1:
                self._switch_tab("weapon")
            elif event.key == pygame.K_2:
                self._switch_tab("armor")
            elif event.key == pygame.K_3:
                self._switch_tab("concoction")

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            self._handle_mouse_down(pos)

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            pos = event.pos
            self._handle_mouse_up(pos)

    def _handle_mouse_down(self, pos: Tuple[int, int]):
        """Handle mouse button down for drag start."""
        # Check fight button first
        if self.fight_button.contains_point(pos):
            # Go to combat with current equipment
            self.game.change_scene(CombatScene(self.game, self.equipment_slots))
            return
        
        # Check tabs (they're at the top, centered, shifted down)
        tab_names = {"weapon": "[1] Weapons", "armor": "[2] Armor", "concoction": "[3] Concoctions"}
        offset_y = 60
        tab_y = 60 + offset_y  # Same as in render
        # Calculate centered tab positions
        total_tabs_width = len(self.tabs) * 250 - 10  # 240 width + 10 spacing
        tab_start_x = (self.game.width - total_tabs_width) // 2
        for i, tab in enumerate(self.tabs):
            tab_rect = pygame.Rect(tab_start_x + i * 250, tab_y, 240, 40)
            if tab_rect.collidepoint(pos):
                self._switch_tab(tab)
                return  # Don't process other clicks when switching tabs
        
        # Check inventory
        slot_index = self.inventory.get_slot_at_pos(pos)
        if slot_index is not None and self.inventory.slots[slot_index].item:
            self.dragging_item = self.inventory.slots[slot_index].item
            self.drag_source = "inventory"
            self.drag_source_index = slot_index
            return

        # Check crafting grid
        grid_pos = self.crafting_grid.get_slot_at_pos(pos)
        if grid_pos:
            row, col = grid_pos
            item = self.crafting_grid.slots[row][col].item
            if item:
                self.dragging_item = item
                self.drag_source = "grid"
                self.drag_source_index = (row, col)
                self.crafting_grid.remove_item(row, col)
            return

        # Check result slot
        if self.result_slot.contains_point(pos):
            item = self.result_slot.get_item()
            if item:
                self.dragging_item = item
                self.drag_source = "result"
            return

        # Check equipment slots
        slot_name = self.equipment_slots.get_slot_at_pos(pos)
        if slot_name:
            item = self.equipment_slots.get_equipped_item(slot_name)
            if item:
                self.dragging_item = item
                self.drag_source = "equipment"
                self.drag_source_index = slot_name
                self.equipment_slots.equip_item(slot_name, None)
            return

        # Check craft button
        if self.craft_button.contains_point(pos) and self.craft_button.enabled and not self.generating:
            self._start_crafting()

    def _handle_mouse_up(self, pos: Tuple[int, int]):
        """Handle mouse button up for drag end."""
        if not self.dragging_item:
            return

        dropped = False

        # Try to drop in inventory
        slot_index = self.inventory.get_slot_at_pos(pos)
        if slot_index is not None:
            if self.inventory.slots[slot_index].item is None:
                self.inventory.slots[slot_index].item = self.dragging_item
                dropped = True

        # Try to drop in crafting grid
        if not dropped:
            grid_pos = self.crafting_grid.get_slot_at_pos(pos)
            if grid_pos and self.dragging_item.item_type == ItemType.MATERIAL:
                row, col = grid_pos
                if self.crafting_grid.slots[row][col].item is None:
                    self.crafting_grid.place_item(row, col, self.dragging_item)
                    dropped = True

        # Try to drop in equipment
        if not dropped:
            slot_name = self.equipment_slots.get_slot_at_pos(pos)
            if slot_name:
                # Check if item type matches slot
                item_type_match = {
                    "weapon": ItemType.WEAPON,
                    "armor": ItemType.ARMOR,
                    "concoction": ItemType.CONCOCTION
                }
                if self.dragging_item.item_type == item_type_match.get(slot_name):
                    old_item = self.equipment_slots.equip_item(slot_name, self.dragging_item)
                    if old_item:
                        # Return old item to inventory
                        self.inventory.add_item(old_item)
                    dropped = True

        # If not dropped, return to source
        if not dropped:
            if self.drag_source == "inventory" and self.drag_source_index is not None:
                self.inventory.slots[self.drag_source_index].item = self.dragging_item
            elif self.drag_source == "grid" and self.drag_source_index is not None:
                row, col = self.drag_source_index
                self.crafting_grid.place_item(row, col, self.dragging_item)
            elif self.drag_source == "equipment" and self.drag_source_index is not None:
                self.equipment_slots.equip_item(self.drag_source_index, self.dragging_item)
            elif self.drag_source == "result":
                self.result_slot.set_item(self.dragging_item)

        # Clear drag state
        self.dragging_item = None
        self.drag_source = None
        self.drag_source_index = None

    def _start_crafting(self):
        """Start the crafting process with AI generation."""
        materials = self.crafting_grid.get_materials()

        if len(materials) < 1:  # Need at least 1 material
            return

        self.generating = True
        self.generation_message = "Generating item with AI..."

        # Determine item type based on current tab
        from game.item import ItemType
        if self.current_tab == "weapon":
            item_type = ItemType.WEAPON
        elif self.current_tab == "armor":
            item_type = ItemType.ARMOR
        else:  # concoction
            item_type = ItemType.CONCOCTION

        # Start async AI generation with explicit type
        def on_complete(item: Item):
            self.generating = False
            self.generation_message = f"Created: {item.name}! (via {item.generation_method})"
            self.result_slot.set_item(item)
            self.crafting_grid.clear()

        # Pass explicit item type based on current tab
        self.ai_client.generate_item_async(materials, item_type, on_complete)

    def update(self, dt: float):
        # Update craft button state - need at least 1 material
        materials = self.crafting_grid.get_materials()
        self.craft_button.enabled = (len(materials) >= 1) and not self.generating

        # Update button hover states
        mouse_pos = pygame.mouse.get_pos()
        self.craft_button.hovered = self.craft_button.contains_point(mouse_pos)
        self.fight_button.hovered = self.fight_button.contains_point(mouse_pos)

    def render(self):
        mouse_pos = pygame.mouse.get_pos()

        # Draw Fight button at top right
        self.fight_button.hovered = self.fight_button.contains_point(mouse_pos)
        self.fight_button.render(self.screen, self.game.font)

        # Draw status message at top left
        status_surf = self.game.small_font.render(self.status_message, True, (100, 255, 100))
        self.screen.blit(status_surf, (80, 10))

        # Draw title at the very top, centered (shifted down)
        offset_y = 60
        title = self.game.font.render(f"Crafting: {self.current_tab.capitalize()}", True, (255, 200, 50))
        title_rect = title.get_rect(center=(self.game.width // 2, 30 + offset_y))
        self.screen.blit(title, title_rect)

        # Draw tabs below title, centered (shifted down)
        tab_names = {"weapon": "[1] Weapons", "armor": "[2] Armor", "concoction": "[3] Concoctions"}
        tab_y = 60 + offset_y  # Position tabs below title
        # Calculate centered tab positions
        total_tabs_width = len(self.tabs) * 250 - 10  # 240 width + 10 spacing
        tab_start_x = (self.game.width - total_tabs_width) // 2
        for i, tab in enumerate(self.tabs):
            tab_rect = pygame.Rect(tab_start_x + i * 250, tab_y, 240, 40)

            # Tab color
            is_active = (tab == self.current_tab)
            is_hovered = tab_rect.collidepoint(mouse_pos)
            
            if is_active:
                color = self.tab_colors[tab]
                text_color = (255, 255, 255)
            elif is_hovered:
                # Hover effect - slightly brighter than inactive
                color = tuple(min(255, c + 30) for c in (60, 60, 60))
                text_color = (200, 200, 200)
            else:
                color = (60, 60, 60)
                text_color = (150, 150, 150)

            # Draw tab
            pygame.draw.rect(self.screen, color, tab_rect)
            border_color = (255, 255, 255) if is_hovered and not is_active else (200, 200, 200)
            pygame.draw.rect(self.screen, border_color, tab_rect, 2)

            # Draw tab text
            tab_text = self.game.small_font.render(tab_names[tab], True, text_color)
            text_rect = tab_text.get_rect(center=tab_rect.center)
            self.screen.blit(tab_text, text_rect)

        # Draw instructions below tabs with spacing, centered
        instructions = [
            "Drag materials to grid - AI creates unique items!",
            f"Press 1/2/3 to switch tabs. Click Fight or press ESC for combat"
        ]
        instructions_y = tab_y + 60  # Add spacing below tabs
        for i, inst in enumerate(instructions):
            inst_surf = self.game.small_font.render(inst, True, (200, 200, 200))
            # Center the text horizontally
            inst_rect = inst_surf.get_rect(center=(self.game.width // 2, instructions_y + i * 25))
            self.screen.blit(inst_surf, inst_rect)

        # Calculate crafting grid height: 3 rows * 80px + 2 spacing * 10px = 260px
        grid_height = 3 * 80 + 2 * 10
        grid_bottom = self.crafting_grid.y + grid_height
        
        # Draw crafting status (materials count) - below crafting grid
        materials = self.crafting_grid.get_materials()
        mat_count = len(materials)
        
        # Materials count label below grid, above inventory
        materials_y = grid_bottom + 10
        status_text = f"Materials: {mat_count}"
        status_color = (100, 255, 100) if mat_count >= 1 else (255, 255, 100)
        status_surf = self.game.small_font.render(status_text, True, status_color)
        self.screen.blit(status_surf, (150, materials_y))
        
        # Position inventory dynamically below materials label
        # Text height is approximately 20px, add 10px spacing
        inventory_y = materials_y + 30
        # Update inventory position if it changed
        if self.inventory.y != inventory_y:
            # Recreate inventory at new position (or update position if Inventory supports it)
            # For now, we'll update slots manually
            for i, slot in enumerate(self.inventory.slots):
                row = i // self.inventory.cols
                col = i % self.inventory.cols
                slot.x = self.inventory.x + col * (self.inventory.slot_size + self.inventory.spacing)
                slot.y = inventory_y + row * (self.inventory.slot_size + self.inventory.spacing)
            self.inventory.y = inventory_y

        # Draw generation message - bottom right (below equipment slots)
        if self.generation_message:
            gen_color = (255, 255, 100) if self.generating else (100, 255, 100)
            gen_surf = self.game.small_font.render(self.generation_message, True, gen_color)
            # Position at bottom right, below equipment slots
            # Equipment slots height: slot_size (80) + label (~20) = ~100px
            gen_y = 420  # Below equipment slots with spacing
            self.screen.blit(gen_surf, (self.equipment_slots.x - 10, gen_y))

        # Draw UI elements
        self.inventory.render(self.screen, mouse_pos)
        self.crafting_grid.render(self.screen, mouse_pos)
        self.craft_button.render(self.screen, self.game.small_font)
        
        # Determine item type hint based on current tab
        from game.item import ItemType
        item_type_map = {
            "weapon": ItemType.WEAPON,
            "armor": ItemType.ARMOR,
            "concoction": ItemType.CONCOCTION
        }
        item_type_hint = item_type_map.get(self.current_tab)
        self.result_slot.render(self.screen, self.game.small_font, mouse_pos, item_type_hint=item_type_hint)
        self.equipment_slots.render(self.screen, self.game.small_font, mouse_pos)

        # Draw dragging item
        if self.dragging_item:
            self.dragging_item.render(self.screen, mouse_pos[0] - 32, mouse_pos[1] - 32, 64)


class CombatScene(Scene):
    """Combat scene where players fight with their crafted items."""

    def __init__(self, game, equipment_slots: EquipmentSlots):
        super().__init__(game)

        # Store equipment for restart functionality
        self.equipment_slots = equipment_slots

        # Create fighters
        self.player = Fighter("Player", max_health=100, is_player=True)
        self.enemy = Fighter("Enemy", max_health=800, is_player=False)  # Strong enemy for longer battles

        # Equip player items
        self.player.equip_items(
            equipment_slots.get_equipped_item("weapon"),
            equipment_slots.get_equipped_item("armor"),
            equipment_slots.get_equipped_item("concoction")
        )

        # Equip enemy with strong stats (for testing)
        self.enemy.base_damage = 25
        self.enemy.base_armor = 20

        # Initialize combat
        self.combat = CombatSystem(self.player, self.enemy)
        self.renderer = CombatRenderer(self.game.font, self.game.small_font)

        self.auto_combat = False
        self.auto_combat_timer = 0
        self.auto_combat_delay = 1.0  # Seconds between turns

    def restart_battle(self):
        """Restart the battle with the same equipment."""
        # Create new fighters
        self.player = Fighter("Player", max_health=100, is_player=True)
        self.enemy = Fighter("Enemy", max_health=800, is_player=False)

        # Re-equip player items
        self.player.equip_items(
            self.equipment_slots.get_equipped_item("weapon"),
            self.equipment_slots.get_equipped_item("armor"),
            self.equipment_slots.get_equipped_item("concoction")
        )

        # Re-equip enemy stats
        self.enemy.base_damage = 25
        self.enemy.base_armor = 20

        # Reset combat system
        self.combat = CombatSystem(self.player, self.enemy)
        self.auto_combat = False
        self.auto_combat_timer = 0

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not self.combat.combat_over:
                # Execute next turn
                self.combat.execute_turn()
            elif event.key == pygame.K_a and not self.combat.combat_over:
                # Toggle auto combat
                self.auto_combat = not self.auto_combat
            elif event.key == pygame.K_r and self.combat.combat_over:
                # Restart battle with same equipment
                self.restart_battle()
            elif event.key == pygame.K_ESCAPE:
                # Return to crafting
                self.game.change_scene(CraftingScene(self.game))

    def update(self, dt: float):
        # Update sprite animations
        self.player.update_sprite(dt)
        self.enemy.update_sprite(dt)

        # Update particle effects
        self.combat.update_effects(dt)

        if self.auto_combat and not self.combat.combat_over:
            self.auto_combat_timer += dt
            if self.auto_combat_timer >= self.auto_combat_delay:
                self.combat.execute_turn()
                self.auto_combat_timer = 0

    def render(self):
        # Draw background pattern (subtle lines over gradient)
        # Lines are slightly darker than gradient for subtle texture
        for y in range(0, self.game.height, 40):
            # Use darker color that works with gradient
            line_color = (35, 35, 35)
            pygame.draw.line(self.screen, line_color, (0, y), (self.game.width, y), 1)
        
        # Draw title
        title = self.game.font.render("COMBAT!", True, (255, 100, 100))
        title_rect = title.get_rect(center=(self.game.width // 2, 30))
        self.screen.blit(title, title_rect)
        
        # Calculate column centers for fighters
        player_column_center = self.game.width // 4  # Left quarter
        enemy_column_center = 3 * self.game.width // 4  # Right quarter
        
        # Draw VS indicator (centered between columns)
        vs_text = self.game.font.render("VS", True, (255, 255, 100))
        vs_rect = vs_text.get_rect(center=(self.game.width // 2, 200))
        self.screen.blit(vs_text, vs_rect)

        # Draw fighters (centered in their columns)
        self.renderer.render_fighter(self.screen, self.player, player_column_center, 80, True)
        self.renderer.render_fighter(self.screen, self.enemy, enemy_column_center, 80, False)

        # Draw particle effects (on top of fighters, below UI)
        self.renderer.render_effects(self.screen, self.combat.effect_animator)

        # Draw turn indicator (centered, above combat log)
        if not self.combat.combat_over:
            current_fighter = self.combat.turn_order[self.combat.turn % 2]
            turn_text = f"Turn {self.combat.turn + 1}: {current_fighter.name}'s turn"
            turn_surf = self.game.font.render(turn_text, True, (255, 255, 100))
            turn_rect = turn_surf.get_rect(center=(self.game.width // 2, 350))
            self.screen.blit(turn_surf, turn_rect)

        # Draw combat log (centered, below turn indicator)
        log_x = self.game.width // 2 - 150  # Center with width of ~300
        log_y = 380
        self.renderer.render_combat_log(self.screen, self.combat.combat_log, log_x, log_y)

        # Draw controls (centered, at bottom)
        if not self.combat.combat_over:
            controls = [
                "SPACE - Next Turn",
                "A - Toggle Auto Combat",
                "ESC - Return to Crafting"
            ]
        else:
            result = "Victory!" if self.combat.player_won else "Defeat!"
            controls = [
                f"Result: {result}",
                "R - Restart Battle",
                "ESC - Return to Crafting"
            ]

        controls_start_y = 580
        for i, control in enumerate(controls):
            control_surf = self.game.small_font.render(control, True, (200, 200, 200))
            control_rect = control_surf.get_rect(center=(self.game.width // 2, controls_start_y + i * 25))
            self.screen.blit(control_surf, control_rect)
