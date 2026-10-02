# blender-ply

Lavoro su modelli **PLY esportati da CAD** (in mm, colori per vertice, nessun materiale) dentro
Blender, guidato da Claude tramite il bridge MCP di Blender (`mcp__Blender__execute_blender_code`,
porta 9876). Ogni skill esegue uno script Python bundlato **dentro Blender** e restituisce un
report JSON.

## Skill

| Skill | Cosa fa | Modifica |
| :---- | :------ | :------- |
| `/blender-ply:visualizzaply` | dopo un import: colori per vertice visibili, clip calcolato sulla diagonale del modello, vista 3/4 in prospettiva centrata, *Zoom to Mouse Position* + *Auto Depth* | vista, clip, preferenze globali di zoom, materiale `<Oggetto>_Col` |
| `/blender-ply:centrablender` | centra il modello sulla sagoma a schermo; inclinazione invariata, zoom allontanato solo se il modello non ci sta | solo la vista |
| `/blender-ply:centraply` | porta il vertice selezionato (o il punto medio) su (0,0,0): origine oggetto = cursore 3D = origine mondo; `dry_run` per l'anteprima | la mesh (passo di undo "CentraPLY") |
| `/blender-ply:fotografaply` | centra e salva un PNG su sfondo bianco senza overlay (viewport render, view transform `Standard`), poi ripristina | file `.png`; impostazioni di render solo durante lo scatto |
| `/blender-ply:ply-colors` | ripristina i colori per vertice (Solid → `VERTEX`, materiale per Material Preview); `detect_ply_colors.py` è la versione read-only | vista, materiali nuovi (mai quelli esistenti) |

## Hook

| Evento | Script | Cosa fa |
| :----- | :----- | :------ |
| `PostToolUse` su `mcp__Blender__.*` | `hooks/ply-colors-nudge.py` | dopo un import PLY, o alla prima chiamata Blender della sessione, interroga Blender **in sola lettura** (`detect_ply_colors.py` sul socket 9876, timeout 2 s) e avvisa Claude solo se un modello con colori per vertice è davvero mostrato grigio. Non corregge nulla: la correzione passa da `/blender-ply:ply-colors`. Le altre chiamate escono subito dopo una regex. Se Blender non risponde resta in silenzio |

L'hook segna la "prima chiamata della sessione" con un file in
`%TEMP%\claude-blender-ply-colors\`; i marker più vecchi di 7 giorni vengono cancellati.

## Regola opzionale

`rules/blender-ply-colors.md` copre il caso che l'hook non vede: un modello importato
dall'interfaccia di Blender **dopo** la prima chiamata MCP della sessione. Un plugin non può
installare regole, quindi chi la vuole la copia a mano:

```powershell
Copy-Item "<cartella del plugin>\rules\blender-ply-colors.md" "$env:USERPROFILE\.claude\rules\"
```

Senza la regola resta la description di `ply-colors`, che chiede già di controllare i colori a
ogni ispezione della scena.

## Requisiti

- Blender con l'add-on MCP attivo e il server avviato (Preferences → Add-ons → MCP → Start).
- Il server MCP di Blender configurato in Claude Code (tool `mcp__Blender__*`).
- Blender in esecuzione **sulla stessa macchina** di Claude Code: gli script vengono letti da
  Blender direttamente dalla cartella della skill (`${CLAUDE_SKILL_DIR}/scripts/…`), quindi il
  codice non passa per la conversazione.

## Note

- Gli script sono idempotenti e vanno rilanciati a ogni turno: l'utente naviga, importa, entra in
  Edit Mode tra una chiamata e l'altra.
- Nessuna skill salva il `.blend` o esporta il PLY se l'utente non lo chiede.
- La matematica del viewport comune (proiezione, centratura sulla sagoma, vertici nel mondo) sta in
  `lib/view_projection.py` ed è usata da `centrablender`, `fotografaply` e `visualizzaply`.
  `visualizzaply` riusa anche lo script di `ply-colors`. Gli script trovano entrambi partendo dal
  proprio `__file__`, quindi la struttura del plugin va mantenuta.
- Gli script di `ply-colors` restano autosufficienti di proposito: `detect_ply_colors.py` si può
  inviare anche direttamente sul socket del bridge, dove `__file__` non c'è.

## Installazione

```shell
/plugin install blender-ply@sistec-plugins
```
