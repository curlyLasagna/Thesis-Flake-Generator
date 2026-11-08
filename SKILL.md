---
name: course-flake-generator
description: Generates a nix flake file based on an instructor's requirements or with a provided project folder with source code and other artifacts. Use when creating, generating, or configuring a Nix flake (flake.nix) for course assignments, lab environments, or software projects from specifications, natural language instructions, or existing codebases. Don't use for non-Nix environments, simple shell scripts, or general documentation generation.
---

# Course Flake Generator

Generate deterministic `flake.nix` files providing reproducible development environments triggered via `nix develop` for academic courses, laboratory assignments, and software projects. 

When a course or repository contains multiple modules or assignments, this skill generates an independent `flake.nix` inside **each** module/assignment directory, allowing them to enter any assignment folder and simply run `nix develop`.

## Workflow Procedures

### Step 1: Analyze Input and Requirements
Determine whether the task is a greenfield creation from natural language instructions, a brownfield migration from an existing project directory, or an instruction document (PDF/DOCX/Markdown):

* **Case A: Greenfield Assignments (Natural Language Instructions)**
  Use this case when an instructor is creating a totally new assignment or course module for the first time from scratch and already knows the languages, compilers, runtimes, and dependencies they plan to use:
  1. Determine the target project directory:
     * By default, generate all files directly inside the **current working directory (`.`)**.
     * If the prompt or instructor explicitly specifies a subfolder or path name, create that directory relative to the current working directory (`mkdir -p <project-dir>`).
     * Never create projects in the global agent scratch directory (e.g. `~/.gemini/antigravity-cli/scratch`) unless explicitly requested.
  2. Initialize or confirm a Git repository inside the target project directory if not already present:
     ```bash
     git init
     ```
  3. If multiple course modules or assignments are described within the prompt:
     * Create distinct subdirectories for each module/assignment (e.g., `./assignment-1/`, `./assignment-2/`).
     * Extract the planned languages, compilers, runtimes, and libraries for each module.
  4. Prepare the candidate tool list per module for deterministic verification via `mcp-nixos` in Step 3.
  5. The `flake.nix` file will be generated directly inside that target directory (or within each module subdirectory if multiple assignments are specified).

* **Case B: Brownfield Projects & Flake Migrations (Project Folder Provided)**
  Use this case for existing codebases or when instructors are migrating existing assignments/repositories to use `flake.nix` development environments:
  1. Scan the project folder to detect distinct submodules, assignment folders, build manifests, and localized instruction documents:
     ```bash
     uv run scripts/detect-project-requirements.py --project-path <PROJECT_DIR>
     ```
  2. Inspect the output:
     * If `mode: "per_module"`, process each detected module in `modules` independently (e.g., `Assignment 1`, `Project2`, `hw1`). Each module directory will receive its own `flake.nix` inferred from its localized artifacts.
     * If `mode: "single_project"`, process the single project root directory.
  3. If localized documentation (`README.md`, lab guides, instructions) was discovered in `docs`, read the file contents to infer any additional tools, libraries, or external dependencies not captured in build manifests.
  4. For complex artifact heuristics (e.g., inferring versions from `pom.xml`, `pyproject.toml`, or syllabus documents), read `references/inferring-requirements.md`.

* **Case C: Syllabus, Assignment Guides, or Instruction Documents (PDF, DOCX, or Text Files Provided)**
  Use this case when an instructor or student provides an instructional document file (e.g., `lab1.pdf`, `assignment-guide.docx`, `setup.txt`, `README.md`, or course syllabus):
  1. Parse the document using the extraction script executed via Astral `uv`:
     ```bash
     uv run scripts/extract-document-content.py <PATH_TO_DOCUMENT>
     ```
     The script uses `Docling` with PEP 723 inline script metadata (`# /// script ... # ///`) configured specifically to optimize for pure text extraction by disabling image generation and picture classification (`generate_page_images=False`, `generate_picture_images=False`, `do_picture_classification=False`, `image_placeholder=""`, with optional OCR via `--ocr`). It natively parses Word documents (`.docx`), PDFs, and text files under the open-source MIT license, extracting clean structured markdown text without commercial licensing restrictions.
  2. The script provides the agent with:
     * `instructional_context`: Sections describing prerequisites, tools, environment variables, and execution steps.
     * `extracted_content`: Full markdown text extracted from the document.
  3. Carefully analyze `instructional_context` and `extracted_content` to infer required programming languages, compilers, runtimes, databases, services, or developer utilities without relying on pre-mapped keyword dictionaries.
  4. Proceed to Step 2 & 3 to resolve the candidate tools deterministically and Step 4 to generate the tailored `flake.nix`.

### Step 2: Determine Package Resolution Strategy (MCP or Nix CLI)
To ensure package names and development dependencies are deterministic across all environments, check the available package discovery tools:

1. **Check for `mcp-nixos` MCP Server:** Check if `.agents/mcp_config.json` is present and the `mcp-nixos` tools (`nix` and `nix_versions`) are available.
   * If available, query package attributes deterministically via `mcp-nixos` in Step 3. For query shapes and search parameters, read `references/mcp-nixos.md`.
2. **Nix CLI Mode / Fallback:** If `mcp-nixos` is not configured or unavailable (e.g., running with `--no-mcp`), do NOT hallucinate package names or halt. Instead, use the native Nix CLI via `run_command` to discover and verify package attributes:
   * Search packages: `nix search --extra-experimental-features 'nix-command flakes' nixpkgs <candidate_tool>` (or `nix-env -qaP <candidate_tool>`).

### Step 3: Query and Resolve Packages Deterministically
For each module/assignment identified:

1. **Query Packages:**
   * **If `mcp-nixos` is available:** Call the `nix` tool (`action: "search"`, `type: "packages"`):
     ```json
     {
       "action": "search",
       "query": "<candidate_tool>",
       "type": "packages",
       "channel": "stable",
       "limit": 10
     }
     ```
     If specific version compatibility is required, inspect details using the `nix` tool (`action: "info"`, `type: "package"`) or the `nix_versions` tool.
   * **If `mcp-nixos` is unavailable (Nix CLI mode):** Run `nix search --extra-experimental-features 'nix-command flakes' github:NixOS/nixpkgs/nixos-24.11 <candidate_tool>` via `run_command` to inspect matching attributes and descriptions.
2. Verify exact attribute paths (e.g., `mysql84` instead of `mysql80`, `openjdk17` instead of `jdk17`).
3. If packages require unfree licenses (e.g., CUDA, proprietary database tools, MySQL Workbench), note that `allowUnfree = true` must be enabled in that module's devShell.

### Step 4: Synthesize a `flake.nix` for Each Module / Assignment
For **each** project or module/assignment directory:

1. Read `assets/flake-devshell.template.nix` and `references/flake-patterns.md`.
2. Write a self-contained `flake.nix` located directly inside that target directory (the new greenfield project directory created in Case A, or each assignment directory):
   * Populate `description` with the module/assignment name.
   * Include standard inputs: `nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11"` and `flake-utils.url = "github:numtide/flake-utils"`.
   * Under `flake-utils.lib.eachDefaultSystem`, import `pkgs` with `config.allowUnfree = true;`.
   * Define `devShells.default = pkgs.mkShell { ... }` populated strictly with that module's packages.
   * Set relevant environment variables (e.g., `JAVA_HOME = "${pkgs.openjdk17}";` for Java modules).
   * Configure `shellHook` with a clear message: `"Entering environment for <Module Name>"`.
   * **Daemon / Service Safety:** For database or daemon environments (e.g., MySQL, Postgres), NEVER place unbounded polling loops (`while ! ping; do sleep; done` or `until [ -S ... ]; do sleep; done`) inside `shellHook`. `shellHook` executes non-interactively on every `nix develop --command` invocation; unbounded loops permanently freeze automated tools and tests. Instead, print startup commands or non-blocking setup.
3. In Git repositories (such as the newly initialized project from Case A), stage `flake.nix` so the Nix flake evaluator recognizes the file:
   ```bash
   git -C <target_dir> add flake.nix
   ```
4. **Architecture Rule:** Do NOT combine multiple assignments into a single monolithic flake with named shells (e.g., `devShells.module1`, `devShells.module2`). Generating an individual `flake.nix` per module guarantees that `cd <module_dir> && nix develop` works immediately without parameters.

### Step 5: Validate Flake Environments
Test the generated `flake.nix` in every module/assignment directory before concluding:

1. Run the validation script for each module directory via Astral `uv`:
   ```bash
   uv run scripts/validate-flake.py --flake-dir <MODULE_DIR>
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

* **Missing MCP Server Connection:** If `mcp-nixos` is not configured, fails to start, or `--no-mcp` is active, use the native Nix CLI (`nix search nixpkgs <query>` or `nix-env -qaP <query>`) to search and verify package attributes deterministically.
* **Package Attribute Not Found:** If a search query returns no results via MCP or Nix CLI, try querying with broader generic keywords or alternative tool names.
* **Unfree Package Evaluation Error:** If `nix develop` fails with "Package has an unfree license", verify that `config.allowUnfree = true;` is present in `flake.nix` and `NIXPKGS_ALLOW_UNFREE=1` is exported.
* **Module Disambiguation:** If an assignment folder contains no manifests or obvious source files, inspect parent documentation (`README.md`, syllabus) or prompt text to determine the intended tooling.
