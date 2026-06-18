#!/usr/bin/env python3
import os
import sys
import time
import subprocess

WATCH_DIRS = ["src", "tests", "specs", "configs"]
WATCH_EXTENSIONS = (".py", ".yaml", ".json", ".md")
CHECK_INTERVAL_SECONDS = 1.0

def get_watched_files():
    """Recursively lists all files in WATCH_DIRS matching WATCH_EXTENSIONS."""
    files = {}
    for watch_dir in WATCH_DIRS:
        full_dir = os.path.join(os.getcwd(), watch_dir)
        if not os.path.exists(full_dir):
            continue
        for root, _, filenames in os.walk(full_dir):
            for filename in filenames:
                if filename.endswith(WATCH_EXTENSIONS):
                    filepath = os.path.join(root, filename)
                    try:
                        files[filepath] = os.path.getmtime(filepath)
                    except OSError:
                        # File might have been deleted mid-scan
                        pass
    return files

def trigger_verification():
    """Clears the terminal and runs verify_implementation.py."""
    # Clear terminal screen (works on macOS/Linux and Windows)
    os.system("clear" if os.name != "nt" else "cls")
    print("=" * 60)
    print(" CHANGE DETECTED - RUNNING VERIFICATION")
    print("=" * 60)
    
    verify_script = os.path.join(os.getcwd(), "scripts", "verify_implementation.py")
    try:
        # Run verify_implementation.py using the active python interpreter
        result = subprocess.run(
            [sys.executable, verify_script],
            check=False
        )
    except Exception as e:
        print(f"Error running verification script: {e}")

def main():
    print(f"Starting developer daemon watcher...")
    print(f"Monitoring directories: {', '.join(WATCH_DIRS)}")
    print(f"Watching extensions: {', '.join(WATCH_EXTENSIONS)}")
    print("Press Ctrl+C to stop.")
    print("-" * 60)
    
    # Initial scan
    last_state = get_watched_files()
    print(f"Initial scan complete. Watching {len(last_state)} files...")
    
    try:
        while True:
            time.sleep(CHECK_INTERVAL_SECONDS)
            current_state = get_watched_files()
            
            # Detect changes (additions, deletions, modifications)
            changed = False
            
            # Check for modified or deleted files
            for filepath, mtime in last_state.items():
                if filepath not in current_state:
                    print(f"\n[Change Detected] File deleted: {os.path.basename(filepath)}")
                    changed = True
                    break
                elif current_state[filepath] != mtime:
                    print(f"\n[Change Detected] File modified: {os.path.basename(filepath)}")
                    changed = True
                    break
            
            # Check for new files
            if not changed:
                for filepath in current_state:
                    if filepath not in last_state:
                        print(f"\n[Change Detected] File created: {os.path.basename(filepath)}")
                        changed = True
                        break
            
            if changed:
                trigger_verification()
                last_state = current_state
                print("\nWatching for changes...")
                
    except KeyboardInterrupt:
        print("\nWatcher daemon stopped by user. Goodbye!")
        sys.exit(0)

if __name__ == "__main__":
    main()
