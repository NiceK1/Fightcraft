"""Stats generation module with AI integration."""
import random
from typing import List, Dict, Any, Optional
import os


class StatsGenerator:
    """Generates item stats using AI or fallback methods."""

    def __init__(self, use_ai: bool = True, ai_provider: str = "anthropic"):
        """
        Initialize stats generator.

        Args:
            use_ai: Whether to use AI for generation
            ai_provider: 'anthropic' or 'openai'
        """
        self.use_ai = use_ai
        self.ai_provider = ai_provider
        self.client = None

        if not use_ai:
            return

        # Try Anthropic first (preferred)
        if ai_provider == "anthropic":
            try:
                import anthropic
                api_key = os.getenv("ANTHROPIC_API_KEY")
                if api_key:
                    self.client = anthropic.Anthropic(api_key=api_key)
                    print("[OK] Anthropic Claude API initialized for stats generation")
                else:
                    print("ANTHROPIC_API_KEY not found, using fallback stats generation")
                    self.use_ai = False
            except ImportError:
                print("Anthropic package not installed, using fallback stats generation")
                self.use_ai = False

        # Fallback to OpenAI
        elif ai_provider == "openai":
            try:
                import openai
                api_key = os.getenv("OPENAI_API_KEY")
                if api_key:
                    self.client = openai.OpenAI(api_key=api_key)
                    print("[OK] OpenAI API initialized for stats generation")
                else:
                    print("OPENAI_API_KEY not found, using fallback stats generation")
                    self.use_ai = False
            except ImportError:
                print("OpenAI package not installed, using fallback stats generation")
                self.use_ai = False

    def generate(
        self,
        materials: List[str],
        item_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate item stats and properties."""

        # If item_type not specified, determine automatically
        if item_type is None:
            item_type = self._determine_item_type(materials)
            print(f"Auto-determined item type: {item_type} for materials: {materials}")

        if self.use_ai and self.client:
            try:
                if self.ai_provider == "anthropic":
                    return self._generate_with_anthropic(materials, item_type)
                elif self.ai_provider == "openai":
                    return self._generate_with_openai(materials, item_type)
            except Exception as e:
                print(f"AI generation failed: {e}, using fallback")

        # Fallback to procedural generation
        return self._generate_fallback(materials, item_type)

    def _determine_item_type(self, materials: List[str]) -> str:
        """Automatically determine item type based on materials."""
        materials_str = " ".join(materials).lower()

        # Count keywords for each type (updated for new materials)
        weapon_keywords = ["blade", "sword", "axe", "ingot", "steel", "iron", "fang", "obsidian", "mithril", "horn", "demon"]
        armor_keywords = ["plate", "shield", "guard", "leather", "stone", "wood", "scale", "titanium", "reinforced", "thick"]
        concoction_keywords = ["essence", "magic", "potion", "crystal", "powder", "feather", "phoenix", "moonflower", "blood", "star", "dust"]

        weapon_score = sum(1 for kw in weapon_keywords if kw in materials_str)
        armor_score = sum(1 for kw in armor_keywords if kw in materials_str)
        concoction_score = sum(1 for kw in concoction_keywords if kw in materials_str)

        print(f"Material analysis: weapon={weapon_score}, armor={armor_score}, concoction={concoction_score}")

        # Determine based on highest score
        if concoction_score > weapon_score and concoction_score > armor_score:
            return "concoction"
        elif armor_score > weapon_score:
            return "armor"
        else:
            return "weapon"  # Default to weapon

    def _generate_with_anthropic(
        self,
        materials: List[str],
        item_type: str
    ) -> Dict[str, Any]:
        """Generate stats using Anthropic Claude."""

        materials_str = ", ".join(materials)

        prompt = f"""You are a game balance designer for an RPG crafting game. Create an item with these properties:

**Item Type:** {item_type}
**Materials Used:** {materials_str}

Generate balanced and creative stats. Consider the properties implied by each material name.

Provide your response in this exact JSON format:
{{
  "name": "creative name for the item",
  "damage": 0-100 (integer, for weapons only, 0 for non-weapons),
  "armor": 0-100 (integer, for armor only, 0 for non-armor),
  "health": 0-50 (integer, health boost, mainly for concoctions),
  "speed": 0.5-2.0 (float, speed multiplier, 1.0 is normal),
  "special_effect": "brief description of special ability or empty string",
  "rarity": "common|uncommon|rare|epic|legendary",
  "description": "1-2 sentences of flavor text"
}}

**Balance Guidelines:**
- Weapons: high damage, low/zero armor
- Armor: high armor, low/zero damage
- Concoctions: buffs (health, speed, special effects)
- Rarer materials = higher rarity and stats
- Total stat budget: common=30, uncommon=50, rare=80, epic=120, legendary=180

Return ONLY the JSON, no other text."""

        message = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        import json
        # Extract JSON from response
        content = message.content[0].text
        # Try to find JSON in the response
        if "{" in content and "}" in content:
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            json_str = content[json_start:json_end]
            stats = json.loads(json_str)
        else:
            stats = json.loads(content)

        # Add item_type and generation_method to response
        stats["item_type"] = item_type
        stats["generation_method"] = "Anthropic Claude"

        # Log AI-generated stats
        print(f"[AI-STATS] Generated stats via Anthropic Claude:")
        print(f"  Item: {stats.get('name', 'Unknown')}")
        print(f"  Type: {item_type} | Rarity: {stats.get('rarity', 'unknown')}")
        print(f"  Damage: {stats.get('damage', 0)} | Armor: {stats.get('armor', 0)} | Health: {stats.get('health', 0)} | Speed: {stats.get('speed', 1.0)}")
        print(f"  Effect: {stats.get('special_effect', 'None')}")
        print(f"  Description: {stats.get('description', 'No description')}")

        return stats

    def _generate_with_openai(
        self,
        materials: List[str],
        item_type: str
    ) -> Dict[str, Any]:
        """Generate stats using OpenAI GPT-4."""

        materials_str = ", ".join(materials)

        system_prompt = """You are a game balance designer for an RPG crafting game.
Generate balanced and creative item stats based on the materials used in crafting.
Consider the properties implied by each material name when assigning stats."""

        user_prompt = f"""Create an item with these properties:
- Type: {item_type}
- Materials used: {materials_str}

Provide the following in JSON format:
- name: creative name for the item
- damage: integer 0-100 (for weapons, 0 for non-weapons)
- armor: integer 0-100 (for armor, 0 for non-armor)
- health: integer 0-50 (health boost, mainly for concoctions)
- speed: float 0.5-2.0 (speed multiplier, 1.0 is normal)
- special_effect: brief description of special ability (optional, can be empty)
- rarity: one of [common, uncommon, rare, epic, legendary]
- description: brief flavor text (1-2 sentences)

Balance guidelines:
- Weapons should have high damage, low/zero armor
- Armor should have high armor, low/zero damage
- Concoctions should provide buffs (health, speed, special effects)
- Rarer materials should increase item rarity and stats
- Total stat budget: common=30, uncommon=50, rare=80, epic=120, legendary=180"""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.8
        )

        import json
        stats = json.loads(response.choices[0].message.content)

        # Add item_type and generation_method to response
        stats["item_type"] = item_type
        stats["generation_method"] = "OpenAI GPT-4o-mini"

        # Log AI-generated stats
        print(f"[AI-STATS] Generated stats via OpenAI GPT-4o-mini:")
        print(f"  Item: {stats.get('name', 'Unknown')}")
        print(f"  Type: {item_type} | Rarity: {stats.get('rarity', 'unknown')}")
        print(f"  Damage: {stats.get('damage', 0)} | Armor: {stats.get('armor', 0)} | Health: {stats.get('health', 0)} | Speed: {stats.get('speed', 1.0)}")
        print(f"  Effect: {stats.get('special_effect', 'None')}")
        print(f"  Description: {stats.get('description', 'No description')}")

        return stats

    def _generate_fallback(
        self,
        materials: List[str],
        item_type: str
    ) -> Dict[str, Any]:
        """Generate stats using procedural logic."""

        # Log that fallback is being used
        print(f"[FALLBACK] Using procedural generation for {item_type}")

        # Calculate power level from materials
        power_level = self._calculate_power_level(materials)
        rarity = self._determine_rarity(power_level)

        # Generate name
        name = self._generate_name(materials, item_type)

        # Base stats by type
        stats = {
            "name": name,
            "item_type": item_type,  # Include item type in response
            "generation_method": "Fallback",
            "damage": 0,
            "armor": 0,
            "health": 0,
            "speed": 1.0,
            "special_effect": "",
            "rarity": rarity,
            "description": ""
        }

        # Assign stats based on item type
        if item_type == "weapon":
            stats["damage"] = self._scale_stat(power_level, 10, 80)
            stats["speed"] = random.uniform(0.8, 1.3)
            stats["special_effect"] = self._generate_weapon_effect(materials, power_level)
            stats["description"] = f"A powerful {item_type} forged from {', '.join(materials)}."

        elif item_type == "armor":
            stats["armor"] = self._scale_stat(power_level, 10, 80)
            stats["speed"] = random.uniform(0.7, 1.0)  # Armor slows you down
            stats["special_effect"] = self._generate_armor_effect(materials, power_level)
            stats["description"] = f"Sturdy {item_type} crafted from {', '.join(materials)}."

        elif item_type == "concoction":
            stats["health"] = self._scale_stat(power_level, 15, 50)
            stats["speed"] = random.uniform(1.0, 1.5)
            stats["special_effect"] = self._generate_concoction_effect(materials, power_level)
            stats["description"] = f"A magical brew created from {', '.join(materials)}."

        return stats

    def _calculate_power_level(self, materials: List[str]) -> float:
        """Calculate power level (0-1) from materials."""
        # Assign power values to material keywords
        power_keywords = {
            "dragon": 0.9,
            "legendary": 0.9,
            "crystal": 0.7,
            "magic": 0.7,
            "essence": 0.6,
            "gold": 0.6,
            "dark": 0.5,
            "iron": 0.4,
            "steel": 0.5,
            "leather": 0.3,
            "wood": 0.2,
            "oak": 0.3,
            "stone": 0.3,
        }

        total_power = 0
        for material in materials:
            material_lower = material.lower()
            material_power = 0.3  # Default
            for keyword, power in power_keywords.items():
                if keyword in material_lower:
                    material_power = max(material_power, power)
            total_power += material_power

        # Normalize to 0-1 range
        return min(total_power / len(materials), 1.0)

    def _determine_rarity(self, power_level: float) -> str:
        """Determine rarity based on power level."""
        if power_level >= 0.8:
            return "legendary"
        elif power_level >= 0.65:
            return "epic"
        elif power_level >= 0.5:
            return "rare"
        elif power_level >= 0.35:
            return "uncommon"
        else:
            return "common"

    def _scale_stat(self, power_level: float, min_val: int, max_val: int) -> int:
        """Scale a stat value based on power level."""
        value = min_val + (max_val - min_val) * power_level
        # Add some randomness
        value *= random.uniform(0.85, 1.15)
        return int(max(min_val, min(max_val, value)))

    def _generate_name(self, materials: List[str], item_type: str) -> str:
        """Generate an item name."""
        # Use first material as primary
        primary_material = materials[0] if materials else "Mysterious"

        prefixes = {
            "weapon": ["Blade", "Sword", "Axe", "Spear", "Dagger"],
            "armor": ["Plate", "Mail", "Guard", "Shield", "Helm"],
            "concoction": ["Elixir", "Potion", "Brew", "Tonic", "Draught"]
        }

        suffix = random.choice(prefixes.get(item_type, ["Item"]))

        return f"{primary_material} {suffix}"

    def _generate_weapon_effect(self, materials: List[str], power_level: float) -> str:
        """Generate special effect for weapon."""
        if power_level < 0.4:
            return ""

        effects = []
        materials_str = " ".join(materials).lower()

        if "fire" in materials_str or "dragon" in materials_str:
            effects.append("Burns enemies for extra damage")
        if "ice" in materials_str or "crystal" in materials_str:
            effects.append("Chance to freeze enemies")
        if "dark" in materials_str or "shadow" in materials_str:
            effects.append("Drains enemy health")
        if "magic" in materials_str or "essence" in materials_str:
            effects.append("Deals bonus magical damage")

        return random.choice(effects) if effects else "Sharp and deadly"

    def _generate_armor_effect(self, materials: List[str], power_level: float) -> str:
        """Generate special effect for armor."""
        if power_level < 0.4:
            return ""

        effects = []
        materials_str = " ".join(materials).lower()

        if "dragon" in materials_str:
            effects.append("High resistance to fire")
        if "crystal" in materials_str or "magic" in materials_str:
            effects.append("Reflects magical attacks")
        if "iron" in materials_str or "steel" in materials_str:
            effects.append("Reduces physical damage")
        if "dark" in materials_str:
            effects.append("Grants stealth bonus")

        return random.choice(effects) if effects else "Sturdy protection"

    def _generate_concoction_effect(self, materials: List[str], power_level: float) -> str:
        """Generate special effect for concoction."""
        effects = []
        materials_str = " ".join(materials).lower()

        if "magic" in materials_str or "essence" in materials_str:
            effects.append("Grants temporary magic power")
        if "dragon" in materials_str:
            effects.append("Increases damage resistance")
        if "crystal" in materials_str:
            effects.append("Speeds up health regeneration")
        if "dark" in materials_str:
            effects.append("Grants temporary invisibility")

        return random.choice(effects) if effects else "Boosts vitality"
