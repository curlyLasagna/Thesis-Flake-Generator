# Flake Patterns and Best Practices for Course Environments

This reference defines canonical Nix flake patterns for course development environments triggered via `nix develop`.

## 1. Per-Module / Per-Assignment Flake Architecture

Each module, project, or assignment directory must have its own dedicated `flake.nix` that exports `devShells.default`.

### Directory Layout

```text
course-repo/
├── assignment-1-java/
│   ├── src/
│   ├── pom.xml
│   └── flake.nix        # devShells.default: openjdk17, maven, git
├── assignment-2-python/
│   ├── pyproject.toml
│   └── flake.nix        # devShells.default: python313, uv, git
└── assignment-3-database/
    ├── schema.sql
    └── flake.nix        # devShells.default: mysql84, mysql-shell, git
```

### Student Usage Pattern

Students simply change directory into the assignment and run `nix develop`:

```bash
cd assignment-1-java
nix develop
```

This immediately drops them into the tailored shell

---

## 2. Standard DevShell Flake Pattern

Every per-module `flake.nix` uses `flake-utils.lib.eachDefaultSystem` to support `x86_64-linux`, `aarch64-linux`, `x86_64-darwin`, and `aarch64-darwin` seamlessly.

```nix
{
  description = "Assignment 1: Java Graph Analysis";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      nixpkgs,
      flake-utils,
      ...
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs {
          inherit system;
          config.allowUnfree = true;
        };
      in
      {
        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            git
            openjdk17
            maven
          ];

          JAVA_HOME = "${pkgs.openjdk17}";

          shellHook = ''
            echo "Environment for Assignment 1 activated."
            echo "Java version: $(java -version 2>&1 | head -n 1)"
          '';
        };

        formatter = pkgs.nixfmt-rfc-style;
      }
    );
}
```

---

## 3. Environment Variables & Runtime Hooks

Certain software requires environment variables to locate libraries or runtimes:

* **Java**:
  ```nix
  JAVA_HOME = "${pkgs.openjdk17}";
  ```
* **Python with native C/C++ dependencies (e.g. PyTorch, OpenCV)**:
  ```nix
  LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [ pkgs.stdenv.cc.cc.lib pkgs.zlib ];
  ```
* **C / C++ with pkg-config**:
  ```nix
  PKG_CONFIG_PATH = "${pkgs.openssl.dev}/lib/pkgconfig";
  ```
