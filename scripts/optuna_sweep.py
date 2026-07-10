#!/usr/bin/env python3
"""Parses Optuna study log and prints validation summary, elapsed time, workers, and ETA.

Example:
    python3 scripts/optuna_sweep.py optuna_study.log 100
"""

import sys
import json
from datetime import datetime

# ANSI Colors for terminal output
COLOR_GREEN = "\033[1;32m"
COLOR_YELLOW = "\033[1;33m"
COLOR_RED = "\033[1;31m"
COLOR_MAGENTA = "\033[1;35m"
COLOR_GRAY = "\033[1;30m"
COLOR_RESET = "\033[0m"


def main():
    if len(sys.argv) < 2:
        print("Usage: optuna_sweep.py <log_path> [target_trials]")
        sys.exit(1)

    log_path = sys.argv[1]
    target_trials = int(sys.argv[2]) if len(sys.argv) > 2 else 0

    trials = {}
    direction = 'maximize'
    next_trial_id = 0

    try:
        with open(log_path, 'r', encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except Exception:
                    continue
                op_code = record.get('op_code')
                if op_code == 0:  # CREATE_STUDY
                    directions = record.get('directions')
                    if directions and len(directions) > 0:
                        if directions[0] == 1 or str(directions[0]).upper() == 'MINIMIZE':
                            direction = 'minimize'
                elif op_code == 4:  # CREATE_TRIAL
                    trial_id = next_trial_id
                    next_trial_id += 1
                    start_time = record.get('datetime_start')
                    trials[trial_id] = {
                        'state': 0, 
                        'value': None, 
                        'start_time': start_time,
                        'end_time': None
                    }
                elif op_code == 6:  # SET_TRIAL_STATE_VALUES
                    trial_id = record.get('trial_id')
                    state = record.get('state')
                    values = record.get('values')
                    end_time = record.get('datetime_complete')
                    if trial_id is not None:
                        if trial_id not in trials:
                            trials[trial_id] = {}
                        if state is not None:
                            trials[trial_id]['state'] = state
                        if values and len(values) > 0:
                            trials[trial_id]['value'] = values[0]
                        trials[trial_id]['end_time'] = end_time

        # Calculate trial durations
        durations = []
        for t in trials.values():
            if t.get('start_time') and t.get('end_time'):
                try:
                    start = datetime.fromisoformat(t['start_time'].replace('Z', ''))
                    end = datetime.fromisoformat(t['end_time'].replace('Z', ''))
                    durations.append((end - start).total_seconds())
                except Exception:
                    pass

        completed_trials = {tid: t for tid, t in trials.items() if t.get('state') == 1 and t.get('value') is not None}
        running = sum(1 for t in trials.values() if t.get('state') == 0)
        completed = len(completed_trials)
        pruned = sum(1 for t in trials.values() if t.get('state') == 2)
        failed = sum(1 for t in trials.values() if t.get('state') == 3)
        total_finished = completed + pruned + failed
        trials_left = max(0, target_trials - total_finished)

        if target_trials > 0:
            pct = (len(trials) / target_trials) * 100
            print(f'  - Total Trials:   {len(trials)} / {target_trials} ({pct:.1f}%)')
        else:
            print(f'  - Total Trials:   {len(trials)}')

        print(f'  - Completed:      {COLOR_GREEN}{completed}{COLOR_RESET}')
        print(f'  - Pruned/Stopped: {COLOR_YELLOW}{pruned}{COLOR_RESET}')
        print(f'  - Failed:         {COLOR_RED}{failed}{COLOR_RESET}')

        if completed > 0:
            if direction == 'minimize':
                best_trial_id = min(completed_trials, key=lambda tid: completed_trials[tid]['value'])
            else:
                best_trial_id = max(completed_trials, key=lambda tid: completed_trials[tid]['value'])
            best_value = completed_trials[best_trial_id]['value']
            print(f'  - Best Val Score: {COLOR_MAGENTA}{best_value:.4f}{COLOR_RESET} (Trial {best_trial_id})')

        # Display elapsed time
        start_times = [datetime.fromisoformat(t['start_time'].replace('Z', '')) for t in trials.values() if t.get('start_time')]
        if start_times:
            sweep_start = min(start_times)
            now = datetime.now()
            elapsed = now - sweep_start
            elapsed_sec = elapsed.total_seconds()
            elapsed_h = int(elapsed_sec // 3600)
            elapsed_m = int((elapsed_sec % 3600) // 60)
            start_str = sweep_start.strftime('%b %d %H:%M')
            now_str = now.strftime('%b %d %H:%M')
            print(f'  - Elapsed Time:   {COLOR_GRAY}{elapsed_h}h {elapsed_m}m{COLOR_RESET} (Start: {start_str} | Current: {now_str})')

        # Display duration stats and ETA
        if durations:
            durations.sort()
            n = len(durations)
            if n % 2 == 1:
                median_dur = durations[n // 2]
            else:
                median_dur = (durations[n // 2 - 1] + durations[n // 2]) / 2.0
            
            m_minutes = int(median_dur // 60)
            m_seconds = int(median_dur % 60)
            print(f'  - Median Duration:{COLOR_GRAY} {m_minutes}m {m_seconds}s{COLOR_RESET}')

            if target_trials > 0:
                if trials_left > 0:
                    workers = running if running > 0 else 8
                    eta_seconds = (trials_left * median_dur) / workers
                    eta_h = int(eta_seconds // 3600)
                    eta_m = int((eta_seconds % 3600) // 60)
                    worker_str = f'{workers} active workers' if running > 0 else 'assuming 8 parallel workers'
                    print(f'  - Est. Time Left: \033[1;36m{eta_h}h {eta_m}m\033[0m ({worker_str})')
                else:
                    print(f'  - Est. Time Left: {COLOR_GREEN}0h 0m (Sweep Finished){COLOR_RESET}')

    except Exception as e:
        print(f'Error reading study: {e}')


if __name__ == "__main__":
    main()
