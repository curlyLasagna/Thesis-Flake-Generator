#!/usr/bin/env python3
"""
Inspects a project folder for manifest files, source code, and documentation
to infer environment requirements for each distinct module/assignment.
Ensures each module/assignment can receive a dedicated flake.nix for 'nix develop'.
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path

IGNORED_DIRS = {
    ".git", ".hg", ".svn", "node_modules", ".venv", "venv", "env",
    "__pycache__", "target", "build", "dist", "result", ".devenv", ".direnv",
    ".ipynb_checkpoints"
}

EXTENSION_MAP = {
    ".py": ("python", "python3"),
    ".ipynb": ("python", "python3"),
    ".java": ("java", "openjdk"),
    ".rs": ("rust", "rustc"),
    ".go": ("go", "go"),
    ".c": ("c", "gcc"),
    ".h": ("c", "gcc"),
    ".cpp": ("cpp", "gcc"),
    ".cc": ("cpp", "gcc"),
    ".hpp": ("cpp", "gcc"),
    ".ts": ("typescript", "nodejs"),
    ".js": ("javascript", "nodejs"),
    ".scala": ("scala", "scala"),
    ".r": ("r", "R"),
    ".sql": ("sql", "mysql84"),
}

MANIFEST_RULES = [
    ("pom.xml", ["maven", "openjdk17"]),
    ("build.gradle", ["gradle", "openjdk17"]),
    ("build.gradle.kts", ["gradle", "openjdk17"]),
    ("requirements.txt", ["python3", "uv"]),
    ("pyproject.toml", ["python3", "uv", "poetry"]),
    ("Pipfile", ["python3", "pipenv"]),
    ("package.json", ["nodejs"]),
    ("pnpm-lock.yaml", ["nodejs", "pnpm"]),
    ("yarn.lock", ["nodejs", "yarn"]),
    ("Cargo.toml", ["rustc", "cargo"]),
    ("go.mod", ["go"]),
    ("CMakeLists.txt", ["cmake", "gcc", "gnumake"]),
    ("Makefile", ["gnumake", "gcc"]),
    ("docker-compose.yml", ["docker-compose"]),
    ("Dockerfile", ["docker"]),
]

DOC_KEYWORDS = {
    r"\bmysql[\s_-]?workbench\b": ["mysql-workbench", "mysql84"],
    r"\bmysql\b": ["mysql84", "mysql-client"],
    r"\bpostgres(ql)?\b": ["postgresql"],
    r"\bmongodb\b": ["mongodb"],
    r"\bsqlite\b": ["sqlite"],
    r"\bredis\b": ["redis"],
    r"\bpytorch\b": ["python3", "uv"],
    r"\btensorflow\b": ["python3", "uv"],
    r"\bopencv\b": ["opencv"],
    r"\bjava\s?17\b": ["openjdk17"],
    r"\bjava\s?21\b": ["openjdk21"],
    r"\bjava\s?8\b": ["openjdk8"],
    r"\bjava\s?11\b": ["openjdk11"],
    r"\bpython\s?3\.13\b": ["python313"],
    r"\bpython\s?3\.12\b": ["python312"],
    r"\bpython\s?3\.11\b": ["python311"],
    r"\bnode(js)?\s?20\b": ["nodejs_20"],
    r"\bnode(js)?\s?22\b": ["nodejs_22"],
    r"\bwireshark\b": ["wireshark"],
    r"\bvalgrind\b": ["valgrind"],
    r"\bgdb\b": ["gdb"],
    r"\bclang\b": ["clang"],
    r"\bgcc\b": ["gcc"],
}

MODULE_DIR_PATTERN = re.compile(
    r"^(assignment[\s_-]?\d+|project[\s_-]?\d+|hw[\s_-]?\d+|homework[\s_-]?\d+|lab[\s_-]?\d+|module[\s_-]?\d+|week[\s_-]?\d+)",
    re.IGNORECASE
)

def analyze_directory(dir_path: Path):
    detected_languages = set()
    manifests = []
    docs = []
    candidates = set()

    for root, dirs, files in os.walk(dir_path):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".")]
        rel_root = Path(root).relative_to(dir_path)

        for filename in files:
            file_path = Path(root) / filename
            rel_file = str(rel_root / filename) if str(rel_root) != "." else filename

            ext = file_path.suffix.lower()
            if ext in EXTENSION_MAP:
                lang, default_pkg = EXTENSION_MAP[ext]
                detected_languages.add(lang)
                candidates.add(default_pkg)

            for manifest_name, suggested_pkgs in MANIFEST_RULES:
                if filename.lower() == manifest_name.lower():
                    manifests.append(rel_file)
                    candidates.update(suggested_pkgs)
                    try:
                        content = file_path.read_text(errors="ignore")
                        if filename == "pom.xml":
                            m = re.search(r"<java\.version>(\d+)</java\.version>", content)
                            if m:
                                candidates.add(f"openjdk{m.group(1)}")
                        elif filename == "pyproject.toml":
                            if "torch" in content.lower():
                                candidates.update(["python3", "uv"])
                    except Exception:
                        pass

            if filename.lower().endswith((".md", ".txt", ".pdf", ".rst")):
                if any(k in filename.lower() for k in ["readme", "instruction", "syllabus", "lab", "setup", "assignment"]):
                    docs.append(rel_file)
                    try:
                        text = file_path.read_text(errors="ignore").lower()
                        for pattern, pkgs in DOC_KEYWORDS.items():
                            if re.search(pattern, text):
                                candidates.update(pkgs)
                    except Exception:
                        pass

    candidates.add("git")
    return {
        "detected_languages": sorted(list(detected_languages)),
        "manifests": manifests,
        "docs": docs,
        "candidate_packages": sorted(list(candidates)),
        "suggested_mcp_queries": [{"query": pkg} for pkg in sorted(candidates)]
    }

def scan_project(project_path: Path):
    if not project_path.exists():
        print(f"ERROR: Directory '{project_path}' does not exist.", file=sys.stderr)
        sys.exit(1)

    # 1. Discover submodules / assignments
    submodules = []
    top_entries = [p for p in project_path.iterdir() if p.is_dir() and p.name not in IGNORED_DIRS and not p.name.startswith(".")]

    for entry in sorted(top_entries, key=lambda x: x.name):
        # A subdirectory is considered a separate module if:
        # 1. Name matches assignment / project / lab / hw pattern, OR
        # 2. Contains its own manifest (e.g., pom.xml, pyproject.toml, package.json, Cargo.toml)
        is_named_module = bool(MODULE_DIR_PATTERN.match(entry.name))
        has_manifest = any((entry / m[0]).exists() for m in MANIFEST_RULES)

        if is_named_module or has_manifest:
            mod_data = analyze_directory(entry)
            if mod_data["detected_languages"] or mod_data["manifests"]:
                submodules.append({
                    "module_name": entry.name,
                    "module_path": str(entry.resolve()),
                    "relative_path": str(entry.relative_to(project_path)),
                    "analysis": mod_data
                })

    # If distinct submodules are found, each should have its own flake.nix
    if submodules:
        result = {
            "mode": "per_module",
            "project_path": str(project_path.resolve()),
            "total_modules": len(submodules),
            "modules": submodules
        }
    else:
        # Single module project
        single_data = analyze_directory(project_path)
        result = {
            "mode": "single_project",
            "project_path": str(project_path.resolve()),
            "total_modules": 1,
            "modules": [
                {
                    "module_name": project_path.name,
                    "module_path": str(project_path.resolve()),
                    "relative_path": ".",
                    "analysis": single_data
                }
            ]
        }

    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Infer per-module requirements for dedicated flake.nix files")
    parser.add_argument("--project-path", default=".", help="Path to project directory (default: current dir)")
    args = parser.parse_args()
    scan_project(Path(args.project_path))
