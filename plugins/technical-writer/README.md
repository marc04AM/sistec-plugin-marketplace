# technical-writer

Plugin del marketplace Sistec per il **manuale operatore di un'HMI** in italiano, su due
fronti: **generare** un manuale nuovo (Markdown → HTML) dalle control narrative, e **manutenere**
un manuale Word (`.docx`) già esistente (revisioni, copy-edit, audit vs codice, struttura, commenti).

## Componenti

| Componente | File | Cosa fa |
| :--------- | :--- | :------ |
| Skill | `skills/technical-writer/SKILL.md` | **Genera** il manuale (MD/HTML) dalle control narrative; invocabile come `/technical-writer:technical-writer` o automaticamente quando si chiede di creare un manuale HMI |
| Skill | `skills/maintain-manual/SKILL.md` | **Manutiene** un manuale Word (`.docx`) esistente via python-docx: porta revisioni (inclusi commenti/tracked-changes nascosti), copy-edit, audit di copertura vs codice, fix struttura, commenti di revisione. Lavora su una copia versionata (master intatto) |
| Asset | `assets/exampleManual.md` | Manuale di esempio: riferimento di **forma**, non di contenuto |
| Asset | `assets/style.css` | Stile per la resa HTML finale |
| Asset | `assets/struttura-manuale.template.md` | Template dell'indice delle sezioni |
| Asset | `assets/img-README.md` | Convenzioni di denominazione delle immagini |

## Come funziona

1. Predisponi il progetto: immagini in `src/img/`, indice in `docs/struttura-manuale.md`,
   control narrative in `ControlNarrative/`. La skill può creare lo scaffolding
   copiando i template inclusi.
2. Chiedi di generare il manuale.
3. La skill produce, a livello root del progetto:
   - `ManualeHMI.md` — manuale in Markdown,
   - `ManualeHMI.html` — manuale in HTML (linka `style.css`),
   - `immagini-richieste.md` — segnaposto immagine ancora da fornire.

## Principi

- **Lingua**: italiano, forma impersonale.
- **Fonte di verità**: le control narrative. Non inventare funzionalità; le lacune
  si marcano con `<!-- TODO: ... -->`.
- **Esempio = forma, non contenuto**: `exampleManual.md` è un modello di struttura
  e stile; mai copiarne i dati tecnici.

## Test rapido

```bash
claude --plugin-dir ./plugins/technical-writer
```

Poi in sessione:

```shell
/technical-writer:technical-writer
```
