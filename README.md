# Sistec Plugin Marketplace

Marketplace di plugin per [Claude Code](https://code.claude.com/docs) del team Sistec.

Repository: <https://github.com/marc04AM/sistec-plugin-marketplace>

## Plugin disponibili

| Plugin | Cosa fa |
| :----- | :------ |
| `hello-sistec` | Plugin di esempio: skill, agent e hook per partire velocemente |

## Struttura del repository

```text
sistec-plugin-marketplace/
├── .claude-plugin/
│   └── marketplace.json          # Catalogo del marketplace (lista dei plugin)
├── plugins/
│   ├── hello-sistec/             # Plugin di esempio
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json       # Manifest del plugin
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

# Prova una skill (namespaced con il nome del plugin)
/hello-sistec:hello Marco
```

## Riferimenti

- [Create plugins](https://code.claude.com/docs/en/plugins)
- [Create and distribute a plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces)
- [Plugins reference](https://code.claude.com/docs/en/plugins-reference)
