# Sistec Plugin Marketplace

Marketplace di plugin per [Claude Code](https://code.claude.com/docs) del team Sistec.

## Struttura del repository

```
sistec-plugin-marketplace/
├── .claude-plugin/
│   └── marketplace.json          # Catalogo del marketplace (lista dei plugin)
├── plugins/
│   └── hello-sistec/             # Un plugin
│       ├── .claude-plugin/
│       │   └── plugin.json       # Manifest del plugin
│       ├── skills/
│       │   └── hello/
│       │       └── SKILL.md      # Skill (invocabile come /hello-sistec:hello)
│       ├── agents/
│       │   └── code-reviewer.md  # Agent custom
│       ├── hooks/
│       │   └── hooks.json        # Hook su eventi (PostToolUse, ...)
│       └── README.md
├── LICENSE
└── README.md
```

> **Nota:** dentro `.claude-plugin/` va **solo** il file manifest (`marketplace.json`
> o `plugin.json`). Le cartelle `skills/`, `agents/`, `hooks/`, `commands/` stanno
> sempre alla radice del plugin, **non** dentro `.claude-plugin/`.

## Uso (per gli utenti)

```shell
# Aggiungi il marketplace (in locale per testare, o da GitHub)
/plugin marketplace add ./sistec-plugin-marketplace
/plugin marketplace add sistec/sistec-plugin-marketplace   # da GitHub

# Installa un plugin
/plugin install hello-sistec@sistec-plugins

# Prova la skill (namespaced con il nome del plugin)
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
