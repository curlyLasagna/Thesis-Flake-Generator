[![SkillPlus Security Report](https://www.skillplus.xyz/api/report/efceca9f-5abf-4bed-8d18-f8e1ef29a7d0/badge.svg)](https://www.skillplus.xyz/report/efceca9f-5abf-4bed-8d18-f8e1ef29a7d0)

Vibed out skill for my thesis 😅

Prompt used to generate this skill:

> create a directory with a local skills.md file in
>     @.agents/skills with a name of course-flake-generator
>     and a description along the lines of "Generates a nix
>     flake file based on an instructor's requirements or
>     with a provided project folder with source code and
>     other artifacts". This skill shall provide an agent the capability to generate a flake.nix file. To ensure options and package names are deterministic, connect to mcp-nixos mcp server via {
>     "mcpServers": {
>       "nixos": {
>         "command": "uvx",
>         "args": ["mcp-nixos"]
>       }
>     }
>   }
> 
>   If provided with natural language instructions, create a directory with a flake.nix file that matches the requirements. If a project is provided, generate a flake.nix file with the requirements infered from any
>   readable artifacts such as the source code, a readme, or instructions

## Installation Guide

### Prerequisites

Ensure the following tools are installed on your host system:
1. **[Nix Package Manager](https://nixos.org/download/)** with experimental features enabled:
   ```bash
   # In ~/.config/nix/nix.conf (or /etc/nix/nix.conf)
   experimental-features = nix-command flakes
   ```
2. **[Astral uv](https://docs.astral.sh/uv/)** (Python 3.10+ package and script runner):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
3. **Git** (`git --version`)

---

### Instructions for Humans

#### Option A: Workspace Installation (Project-Specific — Recommended)

To install this skill specifically for a project repository so any team member or agent working in this repo can discover it:

1. Navigate to your repository root:
   ```bash
   cd /path/to/your/project
   ```
2. Create the `.agents/skills` directory if it does not already exist:
   ```bash
   mkdir -p .agents/skills
   ```
3. Add the skill as a Git submodule (or clone it directly):
   ```bash
   # Using git submodule (recommended for version control tracking):
   git submodule add https://github.com/curlyLasagna/Thesis-Flake-Generator.git .agents/skills/course-flake-generator

   # Or via direct clone:
   git clone https://github.com/curlyLasagna/Thesis-Flake-Generator.git .agents/skills/course-flake-generator
   ```
4. *(Optional but Recommended)* Enable deterministic Nix package search via the `mcp-nixos` MCP server. Add or update `.agents/mcp_config.json`:
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
   *(If `mcp-nixos` is omitted, the skill automatically falls back to native `nix search` CLI queries).*

#### Option B: Global Installation (Machine-Wide)

To make this skill available across all workspaces on your machine:

1. Clone the repository into your global agent configuration directory:
   ```bash
   mkdir -p ~/.gemini/config/skills
   git clone https://github.com/curlyLasagna/Thesis-Flake-Generator.git ~/.gemini/config/skills/course-flake-generator
   ```
2. For harnesses that read from `~/.agents/skills`:
   ```bash
   mkdir -p ~/.agents/skills
   git clone https://github.com/curlyLasagna/Thesis-Flake-Generator.git ~/.agents/skills/course-flake-generator
   ```

---

### Instructions for AI Agents

If you are an agent tasked with installing or integrating this skill into an existing repository or harness:

1. **Locate or Create the Customization Root**:
   * Inspect the repository root for `.agents/` or `.gemini/`.
   * Create the target directory:
     ```bash
     mkdir -p .agents/skills
     ```
2. **Install the Skill Directory**:
   * Install the repository into `.agents/skills/course-flake-generator`:
     ```bash
     git submodule add https://github.com/curlyLasagna/Thesis-Flake-Generator.git .agents/skills/course-flake-generator || git clone https://github.com/curlyLasagna/Thesis-Flake-Generator.git .agents/skills/course-flake-generator
     ```
3. **Configure the MCP Server (`mcp-nixos`)**:
   * Check for `.agents/mcp_config.json`.
   * If the file exists, parse it and ensure the `nixos` server entry is present under `mcpServers`. If the file does not exist, create it:
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
4. **Verify Prerequisites**:
   * Verify that `nix` is in `$PATH` and supports flakes:
     ```bash
     nix --extra-experimental-features 'nix-command flakes' --version
     ```
   * Verify that `uv` is available for running the helper scripts:
     ```bash
     uv --version
     ```
5. **Verify Skill Registration**:
   * Confirm that `.agents/skills/course-flake-generator/SKILL.md` exists and contains valid YAML frontmatter (`name: course-flake-generator` and `description`).
   * The harness will automatically register the skill via progressive disclosure and invoke it when prompts mention generating or configuring Nix flakes for course environments.

---

## Helper Scripts

This skill includes standalone Python scripts located in the [`scripts/`](file:///Users/luis/Code/Thesis_Implementation/.agents/skills/course-flake-generator/scripts) directory. Each script uses [PEP 723 inline script metadata](https://peps.python.org/pep-0723/) and can be executed directly using [`uv run`](https://docs.astral.sh/uv/):

### 1. [`scripts/detect-project-requirements.py`](file:///Users/luis/Code/Thesis_Implementation/.agents/skills/course-flake-generator/scripts/detect-project-requirements.py)

Inspects an existing project directory to infer dependencies, build tools, and structure for brownfield assignments.

* **Purpose**:
  * Detects project structure: determines whether the workspace is a single project (`single_project`) or contains multiple modular assignments/labs/homeworks (`per_module`).
  * Scans for build manifests (e.g., `pom.xml`, `package.json`, `Cargo.toml`, `pyproject.toml`, `Makefile`, `CMakeLists.txt`, `go.mod`).
  * Inspects source file extensions to identify languages and runtimes.
  * Extracts localized documentation paths (`README.md`, instructions, setup guides).
  * Emits JSON containing candidate tools and suggested queries for package resolution.
* **Usage**:
  ```bash
  uv run scripts/detect-project-requirements.py --project-path <PROJECT_DIR>
  ```
* **Key Flags**:
  * `--project-path <PATH>`: Path to the project directory to analyze (defaults to current directory `.`).
  * `--doc-path <PATH>`: Convenience flag to delegate directly to `extract-document-content.py` for instructional documents.

---

### 2. [`scripts/extract-document-content.py`](file:///Users/luis/Code/Thesis_Implementation/.agents/skills/course-flake-generator/scripts/extract-document-content.py)

Extracts clean markdown and instructional setup context from syllabus, assignment, and lab documentation files.

* **Purpose**:
  * Parses PDF, Microsoft Word (`.docx`), and text-based formats (`.md`, `.txt`, `.rst`).
  * Uses [Docling](https://github.com/DS4SD/docling) configured for fast, text-focused extraction (disabling unnecessary image generation and classification).
  * Filters out relevant instructional context sections (e.g., prerequisites, requirements, setup, getting started, dependencies) to help infer tool and runtime needs.
* **Usage**:
  ```bash
  uv run scripts/extract-document-content.py <PATH_TO_DOCUMENT>
  ```
* **Key Flags**:
  * `<doc_path>` or `--doc-path <PATH>`: Path to document file (PDF, DOCX, Markdown, or text).
  * `--raw`: Outputs only the extracted markdown string instead of structured JSON.
  * `--ocr`: Enables optical character recognition (OCR) for scanned PDFs (disabled by default for speed).
  * `-o, --output <PATH>`: Writes output JSON or markdown directly to a file.

---

### 3. [`scripts/validate-flake.py`](file:///Users/luis/Code/Thesis_Implementation/.agents/skills/course-flake-generator/scripts/validate-flake.py)

Validates generated `flake.nix` files to guarantee working, reproducible devShells before deployment.

* **Purpose**:
  * Automatically stages `flake.nix` via `git add -N` if inside a Git repository (ensuring Nix flake evaluation recognizes the file).
  * Runs `nix flake check` to verify flake syntax, schema, and inputs.
  * Runs `nix develop --command <command>` (with `NIXPKGS_ALLOW_UNFREE=1`) to verify devShell activation and package resolution.
  * Guards against hanging background processes or infinite loops in `shellHook` with a process group timeout kill.
* **Usage**:
  ```bash
  uv run scripts/validate-flake.py --flake-dir <MODULE_OR_PROJECT_DIR>
  ```
* **Key Flags**:
  * `--flake-dir <DIR>`: Directory containing `flake.nix` (defaults to current directory `.`).
  * `--command <CMD>`: Shell command to test inside the devShell (defaults to `true`).
  * `--no-allow-unfree`: Prevents setting `NIXPKGS_ALLOW_UNFREE=1`.
  * `--timeout <SECONDS>`: Timeout in seconds for validation commands (defaults to `30`).

