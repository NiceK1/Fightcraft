"""Core game engine for Fightcraft."""
import pygame
from typing import Optional, Tuple
from abc import ABC, abstractmethod


def draw_gradient_background(surface: pygame.Surface, top_color: Tuple[int, int, int], bottom_color: Tuple[int, int, int]):
    """Draw a vertical gradient background."""
    width, height = surface.get_size()
    
    # Create a surface for the gradient
    gradient_surface = pygame.Surface((width, height))
    
    # Calculate color steps
    for y in range(height):
        # Interpolate between top and bottom colors
        ratio = y / height
        r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
        g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
        b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
        
        # Draw horizontal line with interpolated color
        pygame.draw.line(gradient_surface, (r, g, b), (0, y), (width, y))
    
    # Blit the gradient surface to the main surface
    surface.blit(gradient_surface, (0, 0))


class Scene(ABC):
    """Base class for game scenes."""

    def __init__(self, game):
        self.game = game
        self.screen = game.screen

    @abstractmethod
    def handle_event(self, event: pygame.event.Event):
        """Handle pygame events."""
        pass

    @abstractmethod
    def update(self, dt: float):
        """Update scene logic."""
        pass

    @abstractmethod
    def render(self):
        """Render scene to screen."""
        pass


class GameEngine:
    """Main game engine managing game loop and scenes."""

    def __init__(self, width: int = 1280, height: int = 720, title: str = "Fightcraft"):
        pygame.init()

        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption(title)

        self.clock = pygame.time.Clock()
        self.running = False
        self.fps = 60

        self.current_scene: Optional[Scene] = None
        self.font = pygame.font.Font(None, 32)
        self.small_font = pygame.font.Font(None, 24)

    def change_scene(self, scene: Scene):
        """Change the current active scene."""
        self.current_scene = scene

    def run(self):
        """Main game loop."""
        self.running = True

        while self.running:
            dt = self.clock.tick(self.fps) / 1000.0  # Delta time in seconds

            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif self.current_scene:
                    self.current_scene.handle_event(event)

            # Update
            if self.current_scene:
                self.current_scene.update(dt)

            # Render
            # Draw gradient background (lighter at top, darker at bottom)
            draw_gradient_background(self.screen, (50, 50, 50), (30, 30, 30))
            if self.current_scene:
                self.current_scene.render()

            pygame.display.flip()

        pygame.quit()

    def quit(self):
        """Stop the game loop."""
        self.running = False
