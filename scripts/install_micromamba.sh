#!/usr/bin/env bash

# ==============================================================================
# Micromamba HPC Installer Script
# Installs Micromamba to $SCRATCH, redirects package/environment caches to
# $SCRATCH to avoid $HOME quota/inode exhaustion, and configures shell hooks.
# ==============================================================================

set -euo pipefail

# Text styling
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Starting Micromamba HPC Installation ===${NC}\n"

# 1. Enforce that script is running on an HPC cluster with $SCRATCH
if [ -z "${SCRATCH:-}" ]; then
    echo -e "${RED}Error: \$SCRATCH environment variable is not defined.${NC}"
    echo -e "This script is designed for SciNet/Compute Canada cluster environments."
    echo -e "If running locally, please install micromamba manually via standard methods."
    exit 1
fi

echo -e "${GREEN}✓ Found \$SCRATCH directory at: $SCRATCH${NC}"

# Define target paths
BIN_DIR="$SCRATCH/bin"
MAMBA_ROOT="$SCRATCH/micromamba"
MAMBA_CACHE="$SCRATCH/micromamba_cache"
ENVS_DIR="$SCRATCH/envs"

# Create directories
mkdir -p "$BIN_DIR"
mkdir -p "$MAMBA_ROOT"
mkdir -p "$MAMBA_CACHE"
mkdir -p "$ENVS_DIR"

# 2. Download and extract Micromamba binary
if [ -f "$BIN_DIR/micromamba" ]; then
    echo -e "${GREEN}✓ Micromamba binary already exists at $BIN_DIR/micromamba${NC}"
else
    echo -e "${BLUE}Downloading latest Micromamba static binary for Linux 64...${NC}"
    curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xj -C "$BIN_DIR" bin/micromamba --strip-components=1
    chmod +x "$BIN_DIR/micromamba"
    echo -e "${GREEN}✓ Micromamba successfully downloaded to $BIN_DIR/micromamba${NC}"
fi

# Add BIN_DIR to active PATH for the configuration step
export PATH="$BIN_DIR:$PATH"

# 3. Configure package and environment caches on $SCRATCH (prevents home inode issues)
echo -e "${BLUE}Configuring ~/.condarc...${NC}"
micromamba config append pkgs_dirs "$MAMBA_CACHE"
micromamba config append envs_dirs "$ENVS_DIR"
micromamba config set channel_priority strict
echo -e "${GREEN}✓ Configured ~/.condarc package and environment directories on \$SCRATCH.${NC}"

# 4. Initialize Micromamba hooks for both Zsh and Bash
echo -e "${BLUE}Initializing shell configurations...${NC}"

# Initialize Zsh
if [ -d "$HOME/.oh-my-zsh" ] || [ -f "$HOME/.zshrc" ]; then
    echo -e "Initializing hook for Zsh..."
    micromamba shell init --shell zsh --prefix "$MAMBA_ROOT"
fi

# Initialize Bash
if [ -f "$HOME/.bashrc" ] || [ -f "$HOME/.bash_profile" ]; then
    echo -e "Initializing hook for Bash..."
    micromamba shell init --shell bash --prefix "$MAMBA_ROOT"
fi

echo -e "\n${GREEN}====================================================${NC}"
echo -e "${GREEN}🎉 Micromamba installation complete!${NC}"
echo -e "${GREEN}Micromamba root:     ${BLUE}$MAMBA_ROOT${NC}"
echo -e "${GREEN}Environment storage: ${BLUE}$ENVS_DIR${NC}"
echo -e "${GREEN}Package cache:      ${BLUE}$MAMBA_CACHE${NC}"
echo -e "${GREEN}====================================================${NC}"
echo -e "${YELLOW}Please restart your shell or run:${NC}"
echo -e "${CYAN}    source ~/.zshrc    (or source ~/.bashrc)${NC}"
echo -e "${GREEN}To verify execution, try: micromamba --version${NC}"
