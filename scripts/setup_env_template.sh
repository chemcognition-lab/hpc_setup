#!/usr/bin/env bash
# ==============================================================================
# Project Environment Setup Script (Template)
# Copy this script to your project's hpc/ or scripts/ directory.
# Run this on a login node (which has internet access) to initialize your
# micromamba environment on $SCRATCH and install your repository.
# ==============================================================================

set -euo pipefail

# Enforce that script is running on an HPC cluster with $SCRATCH
if [ -z "${SCRATCH:-}" ]; then
    echo "Error: \$SCRATCH environment variable is not defined."
    echo "This script is designed to run in SciNet/Compute Canada cluster environments."
    exit 1
fi

# 1. Resolve project directory structure
# This assumes the script is run from a subfolder (like scripts/ or hpc/) and
# moves up to the root. Adjust if placing this file directly in the repo root.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")" # Parent folder
cd "$PROJECT_ROOT"

echo "=== Switched to repository root: $(pwd) ==="

# Define the environment name (change this to match your project name)
ENV_NAME="my_project"

# Define target paths
BIN_DIR="$HOME/.local/bin"
MICROMAMBA_EXE="$BIN_DIR/micromamba"
MAMBA_CACHE="$SCRATCH/micromamba_cache"
SCRATCH_ENV_DIR="$SCRATCH/envs/$ENV_NAME"

# 2. Ensure Micromamba binary is present
if [ ! -f "$MICROMAMBA_EXE" ]; then
    echo "=== Downloading standalone Micromamba static binary ==="
    mkdir -p "$BIN_DIR"
    curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xj -C "$BIN_DIR" --strip-components=1 bin/micromamba
    chmod +x "$MICROMAMBA_EXE"
fi

# 3. Configure caches to save home quota
echo "=== Configuring Micromamba Caches ==="
mkdir -p "$MAMBA_CACHE"
"$MICROMAMBA_EXE" config append pkgs_dirs "$MAMBA_CACHE"
"$MICROMAMBA_EXE" config append envs_dirs "$(dirname "$SCRATCH_ENV_DIR")"
"$MICROMAMBA_EXE" config set channel_priority strict

# Redirect standard caches to scratch to prevent home directory/inode exhaustion
export XDG_CACHE_HOME="$SCRATCH/.cache"
export XDG_CONFIG_HOME="$SCRATCH/.config"
export PYTHONUSERBASE="$SCRATCH/.local"
mkdir -p "$XDG_CACHE_HOME" "$XDG_CONFIG_HOME" "$PYTHONUSERBASE"

# 4. Initialize micromamba shell hook for this script execution
# Detect shell automatically, fallback to bash
SHELL_NAME=$(basename "$SHELL")
if [[ "$SHELL_NAME" != "bash" && "$SHELL_NAME" != "zsh" ]]; then
    SHELL_NAME="bash"
fi
eval "$("$MICROMAMBA_EXE" shell hook --shell="$SHELL_NAME")"

# 5. Create environment from environment.yml (prefix located on SCRATCH)
if [ -f "environment.yml" ]; then
    echo "=== Creating Environment from environment.yml ==="
    "$MICROMAMBA_EXE" env create --prefix "$SCRATCH_ENV_DIR" -f environment.yml -y
elif [ -f "environment.yaml" ]; then
    echo "=== Creating Environment from environment.yaml ==="
    "$MICROMAMBA_EXE" env create --prefix "$SCRATCH_ENV_DIR" -f environment.yaml -y
else
    echo "=== Creating default environment with Python 3.10 ==="
    "$MICROMAMBA_EXE" create --prefix "$SCRATCH_ENV_DIR" python=3.10 -y
fi

# 6. Activate env and run local installations
echo "=== Activating Environment ==="
micromamba activate "$SCRATCH_ENV_DIR"

if [ -f "setup.py" ] || [ -f "pyproject.toml" ]; then
    echo "=== Installing the local project in editable mode ==="
    pip install -e .
fi

# Create logging outputs
echo "=== Creating results/logs directory ==="
mkdir -p results/logs

echo -e "\n=== Setup complete! ==="
echo "To activate this environment in future scripts or interactive sessions, run:"
echo -e "    eval \"\$($HOME/.local/bin/micromamba shell hook --shell=\$SHELL)\" && micromamba activate $SCRATCH_ENV_DIR"
