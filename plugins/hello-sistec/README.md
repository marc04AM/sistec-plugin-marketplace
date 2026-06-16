# hello-sistec

Plugin di esempio del marketplace Sistec. Mostra come impacchettare insieme una
skill, un agent e un hook.

## Componenti

| Componente | File | Cosa fa |
| :--------- | :--- | :------ |
| Skill | `skills/hello/SKILL.md` | `/hello-sistec:hello <nome>` saluta l'utente |
| Agent | `agents/code-reviewer.md` | Agent `code-reviewer` per review del codice |
| Hook | `hooks/hooks.json` | Logga ogni file modificato con Write/Edit |

## Test rapido

```bash
claude --plugin-dir ./plugins/hello-sistec
```

Poi in sessione:

```shell
/hello-sistec:hello Marco
```
