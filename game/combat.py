"""Combat system for Fightcraft."""
import pygame
import random
from typing import Optional, List
from game.item import Item, ItemType


class Fighter:
    """Represents a fighter in combat."""

    def __init__(self, name: str, max_health: int = 100):
        self.name = name
        self.max_health = max_health
        self.current_health = max_health

        # Equipment
        self.weapon: Optional[Item] = None
        self.armor: Optional[Item] = None
        self.concoction: Optional[Item] = None

        # Stats (base + equipment)
        self.base_damage = 5
        self.base_armor = 0
        self.base_speed = 1.0

    def equip_items(self, weapon: Optional[Item], armor: Optional[Item], concoction: Optional[Item]):
        """Equip items for combat."""
        self.weapon = weapon
        self.armor = armor
        self.concoction = concoction

        # Apply concoction effects immediately
        if concoction:
            self.current_health = min(
                self.max_health + concoction.stats.health,
                self.max_health + 50  # Cap health boost
            )

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
        return actual_damage

    def is_alive(self) -> bool:
        """Check if fighter is still alive."""
        return self.current_health > 0

    def get_health_percentage(self) -> float:
        """Get health as percentage."""
        return self.current_health / self.max_health if self.max_health > 0 else 0


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

        if random.random() < hit_chance:
            # Hit!
            damage = attacker.get_total_damage()
            # Add some variance
            damage = int(damage * random.uniform(0.85, 1.15))

            actual_damage = defender.take_damage(damage)

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
            messages.append(f"{self.enemy.name} wins!")
        elif not self.enemy.is_alive():
            self.combat_over = True
            self.player_won = True
            messages.append(f"{self.player.name} wins!")

        self.combat_log.extend(messages)
        self.turn += 1

        return messages


class CombatRenderer:
    """Renders combat state to screen."""

    def __init__(self, font: pygame.font.Font, small_font: pygame.font.Font):
        self.font = font
        self.small_font = small_font

    def render_fighter(
        self,
        surface: pygame.Surface,
        fighter: Fighter,
        x: int,
        y: int,
        is_player: bool
    ):
        """Render a fighter's status."""
        # Draw name
        name_surf = self.font.render(fighter.name, True, (255, 255, 255))
        surface.blit(name_surf, (x, y))

        # Draw health bar
        bar_width = 200
        bar_height = 20
        bar_x = x
        bar_y = y + 40

        # Background
        pygame.draw.rect(surface, (60, 60, 60), (bar_x, bar_y, bar_width, bar_height))

        # Health
        health_width = int(bar_width * fighter.get_health_percentage())
        health_color = (100, 200, 100) if is_player else (200, 100, 100)
        pygame.draw.rect(surface, health_color, (bar_x, bar_y, health_width, bar_height))

        # Border
        pygame.draw.rect(surface, (200, 200, 200), (bar_x, bar_y, bar_width, bar_height), 2)

        # Health text
        health_text = f"{fighter.current_health} / {fighter.max_health}"
        health_surf = self.small_font.render(health_text, True, (255, 255, 255))
        surface.blit(health_surf, (bar_x + bar_width + 10, bar_y))

        # Draw stats
        stats_y = bar_y + 30
        stats = [
            f"Damage: {fighter.get_total_damage()}",
            f"Armor: {fighter.get_total_armor()}",
            f"Speed: {fighter.get_total_speed():.2f}x"
        ]

        for i, stat in enumerate(stats):
            stat_surf = self.small_font.render(stat, True, (200, 200, 200))
            surface.blit(stat_surf, (x, stats_y + i * 25))

        # Draw equipped items
        items_y = stats_y + 90
        items_surf = self.small_font.render("Equipment:", True, (255, 255, 100))
        surface.blit(items_surf, (x, items_y))

        equipment = [
            ("Weapon", fighter.weapon),
            ("Armor", fighter.armor),
            ("Buff", fighter.concoction)
        ]

        for i, (label, item) in enumerate(equipment):
            item_name = item.name if item else "None"
            item_text = f"  {label}: {item_name}"
            item_surf = self.small_font.render(item_text, True, (180, 180, 180))
            surface.blit(item_surf, (x, items_y + 25 + i * 22))

    def render_combat_log(
        self,
        surface: pygame.Surface,
        combat_log: List[str],
        x: int,
        y: int,
        max_lines: int = 8
    ):
        """Render combat log messages."""
        title_surf = self.font.render("Combat Log:", True, (255, 255, 100))
        surface.blit(title_surf, (x, y))

        # Show last N messages
        recent_messages = combat_log[-max_lines:]

        for i, message in enumerate(recent_messages):
            msg_surf = self.small_font.render(message, True, (220, 220, 220))
            surface.blit(msg_surf, (x, y + 35 + i * 22))
