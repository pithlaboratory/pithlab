#!/usr/bin/env python3
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOLDEN_DIR = ROOT / "eval" / "golden"
RUNNER = ROOT / "scripts" / "run_single_golden_runtime.py"

def main():
    golden_files = sorted(GOLDEN_DIR.glob("*.yaml"))
    if not golden_files:
        print(f"No golden YAMLs found in {GOLDEN_DIR}")
        return

    results = []
    for path in golden_files:
        name = path.stem
        print(f"\n=== Running golden via planner: {name} ===")
        cmd = [
            "python",
            str(RUNNER),
            "--via-planner",
            str(path),
        ]
        proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
        print(proc.stdout)
        print(proc.stderr)

        # грубый парсер статуса из stdout
        status = "unknown"
        quality = None
        for line in proc.stdout.splitlines():
            if line.strip().startswith("Status:"):
                status = line.split("Status:")[1].strip()
            if line.strip().startswith("Quality:"):
                quality = line.split("Quality:")[1].strip()
        results.append((name, status, quality))

    print("\n=== Golden summary ===")
    for name, status, quality in results:
        print(f"{name}: status={status}, quality={quality}")

if __name__ == "__main__":
    main()
