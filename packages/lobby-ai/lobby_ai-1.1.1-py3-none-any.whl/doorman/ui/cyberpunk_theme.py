"""Cyberpunk theme for CLI and TUI."""

import random

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.theme import Theme
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Button, Footer, Header, Static, Tree

# Cyberpunk color palette
CYBERPUNK_THEME = Theme(
    {
        "primary": "bold cyan",
        "secondary": "bold magenta",
        "accent": "bold green",
        "warning": "bold yellow",
        "danger": "bold red",
        "muted": "dim white",
        "background": "on black",
        "neon_cyan": "bold bright_cyan",
        "neon_magenta": "bold bright_magenta",
        "neon_green": "bold bright_green",
        "matrix_green": "green",
    }
)

console = Console(theme=CYBERPUNK_THEME)


class CyberpunkPanel:
    """Helper for creating cyberpunk-styled panels."""

    @staticmethod
    def create(content: str, title: str = "", style: str = "neon_cyan") -> Panel:
        """Create a cyberpunk-styled panel with neon borders."""
        return Panel(
            content,
            title=f"[bold {style}]▮▮ {title} ▮▮[/bold {style}]",
            border_style=style,
            padding=(1, 2),
        )

    @staticmethod
    def matrix_border() -> str:
        """Generate matrix-style border characters."""
        chars = "█▉▊▋▌▍▎▏▎▍▌▋▊▉"
        return "".join(random.choice(chars) for _ in range(50))


class MatrixRain(Static):
    """Animated matrix-style background effect."""

    def __init__(self) -> None:
        super().__init__()
        self.columns = []
        self.chars = "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    def on_mount(self) -> None:
        """Start the matrix rain animation."""
        self.set_interval(0.1, self.update_matrix)

    def update_matrix(self) -> None:
        """Update the matrix rain effect."""
        if len(self.columns) < 20:
            self.columns.append(
                {
                    "x": random.randint(0, 80),
                    "y": 0,
                    "length": random.randint(5, 15),
                    "speed": random.choice([1, 2]),
                }
            )

        # Update existing columns
        for col in self.columns[:]:
            col["y"] += col["speed"]
            if col["y"] > 50:
                self.columns.remove(col)


class CyberpunkHeader(Header):
    """Cyberpunk-themed header with neon effects."""

    def __init__(self) -> None:
        super().__init__()
        self.title = "▮▮▮ DOORMAN.EXE ▮▮▮"

    def render(self) -> Text:
        """Render cyberpunk header."""
        text = Text()
        text.append("▮▮▮ ", style="neon_cyan")
        text.append("DOORMAN", style="bold neon_magenta")
        text.append(".EXE", style="neon_green")
        text.append(" ▮▮▮", style="neon_cyan")
        return text


class TaxonomyTree(Tree):
    """Cyberpunk-styled taxonomy tree visualization."""

    def __init__(self, taxonomy_data: dict) -> None:
        super().__init__("Intent Taxonomy")
        self.taxonomy_data = taxonomy_data
        self._build_tree()

    def _build_tree(self) -> None:
        """Build the taxonomy tree structure."""
        # Intent
        intent_node = self.root.add(
            f"[neon_cyan]▮ Intent:[/neon_cyan] [bold]{self.taxonomy_data.get('intent', 'Unknown')}[/bold]"
        )

        # Confidence
        confidence = self.taxonomy_data.get("context_confidence", 0.0)
        confidence_color = (
            "neon_green"
            if confidence > 0.8
            else "warning"
            if confidence > 0.6
            else "danger"
        )
        intent_node.add(
            f"[{confidence_color}]▮ Confidence: {confidence:.1%}[/{confidence_color}]"
        )

        # Components
        if "components" in self.taxonomy_data:
            components_node = intent_node.add(
                "[neon_magenta]▮ Components[/neon_magenta]"
            )
            for component in self.taxonomy_data["components"]:
                comp_text = f"[accent]▸[/accent] {component.get('name', 'Unknown')} [{component.get('type', 'unknown')}]"
                comp_node = components_node.add(comp_text)

                # Sub-components
                if component.get("components"):
                    for sub_comp in component["components"]:
                        comp_node.add(
                            f"[muted]▹ {sub_comp.get('name', 'Unknown')}[/muted]"
                        )

        # Tools Needed
        if "tools_needed" in self.taxonomy_data:
            tools_node = intent_node.add("[neon_green]▮ Tools[/neon_green]")
            for tool in self.taxonomy_data["tools_needed"]:
                tools_node.add(f"[accent]▸[/accent] {tool}")

        # Assumptions
        if "assumptions" in self.taxonomy_data:
            assumptions_node = intent_node.add("[warning]▮ Assumptions[/warning]")
            for assumption in self.taxonomy_data["assumptions"]:
                assumptions_node.add(f"[muted]▸ {assumption}[/muted]")


class CyberpunkApp(App):
    """Main cyberpunk TUI application."""

    CSS = """
    Screen {
        background: black;
    }
    
    .cyberpunk-container {
        border: solid cyan;
        background: black;
    }
    
    .matrix-bg {
        background: black;
        color: green;
    }
    
    Button {
        background: black;
        color: cyan;
        border: solid cyan;
    }
    
    Button:hover {
        background: cyan;
        color: black;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the UI."""
        yield CyberpunkHeader()

        with Container(classes="cyberpunk-container"):
            yield Static("Enter your intent below:", classes="matrix-bg")

            # Sample taxonomy data
            sample_taxonomy = {
                "intent": "make a sandwich",
                "context_confidence": 0.8,
                "components": [
                    {
                        "name": "bread",
                        "type": "ingredient",
                        "components": [
                            {"name": "flour", "type": "ingredient"},
                            {"name": "yeast", "type": "ingredient"},
                        ],
                    },
                    {"name": "knife", "type": "tool"},
                ],
                "tools_needed": ["plate", "napkin"],
                "assumptions": ["user is not gluten allergic", "no teeth issues"],
            }

            yield TaxonomyTree(sample_taxonomy)

            with Horizontal():
                yield Button("Execute", id="execute")
                yield Button("Modify", id="modify")
                yield Button("Export", id="export")

        yield Footer()

    def action_bell(self) -> None:
        """Ring the terminal bell."""
        self.bell()


def print_cyberpunk_banner() -> None:
    """Print cyberpunk-style banner."""
    banner = """
[neon_cyan]╔══════════════════════════════════════╗[/neon_cyan]
[neon_cyan]║[/neon_cyan] [bold neon_magenta]DOORMAN.EXE[/bold neon_magenta] [neon_green]v2.0[/neon_green] [neon_cyan]▮▮▮ AGENTIC CORE ▮▮▮[/neon_cyan] [neon_cyan]║[/neon_cyan]
[neon_cyan]╠══════════════════════════════════════╣[/neon_cyan]
[neon_cyan]║[/neon_cyan] [accent]Intent → Taxonomy → Execution[/accent]     [neon_cyan]║[/neon_cyan]
[neon_cyan]║[/neon_cyan] [muted]Universal task decomposition[/muted]        [neon_cyan]║[/neon_cyan]
[neon_cyan]╚══════════════════════════════════════╝[/neon_cyan]
"""
    console.print(banner)


def print_taxonomy_yaml(taxonomy: dict) -> None:
    """Print taxonomy in cyberpunk YAML style."""
    console.print("\n[neon_cyan]▮▮▮ TAXONOMY OUTPUT ▮▮▮[/neon_cyan]\n")

    yaml_content = f"""[primary]intent:[/primary] [bold]"{taxonomy.get("intent", "")}"[/bold]
[primary]context_confidence:[/primary] [accent]{taxonomy.get("context_confidence", 0.0)}[/accent]
[primary]confidence_level:[/primary] [accent]{taxonomy.get("confidence_level", "medium")}[/accent]

[secondary]components_needed:[/secondary]"""

    if "components" in taxonomy:
        for component in taxonomy["components"]:
            yaml_content += f"\n  [accent]- name:[/accent] {component.get('name', '')}"
            yaml_content += f"\n    [muted]type:[/muted] {component.get('type', '')}"
            if component.get("mcp_tool"):
                yaml_content += (
                    f"\n    [neon_green]mcp_tool:[/neon_green] {component['mcp_tool']}"
                )

    if "tools_needed" in taxonomy:
        yaml_content += "\n\n[secondary]tools_needed:[/secondary]"
        for tool in taxonomy["tools_needed"]:
            yaml_content += f"\n  [accent]- {tool}[/accent]"

    if "assumptions" in taxonomy:
        yaml_content += "\n\n[warning]assumptions:[/warning]"
        for assumption in taxonomy["assumptions"]:
            yaml_content += f"\n  [muted]- {assumption}[/muted]"

    panel = CyberpunkPanel.create(yaml_content, "TAXONOMY", "neon_magenta")
    console.print(panel)


def create_execution_graph(taxonomy: dict) -> str:
    """Create ASCII art execution graph."""
    graph = """
[neon_cyan]    ┌─────────────┐[/neon_cyan]
[neon_cyan]    │[/neon_cyan] [bold]USER INTENT[/bold] [neon_cyan]│[/neon_cyan]
[neon_cyan]    └──────┬──────┘[/neon_cyan]
[neon_cyan]           │[/neon_cyan]
[neon_cyan]    ┌──────▼──────┐[/neon_cyan]
[neon_cyan]    │[/neon_cyan] [accent]DECOMPOSE[/accent]   [neon_cyan]│[/neon_cyan]
[neon_cyan]    └──────┬──────┘[/neon_cyan]
[neon_cyan]           │[/neon_cyan]
[neon_cyan]      ┌────▼────┐[/neon_cyan]
[neon_cyan]      │[/neon_cyan] [neon_green]EXECUTE[/neon_green] [neon_cyan]│[/neon_cyan]
[neon_cyan]      └─────────┘[/neon_cyan]
"""
    return graph
