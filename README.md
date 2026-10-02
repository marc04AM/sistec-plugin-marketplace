# Sistec Plugin Marketplace

[Claude Code](https://code.claude.com/docs) plugin marketplace of the Sistec team.

Repository: <https://github.com/marc04AM/sistec-plugin-marketplace>

## Available plugins

| Plugin | What it does |
| :----- | :----------- |
| `hello-sistec` | Example plugin: skill, agent and hook to get started quickly |
| `technical-writer` | Generates Italian HMI operator manuals from control narratives (Markdown + HTML) |
| `hmi-developer` | Development assistant for the Sistec.HMI solution (.NET 8 / WinForms): Clean Architecture, TDD cycle, C# rules and project hooks |
| `git-release` | Multi-repo release: `/git-release:gitize` (diff → Conventional-Commits), `/git-release:git-split-commits` / `/git-release:git-amend-commits` (staged → commits), `/git-release:versionize` (release notes from built DLLs + git) and `/git-release:package-release` (zip packaging + repeat) |
| `log-forensics` | Read-only forensics of PLC/HMI logs/captures: `/log-forensics:analyze-crash` (timeline + root cause) and `/log-forensics:track-timing` (Fael/HMI timing and event-chain consistency) |
| `device-spy` | Secret-driven read-only inspectors: `/device-spy:codesys-spy` (encrypted CODESYS → source + analysis) `/device-spy:ubiquity-spy` (Ubiquiti router config snapshot), `/device-spy:network-probe` (local network diagnosis) and `/device-spy:alarm-troubleshooting` (PLC alarms → Troubleshooting workbook) |
| `blender-ply` | CAD PLY models in Blender via the MCP bridge: `/blender-ply:view-ply`, `/blender-ply:center-blender`, `/blender-ply:center-ply`, `/blender-ply:snapshot-ply`, `/blender-ply:ply-colors` |

## Repository layout

```
sistec-plugin-marketplace/
├── .claude-plugin/
│   └── marketplace.json          # Marketplace catalog (list of plugins)
├── plugins/
│   ├── hello-sistec/             # Example plugin
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json       # Plugin manifest
│   │   ├── skills/
│   │   │   └── hello/
│   │   │       └── SKILL.md      # Skill (invocable as /hello-sistec:hello)
│   │   ├── agents/
│   │   │   └── code-reviewer.md  # Custom agent
│   │   ├── hooks/
│   │   │   └── hooks.json        # Event hooks (PostToolUse, ...)
│   │   └── README.md
│   ├── technical-writer/         # Generates HMI operator manuals from control narratives
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   ├── skills/
│   │   │   └── technical-writer/
│   │   │       └── SKILL.md
│   │   ├── assets/               # Example manual, style.css, outline/image templates
│   │   └── README.md
│   ├── hmi-developer/            # Sistec.HMI solution development (.NET/WinForms): rules, TDD, hooks
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   ├── skills/                # tdd, csharp-doc-comments, archive, dpi-anchor-fix, translate, reconcile-solutions
│   │   ├── hooks/                # hooks.json + Python scripts (build/graphify/archive)
│   │   ├── assets/dpiRepair/     # PowerShell scanner/fixer for dpi-anchor-fix
│   │   └── README.md
│   ├── git-release/              # Multi-repo release (shared repo-set cache)
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   ├── skills/                # gitize, git-split-commits, git-amend-commits, versionize, package-release
│   │   └── README.md
│   ├── log-forensics/            # Read-only forensics of PLC/HMI logs/captures
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   ├── skills/                # analyze-crash, track-timing
│   │   └── README.md
│   ├── device-spy/               # Secret-driven read-only inspectors (bundled helpers)
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   ├── skills/                # codesys-spy, ubiquity-spy, network-probe, alarm-troubleshooting (+ scripts/)
│   │   ├── assets/               # codesySpy/resources/*, ubiquitySpy/resources/* (env-driven)
│   │   └── README.md
│   └── blender-ply/              # CAD PLY models in Blender via the MCP bridge
│       ├── .claude-plugin/
│       │   └── plugin.json
│       ├── skills/                # view-ply, center-blender, center-ply, snapshot-ply, ply-colors (+ scripts/*.py)
│       ├── lib/                  # view_projection.py: viewport math shared by the scripts
│       ├── hooks/                # hooks.json + ply-colors-nudge.py (detects grey PLY models)
│       ├── rules/                # blender-ply-colors.md (optional, copy it into ~/.claude/rules)
│       └── README.md
├── LICENSE
└── README.md
```

> **Note:** `.claude-plugin/` holds **only** the manifest file (`marketplace.json`
> or `plugin.json`). The `skills/`, `agents/`, `hooks/`, `commands/` folders always
> live at the plugin root, **not** inside `.claude-plugin/`.

## Usage (for users)

```shell
# Add the marketplace
/plugin marketplace add marc04AM/sistec-plugin-marketplace

# Install a plugin
/plugin install hello-sistec@sistec-plugins
/plugin install technical-writer@sistec-plugins
/plugin install hmi-developer@sistec-plugins
/plugin install git-release@sistec-plugins
/plugin install log-forensics@sistec-plugins
/plugin install device-spy@sistec-plugins
/plugin install blender-ply@sistec-plugins

# Try a skill (namespaced with the plugin name)
/hello-sistec:hello Marco
```

## Development and validation

```bash
# Validate the marketplace.json syntax
claude plugin validate .

# Validate a single plugin (manifest + skills/agents/hooks)
claude plugin validate ./plugins/hello-sistec

# Load a plugin without installing it, to test it
claude --plugin-dir ./plugins/hello-sistec
```

### Adding a new plugin

1. Create a folder under `plugins/<plugin-name>/`.
2. Add the manifest `plugins/<plugin-name>/.claude-plugin/plugin.json`.
3. Add the components (`skills/`, `agents/`, `hooks/`, `.mcp.json`, ...).
4. Register the plugin in the `plugins` array of `.claude-plugin/marketplace.json`.

After changes, `/reload-plugins` reloads everything without restarting.

## References

- [Create plugins](https://code.claude.com/docs/en/plugins)
- [Create and distribute a plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces)
- [Plugins reference](https://code.claude.com/docs/en/plugins-reference)
