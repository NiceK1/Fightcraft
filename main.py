"""Main entry point for Fightcraft game."""
import sys
from game.engine import GameEngine
from game.scenes import MainMenuScene


def main():
    """Initialize and run the game."""
    print("=" * 60)
    print("FIGHTCRAFT - AI-Powered Crafting & Combat Game")
    print("=" * 60)
    print()
    print("Starting game...")
    print()
    print("Controls:")
    print("  - Main Menu: Arrow keys + Enter")
    print("  - Crafting: Drag & drop with mouse, ESC to combat")
    print("  - Combat: SPACE for turn, A for auto-combat, ESC to return")
    print()
    print("Make sure the AI backend is running:")
    print("  python ai_backend/server.py")
    print()
    print("=" * 60)

    try:
        # Create game engine
        game = GameEngine(width=1280, height=720, title="Fightcraft")

        # Start with main menu
        game.change_scene(MainMenuScene(game))

        # Run game loop
        game.run()

    except Exception as e:
        print(f"Error running game: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\nThanks for playing Fightcraft!")


if __name__ == "__main__":
    main()
