"""Script generation engine that converts taxonomies into executable shell commands."""

import os
import platform
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

from rich.console import Console

from .taxonomy import ComponentType, IntentTaxonomy


class CommandSafety(Enum):
    """Safety levels for generated commands."""

    SAFE = "safe"  # Read-only, no side effects
    MODERATE = "moderate"  # File operations, installations
    DANGEROUS = "dangerous"  # System modifications, sudo required


@dataclass
class ShellCommand:
    """A shell command with metadata."""

    command: str
    description: str
    safety_level: CommandSafety
    requires_confirmation: bool = False
    working_directory: Optional[str] = None
    environment_vars: Optional[Dict[str, str]] = None
    expected_duration: Optional[int] = None  # seconds


@dataclass
class ExecutionPlan:
    """Complete execution plan with commands and metadata."""

    title: str
    description: str
    commands: List[ShellCommand]
    estimated_total_time: int  # minutes
    safety_warnings: List[str]
    prerequisites: List[str]
    success_criteria: List[str]


class ScriptEngine:
    """Converts intent taxonomies into executable shell scripts."""

    def __init__(self):
        self.console = Console()
        self.shell = self._detect_shell()
        self.platform = platform.system().lower()

        # Command templates by component type and platform
        self.command_templates = self._load_command_templates()

    def _detect_shell(self) -> str:
        """Detect the user's shell."""
        shell = os.environ.get("SHELL", "/bin/bash")
        if "zsh" in shell:
            return "zsh"
        elif "bash" in shell:
            return "bash"
        elif "fish" in shell:
            return "fish"
        else:
            return "bash"  # Default fallback

    def _load_command_templates(self) -> Dict[str, Dict[str, List[str]]]:
        """Load command templates for different platforms and tools."""
        return {
            "package_manager": {
                "darwin": {
                    "brew": ["brew install {package}", "brew update", "brew upgrade"],
                    "npm": ["npm install -g {package}", "npm update -g"],
                    "pip": ["pip install {package}", "pip install --upgrade {package}"],
                },
                "linux": {
                    "apt": ["sudo apt update", "sudo apt install -y {package}"],
                    "yum": ["sudo yum install -y {package}", "sudo yum update"],
                    "dnf": ["sudo dnf install -y {package}", "sudo dnf upgrade"],
                    "pacman": ["sudo pacman -S {package}", "sudo pacman -Syu"],
                    "npm": ["npm install -g {package}", "npm update -g"],
                    "pip": ["pip install {package}", "pip install --upgrade {package}"],
                },
            },
            "web_server": {
                "nginx": {
                    "darwin": ["brew install nginx", "brew services start nginx"],
                    "linux": [
                        "sudo apt install -y nginx",
                        "sudo systemctl start nginx",
                        "sudo systemctl enable nginx",
                    ],
                },
                "apache": {
                    "darwin": ["brew install httpd", "brew services start httpd"],
                    "linux": [
                        "sudo apt install -y apache2",
                        "sudo systemctl start apache2",
                        "sudo systemctl enable apache2",
                    ],
                },
            },
            "development": {
                "node": {
                    "darwin": ["brew install node", "node --version"],
                    "linux": [
                        "curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -",
                        "sudo apt-get install -y nodejs",
                    ],
                },
                "python": {
                    "darwin": ["brew install python", "python3 --version"],
                    "linux": [
                        "sudo apt update",
                        "sudo apt install -y python3 python3-pip",
                    ],
                },
                "docker": {
                    "darwin": ["brew install --cask docker", "open -a Docker"],
                    "linux": [
                        "curl -fsSL https://get.docker.com -o get-docker.sh",
                        "sh get-docker.sh",
                        "sudo usermod -aG docker $USER",
                    ],
                },
            },
            "file_operations": {
                "create_directory": ["mkdir -p {path}"],
                "create_file": ["touch {file}", "echo '{content}' > {file}"],
                "copy_file": ["cp {source} {destination}"],
                "move_file": ["mv {source} {destination}"],
                "delete_file": ["rm {file}"],
                "delete_directory": ["rm -rf {directory}"],
                "change_permissions": ["chmod {permissions} {file}"],
            },
            "git_operations": {
                "clone": ["git clone {repo} {directory}"],
                "init": ["git init", "git add .", "git commit -m 'Initial commit'"],
                "branch": ["git checkout -b {branch_name}"],
                "push": [
                    "git add .",
                    "git commit -m '{message}'",
                    "git push origin {branch}",
                ],
            },
        }

    async def generate_execution_plan(self, taxonomy: IntentTaxonomy) -> ExecutionPlan:
        """Generate executable commands from taxonomy using AI."""

        commands = []
        safety_warnings = []
        prerequisites = []
        success_criteria = []

        # Use AI to generate commands for ALL categories
        try:
            commands = await self._generate_ai_commands(taxonomy)
        except Exception as e:
            print(f"AI command generation failed: {e}")
            # Fallback to rule-based generation for coding tasks only
            intent_lower = taxonomy.intent.lower()
            category = taxonomy.intent_category.lower()

            if category == "coding" or category == "devops":
                if any(
                    word in intent_lower for word in ["install", "setup", "configure"]
                ):
                    commands.extend(
                        await self._generate_installation_commands(taxonomy)
                    )
                elif any(word in intent_lower for word in ["create", "make", "build"]):
                    commands.extend(await self._generate_creation_commands(taxonomy))
                elif any(
                    word in intent_lower for word in ["deploy", "publish", "release"]
                ):
                    commands.extend(await self._generate_deployment_commands(taxonomy))
                else:
                    commands.extend(await self._generate_generic_commands(taxonomy))
            else:
                # For non-coding tasks, create a simple informational command
                commands.append(
                    ShellCommand(
                        command=f"echo 'Task: {taxonomy.intent}'",
                        description="Display task information",
                        safety_level=CommandSafety.SAFE,
                    )
                )

        # Add safety checks and warnings
        for cmd in commands:
            if cmd.safety_level == CommandSafety.DANGEROUS:
                safety_warnings.append(
                    f"⚠️  Command '{cmd.command}' requires elevated privileges"
                )

            if "sudo" in cmd.command:
                safety_warnings.append("🔐 Some commands require administrator access")
                prerequisites.append("Administrator/sudo access")

        # Generate success criteria
        success_criteria = self._generate_success_criteria(taxonomy, commands)

        return ExecutionPlan(
            title=f"Execute: {taxonomy.intent}",
            description=f"Generated execution plan for {taxonomy.intent_category} task",
            commands=commands,
            estimated_total_time=taxonomy.estimated_total_time_minutes,
            safety_warnings=list(set(safety_warnings)),  # Remove duplicates
            prerequisites=list(set(prerequisites)),
            success_criteria=success_criteria,
        )

    async def _generate_installation_commands(
        self, taxonomy: IntentTaxonomy
    ) -> List[ShellCommand]:
        """Generate installation commands."""
        commands = []
        intent = taxonomy.intent.lower()

        # Extract package/service name
        if "nginx" in intent:
            if self.platform == "darwin":
                commands.extend(
                    [
                        ShellCommand(
                            command="brew install nginx",
                            description="Install nginx web server",
                            safety_level=CommandSafety.MODERATE,
                        ),
                        ShellCommand(
                            command="brew services start nginx",
                            description="Start nginx service",
                            safety_level=CommandSafety.MODERATE,
                        ),
                        ShellCommand(
                            command="curl http://localhost:8080",
                            description="Test nginx installation",
                            safety_level=CommandSafety.SAFE,
                        ),
                    ]
                )
            else:  # Linux
                commands.extend(
                    [
                        ShellCommand(
                            command="sudo apt update",
                            description="Update package repository",
                            safety_level=CommandSafety.MODERATE,
                            requires_confirmation=True,
                        ),
                        ShellCommand(
                            command="sudo apt install -y nginx",
                            description="Install nginx web server",
                            safety_level=CommandSafety.MODERATE,
                            requires_confirmation=True,
                        ),
                        ShellCommand(
                            command="sudo systemctl start nginx",
                            description="Start nginx service",
                            safety_level=CommandSafety.MODERATE,
                            requires_confirmation=True,
                        ),
                        ShellCommand(
                            command="sudo systemctl enable nginx",
                            description="Enable nginx to start on boot",
                            safety_level=CommandSafety.MODERATE,
                            requires_confirmation=True,
                        ),
                        ShellCommand(
                            command="curl http://localhost",
                            description="Test nginx installation",
                            safety_level=CommandSafety.SAFE,
                        ),
                    ]
                )

        elif "node" in intent or "nodejs" in intent:
            if self.platform == "darwin":
                commands.extend(
                    [
                        ShellCommand(
                            command="brew install node",
                            description="Install Node.js and npm",
                            safety_level=CommandSafety.MODERATE,
                        ),
                        ShellCommand(
                            command="node --version && npm --version",
                            description="Verify Node.js installation",
                            safety_level=CommandSafety.SAFE,
                        ),
                    ]
                )
            else:  # Linux
                commands.extend(
                    [
                        ShellCommand(
                            command="curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -",
                            description="Add NodeSource repository",
                            safety_level=CommandSafety.DANGEROUS,
                            requires_confirmation=True,
                        ),
                        ShellCommand(
                            command="sudo apt-get install -y nodejs",
                            description="Install Node.js and npm",
                            safety_level=CommandSafety.MODERATE,
                            requires_confirmation=True,
                        ),
                        ShellCommand(
                            command="node --version && npm --version",
                            description="Verify Node.js installation",
                            safety_level=CommandSafety.SAFE,
                        ),
                    ]
                )

        elif "docker" in intent:
            if self.platform == "darwin":
                commands.extend(
                    [
                        ShellCommand(
                            command="brew install --cask docker",
                            description="Install Docker Desktop",
                            safety_level=CommandSafety.MODERATE,
                        ),
                        ShellCommand(
                            command="open -a Docker",
                            description="Start Docker Desktop",
                            safety_level=CommandSafety.SAFE,
                        ),
                        ShellCommand(
                            command="docker --version",
                            description="Verify Docker installation",
                            safety_level=CommandSafety.SAFE,
                            expected_duration=30,
                        ),
                    ]
                )
            else:  # Linux
                commands.extend(
                    [
                        ShellCommand(
                            command="curl -fsSL https://get.docker.com -o get-docker.sh",
                            description="Download Docker installation script",
                            safety_level=CommandSafety.MODERATE,
                        ),
                        ShellCommand(
                            command="sh get-docker.sh",
                            description="Install Docker",
                            safety_level=CommandSafety.DANGEROUS,
                            requires_confirmation=True,
                            expected_duration=120,
                        ),
                        ShellCommand(
                            command="sudo usermod -aG docker $USER",
                            description="Add user to docker group",
                            safety_level=CommandSafety.MODERATE,
                            requires_confirmation=True,
                        ),
                        ShellCommand(
                            command="docker --version",
                            description="Verify Docker installation",
                            safety_level=CommandSafety.SAFE,
                        ),
                    ]
                )

        return commands

    async def _generate_creation_commands(
        self, taxonomy: IntentTaxonomy
    ) -> List[ShellCommand]:
        """Generate file/project creation commands."""
        commands = []
        intent = taxonomy.intent.lower()

        if "react app" in intent or "react project" in intent:
            # Extract project name from intent
            project_name = self._extract_project_name(intent)
            commands.extend(
                [
                    ShellCommand(
                        command=f"npx create-react-app {project_name}",
                        description=f"Create React application '{project_name}'",
                        safety_level=CommandSafety.MODERATE,
                        expected_duration=120,
                    ),
                    ShellCommand(
                        command=f"cd {project_name}",
                        description="Navigate to project directory",
                        safety_level=CommandSafety.SAFE,
                        working_directory=f"./{project_name}",
                    ),
                    ShellCommand(
                        command="npm start",
                        description="Start development server",
                        safety_level=CommandSafety.SAFE,
                        working_directory=f"./{project_name}",
                    ),
                ]
            )

        elif "directory" in intent or "folder" in intent:
            # Extract directory name from intent
            dir_name = "new-directory"  # Default
            commands.append(
                ShellCommand(
                    command=f"mkdir -p {dir_name}",
                    description=f"Create directory '{dir_name}'",
                    safety_level=CommandSafety.SAFE,
                )
            )

        elif "file" in intent:
            file_name = "new-file.txt"  # Default
            commands.extend(
                [
                    ShellCommand(
                        command=f"touch {file_name}",
                        description=f"Create file '{file_name}'",
                        safety_level=CommandSafety.SAFE,
                    ),
                    ShellCommand(
                        command=f"echo 'Hello, World!' > {file_name}",
                        description="Add initial content",
                        safety_level=CommandSafety.SAFE,
                    ),
                ]
            )

        return commands

    async def _generate_deployment_commands(
        self, taxonomy: IntentTaxonomy
    ) -> List[ShellCommand]:
        """Generate deployment commands."""
        commands = []
        intent = taxonomy.intent.lower()

        if "vercel" in intent:
            commands.extend(
                [
                    ShellCommand(
                        command="npm install -g vercel",
                        description="Install Vercel CLI",
                        safety_level=CommandSafety.MODERATE,
                    ),
                    ShellCommand(
                        command="vercel login",
                        description="Login to Vercel",
                        safety_level=CommandSafety.SAFE,
                        requires_confirmation=True,
                    ),
                    ShellCommand(
                        command="vercel --prod",
                        description="Deploy to production",
                        safety_level=CommandSafety.MODERATE,
                        requires_confirmation=True,
                    ),
                ]
            )

        elif "git" in intent:
            commands.extend(
                [
                    ShellCommand(
                        command="git add .",
                        description="Stage all changes",
                        safety_level=CommandSafety.SAFE,
                    ),
                    ShellCommand(
                        command="git commit -m 'Deploy updates'",
                        description="Commit changes",
                        safety_level=CommandSafety.SAFE,
                    ),
                    ShellCommand(
                        command="git push origin main",
                        description="Push to remote repository",
                        safety_level=CommandSafety.MODERATE,
                    ),
                ]
            )

        return commands

    async def _generate_generic_commands(
        self, taxonomy: IntentTaxonomy
    ) -> List[ShellCommand]:
        """Generate commands based on taxonomy components."""
        commands = []

        for component in taxonomy.components:
            if component.type == ComponentType.TOOL:
                # Generate tool installation/usage commands
                tool_name = component.name.lower()
                if tool_name in ["git", "curl", "wget"]:
                    commands.append(
                        ShellCommand(
                            command=f"which {tool_name} || echo '{tool_name} not found'",
                            description=f"Check if {tool_name} is installed",
                            safety_level=CommandSafety.SAFE,
                        )
                    )

            elif component.type == ComponentType.ENVIRONMENT:
                # Generate environment setup commands
                if "directory" in component.name.lower():
                    commands.append(
                        ShellCommand(
                            command="mkdir -p workspace",
                            description="Create workspace directory",
                            safety_level=CommandSafety.SAFE,
                        )
                    )

        return commands

    async def _generate_food_commands(
        self, taxonomy: IntentTaxonomy
    ) -> List[ShellCommand]:
        """Generate food preparation commands."""
        commands = []
        intent = taxonomy.intent.lower()

        if "sandwich" in intent:
            commands.extend(
                [
                    ShellCommand(
                        command="echo '🥪 Gathering ingredients for sandwich...'",
                        description="List required ingredients",
                        safety_level=CommandSafety.SAFE,
                    ),
                    ShellCommand(
                        command="echo '- Bread (2 slices)'",
                        description="Check bread availability",
                        safety_level=CommandSafety.SAFE,
                    ),
                    ShellCommand(
                        command="echo '- Protein (meat, cheese, or alternative)'",
                        description="Prepare protein component",
                        safety_level=CommandSafety.SAFE,
                    ),
                    ShellCommand(
                        command="echo '- Vegetables (lettuce, tomato, etc.)'",
                        description="Wash and prepare vegetables",
                        safety_level=CommandSafety.SAFE,
                    ),
                    ShellCommand(
                        command="echo '- Condiments (mayo, mustard, etc.)'",
                        description="Gather condiments",
                        safety_level=CommandSafety.SAFE,
                    ),
                    ShellCommand(
                        command="echo '\n🔪 Assembly instructions:'",
                        description="Show assembly steps",
                        safety_level=CommandSafety.SAFE,
                    ),
                    ShellCommand(
                        command="echo '1. Lay out bread slices'",
                        description="Step 1: Prepare base",
                        safety_level=CommandSafety.SAFE,
                    ),
                    ShellCommand(
                        command="echo '2. Apply condiments to one or both slices'",
                        description="Step 2: Add condiments",
                        safety_level=CommandSafety.SAFE,
                    ),
                    ShellCommand(
                        command="echo '3. Add protein layer'",
                        description="Step 3: Add main filling",
                        safety_level=CommandSafety.SAFE,
                    ),
                    ShellCommand(
                        command="echo '4. Add vegetables'",
                        description="Step 4: Add fresh ingredients",
                        safety_level=CommandSafety.SAFE,
                    ),
                    ShellCommand(
                        command="echo '5. Top with second bread slice'",
                        description="Step 5: Complete sandwich",
                        safety_level=CommandSafety.SAFE,
                    ),
                    ShellCommand(
                        command="echo '✅ Sandwich complete! Enjoy your meal 🎉'",
                        description="Completion confirmation",
                        safety_level=CommandSafety.SAFE,
                    ),
                ]
            )

        elif "cook" in intent or "recipe" in intent:
            # Extract dish name if possible
            dish = "dish"
            if "pasta" in intent:
                dish = "pasta"
            elif "eggs" in intent:
                dish = "eggs"
            elif "rice" in intent:
                dish = "rice"

            commands.extend(
                [
                    ShellCommand(
                        command=f"echo '👩‍🍳 Preparing to cook {dish}...'",
                        description=f"Initialize cooking process for {dish}",
                        safety_level=CommandSafety.SAFE,
                    ),
                    ShellCommand(
                        command="echo '📋 Check ingredients and tools'",
                        description="Verify all ingredients are available",
                        safety_level=CommandSafety.SAFE,
                    ),
                    ShellCommand(
                        command="echo '🔥 Preheat cooking surface/oven as needed'",
                        description="Prepare cooking equipment",
                        safety_level=CommandSafety.MODERATE,
                        requires_confirmation=True,
                    ),
                    ShellCommand(
                        command="echo '⚠️  Follow recipe instructions carefully'",
                        description="Execute cooking steps",
                        safety_level=CommandSafety.MODERATE,
                        expected_duration=1800,  # 30 minutes
                    ),
                    ShellCommand(
                        command="echo '✅ Cooking complete! 🍽️'",
                        description="Finish cooking process",
                        safety_level=CommandSafety.SAFE,
                    ),
                ]
            )

        return commands

    async def _generate_creative_commands(
        self, taxonomy: IntentTaxonomy
    ) -> List[ShellCommand]:
        """Generate creative task commands."""
        commands = []
        intent = taxonomy.intent.lower()

        if "write" in intent or "blog" in intent:
            # Extract topic if possible
            topic = "your topic"
            commands.extend(
                [
                    ShellCommand(
                        command=f"echo '✍️  Starting writing process for: {topic}'",
                        description="Initialize writing session",
                        safety_level=CommandSafety.SAFE,
                    ),
                    ShellCommand(
                        command="mkdir -p ~/Documents/Writing",
                        description="Create writing directory",
                        safety_level=CommandSafety.SAFE,
                    ),
                    ShellCommand(
                        command="touch ~/Documents/Writing/draft.md",
                        description="Create draft file",
                        safety_level=CommandSafety.SAFE,
                    ),
                    ShellCommand(
                        command="echo '# Draft\n\n## Introduction\n\n## Main Content\n\n## Conclusion' > ~/Documents/Writing/draft.md",
                        description="Add basic structure",
                        safety_level=CommandSafety.SAFE,
                    ),
                    ShellCommand(
                        command="open ~/Documents/Writing/draft.md",
                        description="Open file for editing",
                        safety_level=CommandSafety.SAFE,
                    ),
                ]
            )

        elif "design" in intent:
            commands.extend(
                [
                    ShellCommand(
                        command="echo '🎨 Setting up design workspace...'",
                        description="Initialize design session",
                        safety_level=CommandSafety.SAFE,
                    ),
                    ShellCommand(
                        command="mkdir -p ~/Documents/Design",
                        description="Create design directory",
                        safety_level=CommandSafety.SAFE,
                    ),
                    ShellCommand(
                        command="echo 'Consider using: Figma, Sketch, Adobe Creative Suite'",
                        description="Suggest design tools",
                        safety_level=CommandSafety.SAFE,
                    ),
                ]
            )

        return commands

    async def _generate_business_commands(
        self, taxonomy: IntentTaxonomy
    ) -> List[ShellCommand]:
        """Generate business task commands."""
        commands = []
        intent = taxonomy.intent.lower()

        if "meeting" in intent or "schedule" in intent:
            commands.extend(
                [
                    ShellCommand(
                        command="echo '📅 Setting up meeting...'",
                        description="Initialize meeting setup",
                        safety_level=CommandSafety.SAFE,
                    ),
                    ShellCommand(
                        command="open -a Calendar",
                        description="Open Calendar app",
                        safety_level=CommandSafety.SAFE,
                    ),
                    ShellCommand(
                        command="echo '✅ Create meeting invite with:'",
                        description="Meeting checklist header",
                        safety_level=CommandSafety.SAFE,
                    ),
                    ShellCommand(
                        command="echo '- Date and time'",
                        description="Set meeting time",
                        safety_level=CommandSafety.SAFE,
                    ),
                    ShellCommand(
                        command="echo '- Attendee list'",
                        description="Add participants",
                        safety_level=CommandSafety.SAFE,
                    ),
                    ShellCommand(
                        command="echo '- Meeting agenda'",
                        description="Prepare agenda",
                        safety_level=CommandSafety.SAFE,
                    ),
                    ShellCommand(
                        command="echo '- Video call link (Zoom, Meet, etc.)'",
                        description="Add video conference details",
                        safety_level=CommandSafety.SAFE,
                    ),
                ]
            )

        elif "report" in intent:
            commands.extend(
                [
                    ShellCommand(
                        command="echo '📊 Creating business report...'",
                        description="Initialize report creation",
                        safety_level=CommandSafety.SAFE,
                    ),
                    ShellCommand(
                        command="mkdir -p ~/Documents/Reports",
                        description="Create reports directory",
                        safety_level=CommandSafety.SAFE,
                    ),
                    ShellCommand(
                        command="touch ~/Documents/Reports/business_report.md",
                        description="Create report file",
                        safety_level=CommandSafety.SAFE,
                    ),
                    ShellCommand(
                        command="echo '# Business Report\n\n## Executive Summary\n\n## Key Metrics\n\n## Analysis\n\n## Recommendations' > ~/Documents/Reports/business_report.md",
                        description="Add report template",
                        safety_level=CommandSafety.SAFE,
                    ),
                ]
            )

        return commands

    async def _generate_research_commands(
        self, taxonomy: IntentTaxonomy
    ) -> List[ShellCommand]:
        """Generate research task commands."""
        commands = []
        intent = taxonomy.intent.lower()

        commands.extend(
            [
                ShellCommand(
                    command="echo '🔍 Starting research process...'",
                    description="Initialize research session",
                    safety_level=CommandSafety.SAFE,
                ),
                ShellCommand(
                    command="mkdir -p ~/Documents/Research",
                    description="Create research directory",
                    safety_level=CommandSafety.SAFE,
                ),
                ShellCommand(
                    command="touch ~/Documents/Research/notes.md",
                    description="Create research notes file",
                    safety_level=CommandSafety.SAFE,
                ),
                ShellCommand(
                    command="echo '# Research Notes\n\n## Topic\n\n## Sources\n\n## Key Findings\n\n## Next Steps' > ~/Documents/Research/notes.md",
                    description="Add research template",
                    safety_level=CommandSafety.SAFE,
                ),
                ShellCommand(
                    command="open ~/Documents/Research/notes.md",
                    description="Open notes for editing",
                    safety_level=CommandSafety.SAFE,
                ),
            ]
        )

        if "search" in intent or "find" in intent:
            commands.append(
                ShellCommand(
                    command="echo '💡 Recommended search strategies:'",
                    description="Show search guidance",
                    safety_level=CommandSafety.SAFE,
                )
            )
            commands.extend(
                [
                    ShellCommand(
                        command="echo '- Google Scholar for academic sources'",
                        description="Academic research tip",
                        safety_level=CommandSafety.SAFE,
                    ),
                    ShellCommand(
                        command="echo '- Library databases for authoritative sources'",
                        description="Library research tip",
                        safety_level=CommandSafety.SAFE,
                    ),
                    ShellCommand(
                        command="echo '- Industry reports for market data'",
                        description="Industry research tip",
                        safety_level=CommandSafety.SAFE,
                    ),
                ]
            )

        return commands

    async def _generate_personal_commands(
        self, taxonomy: IntentTaxonomy
    ) -> List[ShellCommand]:
        """Generate personal task commands."""
        commands = []
        intent = taxonomy.intent.lower()

        if "organize" in intent or "plan" in intent:
            commands.extend(
                [
                    ShellCommand(
                        command="echo '📋 Starting organization process...'",
                        description="Initialize organization session",
                        safety_level=CommandSafety.SAFE,
                    ),
                    ShellCommand(
                        command="open -a Reminders",
                        description="Open Reminders app",
                        safety_level=CommandSafety.SAFE,
                    ),
                    ShellCommand(
                        command="open -a Notes",
                        description="Open Notes app",
                        safety_level=CommandSafety.SAFE,
                    ),
                    ShellCommand(
                        command="echo '✅ Organization checklist:'",
                        description="Show organization steps",
                        safety_level=CommandSafety.SAFE,
                    ),
                    ShellCommand(
                        command="echo '- List current tasks and priorities'",
                        description="Task inventory",
                        safety_level=CommandSafety.SAFE,
                    ),
                    ShellCommand(
                        command="echo '- Set deadlines and reminders'",
                        description="Time management",
                        safety_level=CommandSafety.SAFE,
                    ),
                    ShellCommand(
                        command="echo '- Create action plan'",
                        description="Planning step",
                        safety_level=CommandSafety.SAFE,
                    ),
                ]
            )

        elif "buy" in intent or "shopping" in intent:
            commands.extend(
                [
                    ShellCommand(
                        command="echo '🛒 Creating shopping plan...'",
                        description="Initialize shopping session",
                        safety_level=CommandSafety.SAFE,
                    ),
                    ShellCommand(
                        command="touch ~/Documents/shopping_list.txt",
                        description="Create shopping list",
                        safety_level=CommandSafety.SAFE,
                    ),
                    ShellCommand(
                        command="echo 'Shopping List:\n- Item 1\n- Item 2\n- Item 3' > ~/Documents/shopping_list.txt",
                        description="Add template items",
                        safety_level=CommandSafety.SAFE,
                    ),
                    ShellCommand(
                        command="open ~/Documents/shopping_list.txt",
                        description="Open list for editing",
                        safety_level=CommandSafety.SAFE,
                    ),
                ]
            )

        return commands

    def _generate_success_criteria(
        self, taxonomy: IntentTaxonomy, commands: List[ShellCommand]
    ) -> List[str]:
        """Generate success criteria for the execution plan."""
        criteria = []

        # Based on intent type
        intent_lower = taxonomy.intent.lower()

        if "install" in intent_lower:
            if "nginx" in intent_lower:
                criteria.extend(
                    [
                        "Nginx service is running",
                        "Port 80/8080 is responding",
                        "Default nginx page is accessible",
                    ]
                )
            elif "node" in intent_lower:
                criteria.extend(
                    [
                        "Node.js version command works",
                        "NPM is available",
                        "Can create new npm projects",
                    ]
                )

        elif "create" in intent_lower:
            if "react" in intent_lower:
                criteria.extend(
                    [
                        "React project directory exists",
                        "Dependencies are installed",
                        "Development server starts successfully",
                    ]
                )

        # Generic criteria based on commands
        if any("sudo" in cmd.command for cmd in commands):
            criteria.append("All privileged operations completed successfully")

        if any(cmd.safety_level == CommandSafety.DANGEROUS for cmd in commands):
            criteria.append("System remains stable after modifications")

        return commands

    async def _generate_ai_commands(
        self, taxonomy: IntentTaxonomy
    ) -> List[ShellCommand]:
        """Generate executable commands using AI for any task category."""
        from ..core.models import get_user_id
        from ..providers.openrouter import get_structured_generator

        # Schema for AI to generate commands
        schema = {
            "type": "object",
            "properties": {
                "commands": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "command": {"type": "string"},
                            "description": {"type": "string"},
                            "safety_level": {"enum": ["safe", "moderate", "dangerous"]},
                            "requires_confirmation": {"type": "boolean"},
                            "expected_duration": {"type": "integer", "minimum": 0},
                            "working_directory": {"type": "string"},
                        },
                        "required": ["command", "description", "safety_level"],
                    },
                }
            },
            "required": ["commands"],
        }

        # Create platform-aware prompt
        platform_info = f"Platform: {self.platform.title()}, Shell: {self.shell}"

        # Build component context
        component_context = ""
        if taxonomy.components:
            comp_list = [
                f"- {c.name}: {c.description}" for c in taxonomy.components[:5]
            ]
            component_context = "\n\nRequired components:\n" + "\n".join(comp_list)

        prompt = f"""Generate executable shell commands for: "{taxonomy.intent}"
Category: {taxonomy.intent_category}
{platform_info}{component_context}

Create a sequence of shell commands that accomplish this task. Commands should be:
- Executable on {self.platform.title()} using {self.shell}
- Real commands (not just echo statements)
- Safe and appropriate for the platform
- Include file operations, app launches, or system commands as needed

For each command specify:
- The actual command to run
- Clear description of what it does
- Safety level (safe/moderate/dangerous)
- Whether it needs user confirmation
- Expected duration in seconds (optional)

Examples of good commands:
- mkdir -p ~/Documents/Projects
- open -a TextEdit ~/Documents/notes.txt
- curl -O https://example.com/file.zip
- npm install express
- git clone https://github.com/user/repo.git

Avoid fake commands like echo statements unless actually displaying information."""

        try:
            user_id = get_user_id()
            generator = await get_structured_generator()

            response = await generator.generate_json(
                prompt=prompt,
                schema=schema,
                model="openai/gpt-3.5-turbo",
                user_id=user_id,
                max_retries=2,
            )

            commands = []
            for cmd_data in response.get("commands", []):
                safety_level = CommandSafety.SAFE
                if cmd_data["safety_level"] == "moderate":
                    safety_level = CommandSafety.MODERATE
                elif cmd_data["safety_level"] == "dangerous":
                    safety_level = CommandSafety.DANGEROUS

                commands.append(
                    ShellCommand(
                        command=cmd_data["command"],
                        description=cmd_data["description"],
                        safety_level=safety_level,
                        requires_confirmation=cmd_data.get(
                            "requires_confirmation", False
                        ),
                        expected_duration=cmd_data.get("expected_duration"),
                        working_directory=cmd_data.get("working_directory"),
                    )
                )

            return commands

        except Exception as e:
            # If AI generation fails, raise exception to trigger fallback
            raise Exception(f"AI command generation failed: {e}")

    def _extract_project_name(self, intent: str) -> str:
        """Extract project name from intent text."""
        import re

        # Look for patterns like "called X", "named X", "app X"
        patterns = [
            r"called\s+([\w-]+)",
            r"named\s+([\w-]+)",
            r"app\s+([\w-]+)",
            r"project\s+([\w-]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, intent.lower())
            if match:
                name = match.group(1)
                # Clean up the name (remove invalid characters)
                name = re.sub(r"[^\w-]", "-", name)
                return name

        # Default fallback
        return "my-react-app"

    def format_execution_plan(self, plan: ExecutionPlan) -> str:
        """Format execution plan for CLI display."""
        output = []

        # Header
        output.append(f"🚀 **{plan.title}**\n")
        output.append(f"📋 {plan.description}")
        output.append(f"⏱️  Estimated time: {plan.estimated_total_time} minutes\n")

        # Prerequisites
        if plan.prerequisites:
            output.append("📋 **Prerequisites:**")
            for prereq in plan.prerequisites:
                output.append(f"  • {prereq}")
            output.append("")

        # Safety warnings
        if plan.safety_warnings:
            output.append("⚠️  **Safety Warnings:**")
            for warning in plan.safety_warnings:
                output.append(f"  • {warning}")
            output.append("")

        # Commands
        output.append("🔧 **Commands to Execute:**\n")
        for i, cmd in enumerate(plan.commands, 1):
            safety_icon = {
                CommandSafety.SAFE: "✅",
                CommandSafety.MODERATE: "⚠️ ",
                CommandSafety.DANGEROUS: "🔴",
            }[cmd.safety_level]

            output.append(f"{i}. {safety_icon} **{cmd.description}**")
            output.append("   ```bash")
            output.append(f"   {cmd.command}")
            output.append("   ```")

            if cmd.expected_duration:
                output.append(f"   ⏱️  Expected duration: {cmd.expected_duration}s")

            if cmd.requires_confirmation:
                output.append("   ❓ Requires confirmation before execution")

            output.append("")

        # Success criteria
        if plan.success_criteria:
            output.append("✅ **Success Criteria:**")
            for criterion in plan.success_criteria:
                output.append(f"  • {criterion}")

        return "\n".join(output)

    def generate_shell_script(self, plan: ExecutionPlan) -> str:
        """Generate a complete shell script from execution plan."""
        script_lines = [
            "#!/bin/bash",
            f"# Generated by Doorman - {plan.title}",
            f"# {plan.description}",
            "",
            "set -e  # Exit on any error",
            "",
            "echo '🚀 Starting execution plan...'",
            "",
        ]

        for i, cmd in enumerate(plan.commands, 1):
            script_lines.extend(
                [
                    f"echo '📝 Step {i}: {cmd.description}'",
                    f"echo '   Command: {cmd.command}'",
                    "",
                ]
            )

            if cmd.requires_confirmation:
                script_lines.extend(
                    [
                        "read -p '⚠️  This command requires confirmation. Continue? (y/N): ' confirm",
                        "if [[ $confirm != [yY] ]]; then",
                        f"    echo '❌ Skipping step {i}'",
                        "else",
                        f"    {cmd.command}",
                        f"    echo '✅ Step {i} completed'",
                        "fi",
                        "",
                    ]
                )
            else:
                script_lines.extend([cmd.command, f"echo '✅ Step {i} completed'", ""])

        script_lines.extend(["echo '🎉 Execution plan completed successfully!'", ""])

        return "\n".join(script_lines)
