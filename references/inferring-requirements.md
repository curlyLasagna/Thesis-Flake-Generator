# Inferring Environment Requirements from Project Artifacts

When dealing with brownfield projects or migrating existing course assignments to use Nix flakes (Case B), infer dependencies and build requirements systematically from repository artifacts.

## 1. Automated Detection Script

Execute the scanning script to gather structured metadata:

```bash
python3 scripts/detect-project-requirements.py --project-path /path/to/project
```

The script outputs JSON listing detected languages, manifests, matched documentation keywords, candidate Nix packages, and suggested queries.

## 2. Artifact Mapping Rules

### Language Manifests
* **Java**:
  * `pom.xml` -> Check `<java.version>` or `<maven.compiler.source>`. Packages: `openjdk<ver>`, `maven`.
  * `build.gradle` / `build.gradle.kts` -> Packages: `openjdk<ver>`, `gradle`.
* **Python**:
  * `pyproject.toml` -> Check `[tool.poetry]`, `[project.dependencies]`, or `flit`. Packages: `python3` (or `python313`), `uv`, `poetry`.
  * `requirements.txt` -> Packages: `python3`, `uv`.
  * `Pipfile` -> Packages: `python3`, `pipenv`.
* **Node.js / Web**:
  * `package.json` -> Check `engines.node`. Packages: `nodejs` (or specific LTS e.g. `nodejs_22`), `corepack`.
  * `pnpm-lock.yaml` -> Package: `pnpm`.
  * `yarn.lock` -> Package: `yarn`.
* **Rust**:
  * `Cargo.toml` -> Packages: `rustc`, `cargo`, `rustfmt`, `clippy`.
* **Go**:
  * `go.mod` -> Package: `go`, `gopls`.
* **C / C++**:
  * `CMakeLists.txt` -> Packages: `cmake`, `gcc` (or `clang`), `gnumake`.
  * `Makefile` -> Packages: `gnumake`, `gcc` (or `clang`).

### Documentation & Course Materials
Inspect files matching `README.md`, `INSTRUCTIONS.md`, `syllabus*.md`, `lab*.pdf`, `assignment*.txt`:
* Mentions of **MySQL / Workbench** -> `mysql84`, `mysql-workbench`, `mysql-shell`.
* Mentions of **PostgreSQL** -> `postgresql`.
* Mentions of **PyTorch / GPU / Machine Learning** -> `python3`, `uv`, optional GPU/CUDA packages.
* Mentions of **Network Analysis** -> `wireshark`, `tcpdump`, `libpcap`.
* Mentions of **System / Security Labs (SEED Labs)** -> `gcc`, `gdb`, `nasm`, `valgrind`, `strace`.

## 3. Ambiguity Resolution
If multiple versions are hinted or conflicting requirements arise:
1. Manifest files take precedence over narrative text.
2. If unspecified, select the active LTS or stable version (e.g. OpenJDK 17 or 21, Python 3.12 or 3.13, Node 22).
3. Validate each chosen package name against `mcp-nixos`.
