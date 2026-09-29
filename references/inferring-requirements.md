# Inferring Environment Requirements from Project Artifacts

When dealing with brownfield projects or migrating existing course assignments to use Nix flakes (Case B), infer dependencies, runtimes, and build requirements systematically from repository artifacts without assuming hardcoded package names.

## 1. Automated Detection Script

Execute the scanning script to gather structured metadata across the project:

```bash
python3 scripts/detect-project-requirements.py --project-path /path/to/project
```

The script outputs JSON describing:
* **Mode**: whether the project is `single_project` or `per_module` (with multiple assignment/lab directories).
* **Detected Languages**: programming languages present based on source extensions.
* **Manifests**: build configuration files found in each module.
* **Documentation**: relevant READMEs, syllabi, or lab instructions.
* **Detected Tools & Keywords**: conceptual tools, frameworks, and search keywords extracted from files and documentation.

## 2. Manifest Inspection Heuristics

Inspect manifest files in each module to determine the required tools and version constraints:

### Java
* `pom.xml`:
  * Inspect `<java.version>`, `<maven.compiler.source>`, `<maven.compiler.target>`, or `<release>` in compiler plugin configurations.
  * Required tools: Java Development Kit (JDK) matching the target version, and Maven.
* `build.gradle` / `build.gradle.kts`:
  * Inspect `sourceCompatibility`, `targetCompatibility`, or `jvmToolchain(...)`.
  * Required tools: Java Development Kit (JDK) matching the target version, and Gradle.

### Python
* `pyproject.toml`:
  * Inspect `requires-python` or `[tool.poetry.dependencies] python`.
  * Check the build backend or package manager indicated (e.g., uv, poetry, flit, setuptools).
  * Note libraries that may require system-level dependencies or specific runtime versions (e.g., PyTorch, scientific libraries).
* `requirements.txt`:
  * Note Python version hints in comments or package constraints.
* `Pipfile`:
  * Check `[requires]` section for the specified Python version.
  * Required tools: Python runtime and Pipenv.

### JavaScript / TypeScript & Web
* `package.json`:
  * Inspect the `engines.node` field for required Node.js runtime version.
  * Check for lockfiles to identify the package manager:
    * `pnpm-lock.yaml` -> pnpm
    * `yarn.lock` -> Yarn
    * `package-lock.json` -> npm
* Required tools: Node.js runtime (matching any engine constraint) and the corresponding package manager.

### Rust
* `Cargo.toml`:
  * Inspect `rust-version` or `edition`.
  * Required tools: Rust compiler, Cargo, and development utilities (e.g., formatter, linter).

### Go
* `go.mod`:
  * Inspect the `go <version>` declaration.
  * Required tools: Go toolchain and language server.

### C / C++
* `CMakeLists.txt`:
  * Inspect `cmake_minimum_required(VERSION ...)` and language standard declarations (e.g., `CMAKE_CXX_STANDARD`).
  * Required tools: CMake, C/C++ compiler toolchain, and build system (e.g., Make or Ninja).
* `Makefile`:
  * Inspect compiler flags and tool invocations.
  * Required tools: Make utility and C/C++ compiler.

## 3. Course Documentation & Syllabus Analysis

Inspect documentation files (`README.md`, `INSTRUCTIONS.md`, syllabi, lab guides, assignment prompts) for mentions of external services, specialized tools, or lab environments:
* **Databases & Data Stores**: Look for mentions of relational databases (e.g., MySQL, PostgreSQL, SQLite) or key-value stores, along with GUI/CLI clients (e.g., database workbenches or shells).
* **Systems, Security & Low-Level Labs**: Look for mentions of debugging tools (e.g., GDB, Valgrind), assemblers, disassemblers, system call tracers, or compilation flags.
* **Networking Labs**: Look for mentions of packet analysis utilities, network sniffers, or socket programming utilities.
* **Data Science / Machine Learning**: Look for mentions of interactive notebook environments, GPU acceleration, or specialized computation libraries.

## 4. Resolving Inferred Tools to Nix Packages

Once conceptual tools and version requirements are identified:
1. Manifest specifications take precedence over general narrative text.
2. If versions are unspecified in manifests or documentation, target current stable or LTS releases.
3. Discover the exact Nixpkgs package attribute names corresponding to the required tools (e.g., query via `mcp-nixos` or search Nixpkgs).
4. Verify that each resolved package attribute exists and evaluates cleanly before finalizing `flake.nix`.
