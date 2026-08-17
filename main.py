import sys
import os
import time
import argparse

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from api import fetch_detectable_apps, search_apps, parse_app_executables
from runner import QuestRunner
from gui import launch_gui

def run_cli():
    print("=" * 60)
    print("      DISCORD ACTIVITY QUEST SOLVER (CLI MODE)")
    print("=" * 60)
    
    print("\n[1/3] Loading Discord detectable games catalog...")
    apps = fetch_detectable_apps()
    print(f"Loaded {len(apps)} detectable applications.\n")

    while True:
        print("\nEnter a game name, executable name (e.g. overwatch), or 'q' to quit:")
        query = input("Search > ").strip()
        
        if not query:
            continue
        if query.lower() in ["q", "quit", "exit"]:
            print("Exiting Discord Quest Solver.")
            sys.exit(0)

        matches = search_apps(apps, query, limit=15)
        if not matches:
            print(f"[!] No games matching '{query}' found in Discord database. Try again.\n")
            continue

        print(f"\nSelect a game from results (1-{len(matches)}):")
        for i, app in enumerate(matches, 1):
            execs = parse_app_executables(app)
            exec_names = [e['name'] for e in execs]
            print(f"  [{i:2d}] {app['name']} (ID: {app['id']}) - Executables: {', '.join(exec_names) or 'None'}")
            
        print("  [ 0] Back to Search")
        
        choice = input("\nChoice > ").strip()
        if not choice.isdigit():
            print("Invalid input.")
            continue
            
        choice_idx = int(choice)
        if choice_idx == 0:
            continue
        if 1 <= choice_idx <= len(matches):
            selected_app = matches[choice_idx - 1]
            execs = parse_app_executables(selected_app)
            selected_exec = execs[0] if execs else {"name": "game.exe"}
            
            if len(execs) > 1:
                print(f"\nMultiple executables found for '{selected_app['name']}':")
                for ex_i, ex in enumerate(execs, 1):
                    print(f"  [{ex_i}] {ex['name']}")
                ex_choice = input(f"Choose executable (1-{len(execs)}, default 1): ").strip()
                if ex_choice.isdigit() and 1 <= int(ex_choice) <= len(execs):
                    selected_exec = execs[int(ex_choice) - 1]

            print(f"\nSelected Game: {selected_app['name']}")
            print(f"Target Executable: {selected_exec['name']}")
            
            dur_str = input("\nEnter run duration in minutes (default 15): ").strip()
            try:
                dur_mins = float(dur_str) if dur_str else 15.0
            except ValueError:
                dur_mins = 15.0
                
            target_secs = int(dur_mins * 60)
            
            print(f"\n[*] Starting Quest Solver for '{selected_app['name']}'...")
            print(f"Duration: {dur_mins:.1f} minutes ({target_secs} seconds)")
            print("Press Ctrl+C at any time to cancel quest manually.\n")
            
            runner = QuestRunner(selected_app, exec_data=selected_exec, target_duration_secs=target_secs)
            
            def cli_tick(elapsed, remaining, status):
                m, s = divmod(remaining, 60)
                pct = (elapsed / target_secs) * 100
                bar = "=" * int(pct // 5) + "-" * (20 - int(pct // 5))
                sys.stdout.write(f"\r[{bar}] {pct:5.1f}% | Time Remaining: {m:02d}:{s:02d} | Ctrl+C to cancel")
                sys.stdout.flush()

            runner.on_tick = cli_tick
            
            try:
                runner.start()
                while runner.is_running:
                    time.sleep(0.5)
                print("\n")
            except KeyboardInterrupt:
                print("\n\n[!] KeyboardInterrupt detected. Cancelling quest...")
                runner.cancel()
                print("Quest cancelled and temporary files cleaned up.\n")
                continue

def main():
    parser = argparse.ArgumentParser(description="Discord Activity Quest Solver")
    parser.add_argument("--cli", action="store_true", help="Run in Command-Line (CLI) interactive mode")
    parser.add_argument("--refresh", action="store_true", help="Force refresh detectable applications cache from Discord API")
    args = parser.parse_args()

    if args.refresh:
        print("Refreshing Discord detectable applications database...")
        fetch_detectable_apps(force_refresh=True)

    if args.cli:
        run_cli()
    else:
        print("Launching Discord Quest Solver GUI...")
        launch_gui()

if __name__ == "__main__":
    main()
