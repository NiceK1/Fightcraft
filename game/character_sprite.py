"""Character sprite system with animations and equipment layering."""
import pygame
import random
import math
from typing import Optional, Dict, List
from enum import Enum
from game.item import Item


class AnimationState(Enum):
    """Character animation states."""
    IDLE = "idle"
    ATTACK = "attack"
    HIT = "hit"
    VICTORY = "victory"
    DEFEATED = "defeated"


class FaceExpression(Enum):
    """Face expressions."""
    NEUTRAL = "neutral"  # Straight mouth
    HIT = "hit"  # Frown/displeased
    ATTACK = "attack"  # Grin/smirk


class CharacterSprite:
    """Manages character sprite rendering with animations and equipment."""

    def __init__(self, base_color: tuple = (100, 150, 200), size: int = 128):
        """
        Initialize character sprite.

        Args:
            base_color: Base color for the character
            size: Size of the sprite
        """
        self.size = size
        self.base_color = base_color
        self.current_state = AnimationState.IDLE
        self.animation_timer = 0.0
        self.animation_duration = 0.0
        
        # Face expression
        self.face_expression = FaceExpression.NEUTRAL
        self.face_expression_timer = 0.0
        self.face_expression_duration = 0.0
        
        # Equipment layers
        self.weapon_sprite: Optional[pygame.Surface] = None
        self.armor_sprite: Optional[pygame.Surface] = None
        
        # Generate base character sprite (without mouth - will be drawn dynamically)
        self.base_sprite = self._generate_base_sprite()
        
        # Animation offsets (for attack motion)
        self.offset_x = 0
        self.offset_y = 0
        
        # Rotation for defeated animation
        self.rotation = 0.0
        
    def _generate_base_sprite(self) -> pygame.Surface:
        """Generate a detailed base character sprite."""
        sprite = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        center_x = self.size // 2
        
        # Body (torso) - more detailed with better proportions
        body_top = center_x - 5
        body_width = 44
        body_height = 55
        body_rect = pygame.Rect(
            center_x - body_width // 2,
            body_top,
            body_width,
            body_height
        )
        
        # Main body with gradient-like shading
        pygame.draw.ellipse(sprite, self.base_color, body_rect)
        
        # Add darker shading on sides
        shadow_color = tuple(max(0, c - 30) for c in self.base_color)
        shadow_left = pygame.Rect(body_rect.x, body_rect.y, body_width // 3, body_height)
        shadow_right = pygame.Rect(body_rect.right - body_width // 3, body_rect.y, body_width // 3, body_height)
        pygame.draw.ellipse(sprite, shadow_color, shadow_left)
        pygame.draw.ellipse(sprite, shadow_color, shadow_right)
        
        # Add highlight on top
        highlight_rect = pygame.Rect(
            center_x - 15,
            body_top + 3,
            30,
            20
        )
        highlight_surf = pygame.Surface((highlight_rect.width, highlight_rect.height), pygame.SRCALPHA)
        highlight_color = tuple(min(255, c + 40) for c in self.base_color)
        pygame.draw.ellipse(highlight_surf, (*highlight_color, 60), (0, 0, highlight_rect.width, highlight_rect.height))
        sprite.blit(highlight_surf, highlight_rect.topleft)
        
        # Body outline
        pygame.draw.ellipse(sprite, (0, 0, 0), body_rect, 2)
        
        # Add chest detail (simple line)
        chest_y = body_top + body_height // 3
        pygame.draw.line(sprite, (0, 0, 0, 100), 
                        (center_x - 8, chest_y), 
                        (center_x + 8, chest_y), 1)
        
        # Neck
        neck_width = 12
        neck_height = 8
        neck_rect = pygame.Rect(center_x - neck_width // 2, body_top - neck_height, neck_width, neck_height)
        pygame.draw.ellipse(sprite, (255, 220, 180), neck_rect)
        pygame.draw.ellipse(sprite, (0, 0, 0), neck_rect, 1)
        
        # Head - positioned closer to body (neck connection)
        head_radius = 22
        # Head should connect to body, so it's positioned at body_top - head_radius + overlap
        head_center_y = body_top - head_radius + 6  # 6 pixels overlap for neck
        head_center = (center_x, head_center_y)
        
        # Head with shading
        pygame.draw.circle(sprite, (255, 220, 180), head_center, head_radius)
        # Add shadow on bottom of head
        shadow_surf = pygame.Surface((head_radius * 2, head_radius), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (200, 180, 160, 100), (0, 0, head_radius * 2, head_radius))
        sprite.blit(shadow_surf, (head_center[0] - head_radius, head_center[1]))
        # Add highlight on top
        highlight_surf = pygame.Surface((head_radius * 2, head_radius), pygame.SRCALPHA)
        pygame.draw.ellipse(highlight_surf, (255, 240, 200, 80), (0, 0, head_radius * 2, head_radius))
        sprite.blit(highlight_surf, (head_center[0] - head_radius, head_center[1] - head_radius))
        
        pygame.draw.circle(sprite, (0, 0, 0), head_center, head_radius, 2)
        
        # Face details - more expressive
        eye_y = head_center[1] - 3
        eye_size = 4
        # Eyes with more detail
        pygame.draw.circle(sprite, (255, 255, 255), (head_center[0] - 7, eye_y), eye_size)
        pygame.draw.circle(sprite, (255, 255, 255), (head_center[0] + 7, eye_y), eye_size)
        pygame.draw.circle(sprite, (0, 0, 0), (head_center[0] - 7, eye_y), eye_size - 1)
        pygame.draw.circle(sprite, (0, 0, 0), (head_center[0] + 7, eye_y), eye_size - 1)
        # Eye highlights
        pygame.draw.circle(sprite, (255, 255, 255), (head_center[0] - 6, eye_y - 1), 2)
        pygame.draw.circle(sprite, (255, 255, 255), (head_center[0] + 8, eye_y - 1), 2)
        
        # Eyebrows
        eyebrow_y = eye_y - 5
        pygame.draw.arc(sprite, (0, 0, 0), (head_center[0] - 12, eyebrow_y - 3, 8, 4), 0, math.pi, 2)
        pygame.draw.arc(sprite, (0, 0, 0), (head_center[0] + 4, eyebrow_y - 3, 8, 4), 0, math.pi, 2)
        
        # Nose - more defined
        nose_y = head_center[1] + 2
        pygame.draw.ellipse(sprite, (200, 180, 160), (center_x - 2, nose_y, 4, 5))
        pygame.draw.line(sprite, (0, 0, 0), (center_x, nose_y), (center_x, nose_y + 3), 1)
        
        # Mouth will be drawn dynamically based on expression
        # Store mouth position for later (as instance variables)
        self.mouth_y = head_center[1] + 9
        self.mouth_center_x = center_x
        
        # Shoulders
        shoulder_y = body_top + 5
        pygame.draw.circle(sprite, self.base_color, (center_x - 20, shoulder_y), 8)
        pygame.draw.circle(sprite, self.base_color, (center_x + 20, shoulder_y), 8)
        pygame.draw.circle(sprite, (0, 0, 0), (center_x - 20, shoulder_y), 8, 1)
        pygame.draw.circle(sprite, (0, 0, 0), (center_x + 20, shoulder_y), 8, 1)
        
        # Arms - more dynamic with better shading
        arm_width = 11
        arm_y = center_x - 2
        # Left arm
        arm_left_x = center_x - 32
        pygame.draw.ellipse(sprite, self.base_color, (arm_left_x, arm_y, arm_width, 38))
        # Arm shading
        shadow_surf = pygame.Surface((arm_width // 2, 38), pygame.SRCALPHA)
        shadow_color = tuple(max(0, c - 25) for c in self.base_color)
        pygame.draw.ellipse(shadow_surf, (*shadow_color, 150), (0, 0, arm_width // 2, 38))
        sprite.blit(shadow_surf, (arm_left_x, arm_y))
        pygame.draw.ellipse(sprite, (0, 0, 0), (arm_left_x, arm_y, arm_width, 38), 2)
        
        # Right arm
        arm_right_x = center_x + 21
        pygame.draw.ellipse(sprite, self.base_color, (arm_right_x, arm_y, arm_width, 38))
        # Arm shading
        sprite.blit(shadow_surf, (arm_right_x + arm_width // 2, arm_y))
        pygame.draw.ellipse(sprite, (0, 0, 0), (arm_right_x, arm_y, arm_width, 38), 2)
        
        # Elbows (subtle detail)
        elbow_y = arm_y + 19
        pygame.draw.circle(sprite, tuple(max(0, c - 20) for c in self.base_color), (arm_left_x + arm_width // 2, elbow_y), 3)
        pygame.draw.circle(sprite, tuple(max(0, c - 20) for c in self.base_color), (arm_right_x + arm_width // 2, elbow_y), 3)
        
        # Hands - more detailed
        hand_size = 9
        hand_left_x = center_x - 28
        hand_right_x = center_x + 28
        hand_y = arm_y + 38
        
        # Left hand
        pygame.draw.circle(sprite, (255, 220, 180), (hand_left_x, hand_y), hand_size)
        pygame.draw.circle(sprite, (0, 0, 0), (hand_left_x, hand_y), hand_size, 1)
        # Fingers hint
        pygame.draw.line(sprite, (0, 0, 0), (hand_left_x - 3, hand_y + 5), (hand_left_x - 3, hand_y + 8), 1)
        pygame.draw.line(sprite, (0, 0, 0), (hand_left_x, hand_y + 5), (hand_left_x, hand_y + 8), 1)
        pygame.draw.line(sprite, (0, 0, 0), (hand_left_x + 3, hand_y + 5), (hand_left_x + 3, hand_y + 8), 1)
        
        # Right hand
        pygame.draw.circle(sprite, (255, 220, 180), (hand_right_x, hand_y), hand_size)
        pygame.draw.circle(sprite, (0, 0, 0), (hand_right_x, hand_y), hand_size, 1)
        # Fingers hint
        pygame.draw.line(sprite, (0, 0, 0), (hand_right_x - 3, hand_y + 5), (hand_right_x - 3, hand_y + 8), 1)
        pygame.draw.line(sprite, (0, 0, 0), (hand_right_x, hand_y + 5), (hand_right_x, hand_y + 8), 1)
        pygame.draw.line(sprite, (0, 0, 0), (hand_right_x + 3, hand_y + 5), (hand_right_x + 3, hand_y + 8), 1)
        
        # Hips/waist detail
        waist_y = body_top + body_height - 5
        pygame.draw.line(sprite, (0, 0, 0), (center_x - 15, waist_y), (center_x + 15, waist_y), 1)
        
        # Legs - more detailed with better proportions
        leg_width = 13
        leg_y = center_x + 50
        leg_color = (60, 60, 120)
        leg_height = 35
        
        # Left leg
        leg_left_x = center_x - 18
        pygame.draw.ellipse(sprite, leg_color, (leg_left_x, leg_y, leg_width, leg_height))
        # Leg shading
        leg_shadow = pygame.Surface((leg_width // 2, leg_height), pygame.SRCALPHA)
        leg_shadow_color = tuple(max(0, c - 20) for c in leg_color)
        pygame.draw.ellipse(leg_shadow, (*leg_shadow_color, 150), (0, 0, leg_width // 2, leg_height))
        sprite.blit(leg_shadow, (leg_left_x, leg_y))
        pygame.draw.ellipse(sprite, (0, 0, 0), (leg_left_x, leg_y, leg_width, leg_height), 2)
        
        # Right leg
        leg_right_x = center_x + 5
        pygame.draw.ellipse(sprite, leg_color, (leg_right_x, leg_y, leg_width, leg_height))
        sprite.blit(leg_shadow, (leg_right_x + leg_width // 2, leg_y))
        pygame.draw.ellipse(sprite, (0, 0, 0), (leg_right_x, leg_y, leg_width, leg_height), 2)
        
        # Knees
        knee_y = leg_y + leg_height // 2
        pygame.draw.circle(sprite, leg_shadow_color, (leg_left_x + leg_width // 2, knee_y), 4)
        pygame.draw.circle(sprite, leg_shadow_color, (leg_right_x + leg_width // 2, knee_y), 4)
        
        # Feet - more detailed
        foot_width = 14
        foot_height = 10
        foot_y = leg_y + leg_height
        
        # Left foot
        foot_left_x = center_x - 20
        pygame.draw.ellipse(sprite, (40, 40, 80), (foot_left_x, foot_y, foot_width, foot_height))
        pygame.draw.ellipse(sprite, (0, 0, 0), (foot_left_x, foot_y, foot_width, foot_height), 1)
        # Toes hint
        pygame.draw.line(sprite, (0, 0, 0), (foot_left_x + 3, foot_y + foot_height), (foot_left_x + 3, foot_y + foot_height + 2), 1)
        pygame.draw.line(sprite, (0, 0, 0), (foot_left_x + foot_width // 2, foot_y + foot_height), (foot_left_x + foot_width // 2, foot_y + foot_height + 2), 1)
        pygame.draw.line(sprite, (0, 0, 0), (foot_left_x + foot_width - 3, foot_y + foot_height), (foot_left_x + foot_width - 3, foot_y + foot_height + 2), 1)
        
        # Right foot
        foot_right_x = center_x + 6
        pygame.draw.ellipse(sprite, (40, 40, 80), (foot_right_x, foot_y, foot_width, foot_height))
        pygame.draw.ellipse(sprite, (0, 0, 0), (foot_right_x, foot_y, foot_width, foot_height), 1)
        # Toes hint
        pygame.draw.line(sprite, (0, 0, 0), (foot_right_x + 3, foot_y + foot_height), (foot_right_x + 3, foot_y + foot_height + 2), 1)
        pygame.draw.line(sprite, (0, 0, 0), (foot_right_x + foot_width // 2, foot_y + foot_height), (foot_right_x + foot_width // 2, foot_y + foot_height + 2), 1)
        pygame.draw.line(sprite, (0, 0, 0), (foot_right_x + foot_width - 3, foot_y + foot_height), (foot_right_x + foot_width - 3, foot_y + foot_height + 2), 1)
        
        return sprite
    
    def set_equipment(self, weapon: Optional[Item], armor: Optional[Item]):
        """Set equipment sprites."""
        self.weapon_sprite = weapon.sprite if weapon and weapon.sprite else None
        self.armor_sprite = armor.sprite if armor and armor.sprite else None
    
    def start_attack_animation(self, duration: float = 0.5):
        """Start attack animation."""
        self.current_state = AnimationState.ATTACK
        self.animation_timer = 0.0
        self.animation_duration = duration
        # Set attack expression
        self.face_expression = FaceExpression.ATTACK
        self.face_expression_timer = 0.0
        self.face_expression_duration = duration
    
    def start_hit_animation(self, duration: float = 0.4):
        """Start hit animation."""
        self.face_expression = FaceExpression.HIT
        self.face_expression_timer = 0.0
        self.face_expression_duration = duration
    
    def start_defeated_animation(self):
        """Start defeated (falling) animation."""
        self.current_state = AnimationState.DEFEATED
        self.animation_timer = 0.0
        self.animation_duration = 1.0  # 1 second to fall
    
    def update(self, dt: float):
        """Update animation state."""
        if self.current_state == AnimationState.ATTACK:
            self.animation_timer += dt
            if self.animation_timer >= self.animation_duration:
                self.current_state = AnimationState.IDLE
                self.offset_x = 0
                self.offset_y = 0
            else:
                # Attack motion: move forward and back
                progress = self.animation_timer / self.animation_duration
                # Ease in-out curve
                if progress < 0.5:
                    t = progress * 2
                    self.offset_x = int(30 * t * (2 - t))
                else:
                    t = (progress - 0.5) * 2
                    self.offset_x = int(30 * (1 - t * t))
        
        elif self.current_state == AnimationState.DEFEATED:
            self.animation_timer += dt
            if self.animation_timer < self.animation_duration:
                # Fall animation: rotate and move down
                progress = min(self.animation_timer / self.animation_duration, 1.0)
                # Rotate from 0 to 90 degrees (falling on side)
                self.rotation = 90 * progress
                # Move down slightly
                self.offset_y = int(20 * progress)
            else:
                # Keep fallen state
                self.rotation = 90
                self.offset_y = 20
        
        # Update face expression timer
        if self.face_expression_timer < self.face_expression_duration:
            self.face_expression_timer += dt
        else:
            # Reset to neutral after expression duration
            if self.current_state != AnimationState.ATTACK:
                self.face_expression = FaceExpression.NEUTRAL
            elif self.current_state == AnimationState.ATTACK and self.animation_timer >= self.animation_duration:
                self.face_expression = FaceExpression.NEUTRAL
    
    def render(self, surface: pygame.Surface, x: int, y: int, facing_right: bool = True):
        """
        Render character sprite with equipment.
        
        Args:
            surface: Target surface
            x: X position
            y: Y position
            facing_right: Whether character faces right
        """
        # Apply animation offset
        render_x = x + self.offset_x
        render_y = y + self.offset_y
        
        # Flip sprite if facing left
        sprite_to_render = self.base_sprite
        if not facing_right:
            sprite_to_render = pygame.transform.flip(self.base_sprite, True, False)
        
        # Rotate if defeated
        if self.current_state == AnimationState.DEFEATED and self.rotation > 0:
            sprite_to_render = pygame.transform.rotate(sprite_to_render, self.rotation)
            # Adjust position after rotation to keep center point
            rotated_rect = sprite_to_render.get_rect(center=(render_x + self.size // 2, render_y + self.size // 2))
            render_x = rotated_rect.x
            render_y = rotated_rect.y
        
        # Draw base character
        surface.blit(sprite_to_render, (render_x, render_y))
        
        # Draw mouth based on expression (after rotation/flip)
        # If rotated, we need to account for rotation
        if self.current_state == AnimationState.DEFEATED and self.rotation > 0:
            # Draw mouth on rotated surface
            mouth_surf = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            self._draw_mouth(mouth_surf, 0, 0, facing_right)
            rotated_mouth = pygame.transform.rotate(mouth_surf, self.rotation)
            mouth_rect = rotated_mouth.get_rect(center=(render_x + self.size // 2, render_y + self.size // 2))
            surface.blit(rotated_mouth, mouth_rect.topleft)
        else:
            self._draw_mouth(surface, render_x, render_y, facing_right)
        
        # Draw armor layer (also rotated if defeated)
        if self.armor_sprite:
            armor_scaled = pygame.transform.scale(self.armor_sprite, (self.size, self.size))
            if not facing_right:
                armor_scaled = pygame.transform.flip(armor_scaled, True, False)
            # Rotate armor if defeated
            if self.current_state == AnimationState.DEFEATED and self.rotation > 0:
                armor_scaled = pygame.transform.rotate(armor_scaled, self.rotation)
                armor_rect = armor_scaled.get_rect(center=(render_x + self.size // 2, render_y + self.size // 2))
                armor_x = armor_rect.x
                armor_y = armor_rect.y
            else:
                armor_x = render_x
                armor_y = render_y
            # Blend armor with character (semi-transparent overlay)
            armor_overlay = armor_scaled.copy()
            armor_overlay.set_alpha(180)
            surface.blit(armor_overlay, (armor_x, armor_y))
        
        # Draw weapon (in hand) - skip if defeated (falls with character)
        if self.weapon_sprite and self.current_state != AnimationState.DEFEATED:
            weapon_size = self.size // 2
            weapon_scaled = pygame.transform.scale(self.weapon_sprite, (weapon_size, weapon_size))
            
            # Position weapon in hand
            hand_offset_x = 28 if facing_right else -28
            hand_offset_y = 38
            
            if facing_right:
                weapon_x = render_x + self.size // 2 + hand_offset_x - weapon_size // 2 + (self.offset_x // 2)
                weapon_y = render_y + self.size // 2 - 10 + hand_offset_y - weapon_size // 2
                # Rotate weapon during attack
                if self.current_state == AnimationState.ATTACK:
                    progress = self.animation_timer / self.animation_duration
                    angle = -60 * math.sin(progress * math.pi)
                    # Rotate around hand position
                    rotated_weapon = pygame.transform.rotate(weapon_scaled, angle)
                    weapon_rect = rotated_weapon.get_rect(center=(render_x + self.size // 2 + hand_offset_x, 
                                                                  render_y + self.size // 2 - 10 + hand_offset_y))
                    surface.blit(rotated_weapon, weapon_rect.topleft)
                else:
                    surface.blit(weapon_scaled, (weapon_x, weapon_y))
            else:
                weapon_x = render_x + self.size // 2 + hand_offset_x - weapon_size // 2 - (self.offset_x // 2)
                weapon_y = render_y + self.size // 2 - 10 + hand_offset_y - weapon_size // 2
                weapon_scaled = pygame.transform.flip(weapon_scaled, True, False)
                if self.current_state == AnimationState.ATTACK:
                    progress = self.animation_timer / self.animation_duration
                    angle = 60 * math.sin(progress * math.pi)
                    rotated_weapon = pygame.transform.rotate(weapon_scaled, angle)
                    weapon_rect = rotated_weapon.get_rect(center=(render_x + self.size // 2 + hand_offset_x, 
                                                                  render_y + self.size // 2 - 10 + hand_offset_y))
                    surface.blit(rotated_weapon, weapon_rect.topleft)
                else:
                    surface.blit(weapon_scaled, (weapon_x, weapon_y))
        
        # Draw attack effect (sparkles/swing trail)
        if self.current_state == AnimationState.ATTACK:
            progress = self.animation_timer / self.animation_duration
            if progress < 0.3:  # Only show at start of attack
                self._draw_attack_effect(surface, render_x, render_y, facing_right, progress)
    
    def _draw_mouth(self, surface: pygame.Surface, x: int, y: int, facing_right: bool):
        """Draw mouth based on current expression."""
        # Calculate mouth position
        # Note: x and y already account for rotation offset, so we use relative positions
        mouth_x = x + self.mouth_center_x
        mouth_y = y + self.mouth_y
        
        # If rotated, we need to adjust (but rotation is handled in render, so this should be fine)
        # The mouth will be drawn on the rotated sprite surface, so position is relative to x, y
        
        if self.face_expression == FaceExpression.NEUTRAL:
            # Straight line (neutral)
            pygame.draw.line(surface, (0, 0, 0), 
                           (mouth_x - 6, mouth_y), 
                           (mouth_x + 6, mouth_y), 2)
        
        elif self.face_expression == FaceExpression.HIT:
            # Frown (displeased) - inverted arc
            pygame.draw.arc(surface, (0, 0, 0), 
                          (mouth_x - 7, mouth_y - 2, 14, 8), 
                          math.pi, 2 * math.pi, 2)
        
        elif self.face_expression == FaceExpression.ATTACK:
            # Grin/smirk - upward arc with slight asymmetry
            pygame.draw.arc(surface, (0, 0, 0), 
                          (mouth_x - 8, mouth_y - 4, 16, 10), 
                          0, math.pi, 2)
            # Add a small line on one side for smirk effect
            if facing_right:
                pygame.draw.line(surface, (0, 0, 0), 
                               (mouth_x + 6, mouth_y - 2), 
                               (mouth_x + 8, mouth_y - 1), 2)
            else:
                pygame.draw.line(surface, (0, 0, 0), 
                               (mouth_x - 6, mouth_y - 2), 
                               (mouth_x - 8, mouth_y - 1), 2)
    
    def _draw_attack_effect(self, surface: pygame.Surface, x: int, y: int, facing_right: bool, progress: float):
        """Draw visual effect for attack animation."""
        # Draw swing trail/sparkles
        effect_x = x + self.size // 2 + (30 if facing_right else -30)
        effect_y = y + self.size // 2
        
        # Sparkles
        for i in range(5):
            spark_x = effect_x + random.randint(-20, 20)
            spark_y = effect_y + random.randint(-20, 20)
            spark_size = random.randint(2, 4)
            spark_color = (255, 255, 200)
            pygame.draw.circle(surface, spark_color, (spark_x, spark_y), spark_size)
        
        # Swing arc (semi-transparent)
        if facing_right:
            arc_rect = pygame.Rect(effect_x - 10, effect_y - 20, 30, 40)
        else:
            arc_rect = pygame.Rect(effect_x - 20, effect_y - 20, 30, 40)
        
        # Draw arc as semi-circle
        arc_surface = pygame.Surface((arc_rect.width, arc_rect.height), pygame.SRCALPHA)
        pygame.draw.arc(arc_surface, (255, 255, 100, 150), (0, 0, arc_rect.width, arc_rect.height), 0, math.pi, 3)
        surface.blit(arc_surface, arc_rect.topleft)

