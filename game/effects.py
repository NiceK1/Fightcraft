"""Effect system for combat abilities and special effects."""
import pygame
import random
import math
from enum import Enum
from typing import Optional, List, Tuple
from dataclasses import dataclass


class EffectType(Enum):
    """Types of effects that can be applied in combat."""
    FIRE = "fire"  # DoT (damage over time)
    LIFESTEAL = "lifesteal"  # Heal attacker for % of damage
    POISON = "poison"  # Weaker DoT, lasts longer
    CRITICAL = "critical"  # Bonus damage multiplier
    BLEED = "bleed"  # Physical DoT
    FREEZE = "freeze"  # Slow/reduce speed
    LIGHTNING = "lightning"  # Instant bonus damage
    REFLECT = "reflect"  # Return % of damage to attacker
    SHIELD = "shield"  # Block/reduce next hit
    VAMPIRIC = "vampiric"  # Similar to lifesteal but more powerful


@dataclass
class EffectData:
    """Data for a special effect."""
    effect_type: EffectType
    power: float  # Magnitude of effect (e.g., 0.5 = 50% for lifesteal, 10 = 10 damage for fire)
    description: str  # Human-readable description


class ActiveEffect:
    """An active effect applied to a fighter."""

    def __init__(self, effect_type: EffectType, power: float, duration: int, source_name: str = ""):
        self.effect_type = effect_type
        self.power = power
        self.duration = duration  # Turns remaining
        self.source_name = source_name  # Who applied this effect
        self.stacks = 1  # Some effects can stack

    def tick(self) -> Tuple[int, str]:
        """Process one turn of this effect. Returns (damage, message)."""
        self.duration -= 1

        # DoT effects deal damage each turn
        if self.effect_type in [EffectType.FIRE, EffectType.POISON, EffectType.BLEED]:
            damage = int(self.power * self.stacks)
            effect_name = self.effect_type.value.title()
            return damage, f"{effect_name} deals {damage} damage!"

        return 0, ""

    def is_expired(self) -> bool:
        """Check if effect has expired."""
        return self.duration <= 0


class EffectManager:
    """Manages active effects on a fighter."""

    def __init__(self):
        self.active_effects: List[ActiveEffect] = []

    def add_effect(self, effect: ActiveEffect):
        """Add a new effect or stack existing one."""
        # Check if same effect type already exists
        for existing in self.active_effects:
            if existing.effect_type == effect.effect_type:
                # Stack certain effects
                if effect.effect_type in [EffectType.BLEED, EffectType.POISON]:
                    existing.stacks += 1
                    existing.duration = max(existing.duration, effect.duration)
                else:
                    # Refresh duration
                    existing.duration = max(existing.duration, effect.duration)
                return

        # Add new effect
        self.active_effects.append(effect)

    def process_turn(self) -> Tuple[int, List[str]]:
        """Process all active effects for one turn. Returns (total_damage, messages)."""
        total_damage = 0
        messages = []

        for effect in self.active_effects[:]:
            damage, message = effect.tick()
            total_damage += damage
            if message:
                messages.append(message)

            # Remove expired effects
            if effect.is_expired():
                self.active_effects.remove(effect)

        return total_damage, messages

    def get_stat_modifiers(self) -> dict:
        """Get stat modifiers from active effects."""
        modifiers = {
            "damage_multiplier": 1.0,
            "speed_multiplier": 1.0,
            "armor_bonus": 0,
            "damage_reduction": 0.0
        }

        for effect in self.active_effects:
            if effect.effect_type == EffectType.FREEZE:
                modifiers["speed_multiplier"] *= (1.0 - effect.power)
            elif effect.effect_type == EffectType.SHIELD:
                modifiers["armor_bonus"] += int(effect.power)

        return modifiers

    def has_effect(self, effect_type: EffectType) -> bool:
        """Check if a specific effect is active."""
        return any(e.effect_type == effect_type for e in self.active_effects)

    def get_effect_power(self, effect_type: EffectType) -> float:
        """Get the power of a specific effect if active."""
        for effect in self.active_effects:
            if effect.effect_type == effect_type:
                return effect.power
        return 0.0


# Effect pool for AI to choose from
EFFECT_POOL = [
    {
        "type": "fire",
        "name": "Burning Strike",
        "description": "Sets enemies ablaze",
        "applies_to": ["weapon"]
    },
    {
        "type": "lifesteal",
        "name": "Vampiric Touch",
        "description": "Drains life from enemies",
        "applies_to": ["weapon"]
    },
    {
        "type": "poison",
        "name": "Toxic Coating",
        "description": "Poisons enemies over time",
        "applies_to": ["weapon"]
    },
    {
        "type": "critical",
        "name": "Deadly Precision",
        "description": "Chance for devastating strikes",
        "applies_to": ["weapon"]
    },
    {
        "type": "bleed",
        "name": "Rending Slash",
        "description": "Causes bleeding wounds",
        "applies_to": ["weapon"]
    },
    {
        "type": "freeze",
        "name": "Frost Aura",
        "description": "Slows enemy movement",
        "applies_to": ["armor"]
    },
    {
        "type": "lightning",
        "name": "Thunder Strike",
        "description": "Deals bonus lightning damage",
        "applies_to": ["weapon"]
    },
    {
        "type": "reflect",
        "name": "Thorns",
        "description": "Reflects damage back to attacker",
        "applies_to": ["armor"]
    },
    {
        "type": "shield",
        "name": "Fortified",
        "description": "Provides additional protection",
        "applies_to": ["armor"]
    },
    {
        "type": "vampiric",
        "name": "Blood Drain",
        "description": "Significantly heals on hit",
        "applies_to": ["weapon"]
    }
]


class EffectParticle:
    """Visual particle for effect animations."""

    def __init__(self, x: float, y: float, effect_type: EffectType):
        self.x = x
        self.y = y
        self.effect_type = effect_type
        self.lifetime = 1.0  # Seconds
        self.age = 0.0

        # Particle properties based on effect type
        if effect_type == EffectType.FIRE:
            self.vx = random.uniform(-20, 20)
            self.vy = random.uniform(-80, -40)
            self.color_start = (255, 100, 0)
            self.color_end = (255, 0, 0)
            self.size_start = 16
            self.size_end = 4
        elif effect_type == EffectType.POISON:
            self.vx = random.uniform(-15, 15)
            self.vy = random.uniform(-40, -20)
            self.color_start = (100, 255, 100)
            self.color_end = (0, 150, 0)
            self.size_start = 12
            self.size_end = 5
        elif effect_type == EffectType.LIGHTNING:
            self.vx = random.uniform(-30, 30)
            self.vy = random.uniform(-60, 60)
            self.color_start = (200, 200, 255)
            self.color_end = (100, 100, 255)
            self.size_start = 18
            self.size_end = 2
        elif effect_type == EffectType.FREEZE:
            self.vx = random.uniform(-10, 10)
            self.vy = random.uniform(-30, -10)
            self.color_start = (150, 200, 255)
            self.color_end = (200, 230, 255)
            self.size_start = 10
            self.size_end = 4
        elif effect_type == EffectType.BLEED:
            self.vx = random.uniform(-25, 25)
            self.vy = random.uniform(-50, -20)
            self.color_start = (200, 0, 0)
            self.color_end = (100, 0, 0)
            self.size_start = 12
            self.size_end = 4
        else:  # Default
            self.vx = random.uniform(-20, 20)
            self.vy = random.uniform(-40, -20)
            self.color_start = (255, 255, 255)
            self.color_end = (200, 200, 200)
            self.size_start = 12
            self.size_end = 4

    def update(self, dt: float):
        """Update particle position and age."""
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.age += dt

        # Apply gravity for some effects
        if self.effect_type in [EffectType.FIRE, EffectType.BLEED]:
            self.vy += 100 * dt  # Gravity

    def is_dead(self) -> bool:
        """Check if particle should be removed."""
        return self.age >= self.lifetime

    def render(self, surface: pygame.Surface):
        """Render the particle."""
        if self.is_dead():
            return

        # Interpolate properties based on age
        progress = self.age / self.lifetime

        # Interpolate color
        r = int(self.color_start[0] * (1 - progress) + self.color_end[0] * progress)
        g = int(self.color_start[1] * (1 - progress) + self.color_end[1] * progress)
        b = int(self.color_start[2] * (1 - progress) + self.color_end[2] * progress)

        # Interpolate size
        size = int(self.size_start * (1 - progress) + self.size_end * progress)

        # Fade out alpha
        alpha = int(255 * (1 - progress))

        if size > 0:
            # Create particle surface with alpha
            particle_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(particle_surf, (r, g, b, alpha), (size, size), size)
            surface.blit(particle_surf, (int(self.x - size), int(self.y - size)))


class EffectAnimator:
    """Manages particle effects and animations."""

    def __init__(self):
        self.particles: List[EffectParticle] = []

    def spawn_effect(self, x: float, y: float, effect_type: EffectType, count: int = 20):
        """Spawn particles for an effect."""
        for _ in range(count):
            self.particles.append(EffectParticle(x, y, effect_type))

    def update(self, dt: float):
        """Update all particles."""
        for particle in self.particles[:]:
            particle.update(dt)
            if particle.is_dead():
                self.particles.remove(particle)

    def render(self, surface: pygame.Surface):
        """Render all particles."""
        for particle in self.particles:
            particle.render(surface)
