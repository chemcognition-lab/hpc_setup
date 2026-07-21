#!/usr/bin/env bash

# ==============================================================================
# Zsh & Oh My Zsh Setup Script for HPC Trainees
# This script installs Oh My Zsh, clones theme/plugin dependencies, copies the
# templates, and configures bash to auto-switch to zsh for interactive shells.
# ==============================================================================

set -euo pipefail

# Define text styling
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Starting Zsh & Oh My Zsh Environment Setup ===${NC}"

# 1. Install Oh My Zsh if not already present
if [ ! -d "$HOME/.oh-my-zsh" ]; then
    echo -e "${BLUE}Installing Oh My Zsh...${NC}"
    # Run the installation script in unattended mode (doesn't change default shell or prompt for input)
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended --keep-zshrc
    echo -e "${GREEN}✓ Oh My Zsh installed successfully!${NC}"
else
    echo -e "${GREEN}✓ Oh My Zsh is already installed.${NC}"
fi

# Define custom directory path (with fallback to default OMZ path)
ZSH_CUSTOM="${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}"

# 2. Clone Powerlevel10k theme
P10K_DIR="$ZSH_CUSTOM/themes/powerlevel10k"
if [ ! -d "$P10K_DIR" ]; then
    echo -e "${BLUE}Cloning Powerlevel10k theme...${NC}"
    git clone --depth=1 https://github.com/romkatv/powerlevel10k.git "$P10K_DIR"
    echo -e "${GREEN}✓ Powerlevel10k theme cloned.${NC}"
else
    echo -e "${GREEN}✓ Powerlevel10k theme is already present.${NC}"
fi

# 3. Clone zsh-autosuggestions plugin
AUTOSUGGEST_DIR="$ZSH_CUSTOM/plugins/zsh-autosuggestions"
if [ ! -d "$AUTOSUGGEST_DIR" ]; then
    echo -e "${BLUE}Cloning zsh-autosuggestions plugin...${NC}"
    git clone https://github.com/zsh-users/zsh-autosuggestions "$AUTOSUGGEST_DIR"
    echo -e "${GREEN}✓ zsh-autosuggestions plugin cloned.${NC}"
else
    echo -e "${GREEN}✓ zsh-autosuggestions plugin is already present.${NC}"
fi

# 4. Copy configurations (with backup)
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}Configuring ~/.zshrc...${NC}"
if [ -f "$HOME/.zshrc" ]; then
    cp "$HOME/.zshrc" "$HOME/.zshrc.bak"
    echo -e "${YELLOW}Backed up existing ~/.zshrc to ~/.zshrc.bak${NC}"
fi
cp "$SCRIPT_DIR/dotzshrc" "$HOME/.zshrc"
echo -e "${GREEN}✓ Copied .zshrc configuration to ~/.zshrc${NC}"

echo -e "${BLUE}Configuring ~/.slurm_shortcuts...${NC}"
if [ -f "$HOME/.slurm_shortcuts" ]; then
    cp "$HOME/.slurm_shortcuts" "$HOME/.slurm_shortcuts.bak"
    echo -e "${YELLOW}Backed up existing ~/.slurm_shortcuts to ~/.slurm_shortcuts.bak${NC}"
fi
cp "$SCRIPT_DIR/slurm_shortcuts" "$HOME/.slurm_shortcuts"
echo -e "${GREEN}✓ Copied slurm shortcuts to ~/.slurm_shortcuts${NC}"

echo -e "${BLUE}Installing helper scripts into ~/.local/bin...${NC}"
mkdir -p "$HOME/.local/bin"
if [ -f "$PROJECT_ROOT/scripts/slurm_shares.py" ]; then
    cp "$PROJECT_ROOT/scripts/slurm_shares.py" "$HOME/.local/bin/slurm_shares.py"
    chmod +x "$HOME/.local/bin/slurm_shares.py"
fi
if [ -f "$PROJECT_ROOT/scripts/optuna_sweep.py" ]; then
    cp "$PROJECT_ROOT/scripts/optuna_sweep.py" "$HOME/.local/bin/optuna_sweep.py"
    chmod +x "$HOME/.local/bin/optuna_sweep.py"
fi
echo -e "${GREEN}✓ Installed Slurm helper scripts to ~/.local/bin${NC}"

# 5. Enable auto-switching to Zsh in ~/.bash_profile
BASH_PROFILE="$HOME/.bash_profile"
# Fallback to ~/.bashrc if ~/.bash_profile does not exist (some environments differ)
if [ ! -f "$BASH_PROFILE" ] && [ -f "$HOME/.bashrc" ]; then
    BASH_PROFILE="$HOME/.bashrc"
fi

SWITCH_CHECK="exec zsh -l"
if grep -qF "$SWITCH_CHECK" "$BASH_PROFILE"; then
    echo -e "${GREEN}✓ Interactive Zsh switcher is already configured in $BASH_PROFILE.${NC}"
else
    echo -e "${BLUE}Adding Zsh switcher to $BASH_PROFILE...${NC}"
    cat >> "$BASH_PROFILE" << 'EOF'

# Check if the shell is interactive (-i flag) before switching to zsh
if [[ $- == *i* ]] && command -v zsh >/dev/null 2>&1; then
    exec zsh -l
fi
EOF
    echo -e "${GREEN}✓ Zsh switcher configured in $BASH_PROFILE.${NC}"
fi

echo -e "\n${GREEN}====================================================${NC}"
echo -e "${GREEN}🎉 Setup Complete!${NC}"
echo -e "${GREEN}To enter your new shell environment, run:${NC}"
echo -e "${YELLOW}    exec zsh -l${NC}"
echo -e "${GREEN}====================================================${NC}"
