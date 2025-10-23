"""16-bit sprite assets and character definitions."""

from typing import Dict

# ASCII Art 16-bit style sprites (Street Fighter/Sega era inspired)
SPRITE_CHARS = {
    # Ryu - Basic/Free tier character
    "ryu_basic": {
        "idle": """
    ████████
  ██▓▓▓▓▓▓██
  ██▓▓▓▓▓▓██
  ██▓▓██▓▓██
  ████▓▓▓▓██
    ████████
    ██████
    ████████
  ██████████
  ██████████
    ████
    ████
    ████    ████
    ████    ████""",
        "colors": ["white", "bright_yellow", "red"],
        "description": "Disciplined warrior - Free tier",
    },
    # Chun-Li - Premium tier character
    "chun_li_premium": {
        "idle": """
    ████████
  ██▓▓▓▓▓▓██
  ██▓▓▓▓▓▓██
  ██▓▓██▓▓██
  ████▓▓▓▓██
    ████████
  ████████████
██████████████
██████████████
  ████████████
    ████████
    ████████
██████  ██████
██████  ██████""",
        "colors": ["bright_cyan", "bright_magenta", "blue"],
        "description": "Lightning legs - Premium features",
    },
    # Ken - Enterprise tier character
    "ken_enterprise": {
        "idle": """
    ████████
  ██▓▓▓▓▓▓██
  ██▓▓▓▓▓▓██
  ██▓▓██▓▓██
  ████▓▓▓▓██
    ████████
    ██████
  ████████████
████████████████
████████████████
  ████████████
    ██████
  ████    ████
  ████    ████""",
        "colors": ["bright_yellow", "bright_red", "yellow"],
        "description": "Fiery dragon - Enterprise scale",
    },
    # Blanka - Developer agent
    "blanka_dev": {
        "idle": """
  ████████████
██▓▓▓▓▓▓▓▓▓▓██
██▓▓██▓▓██▓▓██
██▓▓▓▓▓▓▓▓▓▓██
██▓▓████████▓▓██
  ████████████
    ██████
  ████████████
████████████████
████████████████
  ████████████
    ████████
  ████    ████
  ████    ████""",
        "colors": ["bright_green", "green", "yellow"],
        "description": "Electric coding beast",
    },
    # Zangief - System admin/ops
    "zangief_ops": {
        "idle": """
██████████████
██▓▓▓▓▓▓▓▓▓▓██
██▓▓██▓▓██▓▓██
██▓▓▓▓▓▓▓▓▓▓██
██▓▓████████▓▓██
██████████████
  ████████████
████████████████
████████████████
████████████████
████████████████
  ████████████
████████████████
████████████████""",
        "colors": ["bright_red", "red", "yellow"],
        "description": "Wrestling with infrastructure",
    },
    # Dhalsim - Data analyst
    "dhalsim_analyst": {
        "idle": """
    ████████
  ██▓▓▓▓▓▓██
  ██▓▓▓▓▓▓██
  ██▓▓██▓▓██
  ████▓▓▓▓██
    ████████
████████████████
██████████████
████████████████
██  ████████  ██
██  ████████  ██
██  ████████  ██
    ████████
    ████████""",
        "colors": ["bright_magenta", "yellow", "cyan"],
        "description": "Stretches data insights",
    },
    # E.Honda - Writer/content creator
    "honda_writer": {
        "idle": """
████████████████
██▓▓▓▓▓▓▓▓▓▓▓▓██
██▓▓██▓▓▓▓██▓▓██
██▓▓▓▓▓▓▓▓▓▓▓▓██
██▓▓▓▓████▓▓▓▓██
████████████████
████████████████
████████████████
████████████████
████████████████
████████████████
████████████████
  ████████████
  ████████████""",
        "colors": ["blue", "bright_white", "cyan"],
        "description": "Sumo slam storytelling",
    },
    # Vega - UI/UX Designer
    "vega_designer": {
        "idle": """
    ████████
  ██▓▓▓▓▓▓██
  ██▓▓▓▓▓▓██
██████▓▓██▓▓██
██▓▓████▓▓▓▓██
██▓▓▓▓████████
██▓▓▓▓██████
██████████████
██████████████
  ████████████
    ██████
    ██████
    ████████
    ████████""",
        "colors": ["bright_magenta", "magenta", "yellow"],
        "description": "Beautiful deadly design",
    },
    # Sagat - Project manager
    "sagat_pm": {
        "idle": """
    ████████
  ██▓▓▓▓▓▓██
  ██████▓▓██
  ██▓▓██▓▓██
  ████▓▓▓▓██
    ████████
  ████████████
████████████████
████████████████
████████████████
  ████████████
    ██████
  ████    ████
  ████    ████""",
        "colors": ["bright_yellow", "yellow", "red"],
        "description": "Tiger shot project delivery",
    },
    # Doorman - Main mascot
    "doorman_mascot": {
        "idle": """
    ████████
  ██▓▓▓▓▓▓██
  ██▓▓▓▓▓▓██
  ██▓▓██▓▓██
  ████▓▓▓▓██
    ████████
  ████████████
████████████████
████▓▓▓▓▓▓████
████▓▓▓▓▓▓████
████▓▓▓▓▓▓████
████████████████
  ████████████
  ████    ████""",
        "colors": ["bright_cyan", "cyan", "blue"],
        "description": "Your agentic doorman",
    },
}


# UI Elements in 16-bit style
UI_ELEMENTS = {
    "health_bar_full": "████████████████████",
    "health_bar_75": "███████████████░░░░░",
    "health_bar_50": "██████████░░░░░░░░░░",
    "health_bar_25": "█████░░░░░░░░░░░░░░░",
    "health_bar_empty": "░░░░░░░░░░░░░░░░░░░░",
    "power_meter": {
        "level_1": "▮",
        "level_2": "▮▮",
        "level_3": "▮▮▮",
        "level_max": "▮▮▮▮▮ MAX",
    },
    "combo_counter": "HIT: {}",
    "score_display": "SCORE: {:08d}",
    # Borders and frames
    "frame_corner_tl": "╔",
    "frame_corner_tr": "╗",
    "frame_corner_bl": "╚",
    "frame_corner_br": "╝",
    "frame_horizontal": "═",
    "frame_vertical": "║",
    # 16-bit style buttons
    "button_a": "Ⓐ",
    "button_b": "Ⓑ",
    "button_x": "Ⓧ",
    "button_y": "Ⓨ",
    # Direction indicators
    "dpad_up": "△",
    "dpad_down": "▽",
    "dpad_left": "◁",
    "dpad_right": "▷",
}


# Character select screen data
CHARACTER_SELECT = {
    "grid": [
        ["ryu_basic", "chun_li_premium", "ken_enterprise"],
        ["blanka_dev", "zangief_ops", "dhalsim_analyst"],
        ["honda_writer", "vega_designer", "sagat_pm"],
    ],
    "descriptions": {
        "ryu_basic": "Balanced free tier - perfect for starting your journey",
        "chun_li_premium": "Premium speed - lightning fast advanced features",
        "ken_enterprise": "Enterprise fire - unlimited power and scale",
        "blanka_dev": "Wild coding - electric development skills",
        "zangief_ops": "Grappling infrastructure - powerful system control",
        "dhalsim_analyst": "Data stretching - flexible insight generation",
        "honda_writer": "Content sumo - heavyweight storytelling",
        "vega_designer": "Beautiful interfaces - deadly UX precision",
        "sagat_pm": "Project tiger - fierce delivery management",
    },
}


# Animation sequences (simplified for ASCII)
ANIMATIONS = {
    "victory_pose": {
        "ryu_basic": [
            "    ██████\n  ████████\n    ██████",  # Frame 1
            "  ████████\n████████████\n  ████████",  # Frame 2
        ],
        "duration_ms": 500,
    },
    "special_move": {"ryu_basic": ["HADOKEN!", "◎ → ↘ ↓ + P"]},
    "level_up": {"frames": ["⭐", "✨", "🌟", "✨", "⭐"], "duration_ms": 200},
}


# Tier progression visual
TIER_PROGRESSION = {
    "path": [
        {"tier": "free", "sprite": "ryu_basic", "stage": "Training Dojo"},
        {"tier": "premium", "sprite": "chun_li_premium", "stage": "World Tournament"},
        {"tier": "enterprise", "sprite": "ken_enterprise", "stage": "Master's Arena"},
    ],
    "unlock_animations": {
        "free_to_premium": "🥋 → 👑",
        "premium_to_enterprise": "👑 → 🏆",
    },
}


def get_sprite(character: str, animation: str = "idle") -> Dict[str, any]:
    """Get sprite data for a character."""
    if character in SPRITE_CHARS:
        sprite_data = SPRITE_CHARS[character]
        return {
            "ascii": sprite_data.get(animation, sprite_data["idle"]),
            "colors": sprite_data["colors"],
            "description": sprite_data["description"],
        }
    return {"ascii": "████", "colors": ["white"], "description": "Unknown"}


def get_tier_sprite(tier: str) -> str:
    """Get the sprite character for a tier."""
    tier_map = {
        "free": "ryu_basic",
        "premium": "chun_li_premium",
        "enterprise": "ken_enterprise",
    }
    return tier_map.get(tier.lower(), "ryu_basic")


def get_agent_sprite(agent_type: str) -> str:
    """Get the sprite character for an agent type."""
    agent_map = {
        "developer": "blanka_dev",
        "writer": "honda_writer",
        "analyst": "dhalsim_analyst",
        "researcher": "dhalsim_analyst",
        "pm": "sagat_pm",
        "designer": "vega_designer",
        "support": "zangief_ops",
    }
    return agent_map.get(agent_type.lower(), "doorman_mascot")


def render_character_select() -> str:
    """Render the character select screen."""
    output = []
    output.append("═══ SELECT YOUR FIGHTER ═══\n")

    for row in CHARACTER_SELECT["grid"]:
        # Render sprite row
        sprite_row = "  ".join(
            [get_sprite(char)["ascii"].split("\n")[0] for char in row]
        )
        output.append(sprite_row)

        # Render name row
        name_row = "    ".join([char.split("_")[0].upper() for char in row])
        output.append(name_row)
        output.append("")

    return "\n".join(output)


def create_health_bar(current: int, maximum: int, width: int = 20) -> str:
    """Create a 16-bit style health bar."""
    filled = int((current / maximum) * width)
    empty = width - filled
    return "█" * filled + "░" * empty


def create_progress_meter(progress: float, style: str = "power") -> str:
    """Create a 16-bit style progress meter."""
    if style == "power":
        if progress >= 1.0:
            return UI_ELEMENTS["power_meter"]["level_max"]
        elif progress >= 0.75:
            return UI_ELEMENTS["power_meter"]["level_3"]
        elif progress >= 0.50:
            return UI_ELEMENTS["power_meter"]["level_2"]
        elif progress >= 0.25:
            return UI_ELEMENTS["power_meter"]["level_1"]
        else:
            return "░"

    # Default bar style
    width = 10
    filled = int(progress * width)
    return "▮" * filled + "░" * (width - filled)
