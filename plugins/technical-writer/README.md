# technical-writer

Plugin del marketplace Sistec per generare il **manuale operatore di un'HMI** in
italiano, a partire dalle control narrative dell'impianto. Replica struttura, tono
e formattazione del manuale di esempio incluso e produce sia Markdown sia HTML
con stile dedicato.

## Componenti

| Componente | File | Cosa fa |
| :--------- | :--- | :------ |
| Skill | `skills/technical-writer/SKILL.md` | Redige il manuale dalle control narrative; invocabile come `/technical-writer:technical-writer` o automaticamente quando si chiede di creare un manuale HMI |
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
