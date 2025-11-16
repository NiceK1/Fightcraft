"""Combat system for Fightcraft."""
import pygame
import random
import math
from typing import Optional, List
from game.item import Item, ItemType
from game.character_sprite import CharacterSprite


class HealthBarAnimator:
    """Manages smooth health bar animations and hit effects."""
    
    def __init__(self):
        self.displayed_health = 1.0  # Current displayed health percentage (0.0 to 1.0)
        self.target_health = 1.0  # Target health percentage
        self.hit_scale = 1.0  # Scale for hit effect (1.0 -> 0.8 -> 1.0)
        self.hit_timer = 0.0
        self.hit_duration = 0.3  # Duration of hit effect in seconds
        
    def set_target_health(self, health_percentage: float):
        """Set target health percentage (will animate smoothly)."""
        self.target_health = max(0.0, min(1.0, health_percentage))
    
    def trigger_hit_effect(self):
        """Trigger hit effect animation."""
        self.hit_timer = self.hit_duration
    
    def update(self, dt: float):
        """Update animations."""
        # Smoothly animate health bar towards target
        if abs(self.displayed_health - self.target_health) > 0.01:
            # Lerp towards target (speed: 3.0 per second)
            diff = self.target_health - self.displayed_health
            self.displayed_health += diff * min(3.0 * dt, 1.0)
        else:
            self.displayed_health = self.target_health
        
        # Update hit effect
        if self.hit_timer > 0:
            self.hit_timer -= dt
            progress = 1.0 - (self.hit_timer / self.hit_duration)
            # Scale animation: 1.0 -> 0.9 -> 1.0
            if progress < 0.5:
                # Shrink phase
                t = progress * 2
                self.hit_scale = 1.0 - (0.1 * t)
            else:
                # Expand phase
                t = (progress - 0.5) * 2
                self.hit_scale = 0.9 + (0.1 * t)
        else:
            self.hit_scale = 1.0
    
    def get_displayed_health(self) -> float:
        """Get current displayed health percentage."""
        return max(0.0, min(1.0, self.displayed_health))
    
    def get_hit_scale(self) -> float:
        """Get current hit effect scale."""
        return self.hit_scale


class Fighter:
    """Represents a fighter in combat."""

    def __init__(self, name: str, max_health: int = 100, is_player: bool = True):
        self.name = name
        self.max_health = max_health
        self.current_health = max_health
        self.is_player = is_player

        # Equipment
        self.weapon: Optional[Item] = None
        self.armor: Optional[Item] = None
        self.concoction: Optional[Item] = None

        # Stats (base + equipment)
        self.base_damage = 5
        self.base_armor = 0
        self.base_speed = 1.0
        
        # Character sprite
        base_color = (100, 150, 200) if is_player else (200, 100, 100)
        self.sprite = CharacterSprite(base_color=base_color, size=128)
        
        # Health bar animator
        self.health_animator = HealthBarAnimator()
        self.health_animator.set_target_health(1.0)

    def equip_items(self, weapon: Optional[Item], armor: Optional[Item], concoction: Optional[Item]):
        """Equip items for combat."""
        self.weapon = weapon
        self.armor = armor
        self.concoction = concoction

        # Update sprite equipment
        self.sprite.set_equipment(weapon, armor)

        # Apply concoction effects immediately
        if concoction:
            self.current_health = min(
                self.max_health + concoction.stats.health,
                self.max_health + 50  # Cap health boost
            )
            # Update health bar animation
            self.health_animator.set_target_health(self.get_health_percentage())

    def get_total_damage(self) -> int:
        """Calculate total damage including weapon."""
        damage = self.base_damage
        if self.weapon:
            damage += self.weapon.stats.damage
        return damage

    def get_total_armor(self) -> int:
        """Calculate total armor including equipment."""
        armor = self.base_armor
        if self.armor:
            armor += self.armor.stats.armor
        return armor

    def get_total_speed(self) -> float:
        """Calculate total speed including equipment."""
        speed = self.base_speed
        if self.weapon:
            speed *= self.weapon.stats.speed
        if self.armor:
            speed *= self.armor.stats.speed
        if self.concoction:
            speed *= self.concoction.stats.speed
        return speed

    def take_damage(self, damage: int) -> int:
        """Take damage, reduced by armor. Returns actual damage taken."""
        armor = self.get_total_armor()
        # Armor reduces damage by a percentage
        damage_reduction = min(armor / 200.0, 0.75)  # Max 75% reduction
        actual_damage = int(damage * (1 - damage_reduction))

        self.current_health = max(0, self.current_health - actual_damage)
        
        # Update health bar animation
        self.health_animator.set_target_health(self.get_health_percentage())
        self.health_animator.trigger_hit_effect()
        
        return actual_damage

    def is_alive(self) -> bool:
        """Check if fighter is still alive."""
        return self.current_health > 0

    def get_health_percentage(self) -> float:
        """Get health as percentage."""
        return self.current_health / self.max_health if self.max_health > 0 else 0
    
    def update_sprite(self, dt: float):
        """Update character sprite animations."""
        self.sprite.update(dt)
        self.health_animator.update(dt)


class CombatSystem:
    """Manages turn-based combat."""

    def __init__(self, player: Fighter, enemy: Fighter):
        self.player = player
        self.enemy = enemy
        self.turn = 0
        self.combat_log: List[str] = []
        self.combat_over = False
        self.player_won = False

        # Determine turn order based on speed
        self.turn_order = self._determine_turn_order()

    def _determine_turn_order(self) -> List[Fighter]:
        """Determine who goes first based on speed."""
        if self.player.get_total_speed() >= self.enemy.get_total_speed():
            return [self.player, self.enemy]
        else:
            return [self.enemy, self.player]

    def execute_turn(self) -> List[str]:
        """Execute one turn of combat. Returns log messages."""
        if self.combat_over:
            return []

        messages = []
        attacker = self.turn_order[self.turn % 2]
        defender = self.enemy if attacker == self.player else self.player

        # Calculate hit chance (80-95% based on speed)
        hit_chance = 0.8 + (attacker.get_total_speed() - 1.0) * 0.15
        hit_chance = max(0.7, min(0.95, hit_chance))

        # Start attack animation
        attacker.sprite.start_attack_animation(duration=0.5)
        
        if random.random() < hit_chance:
            # Hit!
            damage = attacker.get_total_damage()
            # Add some variance
            damage = int(damage * random.uniform(0.85, 1.15))

            actual_damage = defender.take_damage(damage)
            
            # Trigger hit expression on defender
            defender.sprite.start_hit_animation(duration=0.4)

            messages.append(f"{attacker.name} attacks {defender.name} for {actual_damage} damage!")

            # Check for special effects
            if attacker.weapon and attacker.weapon.stats.special_effect:
                if random.random() < 0.3:  # 30% chance to trigger
                    messages.append(f"  → {attacker.weapon.stats.special_effect}!")
        else:
            # Miss!
            messages.append(f"{attacker.name} attacks but misses!")

        # Check if combat is over
        if not self.player.is_alive():
            self.combat_over = True
            self.player_won = False
            self.player.sprite.start_defeated_animation()
            messages.append(f"{self.enemy.name} wins!")
        elif not self.enemy.is_alive():
            self.combat_over = True
            self.player_won = True
            self.enemy.sprite.start_defeated_animation()
            messages.append(f"{self.player.name} wins!")

        self.combat_log.extend(messages)
        self.turn += 1

        return messages


class CombatRenderer:
    """Renders combat state to screen."""

    def __init__(self, font: pygame.font.Font, small_font: pygame.font.Font):
        self.font = font
        self.small_font = small_font
    
    def _draw_rounded_rect(self, surface: pygame.Surface, color: tuple, rect: tuple, radius: int):
        """Draw a rounded rectangle."""
        x, y, w, h = rect
        pygame.draw.rect(surface, color, (x + radius, y, w - 2 * radius, h))
        pygame.draw.rect(surface, color, (x, y + radius, w, h - 2 * radius))
        pygame.draw.circle(surface, color, (x + radius, y + radius), radius)
        pygame.draw.circle(surface, color, (x + w - radius, y + radius), radius)
        pygame.draw.circle(surface, color, (x + radius, y + h - radius), radius)
        pygame.draw.circle(surface, color, (x + w - radius, y + h - radius), radius)
    
    def _draw_rounded_rect_outline(self, surface: pygame.Surface, color: tuple, rect: tuple, radius: int, width: int):
        """Draw a rounded rectangle outline."""
        x, y, w, h = rect
        # Draw straight edges
        pygame.draw.line(surface, color, (x + radius, y), (x + w - radius, y), width)
        pygame.draw.line(surface, color, (x + radius, y + h), (x + w - radius, y + h), width)
        pygame.draw.line(surface, color, (x, y + radius), (x, y + h - radius), width)
        pygame.draw.line(surface, color, (x + w, y + radius), (x + w, y + h - radius), width)
        # Draw rounded corners
        pygame.draw.arc(surface, color, (x, y, radius * 2, radius * 2), math.pi / 2, math.pi, width)
        pygame.draw.arc(surface, color, (x + w - radius * 2, y, radius * 2, radius * 2), 0, math.pi / 2, width)
        pygame.draw.arc(surface, color, (x, y + h - radius * 2, radius * 2, radius * 2), math.pi, 3 * math.pi / 2, width)
        pygame.draw.arc(surface, color, (x + w - radius * 2, y + h - radius * 2, radius * 2, radius * 2), 3 * math.pi / 2, 2 * math.pi, width)
    
    def _draw_rounded_rect_with_gradient(self, surface: pygame.Surface, color_start: tuple, color_end: tuple, rect: tuple, radius: int):
        """Draw a rounded rectangle with vertical gradient."""
        x, y, w, h = rect
        if w <= 0 or h <= 0:
            return
        
        # Create gradient surface
        gradient_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        
        # Helper function to check if point is inside rounded rect
        def point_in_rounded_rect(px: int, py: int) -> bool:
            # Check if in main rectangle area
            if radius <= px < w - radius and 0 <= py < h:
                return True
            if 0 <= px < w and radius <= py < h - radius:
                return True
            # Check corners
            corners = [
                (radius, radius, radius),  # top-left
                (w - radius, radius, radius),  # top-right
                (radius, h - radius, radius),  # bottom-left
                (w - radius, h - radius, radius)  # bottom-right
            ]
            for cx, cy, r in corners:
                dx = px - cx
                dy = py - cy
                if dx * dx + dy * dy <= r * r:
                    return True
            return False
        
        # Draw gradient pixel by pixel
        for py in range(h):
            # Calculate gradient color for this row
            ratio = py / h if h > 0 else 0
            r = int(color_start[0] * (1 - ratio) + color_end[0] * ratio)
            g = int(color_start[1] * (1 - ratio) + color_end[1] * ratio)
            b = int(color_start[2] * (1 - ratio) + color_end[2] * ratio)
            
            for px in range(w):
                if point_in_rounded_rect(px, py):
                    gradient_surf.set_at((px, py), (r, g, b, 255))
        
        # Blit to surface
        surface.blit(gradient_surf, (x, y))

    def render_fighter(
        self,
        surface: pygame.Surface,
        fighter: Fighter,
        center_x: int,
        y: int,
        is_player: bool
    ):
        """Render a fighter's status with sprite, centered in column."""
        # Column width for centering
        column_width = 250
        
        # Draw name above sprite (centered)
        name_surf = self.font.render(fighter.name, True, (255, 255, 255))
        name_rect = name_surf.get_rect(center=(center_x, y))
        surface.blit(name_surf, name_rect)
        
        # Draw character sprite (centered)
        sprite_x = center_x - fighter.sprite.size // 2
        sprite_y = y + 40  # Position sprite below name
        
        # Draw ground platform (oval) under character - BEFORE sprite so it appears behind
        platform_width = fighter.sprite.size + 20
        platform_height = 15
        platform_x = center_x - platform_width // 2
        platform_y = sprite_y + fighter.sprite.size - 5  # Position at character's feet
        
        # Ground platform with gradient
        platform_surf = pygame.Surface((platform_width, platform_height), pygame.SRCALPHA)
        # Draw oval shape
        pygame.draw.ellipse(platform_surf, (80, 60, 40), (0, 0, platform_width, platform_height))
        # Add darker edge
        pygame.draw.ellipse(platform_surf, (60, 45, 30), (0, 0, platform_width, platform_height), 2)
        # Add highlight on top
        highlight_surf = pygame.Surface((platform_width, platform_height // 2), pygame.SRCALPHA)
        pygame.draw.ellipse(highlight_surf, (100, 75, 50, 100), (0, 0, platform_width, platform_height))
        platform_surf.blit(highlight_surf, (0, 0))
        surface.blit(platform_surf, (platform_x, platform_y))
        
        # Now draw character sprite on top
        fighter.sprite.render(surface, sprite_x, sprite_y, facing_right=is_player)

        # Draw health bar below sprite with spacing (centered)
        bar_width = 200
        bar_height = 20
        bar_x = center_x - bar_width // 2
        bar_y = sprite_y + fighter.sprite.size + 30  # Increased spacing from 10 to 30
        
        # Get animated health and hit scale
        displayed_health = fighter.health_animator.get_displayed_health()
        hit_scale = fighter.health_animator.get_hit_scale()
        
        # Apply hit scale to bar dimensions
        scaled_width = int(bar_width * hit_scale)
        scaled_height = int(bar_height * hit_scale)
        scaled_x = bar_x + (bar_width - scaled_width) // 2
        scaled_y = bar_y + (bar_height - scaled_height) // 2

        # Border radius
        border_radius = 4
        
        # Background with rounded corners
        self._draw_rounded_rect(surface, (60, 60, 60), (scaled_x, scaled_y, scaled_width, scaled_height), border_radius)

        # Health (animated) with gradient
        health_width = int(scaled_width * displayed_health)
        if health_width > 0:
            if is_player:
                # Green gradient for player
                color_start = (120, 220, 120)
                color_end = (80, 180, 80)
            else:
                # Red gradient for enemy
                color_start = (220, 120, 120)
                color_end = (180, 80, 80)
            
            self._draw_rounded_rect_with_gradient(
                surface, 
                color_start, 
                color_end,
                (scaled_x, scaled_y, health_width, scaled_height), 
                border_radius
            )

        # Border with rounded corners
        self._draw_rounded_rect_outline(surface, (200, 200, 200), (scaled_x, scaled_y, scaled_width, scaled_height), border_radius, 2)

        # Health text (centered below bar)
        health_text = f"{fighter.current_health} / {fighter.max_health}"
        health_surf = self.small_font.render(health_text, True, (255, 255, 255))
        health_text_rect = health_surf.get_rect(center=(center_x, bar_y + bar_height + 15))
        surface.blit(health_surf, health_text_rect)

        # Draw stats (centered)
        stats_y = bar_y + bar_height + 35
        stats = [
            f"Damage: {fighter.get_total_damage()}",
            f"Armor: {fighter.get_total_armor()}",
            f"Speed: {fighter.get_total_speed():.2f}x"
        ]

        for i, stat in enumerate(stats):
            stat_surf = self.small_font.render(stat, True, (200, 200, 200))
            stat_rect = stat_surf.get_rect(center=(center_x, stats_y + i * 25))
            surface.blit(stat_surf, stat_rect)

        # Draw equipped items (centered)
        items_y = stats_y + len(stats) * 25 + 10
        items_surf = self.small_font.render("Equipment:", True, (255, 255, 100))
        items_rect = items_surf.get_rect(center=(center_x, items_y))
        surface.blit(items_surf, items_rect)

        equipment = [
            ("Weapon", fighter.weapon),
            ("Armor", fighter.armor),
            ("Buff", fighter.concoction)
        ]

        for i, (label, item) in enumerate(equipment):
            item_name = item.name if item else "None"
            item_text = f"{label}: {item_name}"
            item_surf = self.small_font.render(item_text, True, (180, 180, 180))
            item_rect = item_surf.get_rect(center=(center_x, items_y + 25 + i * 22))
            surface.blit(item_surf, item_rect)

    def render_combat_log(
        self,
        surface: pygame.Surface,
        combat_log: List[str],
        x: int,
        y: int,
        max_lines: int = 6
    ):
        """Render combat log messages."""
        title_surf = self.font.render("Combat Log:", True, (255, 255, 100))
        title_rect = title_surf.get_rect(center=(x + 150, y))
        surface.blit(title_surf, title_rect)

        # Show last N messages (centered)
        recent_messages = combat_log[-max_lines:]

        for i, message in enumerate(recent_messages):
            msg_surf = self.small_font.render(message, True, (220, 220, 220))
            msg_rect = msg_surf.get_rect(center=(x + 150, y + 35 + i * 22))
            surface.blit(msg_surf, msg_rect)
