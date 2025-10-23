#!/bin/bash
set -e

# Doorman installation script - like npx but for Python
# Usage: curl -sSL https://doorman.dev/install.sh | bash

DOORMAN_VERSION="${DOORMAN_VERSION:-latest}"
INSTALL_DIR="${INSTALL_DIR:-$HOME/.local/bin}"
PYTHON_MIN_VERSION="3.9"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m' 
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Cyberpunk banner
echo -e "${CYAN}"
cat << "EOF"
▮▮▮ DOORMAN.EXE INSTALLER ▮▮▮
Universal intent taxonomy system
EOF
echo -e "${NC}"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is required but not installed.${NC}"
    echo "Please install Python 3.9+ and try again."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)"; then
    echo -e "${GREEN}✓ Python ${PYTHON_VERSION} detected${NC}"
else
    echo -e "${RED}Error: Python ${PYTHON_MIN_VERSION}+ required, found ${PYTHON_VERSION}${NC}"
    exit 1
fi

# Create install directory
mkdir -p "$INSTALL_DIR"

# Check if pipx is available (preferred method)
if command -v pipx &> /dev/null; then
    echo -e "${CYAN}▮ Installing via pipx...${NC}"
    pipx install doorman
    echo -e "${GREEN}✓ Doorman installed via pipx${NC}"
    
# Check if uv is available (fast method)
elif command -v uv &> /dev/null; then
    echo -e "${CYAN}▮ Installing via uv...${NC}"
    uv tool install doorman
    echo -e "${GREEN}✓ Doorman installed via uv${NC}"
    
# Fallback to pip + user install
else
    echo -e "${CYAN}▮ Installing via pip (user install)...${NC}"
    python3 -m pip install --user doorman
    
    # Add user bin to PATH if not already there
    USER_BIN="$HOME/.local/bin"
    if [[ ":$PATH:" != *":$USER_BIN:"* ]]; then
        echo -e "${YELLOW}▮ Adding $USER_BIN to PATH${NC}"
        
        # Add to shell profile
        if [[ "$SHELL" == *"zsh"* ]]; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
            echo -e "${YELLOW}Added to ~/.zshrc - restart terminal or run: source ~/.zshrc${NC}"
        elif [[ "$SHELL" == *"bash"* ]]; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
            echo -e "${YELLOW}Added to ~/.bashrc - restart terminal or run: source ~/.bashrc${NC}"
        fi
    fi
    
    echo -e "${GREEN}✓ Doorman installed via pip${NC}"
fi

# Test installation
echo -e "${CYAN}▮ Testing installation...${NC}"
if command -v doorman &> /dev/null; then
    echo -e "${GREEN}✓ Doorman CLI available${NC}"
    
    # Show version and basic info
    echo -e "${CYAN}▮ Version info:${NC}"
    doorman --version 2>/dev/null || echo "doorman v1.0.0"
    
    echo -e "\n${GREEN}🎮 Installation complete!${NC}"
    echo -e "${CYAN}▮▮▮ Quick start:${NC}"
    echo "  doorman plan 'create a todo app'"
    echo "  doorman auth status"
    echo "  doorman fighters"
    echo ""
    echo -e "${YELLOW}📖 Next steps:${NC}"
    echo "  1. Set OpenRouter API key: export OPENROUTER_API_KEY=your_key"
    echo "  2. Initialize database: doorman db init"
    echo "  3. Start planning tasks!"
    
else
    echo -e "${RED}✗ Installation failed - doorman command not found${NC}"
    echo -e "${YELLOW}Try restarting your terminal or adding ~/.local/bin to PATH${NC}"
    exit 1
fi