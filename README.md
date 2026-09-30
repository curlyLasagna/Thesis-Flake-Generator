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
