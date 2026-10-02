# Sistec Plugin Marketplace

Marketplace di plugin per [Claude Code](https://code.claude.com/docs) del team Sistec.

Repository: <https://github.com/marc04AM/sistec-plugin-marketplace>

## Plugin disponibili

| Plugin | Cosa fa |
| :----- | :------ |
| `hello-sistec` | Plugin di esempio: skill, agent e hook per partire velocemente |
| `technical-writer` | Genera manuali operatore HMI in italiano dalle control narrative (Markdown + HTML) |
| `hmi-developer` | Assistente di sviluppo per la solution Sistec.HMI (.NET 8 / WinForms): Clean Architecture, ciclo TDD, regole C# e hook di progetto |
| `git-release` | Rilascio multi-repo: `/git-release:gitize` (diff → Conventional-Commits), `/git-release:git-split-commits` / `/git-release:git-amend-commits` (staged → commit), `/git-release:versionize` (release note dai DLL buildati + git) e `/git-release:package-release` (packaging zip + repeat) |
| `log-forensics` | Forensics read-only di log/capture PLC/HMI: `/log-forensics:analyze-crash` (timeline + root-cause) e `/log-forensics:track-timing` (consistenza timing ed event-chain Fael/HMI) |
| `device-spy` | Ispettori read-only secret-driven: `/device-spy:codesys-spy` (CODESYS cifrato → sorgente + analisi) e `/device-spy:ubiquity-spy` (snapshot config router Ubiquiti) |
| `blender-ply` | Modelli PLY da CAD in Blender via bridge MCP: `/blender-ply:visualizzaply`, `/blender-ply:centrablender`, `/blender-ply:centraply`, `/blender-ply:fotografaply`, `/blender-ply:ply-colors` |

## Struttura del repository

```
sistec-plugin-marketplace/
├── .claude-plugin/
│   └── marketplace.json          # Catalogo del marketplace (lista dei plugin)
├── plugins/
│   ├── hello-sistec/             # Plugin di esempio
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json       # Manifest del plugin
│   │   ├── skills/
│   │   │   └── hello/
│   │   │       └── SKILL.md      # Skill (invocabile come /hello-sistec:hello)
│   │   ├── agents/
│   │   │   └── code-reviewer.md  # Agent custom
│   │   ├── hooks/
│   │   │   └── hooks.json        # Hook su eventi (PostToolUse, ...)
│   │   └── README.md
│   ├── technical-writer/         # Genera manuali operatore HMI dalle control narrative
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   ├── skills/
│   │   │   └── technical-writer/
│   │   │       └── SKILL.md
│   │   ├── assets/               # Manuale di esempio, style.css, template indice/immagini
│   │   └── README.md
│   ├── hmi-developer/            # Sviluppo solution Sistec.HMI (.NET/WinForms): regole, TDD, hook
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   ├── skills/                # tdd, csharp-doc-comments, archive, dpi-anchor-fix, translate, reconcile-solutions
│   │   ├── hooks/                # hooks.json + script Python (build/graphify/archive)
│   │   ├── assets/dpiRepair/     # Scanner/fixer PowerShell per dpi-anchor-fix
│   │   └── README.md
│   ├── git-release/              # Rilascio multi-repo (cache repo-set condivisa)
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   ├── skills/                # gitize, git-split-commits, git-amend-commits, versionize, package-release
│   │   └── README.md
│   ├── log-forensics/            # Forensics read-only di log/capture PLC/HMI
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   ├── skills/                # analyze-crash, track-timing
│   │   └── README.md
│   ├── device-spy/               # Ispettori read-only secret-driven (helper bundlati)
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   ├── skills/                # codesys-spy, ubiquity-spy
│   │   ├── assets/               # codesySpy/resources/*, ubiquitySpy/resources/* (env-driven)
│   │   └── README.md
│   └── blender-ply/              # PLY da CAD in Blender via bridge MCP
│       ├── .claude-plugin/
│       │   └── plugin.json
│       ├── skills/                # visualizzaply, centrablender, centraply, fotografaply, ply-colors (+ scripts/*.py)
│       ├── lib/                  # view_projection.py: matematica del viewport condivisa dagli script
│       ├── hooks/                # hooks.json + ply-colors-nudge.py (rileva modelli PLY grigi)
│       ├── rules/                # blender-ply-colors.md (opzionale, da copiare in ~/.claude/rules)
│       └── README.md
├── LICENSE
└── README.md
```

> **Nota:** dentro `.claude-plugin/` va **solo** il file manifest (`marketplace.json`
> o `plugin.json`). Le cartelle `skills/`, `agents/`, `hooks/`, `commands/` stanno
> sempre alla radice del plugin, **non** dentro `.claude-plugin/`.

## Uso (per gli utenti)

```shell
# Aggiungi il marketplace
/plugin marketplace add marc04AM/sistec-plugin-marketplace

# Installa un plugin
/plugin install hello-sistec@sistec-plugins
/plugin install technical-writer@sistec-plugins
/plugin install hmi-developer@sistec-plugins
/plugin install git-release@sistec-plugins
/plugin install log-forensics@sistec-plugins
/plugin install device-spy@sistec-plugins
/plugin install blender-ply@sistec-plugins

# Prova una skill (namespaced con il nome del plugin)
/hello-sistec:hello Marco
```

## Sviluppo e validazione

```bash
# Valida la sintassi del marketplace.json
claude plugin validate .

# Valida un singolo plugin (manifest + skill/agent/hook)
claude plugin validate ./plugins/hello-sistec

# Carica un plugin senza installarlo, per testarlo
claude --plugin-dir ./plugins/hello-sistec
```

### Aggiungere un nuovo plugin

1. Crea una cartella sotto `plugins/<nome-plugin>/`.
2. Aggiungi il manifest `plugins/<nome-plugin>/.claude-plugin/plugin.json`.
3. Aggiungi i componenti (`skills/`, `agents/`, `hooks/`, `.mcp.json`, ...).
4. Registra il plugin nell'array `plugins` di `.claude-plugin/marketplace.json`.

Dopo modifiche, `/reload-plugins` ricarica tutto senza riavviare.

## Riferimenti

- [Create plugins](https://code.claude.com/docs/en/plugins)
- [Create and distribute a plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces)
- [Plugins reference](https://code.claude.com/docs/en/plugins-reference)
