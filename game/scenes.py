"""Game scenes for Fightcraft."""
import pygame
from typing import Optional, Tuple
from game.engine import Scene
from game.item import create_base_materials, Item, ItemType
from game.inventory import Inventory, EquipmentSlots
from game.crafting import CraftingGrid, CraftingSystem, CraftingButton, ResultSlot
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

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % len(self.options)
            elif event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % len(self.options)
            elif event.key == pygame.K_RETURN:
                if self.selected == 0:
                    # Start game - go to crafting scene
                    self.game.change_scene(CraftingScene(self.game))
                elif self.selected == 1:
                    # Quit
                    self.game.quit()

    def update(self, dt: float):
        pass

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

        # Draw menu options
        for i, option in enumerate(self.options):
            color = (255, 255, 100) if i == self.selected else (200, 200, 200)
            text = self.menu_font.render(option, True, color)
            text_rect = text.get_rect(center=(self.game.width // 2, 350 + i * 60))
            self.screen.blit(text, text_rect)

            # Draw selector
            if i == self.selected:
                pygame.draw.rect(
                    self.screen,
                    (255, 255, 100),
                    text_rect.inflate(20, 10),
                    3
                )


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
            "concoction": (255, 255, 100)
        }

        # Create UI elements
        self.inventory = Inventory(50, 450, rows=2, cols=8)
        self.equipment_slots = EquipmentSlots(950, 100)
        self.crafting_grid = CraftingGrid(300, 150)
        self.result_slot = ResultSlot(700, 200)
        self.craft_button = CraftingButton(650, 320)

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

        # Update button hover state
        mouse_pos = pygame.mouse.get_pos()
        self.craft_button.hovered = self.craft_button.contains_point(mouse_pos)

    def render(self):
        mouse_pos = pygame.mouse.get_pos()

        # Draw tabs at top
        tab_names = {"weapon": "[1] Weapons", "armor": "[2] Armor", "concoction": "[3] Concoctions"}
        tab_x = 50
        for i, tab in enumerate(self.tabs):
            tab_rect = pygame.Rect(tab_x + i * 250, 10, 240, 40)

            # Tab color
            is_active = (tab == self.current_tab)
            if is_active:
                color = self.tab_colors[tab]
                text_color = (255, 255, 255)
            else:
                color = (60, 60, 60)
                text_color = (150, 150, 150)

            # Draw tab
            pygame.draw.rect(self.screen, color, tab_rect)
            pygame.draw.rect(self.screen, (200, 200, 200), tab_rect, 2)

            # Draw tab text
            tab_text = self.game.small_font.render(tab_names[tab], True, text_color)
            text_rect = tab_text.get_rect(center=tab_rect.center)
            self.screen.blit(tab_text, text_rect)

        # Draw title
        title = self.game.font.render(f"Crafting: {self.current_tab.capitalize()}", True, (255, 200, 50))
        self.screen.blit(title, (400, 70))

        # Draw instructions
        instructions = [
            "Drag materials to grid - AI creates unique items!",
            f"Press 1/2/3 to switch tabs. ESC for combat"
        ]
        for i, inst in enumerate(instructions):
            inst_surf = self.game.small_font.render(inst, True, (200, 200, 200))
            self.screen.blit(inst_surf, (50, 50 + i * 25))

        # Draw status message
        status_surf = self.game.small_font.render(self.status_message, True, (100, 255, 100))
        self.screen.blit(status_surf, (50, 100))

        # Draw crafting status (materials count) - below inventory
        materials = self.crafting_grid.get_materials()
        mat_count = len(materials)

        status_text = f"Materials: {mat_count}"
        status_color = (100, 255, 100) if mat_count >= 1 else (255, 255, 100)
        status_surf = self.game.small_font.render(status_text, True, status_color)
        self.screen.blit(status_surf, (50, 630))

        if mat_count >= 1:
            ready_text = "[OK] Ready to craft!" if mat_count > 1 else "[OK] Add more for complexity"
            ready_surf = self.game.small_font.render(ready_text, True, (100, 255, 100))
            self.screen.blit(ready_surf, (200, 630))

        # Draw generation message - below inventory
        if self.generation_message:
            gen_color = (255, 255, 100) if self.generating else (100, 255, 100)
            gen_surf = self.game.font.render(self.generation_message, True, gen_color)
            self.screen.blit(gen_surf, (50, 660))

        # Draw UI elements
        self.inventory.render(self.screen, mouse_pos)
        self.crafting_grid.render(self.screen, mouse_pos)
        self.craft_button.render(self.screen, self.game.small_font)
        self.result_slot.render(self.screen, self.game.small_font, mouse_pos)
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
        # Draw background pattern (subtle)
        for y in range(0, self.game.height, 40):
            pygame.draw.line(self.screen, (50, 50, 50), (0, y), (self.game.width, y), 1)
        
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
