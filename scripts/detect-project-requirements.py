#!/usr/bin/env python3
"""
Inspects a project folder for manifest files, source code, and documentation
to infer environment requirements for each distinct module/assignment.
Ensures each module/assignment can receive a dedicated flake.nix for 'nix develop'.
Outputs high-level conceptual tools and search keywords without hardcoding Nix package names.
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
    ".py": ("python", "python"),
    ".ipynb": ("python", "python"),
    ".java": ("java", "java"),
    ".rs": ("rust", "rust"),
    ".go": ("go", "go"),
    ".c": ("c", "c compiler"),
    ".h": ("c", "c compiler"),
    ".cpp": ("cpp", "c++ compiler"),
    ".cc": ("cpp", "c++ compiler"),
    ".hpp": ("cpp", "c++ compiler"),
    ".ts": ("typescript", "nodejs"),
    ".js": ("javascript", "nodejs"),
    ".scala": ("scala", "scala"),
    ".r": ("r", "r"),
    ".sql": ("sql", "sql"),
}

MANIFEST_RULES = [
    ("pom.xml", ["maven", "java"]),
    ("build.gradle", ["gradle", "java"]),
    ("build.gradle.kts", ["gradle", "java"]),
    ("requirements.txt", ["python"]),
    ("pyproject.toml", ["python"]),
    ("Pipfile", ["python", "pipenv"]),
    ("package.json", ["nodejs"]),
    ("pnpm-lock.yaml", ["nodejs", "pnpm"]),
    ("yarn.lock", ["nodejs", "yarn"]),
    ("Cargo.toml", ["rust", "cargo"]),
    ("go.mod", ["go"]),
    ("CMakeLists.txt", ["cmake", "c/c++ compiler", "make"]),
    ("Makefile", ["make", "c/c++ compiler"]),
    ("docker-compose.yml", ["docker-compose"]),
    ("Dockerfile", ["docker"]),
]

DOC_KEYWORDS = {
    r"\bmysql[\s_-]?workbench\b": ["mysql workbench", "mysql"],
    r"\bmysql\b": ["mysql"],
    r"\bpostgres(ql)?\b": ["postgresql"],
    r"\bmongodb\b": ["mongodb"],
    r"\bsqlite\b": ["sqlite"],
    r"\bredis\b": ["redis"],
    r"\bpytorch\b": ["pytorch", "python"],
    r"\btensorflow\b": ["tensorflow", "python"],
    r"\bopencv\b": ["opencv"],
    r"\bjava\s?17\b": ["java 17"],
    r"\bjava\s?21\b": ["java 21"],
    r"\bjava\s?8\b": ["java 8"],
    r"\bjava\s?11\b": ["java 11"],
    r"\bpython\s?3\.13\b": ["python 3.13"],
    r"\bpython\s?3\.12\b": ["python 3.12"],
    r"\bpython\s?3\.11\b": ["python 3.11"],
    r"\bnode(js)?\s?20\b": ["nodejs 20"],
    r"\bnode(js)?\s?22\b": ["nodejs 22"],
    r"\bwireshark\b": ["wireshark"],
    r"\btcpdump\b": ["tcpdump"],
    r"\bvalgrind\b": ["valgrind"],
    r"\bgdb\b": ["gdb"],
    r"\bclang\b": ["clang"],
    r"\bgcc\b": ["gcc"],
    r"\bnasm\b": ["nasm"],
}

MODULE_DIR_PATTERN = re.compile(
    r"^(assignment[\s_-]?\d+|project[\s_-]?\d+|hw[\s_-]?\d+|homework[\s_-]?\d+|lab[\s_-]?\d+|module[\s_-]?\d+|week[\s_-]?\d+)",
    re.IGNORECASE
)

def analyze_directory(dir_path: Path):
    detected_languages = set()
    manifests = []
    docs = []
    detected_tools = set()

    for root, dirs, files in os.walk(dir_path):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".")]
        rel_root = Path(root).relative_to(dir_path)

        for filename in files:
            file_path = Path(root) / filename
            rel_file = str(rel_root / filename) if str(rel_root) != "." else filename

            ext = file_path.suffix.lower()
            if ext in EXTENSION_MAP:
                lang, default_tool = EXTENSION_MAP[ext]
                detected_languages.add(lang)
                detected_tools.add(default_tool)

            for manifest_name, suggested_tools in MANIFEST_RULES:
                if filename.lower() == manifest_name.lower():
                    manifests.append(rel_file)
                    detected_tools.update(suggested_tools)
                    try:
                        content = file_path.read_text(errors="ignore")
                        if filename == "pom.xml":
                            m = re.search(r"<java\.version>(\d+)</java\.version>", content)
                            if m:
                                detected_tools.add(f"java {m.group(1)}")
                        elif filename == "pyproject.toml":
                            if "poetry" in content.lower():
                                detected_tools.add("poetry")
                            if "uv" in content.lower():
                                detected_tools.add("uv")
                            if "torch" in content.lower():
                                detected_tools.add("pytorch")
                    except Exception:
                        pass

            if filename.lower().endswith((".md", ".txt", ".pdf", ".rst")):
                if any(k in filename.lower() for k in ["readme", "instruction", "syllabus", "lab", "setup", "assignment"]):
                    docs.append(rel_file)
                    try:
                        text = file_path.read_text(errors="ignore").lower()
                        for pattern, tools in DOC_KEYWORDS.items():
                            if re.search(pattern, text):
                                detected_tools.update(tools)
                    except Exception:
                        pass

    detected_tools.add("git")
    tools_list = sorted(list(detected_tools))
    return {
        "detected_languages": sorted(list(detected_languages)),
        "manifests": manifests,
        "docs": docs,
        "detected_tools": tools_list,
        "suggested_queries": [{"query": tool} for tool in tools_list]
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
