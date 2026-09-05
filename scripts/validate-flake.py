#!/usr/bin/env python3
"""
Validates a flake.nix file in a specified directory by executing:
1. nix flake check
2. nix develop --command <command> (with NIXPKGS_ALLOW_UNFREE=1 support)
"""

import os
import sys
import shutil
import argparse
import subprocess
from pathlib import Path

def validate_flake(flake_dir: Path, allow_unfree: bool = True, test_command: str = "true"):
    if not shutil.which("nix"):
        print("ERROR: 'nix' executable not found in PATH.", file=sys.stderr)
        sys.exit(1)

    flake_file = flake_dir / "flake.nix"
    if not flake_file.exists():
        print(f"ERROR: No flake.nix found in directory '{flake_dir}'.", file=sys.stderr)
        sys.exit(1)

    env = os.environ.copy()
    if allow_unfree:
        env["NIXPKGS_ALLOW_UNFREE"] = "1"

    print(f"--> Validating flake at: {flake_file}")

    # Step 1: nix flake check
    print("--> Running: nix flake check --extra-experimental-features 'nix-command flakes'")
    check_proc = subprocess.run(
        ["nix", "flake", "check", "--extra-experimental-features", "nix-command flakes"],
        cwd=flake_dir,
        env=env,
        capture_output=True,
        text=True
    )

    if check_proc.returncode != 0:
        print("FLAKE CHECK FAILED:", file=sys.stderr)
        print(check_proc.stderr, file=sys.stderr)
        sys.exit(1)
    else:
        print("PASS: nix flake check succeeded.")

    # Step 2: nix develop check
    print(f"--> Running: nix develop --extra-experimental-features 'nix-command flakes' --command {test_command}")
    dev_proc = subprocess.run(
        ["nix", "develop", "--extra-experimental-features", "nix-command flakes", "--command", "sh", "-c", test_command],
        cwd=flake_dir,
        env=env,
        capture_output=True,
        text=True
    )

    if dev_proc.returncode != 0:
        print("NIX DEVELOP ACTIVATION FAILED:", file=sys.stderr)
        print(dev_proc.stderr, file=sys.stderr)
        sys.exit(1)
    else:
        print("PASS: nix develop devShell successfully built and verified.")
        print("SUCCESS: flake.nix is valid and working.")

def main():
    parser = argparse.ArgumentParser(description="Validate a flake.nix file")
    parser.add_argument("--flake-dir", default=".", help="Directory containing flake.nix (default: .)")
    parser.add_argument("--no-allow-unfree", action="store_true", help="Do not set NIXPKGS_ALLOW_UNFREE=1")
    parser.add_argument("--command", default="true", help="Command to test inside devShell (default: true)")

    args = parser.parse_args()
    validate_flake(
        flake_dir=Path(args.flake_dir).resolve(),
        allow_unfree=not args.no_allow_unfree,
        test_command=args.command
    )

if __name__ == "__main__":
    main()
