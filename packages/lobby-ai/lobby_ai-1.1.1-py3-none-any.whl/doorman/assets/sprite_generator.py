"""Procedural sprite generation based on user hash."""

import hashlib
import random
from typing import Dict, List


class SpriteGenerator:
    """Generate unique 16-bit style sprites from user identifiers."""

    # Base sprite templates (8x8 character heads)
    BASE_TEMPLATES = {
        "warrior": [
            "  ████  ",
            " ██████ ",
            " ██▓▓██ ",
            " ██▓▓██ ",
            " ██████ ",
            "  ████  ",
            "  ████  ",
            "        ",
        ],
        "mage": [
            " ██████ ",
            "████████",
            "██▓▓▓▓██",
            "██▓██▓██",
            "████████",
            " ██████ ",
            "   ██   ",
            "        ",
        ],
        "rogue": [
            "   ██   ",
            "  ████  ",
            " ██████ ",
            " ██▓▓██ ",
            " ██▓▓██ ",
            "  ████  ",
            "  ████  ",
            "        ",
        ],
        "beast": [
            " ██  ██ ",
            "████████",
            "██████████",
            "██▓██▓██",
            "████████",
            " ██████ ",
            "  ████  ",
            "        ",
        ],
    }

    # Color palettes based on hash
    COLOR_PALETTES = [
        ["bright_cyan", "cyan", "blue"],  # Ice
        ["bright_magenta", "magenta", "red"],  # Fire
        ["bright_green", "green", "yellow"],  # Nature
        ["bright_yellow", "yellow", "red"],  # Lightning
        ["bright_white", "white", "bright_blue"],  # Holy
        ["bright_red", "red", "black"],  # Dark
        ["magenta", "blue", "cyan"],  # Mystic
        ["yellow", "green", "blue"],  # Earth
    ]

    # Accessories that can be added
    ACCESSORIES = {
        "hat": ["▲", "♦", "●", "■"],
        "facial": ["=", "≡", "~", "-"],
        "aura": ["◆", "◇", "○", "□"],
    }

    def __init__(self):
        pass

    def generate_sprite(self, identifier: str, tier: str = "free") -> Dict[str, any]:
        """Generate a unique sprite based on identifier and tier."""
        # Create deterministic hash
        hash_value = hashlib.md5(identifier.encode()).hexdigest()

        # Use hash to seed random for consistency
        seed = int(hash_value[:8], 16)
        rng = random.Random(seed)

        # Choose base template
        template_names = list(self.BASE_TEMPLATES.keys())
        template_name = rng.choice(template_names)
        base_template = self.BASE_TEMPLATES[template_name].copy()

        # Choose color palette
        palette = rng.choice(self.COLOR_PALETTES)

        # Add tier-specific modifications
        if tier == "premium":
            base_template = self._add_premium_effects(base_template, rng)
            palette = self._enhance_colors(palette)
        elif tier == "enterprise":
            base_template = self._add_enterprise_effects(base_template, rng)
            palette = self._add_enterprise_colors(palette)

        # Generate description
        description = self._generate_description(template_name, tier, hash_value)

        return {
            "ascii": "\n".join(base_template),
            "colors": palette,
            "description": description,
            "hash": hash_value[:8],
            "template": template_name,
            "tier": tier,
        }

    def _add_premium_effects(
        self, template: List[str], rng: random.Random
    ) -> List[str]:
        """Add premium tier visual effects."""
        # Add crown or special headgear
        if rng.random() > 0.5:
            template[0] = "   ♦   " if len(template[0]) >= 7 else template[0]

        # Add aura effects (extend width slightly)
        enhanced = []
        for line in template:
            if "██" in line and rng.random() > 0.7:
                enhanced.append("◆" + line + "◇")
            else:
                enhanced.append(" " + line + " ")

        return enhanced

    def _add_enterprise_effects(
        self, template: List[str], rng: random.Random
    ) -> List[str]:
        """Add enterprise tier visual effects."""
        # Add imperial crown
        template[0] = "  ♛♛♛  " if len(template[0]) >= 7 else template[0]

        # Add royal aura
        enhanced = []
        for line in template:
            if "██" in line:
                enhanced.append("◆◆" + line + "◇◇")
            else:
                enhanced.append("  " + line + "  ")

        return enhanced

    def _enhance_colors(self, palette: List[str]) -> List[str]:
        """Enhance colors for premium tier."""
        enhanced = []
        for color in palette:
            if not color.startswith("bright_"):
                enhanced.append("bright_" + color)
            else:
                enhanced.append(color)
        return enhanced

    def _add_enterprise_colors(self, palette: List[str]) -> List[str]:
        """Add enterprise-specific colors."""
        return ["bright_yellow", "bright_white", "gold"] + palette[:1]

    def _generate_description(self, template: str, tier: str, hash_value: str) -> str:
        """Generate a description based on sprite characteristics."""

        # Base descriptions by template
        base_descriptions = {
            "warrior": [
                "Fierce fighter",
                "Battle-hardened veteran",
                "Sword master",
                "Shield bearer",
            ],
            "mage": [
                "Arcane scholar",
                "Spell weaver",
                "Mystic sage",
                "Elemental master",
            ],
            "rogue": [
                "Shadow dancer",
                "Silent striker",
                "Lock picker",
                "Night crawler",
            ],
            "beast": ["Wild hunter", "Pack leader", "Feral guardian", "Primal warrior"],
        }

        # Tier modifiers
        tier_modifiers = {
            "free": ["Apprentice", "Novice", "Student", "Recruit"],
            "premium": ["Expert", "Master", "Champion", "Elite"],
            "enterprise": ["Legendary", "Mythical", "Supreme", "Immortal"],
        }

        # Use hash to select descriptions deterministically
        hash_int = int(hash_value[:4], 16)
        base_desc = base_descriptions[template][
            hash_int % len(base_descriptions[template])
        ]
        tier_mod = tier_modifiers[tier][hash_int % len(tier_modifiers[tier])]

        return f"{tier_mod} {base_desc}"

    def generate_agent_sprite(
        self, agent_type: str, user_id: str = "default"
    ) -> Dict[str, any]:
        """Generate sprite for specific agent types."""

        # Agent-specific templates
        agent_templates = {
            "developer": "beast",  # Wild coding beast
            "writer": "mage",  # Word wizard
            "analyst": "mage",  # Data sorcerer
            "researcher": "rogue",  # Information scout
            "pm": "warrior",  # Project warrior
            "designer": "mage",  # Visual artist
            "support": "warrior",  # Support champion
        }

        # Combine agent type and user for unique sprite per user per agent
        identifier = f"{agent_type}_{user_id}"
        template_type = agent_templates.get(agent_type, "warrior")

        # Generate base sprite
        sprite = self.generate_sprite(identifier, "premium")

        # Add agent-specific description
        agent_descriptions = {
            "developer": "Code-slinging beast",
            "writer": "Word-weaving wizard",
            "analyst": "Data-diving sage",
            "researcher": "Info-hunting scout",
            "pm": "Project battle commander",
            "designer": "Pixel-perfect artist",
            "support": "Help desk champion",
        }

        sprite["description"] = agent_descriptions.get(
            agent_type, sprite["description"]
        )
        sprite["agent_type"] = agent_type

        return sprite

    def create_team_sprites(
        self, team_id: str, team_size: int = 5
    ) -> List[Dict[str, any]]:
        """Generate a team of unique sprites for team spaces."""
        team_sprites = []

        for i in range(team_size):
            member_id = f"{team_id}_member_{i}"
            sprite = self.generate_sprite(member_id, "premium")
            sprite["team_role"] = f"Member {i + 1}"
            team_sprites.append(sprite)

        return team_sprites

    def animate_sprite(
        self, sprite_data: Dict[str, any], animation: str = "idle"
    ) -> List[str]:
        """Create simple animation frames."""
        base_ascii = sprite_data["ascii"]

        if animation == "victory":
            # Simple victory animation - add sparkles
            frame1 = base_ascii
            frame2 = base_ascii.replace("██", "▓▓").replace("▓▓", "░░")
            frame3 = base_ascii.replace("██", "░░").replace("▓▓", "██")
            return [frame1, frame2, frame3, frame2]

        elif animation == "working":
            # Working animation - slight movement
            lines = base_ascii.split("\n")
            frame1 = "\n".join(lines)
            frame2 = "\n".join([" " + line for line in lines])
            return [frame1, frame2]

        return [base_ascii]  # Default idle


# Global sprite generator
_generator = None


def get_sprite_generator() -> SpriteGenerator:
    """Get global sprite generator instance."""
    global _generator
    if _generator is None:
        _generator = SpriteGenerator()
    return _generator


def generate_user_sprite(user_id: str, tier: str = "free") -> Dict[str, any]:
    """Convenient function to generate user sprite."""
    generator = get_sprite_generator()
    return generator.generate_sprite(user_id, tier)


def generate_agent_sprite(agent_type: str, user_id: str = "default") -> Dict[str, any]:
    """Convenient function to generate agent sprite."""
    generator = get_sprite_generator()
    return generator.generate_agent_sprite(agent_type, user_id)
