"""Core game engine for Fightcraft."""
import pygame
from typing import Optional
from abc import ABC, abstractmethod


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
            self.screen.fill((40, 40, 40))  # Dark gray background
            if self.current_scene:
                self.current_scene.render()

            pygame.display.flip()

        pygame.quit()

    def quit(self):
        """Stop the game loop."""
        self.running = False
