---
name: maintain-manual
description: Manutiene un manuale operatore GIÀ ESISTENTE in formato Word (.docx) con python-docx. Modi: porta dentro le modifiche di una copia di revisione (inclusi i canali nascosti — commenti Word e revisioni/tracked-changes); copy-editing (refusi/grammatica/stile); audit di copertura rispetto al software con inserimento in-stile delle funzioni mancanti; fix strutturali (run di paragrafi vuoti → salto pagina, numerazione/rientri); o aggiunta di commenti di revisione. Usala quando l'utente ha un manuale `.docx` esistente da aggiornare, correggere, revisionare o auditare — NON per generare un manuale nuovo (quello è la skill `technical-writer`, che produce Markdown/HTML). Lavora sempre su una COPIA con versione incrementata (il master resta intatto), con backup nello scratchpad, e preserva conteggio immagini, etichette in grassetto e TOC.
---

# Maintain Manual — manutenzione di un manuale Word (.docx)

Manutiene un **manuale operatore già esistente in `.docx`**. È la controparte di `technical-writer`:
quella **genera** un manuale nuovo (Markdown → HTML); questa **manutiene** un Word esistente
(porta modifiche di revisione, corregge, audita, sistema la struttura, commenta). Se l'utente vuole
*creare* un manuale da zero, è `technical-writer` — non questa.

**Meccanismo: python-docx, MAI Word-COM.** L'automazione COM di Word si blocca e corrompe
`Normal.dotm` — non usarla. Usa **python-docx** (testato su 1.2.0, Word-free) scrivendo script
helper ad-hoc nello scratchpad di sessione.

## Regole invarianti (ogni modo)

1. **Non toccare mai il master.** Lavora su una **copia con versione incrementata**: dal token di
   versione nel nome (`V1.7`) l'output è `V1.8` nella **stessa cartella**; un nome senza versione →
   aggiungi `_maintained`. Non sovrascrivere mai l'input.
2. **Backup prima di editare.** Copia il manuale risolto nello scratchpad come `<stem>_pre-<modo>.docx`
   (punto di ripristino), poi copia sul path della nuova versione — tutte le modifiche vanno lì.
3. **Preserva** conteggio immagini (registralo prima, verifica invariato alla fine), **etichette in
   grassetto**, e imposta `<w:updateFields/>` così Word rigenera il TOC all'apertura.

## 1. Risolvi il manuale target

- Path `.docx` dato → quello. Inesistente → segnala e fermati.
- Nessun path → il `.docx` **più recente** (per data di modifica) nella cartella di lavoro / progetto.
  Nessuno trovato → segnala e fermati.

## 2. Scegli il modo (esattamente uno)

- **port `<external.docx>`** — porta le modifiche incrementali della copia esterna nel manuale,
  tenendo le modifiche già fatte nel manuale:
  - diffa il testo del corpo **E i canali che un text-diff salta** — **commenti Word**, **revisioni/
    tracked-changes**, **text box** (una nota di revisione può vivere solo nel canale commenti).
  - isola le modifiche presenti nell'esterno ma non nel manuale; applica via replacement **run-level /
    cross-run** così le **etichette in grassetto** si preservano.
  - **non annullare** le modifiche deliberate del manuale (una correzione già fatta resta; un commento
    risolto resta risolto). Se una "modifica" esterna è già superata, salta e dillo.
- **copyedit** — refusi, grammatica, leggibilità; togli ridondanze. Uniforma lo **stile** (mappa gli
  stili orfani su quelli standard, sistema titoli duplicati). Attenzione al gotcha di codifica
  **cp1252/utf-8**. Rinfresca il TOC.
- **audit [--code "<solution/cartella>"]** — il manuale descrive ogni funzione/procedura implementata?
  - costruisci l'**inventario funzioni HMI** dal codice (`--code`, altrimenti la solution del progetto
    attivo; per inventari grandi delega a un agente **Explore** read-only).
  - classifica la copertura → **gap** (implementate, non documentate) / **stale** (documentate, non nel
    codice) / **procedure implicite**.
  - inserisci i **gap ad alto valore** nello stile esistente del manuale, con segnaposto `Immagine:`
    (gli screenshot si catturano a parte); correggi il testo stale. Traccia i gap minori in un file
    `manual-open-items.md` accanto al manuale.
- **style** — fix meccanici di struttura:
  - ogni **run di ≥3 paragrafi vuoti** → un singolo **salto pagina** (`add_run().add_break(WD_BREAK.PAGE)`
    + rimuovi gli extra) — ma **salta il run finale di fine-documento** (aggiungerebbe solo una pagina
    vuota; offrilo a parte). I run di 1–2 restano.
  - **numerazione/rientri**: dai agli item di lista inseriti un `numPr` corretto (`ilvl` + un `numId`
    coerente con la sezione) invece del default di stile; collassa gli artefatti multi-spazio.
- **comments** — aggiungi commenti di revisione Word:
  `Document.add_comment(runs, text="controllare", author="Revisione", initials=…)` sulle voci di
  procedura opzionali e sui blocchi modificati. Nota gli eventuali **commenti utente preesistenti** e
  tieni i tuoi sotto un autore distinto così sono separabili. Verifica che i riferimenti == commenti
  (nessun orfano).

## 3. Gate di approvazione

`AskUserQuestion` (`Proceed`/`Cancel`): ricapitola il **manuale target**, il **modo**, il **path della
nuova versione** e il **path di backup**. Su `Cancel` → fermati.

## 4. Esegui il modo (python-docx, sulla nuova versione)

Struttura/immagini/tabelle preservate. Applica il modo scelto al punto 2.

## 5. Report

- Path della nuova versione + path del backup nello scratchpad.
- **Conteggio immagini prima/dopo** (deve combaciare — segnala ogni delta e la causa).
- Riepilogo per-modo: modifiche portate / fix applicati / gap inseriti / salti pagina fatti / commenti
  aggiunti.
- Conferma esplicita che il **master/sorgente è rimasto intatto**.

## Note

- I manuali sono documenti, non sorgente git — non fare staging di nulla.
- `--audit` che rimanda lavoro aggiorna `manual-open-items.md` accanto al manuale.
- L'esecuzione di script python/python-docx può chiedere permesso la prima volta — l'utente approva
  caso per caso.
