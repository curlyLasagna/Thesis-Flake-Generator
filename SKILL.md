---
name: course-flake-generator
description: Generates a nix flake file based on an instructor's requirements or with a provided project folder with source code and other artifacts. Use when creating, generating, or configuring a Nix flake (flake.nix) for course assignments, lab environments, or software projects from specifications, natural language instructions, or existing codebases. Don't use for non-Nix environments, simple shell scripts, or general documentation generation.
---

# Course Flake Generator

Generate deterministic `flake.nix` files providing reproducible development environments triggered via `nix develop` for academic courses, laboratory assignments, and software projects. 

When a course or repository contains multiple modules or assignments, this skill generates an independent `flake.nix` inside **each** module/assignment directory, allowing them to enter any assignment folder and simply run `nix develop`.

## Workflow Procedures

### Step 1: Analyze Input and Requirements
Determine whether the task is a greenfield creation from natural language instructions or a brownfield migration from an existing project directory:

* **Case A: Greenfield Assignments (Natural Language Instructions)**
  Use this case when an instructor is creating an assignment or course module for the first time from scratch and already knows the languages, compilers, runtimes, and dependencies they plan to use:
  1. Identify whether the prompt specifies a single assignment or multiple course modules/assignments (e.g., "Assignment 1: Java graph search; Assignment 2: PyTorch neural networks").
  2. If multiple modules/assignments are described:
     * Decompose the course into distinct directories (e.g., `./assignment-1/`, `./assignment-2/`, or `./lab-1/`, `./lab-2/`).
     * Extract the planned languages, compilers, runtimes, and libraries for each module.
  3. If a single assignment is described, determine or create its target directory (e.g., `./course-env` or `<assignment-name>/`).
  4. Prepare the candidate tool list per module for deterministic verification in Step 3.

* **Case B: Brownfield Projects & Flake Migrations (Project Folder Provided)**
  Use this case for existing codebases or when instructors are migrating existing assignments/repositories to use `flake.nix` development environments:
  1. Scan the project folder to detect distinct submodules, assignment folders, and build manifests:
     ```bash
     python3 scripts/detect-project-requirements.py --project-path <PROJECT_DIR>
     ```
  2. Inspect the output:
     * If `mode: "per_module"`, process each detected module in `modules` independently (e.g., `Assignment 1`, `Project2`, `hw1`). Each module directory will receive its own `flake.nix` inferred from its localized artifacts.
     * If `mode: "single_project"`, process the single project root directory.
  3. For complex artifact heuristics (e.g., inferring versions from `pom.xml`, `pyproject.toml`, or syllabus documents), read `references/inferring-requirements.md`.

### Step 2: Ensure `mcp-nixos` MCP Server Connection
To ensure package names and development dependencies are deterministic across all environments, connect to the `mcp-nixos` MCP server:

1. Verify `.agents/mcp_config.json` contains the `nixos` server definition:
   ```json
   {
     "mcpServers": {
       "nixos": {
         "command": "uvx",
         "args": ["mcp-nixos"]
       }
     }
   }
   ```
2. Confirm the `mcp-nixos` tools (`nix` and `nix_versions`) are available. If `mcp-nixos` is not reachable, do not hallucinate package names; notify the user to ensure `uvx` and `mcp-nixos` are configured, or use the local fallback query script `scripts/query-nixos.py`.
3. For query shapes and search parameters, read `references/mcp-nixos.md`.

### Step 3: Query and Resolve Packages Deterministically
For each module/assignment identified:

1. Query `mcp-nixos` using the `nix` tool or run `scripts/query-nixos.py`:
   ```bash
   python3 scripts/query-nixos.py --search "<package_name>"
   ```
2. Verify exact attribute paths (e.g., `mysql84` instead of `mysql80`, `openjdk17` instead of `jdk17`).
3. If specific version compatibility is required, inspect details using `nix` tool (`action: "info"`, `type: "package"`) or:
   ```bash
   python3 scripts/query-nixos.py --info "<exact_attribute>"
   ```
4. If packages require unfree licenses (e.g., CUDA, proprietary database tools, MySQL Workbench), note that `allowUnfree = true` must be enabled in that module's devShell.

### Step 4: Synthesize a `flake.nix` for Each Module / Assignment
For **each** module or assignment directory:

1. Read `assets/flake-devshell.template.nix` and `references/flake-patterns.md`.
2. Write a self-contained `flake.nix` located directly inside that module's directory:
   * Populate `description` with the module/assignment name.
   * Include standard inputs: `nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable"` and `flake-utils.url = "github:numtide/flake-utils"`.
   * Under `flake-utils.lib.eachDefaultSystem`, import `pkgs` with `config.allowUnfree = true;`.
   * Define `devShells.default = pkgs.mkShell { ... }` populated strictly with that module's packages.
   * Set relevant environment variables (e.g., `JAVA_HOME = "${pkgs.openjdk17}";` for Java modules).
   * Configure `shellHook` with a clear message: `"Entering environment for <Module Name>"`.
3. **Architecture Rule:** Do NOT combine multiple assignments into a single monolithic flake with named shells (e.g., `devShells.module1`, `devShells.module2`). Generating an individual `flake.nix` per module guarantees that `cd <module_dir> && nix develop` works immediately without parameters.

### Step 5: Validate Flake Environments
Test the generated `flake.nix` in every module/assignment directory before concluding:

1. Run the validation script for each module directory:
   ```bash
   python3 scripts/validate-flake.py --flake-dir <MODULE_DIR>
   ```
2. Ensure both validation checks pass:
   * `nix flake check`
   * `NIXPKGS_ALLOW_UNFREE=1 nix develop --command true`
3. Provide instructions showing students how to enter each module folder and launch its environment:
   ```bash
   cd <module_dir>
   nix develop
   ```

## Error Handling

* **Missing MCP Server Connection:** If `uvx` fails or `mcp-nixos` cannot start, verify Astral `uv` is installed (`which uvx`). Ensure `.agents/mcp_config.json` matches `assets/mcp-servers.template.json`.
* **Package Attribute Not Found:** If a search query returns no results, check `references/inferring-requirements.md` for alternative aliases or use `python3 scripts/query-nixos.py --search "<broader_term>"`.
* **Unfree Package Evaluation Error:** If `nix develop` fails with "Package has an unfree license", verify that `config.allowUnfree = true;` is present in `flake.nix` and `NIXPKGS_ALLOW_UNFREE=1` is exported.
* **Module Disambiguation:** If an assignment folder contains no manifests or obvious source files, inspect parent documentation (`README.md`, syllabus) or prompt text to determine the intended tooling.
