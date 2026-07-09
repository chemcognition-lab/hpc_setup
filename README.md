# HPC Onboarding and Setup Guide

This repository contains configurations and scripts to set up shell, SSH, GitHub access, and package environments on Killarney, Trillium, Balam, TamIA, Vulcan, and Nibi clusters.

---

## Setup Steps

### 0. Request Compute Access & GitHub Org Access
Before attempting to connect, you must request compute accounts and organization access:
1. Register in the Compute Canada Database: [CCDB Login/Registration](https://ccdb.computecanada.ca/security/login).
2. Apply for a role at [CCDB Add Role](https://ccdb.computecanada.ca/me/add_role) using sponsor CCDB ID: **ask PI**.
3. Ask me to approve your sponsorship request and add you to our **AIP project** (not RAP or RRG).
4. Opt into Killarney services at [CCDB Access Services](https://ccdb.alliancecan.ca/me/access_services).
5. Set up Duo Two-Factor Authentication: [Duo 2FA Setup Guide](https://docs.alliancecan.ca/wiki/Multifactor_authentication#Use_a_smartphone_or_tablet).
6. Verify your allocation is active at [CCDB Allocations](https://ccdb.alliancecan.ca/me/allocations).
7. Request access to Vector Institute: [Vector Onboarding Request Form](https://vectorinstitute.ai/onboarding-request-form/).
8. Ask to be added to the `chemcognition-lab` GitHub organization to access the private code repositories.

---

### 1. Configure SSH Access (Makes it faster and easier to connect)
Connecting to cluster terminals usually requires typing long hostnames and credentials. Sourcing this SSH configuration allows you to connect instantly using short nicknames (like `ssh killarney`) and enables multiplexing, which keeps connections active and speeds up logins.
1. Copy the contents of `ssh_config_template` into your local `~/.ssh/config` file.
2. Replace `<your_username>` with your actual cluster username (e.g., `taco`).
3. Create the local sockets directory required for multiplexing:
   ```bash
   mkdir -p ~/.ssh/sockets
   ```
4. Connect using the short aliases: `ssh killarney`, `ssh trillium-gpu`, `ssh balam`, `ssh tamia`, `ssh vulcan`, or `ssh nibi`.
*(Note: Killarney requires connecting to Vector or UofT VPN if off-campus).*

---

### 2. Configure Zsh (Way nicer terminal environment)
HPC clusters default to a basic Bash shell. Switching to Zsh and Oh My Zsh gives you auto-suggestions, tab-completions, prompt styling, and loads custom Slurm productivity shortcuts.
1. Run the setup script:
   ```bash
   bash zsh/zsh_setup.sh
   ```
2. Activate zsh:
   ```bash
   exec zsh -l
   ```
This configures Oh My Zsh, Powerlevel10k, zsh-autosuggestions, and sources `~/.slurm_shortcuts`. It also redirects your standard cache directories (like `XDG_CACHE_HOME`) to `$SCRATCH` so you don't run out of space or cause write errors on read-only compute nodes.

Available shortcuts:
- `squeue`: Shows only your active jobs.
- `shistory`: Lists status and runtime of your last 10 jobs.
- `stail`: Tails the latest log in `results/logs/` and monitors until completion.
- `sabort`: Cancels your latest active job.

---

### 3. Setup GitHub SSH Keys (Easier code and data downloads)
To download data and clone code repositories without typing your username and password every time, link your cluster environment to GitHub using SSH keys.

> [!WARNING]
> **SSH Key Security & Sharing:**
> - **Do NOT copy your personal computer's private SSH key** (from your own local machine) to any of the clusters. This is a severe security risk.
> - **Generate a key on one of the clusters** (e.g., Killarney) using the steps below.
> - **You can copy the generated key in-between clusters** (e.g., copy it from Killarney to Trillium and Balam) so they share the same key. This is safe, convenient, and prevents you from having to register multiple unique keys on GitHub.

```bash
# 1. Generate Ed25519 SSH key (press Enter to accept default path and empty passphrase)
ssh-keygen -t ed25519 -C "your_email@domain.com" -f ~/.ssh/id_ed25519 -N ""

# 2. Start the SSH agent and add the key
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# 3. Print public key, then copy it to your settings at https://github.com/settings/keys
cat ~/.ssh/id_ed25519.pub

# 4. Test connection
ssh -T git@github.com
```

---

### 4. Install Micromamba (Scientific software package manager)
To run scientific software, we need a package manager. We install the Micromamba binary in your home directory (so it is permanent), but configure its package caches and environments to live on `$SCRATCH` to avoid filling up the cluster's limited home space/inodes.
*(Note: Other modern packaging tools like `uv` exist, and Pixi may work on clusters in the future, but Micromamba is currently the stable standard).*
1. Run the installer:
   ```bash
   bash scripts/install_micromamba.sh
   ```
2. Reload your configuration:
   ```bash
   source ~/.zshrc
   ```

---

### 5. Setup Project Environments (Isolates project dependencies)
To configure environment libraries for a cloned project, you can copy the setup script template to build dependencies from a repo's `environment.yml` and install the project locally in editable mode.
1. Copy the environment script template to your project's repository:
   ```bash
   cp scripts/setup_env_template.sh /path/to/project/hpc/setup_env.sh
   ```
2. Edit the `ENV_NAME` variable in the script.
3. Run the script on a cluster login node:
   ```bash
   bash /path/to/project/hpc/setup_env.sh
   ```
This builds your environment under `$SCRATCH/envs/` using this repository's [environment.yml](environment.yml) as a baseline.

For concrete examples, see the [project_template](https://github.com/chemcognition-lab/project_template) repository for structural layout, or look at the active [MLP_BayesOpt](https://github.com/chemcognition-lab/MLP_BayesOpt) repository for a real-world example of running a Bayesian Optimization sweep.

---

## Documentation and Resources Links

### Registration and Account Management
- [Vector Institute Onboarding Request Form](https://vectorinstitute.ai/onboarding-request-form/)
- [Alliance Canada Account Apply Guide](https://alliancecan.ca/en/services/advanced-research-computing/account-management/apply-account)
- [CCDB Portal Registration](https://ccdb.computecanada.ca/security/login)

### Cluster Documentation and Best Practices
- [Alliance Canada Getting Started Wiki](https://docs.alliancecan.ca/wiki/Getting_started)
- [Alliance Canada Technical Documentation](https://docs.alliancecan.ca/wiki/Technical_documentation)
- [Alliance Canada AI and Machine Learning Wiki](https://docs.alliancecan.ca/wiki/AI_and_Machine_Learning)
- [Alliance Canada Python Wiki](https://docs.alliancecan.ca/wiki/Python)
- [Alliance Canada Dataset Guide (Handling Large Collections of Files)](https://docs.alliancecan.ca/wiki/Handling_large_collections_of_files)
- [SciNet Killarney Documentation](https://docs.scinet.utoronto.ca/index.php/Killarney)
- [SciNet Trillium Documentation](https://docs.scinet.utoronto.ca/index.php/Trillium)
- [SciNet Balam Documentation](https://docs.scinet.utoronto.ca/index.php/Balam)
- [Alliance TamIA Documentation](https://docs.alliancecan.ca/wiki/TamIA/en)
- [Alliance Vulcan Documentation](https://docs.alliancecan.ca/wiki/Vulcan)
- [Alliance Nibi Documentation](https://docs.alliancecan.ca/wiki/Nibi)

### Lab Code Repositories
*(Note: Accessing and cloning these private repositories requires your GitHub account to be added to the `chemcognition-lab` organization).*
- [agent_skills](https://github.com/chemcognition-lab/agent_skills) (HPC skills and example scripts)
- [project_template](https://github.com/chemcognition-lab/project_template) (Basic data science project structure to start with)
- [MLP_BayesOpt](https://github.com/chemcognition-lab/MLP_BayesOpt) (Concrete example of Bayesian Optimization runs)
