#!/usr/bin/env python3
import glob
import os
import subprocess
import sys


def print_header(title):
    print("=" * 60)
    print(f" {title}")
    print("=" * 60)

def check_file_stubs():
    print_header("Checking File Structure and Non-Empty Implementations")
    required_paths = [
        "src/copa_forecast/config.py",
        "src/copa_forecast/timeutils.py",
        "src/copa_forecast/data/contracts.py",
        "src/copa_forecast/data/ingest.py",
        "src/copa_forecast/data/normalize.py",
        "src/copa_forecast/data/recent_matches.py",
        "src/copa_forecast/data/validate.py",
        "src/copa_forecast/features/recent.py",
        "src/copa_forecast/features/windows.py",
        "src/copa_forecast/features/pillars.py",
        "src/copa_forecast/features/leakage.py",
        "src/copa_forecast/models/baselines.py",
        "src/copa_forecast/models/match_model.py",
        "src/copa_forecast/models/calibration.py",
        "src/copa_forecast/models/evaluation.py",
        "src/copa_forecast/simulation/rules.py",
        "src/copa_forecast/simulation/monte_carlo.py",
        "src/copa_forecast/simulation/standings.py",
        "src/copa_forecast/reporting/explanations.py",
        "src/copa_forecast/reporting/artifacts.py",
    ]
    
    failures = 0
    for path in required_paths:
        full_path = os.path.join(os.getcwd(), path)
        if not os.path.exists(full_path):
            print(f"[-] MISSING: {path}")
            failures += 1
            continue
        
        # Check size / content to avoid empty stubs
        size = os.path.getsize(full_path)
        with open(full_path, encoding="utf-8") as f:
            content = f.read().strip()
            
        is_stub = content in {"pass", ""} or content.splitlines()[:1] == ["pass"]
        if size < 50 or len(content) < 10 or is_stub:
            print(f"[-] STUB OR EMPTY FILE: {path} (size: {size} bytes)")
            failures += 1
        else:
            print(f"[+] VERIFIED: {path} ({len(content.splitlines())} lines)")
            
    return failures == 0

def run_tests():
    print_header("Executing Test Suite")
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        item for item in ["src", env.get("PYTHONPATH", "")] if item
    )
    commands = [
        (["pytest", "-v"], "pytest"),
        ([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], "unittest"),
    ]
    saw_missing_pytest = False
    for command, label in commands:
        if label == "unittest" and not saw_missing_pytest:
            continue
        print(f"[*] Running {label}: {' '.join(command)}")
        try:
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
                env=env,
            )
            print(result.stdout)
            if result.returncode == 0:
                print(f"[+] ALL TESTS PASSED via {label}.")
                return True
            print(f"[-] {label.upper()} FAILED with exit code {result.returncode}")
            return False
        except FileNotFoundError:
            if label != "pytest":
                print(f"[-] {label} is not available.")
                return False
            print("[!] pytest is not installed or not in PATH; falling back to unittest.")
            saw_missing_pytest = True
            continue
    return False

def verify_data_contracts():
    print_header("Verifying Output Schemas and CSV BOMs")
    # Search for generated CSVs in processed data folder
    csv_files = glob.glob("data/processed/**/*.csv", recursive=True)
    if not csv_files:
        print("[!] No CSV artifacts found in data/processed/. Verify if any run was executed.")
        return True
        
    failures = 0
    for csv_file in csv_files:
        try:
            with open(csv_file, "rb") as f:
                header = f.read(3)
                if header == b'\xef\xbb\xbf':
                    print(f"[+] BOM OK: {csv_file}")
                else:
                    print(f"[-] MISSING UTF-8 BOM: {csv_file}")
                    failures += 1
        except Exception as e:
            print(f"[-] Error reading {csv_file}: {e}")
            failures += 1
    return failures == 0

def check_temporal_leakage_compliance():
    print_header("Sanity Checking Temporal Leakage Prevention")
    # Functionally exercise the guard instead of grepping for keywords: a
    # future-dated record MUST raise TemporalLeakageError.
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        item for item in ["src", env.get("PYTHONPATH", "")] if item
    )
    probe = (
        "from datetime import date\n"
        "from copa_forecast.features.leakage import (\n"
        "    assert_no_future_records, TemporalLeakageError,\n"
        ")\n"
        "records = [{'match_date': '2099-01-01'}]\n"
        "try:\n"
        "    assert_no_future_records(records, date_field='match_date',"
        " as_of_date=date(2026, 1, 1))\n"
        "    raise SystemExit(1)\n"
        "except TemporalLeakageError:\n"
        "    raise SystemExit(0)\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", probe], env=env, capture_output=True, text=True
    )
    if result.returncode == 0:
        print("[+] Leakage guard rejects future-dated records.")
        return True
    print("[-] Leakage guard did NOT reject a future-dated record.")
    print(result.stdout)
    print(result.stderr)
    return False

def main():
    print("=" * 60)
    print(" COPA 2026 AI FORECAST IMPLEMENTATION REVIEWER")
    print("=" * 60)
    
    success = True
    
    # 1. Structure check
    if not check_file_stubs():
        success = False
        
    # 2. Pytest execution
    if not run_tests():
        success = False
        
    # 3. CSV headers validation
    if not verify_data_contracts():
        success = False
        
    # 4. Leakage checks
    if not check_temporal_leakage_compliance():
        success = False
        
    print_header("FINAL VERDICT")
    if success:
        print("[SUCCESS] All automated verification checks passed. The implementation is robust!")
        sys.exit(0)
    else:
        print("[FAILURE] Some verification checks failed. Review the logs above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
