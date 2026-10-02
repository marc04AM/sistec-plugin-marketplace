# hello-sistec

Example plugin for the Sistec marketplace. Shows how to package a skill, an
agent and a hook together.

## Components

| Component | File | What it does |
| :-------- | :--- | :----------- |
| Skill | `skills/hello/SKILL.md` | `/hello-sistec:hello <name>` greets the user |
| Agent | `agents/code-reviewer.md` | `code-reviewer` agent for code reviews |
| Hook | `hooks/hooks.json` | Logs every file modified with Write/Edit |

## Quick test

```bash
claude --plugin-dir ./plugins/hello-sistec
```

Then, in the session:

```shell
/hello-sistec:hello Marco
```
