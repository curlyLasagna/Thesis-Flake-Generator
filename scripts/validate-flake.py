#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
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

import signal

def run_cmd_with_timeout(cmd, cwd, env, timeout=30):
    proc = subprocess.Popen(
        cmd,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True
    )
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
        return proc.returncode, stdout, stderr
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except OSError:
            pass
        proc.communicate()
        return -1, "", f"Command timed out after {timeout} seconds (check shellHook for hanging background processes or infinite loops)."

def validate_flake(flake_dir: Path, allow_unfree: bool = True, test_command: str = "true", timeout: int = 30):
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

    # Ensure flake.nix is staged if inside a git repository (Nix flakes require tracked files)
    if (flake_dir / ".git").exists() or subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=flake_dir, capture_output=True).returncode == 0:
        subprocess.run(["git", "add", "-N", "flake.nix"], cwd=flake_dir, capture_output=True)

    # Step 1: nix flake check
    print("--> Running: nix flake check --extra-experimental-features 'nix-command flakes'")
    code, stdout, stderr = run_cmd_with_timeout(
        ["nix", "flake", "check", "--extra-experimental-features", "nix-command flakes"],
        cwd=flake_dir,
        env=env,
        timeout=timeout
    )

    if code != 0:
        print("FLAKE CHECK FAILED:", file=sys.stderr)
        print(stderr, file=sys.stderr)
        sys.exit(1)
    else:
        print("PASS: nix flake check succeeded.")

    # Step 2: nix develop check
    print(f"--> Running: nix develop --extra-experimental-features 'nix-command flakes' --command {test_command}")
    code, stdout, stderr = run_cmd_with_timeout(
        ["nix", "develop", "--extra-experimental-features", "nix-command flakes", "--command", "sh", "-c", test_command],
        cwd=flake_dir,
        env=env,
        timeout=timeout
    )

    if code != 0:
        print("NIX DEVELOP ACTIVATION FAILED:", file=sys.stderr)
        print(stderr, file=sys.stderr)
        sys.exit(1)
    else:
        print("PASS: nix develop devShell successfully built and verified.")
        print("SUCCESS: flake.nix is valid and working.")

def main():
    parser = argparse.ArgumentParser(description="Validate a flake.nix file")
    parser.add_argument("--flake-dir", default=".", help="Directory containing flake.nix (default: .)")
    parser.add_argument("--no-allow-unfree", action="store_true", help="Do not set NIXPKGS_ALLOW_UNFREE=1")
    parser.add_argument("--command", default="true", help="Command to test inside devShell (default: true)")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout in seconds for validation commands (default: 30)")

    args = parser.parse_args()
    validate_flake(
        flake_dir=Path(args.flake_dir).resolve(),
        allow_unfree=not args.no_allow_unfree,
        test_command=args.command,
        timeout=args.timeout
    )

if __name__ == "__main__":
    main()
