#!/usr/bin/env python3
"""Utility to parse Slurm sshare output and display group/user priority summaries relative to the cluster.

Example:
    python3 scripts/slurm_shares.py --group aip-bensl
"""

import argparse
import getpass
import os
import subprocess
import sys

# ANSI Colors for terminal output
COLOR_BOLD = "\033[1m"
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_RED = "\033[91m"
COLOR_RESET = "\033[0m"


def format_usage(raw_seconds: float) -> str:
    """Format raw cpu/tres-seconds into human-readable CPU-hours (no suffix)."""
    hours = raw_seconds / 3600.0
    if hours >= 1_000_000:
        return f"{hours / 1_000_000:.2f}M"
    elif hours >= 1_000:
        return f"{hours / 1_000:.1f}k"
    return f"{hours:.1f}"


def get_ratio_status(ratio: float) -> tuple[str, str]:
    """Get the status name and color code for a given utilization ratio."""
    if ratio > 1.1:
        return "OVER-utilizing", COLOR_RED
    elif ratio < 0.9:
        return "UNDER-utilizing", COLOR_GREEN
    return "NEUTRAL", COLOR_YELLOW


def get_fairshare_color(fairshare: float) -> str:
    """Determine terminal color based on FairShare status."""
    if fairshare >= 0.5:
        return COLOR_GREEN
    elif fairshare >= 0.2:
        return COLOR_YELLOW
    return COLOR_RED


def parse_sshare_data(lines: list[str]) -> dict[str, dict]:
    """Parse raw Slurm bar-delimited sshare lines into structured dictionary."""
    # Expected header: Account|User|RawShares|NormShares|RawUsage|EffectvUsage|FairShare
    groups = {}
    for line in lines:
        line = line.strip()
        if not line or line.startswith("Account|") or line.startswith("root|"):
            continue

        parts = line.split("|")
        if len(parts) < 7:
            continue

        account, user, raw_shares, norm_shares, raw_usage, effectv_usage, fairshare = parts[:7]

        # Convert numerical values
        raw_usage_val = float(raw_usage) if raw_usage else 0.0
        norm_shares_val = float(norm_shares) if norm_shares else 0.0
        effectv_usage_val = float(effectv_usage) if effectv_usage else 0.0
        fairshare_val = float(fairshare) if (fairshare and fairshare.strip()) else None

        if not user:
            # Group row
            groups[account] = {
                "raw_shares": int(raw_shares or 0),
                "norm_shares": norm_shares_val,
                "raw_usage": raw_usage_val,
                "effectv_usage": effectv_usage_val,
                "users": [],
            }
        else:
            # User row
            if account not in groups:
                groups[account] = {
                    "raw_shares": 0,
                    "norm_shares": 0.0,
                    "raw_usage": 0.0,
                    "effectv_usage": 0.0,
                    "users": [],
                }
            groups[account]["users"].append(
                {
                    "username": user,
                    "raw_shares": int(raw_shares or 0),
                    "norm_shares": norm_shares_val,
                    "raw_usage": raw_usage_val,
                    "effectv_usage": effectv_usage_val,
                    "fairshare": fairshare_val,
                }
            )

    return groups


def print_dashboard(groups: dict[str, dict], target_group: str | None, current_user: str):
    """Print clean cluster-wide status and detailed group breakdown."""
    all_groups_metrics = []
    all_users_metrics = []

    # Calculate ratios and prepare cluster-wide metrics
    for g_name, g_data in groups.items():
        # Avoid division by zero
        ratio = 0.0
        if g_data["norm_shares"] > 0:
            ratio = g_data["effectv_usage"] / g_data["norm_shares"]
        elif g_data["effectv_usage"] > 0:
            ratio = float("inf")

        g_data["ratio"] = ratio
        all_groups_metrics.append((g_name, ratio))

        for u in g_data["users"]:
            # User level ratio
            u_ratio = 0.0
            if u["norm_shares"] > 0:
                u_ratio = u["effectv_usage"] / u["norm_shares"]
            elif u["effectv_usage"] > 0:
                u_ratio = float("inf")
            u["ratio"] = u_ratio
            if u["fairshare"] is not None:
                all_users_metrics.append((g_name, u["username"], u["fairshare"], u_ratio))

    # Cluster-wide statistics
    total_groups = len(all_groups_metrics)
    over_groups = sum(1 for _, r in all_groups_metrics if r > 1.1)
    under_groups = sum(1 for _, r in all_groups_metrics if r < 0.9)
    neutral_groups = total_groups - over_groups - under_groups

    # Sort groups by ratio ascending (lower ratio = better standing / under-utilizing)
    sorted_groups = sorted(all_groups_metrics, key=lambda x: x[1])
    group_ranks = {g[0]: idx + 1 for idx, g in enumerate(sorted_groups)}

    # Sort users by FairShare descending (higher FairShare = better priority)
    sorted_users = sorted(all_users_metrics, key=lambda x: x[2], reverse=True)
    user_ranks = {(u[0], u[1]): idx + 1 for idx, u in enumerate(sorted_users)}

    # Auto-detect target group if not provided
    if not target_group:
        for g_name, g_data in groups.items():
            if any(u["username"] == current_user for u in g_data["users"]):
                target_group = g_name
                break

    if not target_group or target_group not in groups:
        # Fallback to showing cluster overview only
        print(f"\n{COLOR_BOLD}=== Slurm Cluster-Wide Utilization Summary ==={COLOR_RESET}")
        print(f"Total Active Groups  : {total_groups}")
        print(f"  - {COLOR_GREEN}Under-utilizing    : {under_groups} ({under_groups/total_groups*100:.1f}%){COLOR_RESET}")
        print(f"  - {COLOR_YELLOW}Neutral            : {neutral_groups} ({neutral_groups/total_groups*100:.1f}%){COLOR_RESET}")
        print(f"  - {COLOR_RED}Over-utilizing     : {over_groups} ({over_groups/total_groups*100:.1f}%){COLOR_RESET}")
        print("\nSpecify a group using -g/--group to view member details.")
        return

    g_data = groups[target_group]
    g_ratio = g_data["ratio"]
    g_status, g_color = get_ratio_status(g_ratio)
    g_rank = group_ranks[target_group]
    g_pct = (1.0 - (g_rank / total_groups)) * 100

    # Cluster-wide section
    print(f"\n{COLOR_BOLD}=== 1. Cluster-Wide Standing ==={COLOR_RESET}")
    print(f"Total Active Groups  : {total_groups}")
    print(f"  - {COLOR_GREEN}Under-utilizing    : {under_groups} ({under_groups/total_groups*100:.1f}%){COLOR_RESET}")
    print(f"  - {COLOR_YELLOW}Neutral            : {neutral_groups} ({neutral_groups/total_groups*100:.1f}%){COLOR_RESET}")
    print(f"  - {COLOR_RED}Over-utilizing     : {over_groups} ({over_groups/total_groups*100:.1f}%){COLOR_RESET}")
    print(f"Group Standing ({target_group}): Ranked {COLOR_BOLD}#{g_rank}{COLOR_RESET} of {total_groups} in priority (Better than {g_pct:.1f}% of groups)")
    print(f"Group Status         : {g_color}{g_status}{COLOR_RESET} (Utilization Ratio: {g_ratio:.2f})")

    # Group detail section
    print(f"\n{COLOR_BOLD}=== 2. Group Breakdown ({target_group}) ==={COLOR_RESET}")
    print(f"Group Total Usage    : {format_usage(g_data['raw_usage'])} CPU-h")
    print(f"Group Allocation     : {g_data['norm_shares'] * 100:.3f}% of cluster")
    print(f"Group Effective Usage: {g_data['effectv_usage'] * 100:.3f}% of cluster")
    
    num_users = len(all_users_metrics)
    total_width = 82 + len(f"Cluster Rank (of {num_users})")
    print("-" * total_width)

    header = f"{'User':<20} | {'Usage (CPU-h)':<13} | {'Usage %':<9} | {'FairShare':<10} | {'Status':<15} | Cluster Rank (of {num_users})"
    print(header)
    print("-" * total_width)

    # Sort users in the group by raw usage descending
    sorted_group_users = sorted(g_data["users"], key=lambda x: x["raw_usage"], reverse=True)

    for u in sorted_group_users:
        username = u["username"]
        is_me = username == current_user
        if is_me:
            user_display = f"{COLOR_BOLD}{username + ' (you)':<20}{COLOR_RESET}"
        else:
            user_display = f"{username:<20}"

        fs_val = u["fairshare"]
        if fs_val is not None:
            fs_raw = f"{fs_val:.5f}"
            fs_color = get_fairshare_color(fs_val)
            fs_str = f"{fs_color}{fs_raw:<10}{COLOR_RESET}"
        else:
            fs_str = f"{'N/A':<10}"

        u_ratio = u["ratio"]
        u_status, u_color = get_ratio_status(u_ratio)
        u_status_str = f"{u_color}{u_status:<15}{COLOR_RESET}"

        # Get user's cluster-wide rank if available
        rank_key = (target_group, username)
        if rank_key in user_ranks:
            u_rank_str = f"#{user_ranks[rank_key]}"
        else:
            u_rank_str = "N/A"

        eff_pct = u["effectv_usage"] * 100
        pct_str = f"{eff_pct:.2f}%"

        print(
            f"{user_display} | "
            f"{format_usage(u['raw_usage']):<13} | "
            f"{pct_str:<9} | "
            f"{fs_str} | "
            f"{u_status_str} | "
            f"{u_rank_str}"
        )
    print("-" * total_width)


def main():
    parser = argparse.ArgumentParser(description="Cleanly display Slurm sshare info.")
    parser.add_argument("-g", "--group", help="Filter by Slurm account/group.")
    parser.add_argument("-f", "--file", help="Parse a saved sshare output file instead of running command.")
    args = parser.parse_args()

    current_user = getpass.getuser()

    if args.file:
        with open(args.file, encoding="utf-8") as f:
            lines = f.readlines()
    else:
        # Run sshare on the cluster directly with parsable bar-delimited output
        try:
            res = subprocess.run(
                ["sshare", "-P", "-a"],
                capture_output=True,
                text=True,
                check=True
            )
            lines = res.stdout.splitlines()
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            print(f"{COLOR_RED}Error running 'sshare' command: {e}{COLOR_RESET}")
            print("If you are testing locally, please provide a file with '-f'.")
            sys.exit(1)

    groups = parse_sshare_data(lines)
    print_dashboard(groups, args.group, current_user)


if __name__ == "__main__":
    main()
