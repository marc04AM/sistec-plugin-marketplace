---
name: reconcile-solutions
description: Porta una feature/innovazione da una solution SOURCE dentro una solution DEST, con ambito una singola finalità. Usa git merge/cherry-pick dove la feature vive in un repo condiviso da entrambe le solution su branch diversi; altrimenti fa un port manuale cross-repo ri-applicando l'*intento* del cambiamento (non un diff testuale) sul codice divergente della dest. Pianifica tutto, conferma le decisioni non banali, verifica con build e lascia gli edit unstaged. Usala quando devi allineare due solution della stessa famiglia (tipicamente checkout su branch-milestone diversi) portando una specifica feature dall'una all'altra.
disable-model-invocation: true
---

# reconcile-solutions — porta una feature da una solution a un'altra

Porta le **innovazioni** di una solution SOURCE dentro una solution DEST, con ambito **una sola
finalità/feature**. Le due solution sono tipicamente checkout della **stessa** famiglia di repo su
branch-milestone diversi: dove la feature vive in un repo **condiviso**, la riconciliazione è un
**git merge/cherry-pick**; dove il repo è **distinto** (o il codice è divergente), è un **port
manuale semantico**.

Regola guida: *merge preferito quando esiste lo stesso repo su branch diversi; le decisioni
banali/dipendenti procedono da sole; ogni decisione non banale si conferma.*

## 1. Input (tutti richiesti)

- **source** — la solution (`.sln`/`.slnx`/cartella) di cui si portano le innovazioni.
- **dest** — la solution che le riceve.
- **purpose** — la **feature/finalità** da riconciliare (il cambiamento specifico, **non** l'intero branch).

Manca uno dei tre → chiedilo e fermati finché non è chiaro.

## 2. Survey dei due repo-set (read-only) + classifica

Per ogni solution risolvi root + sub-repo (multi-repo → la root non è un repo; ogni subfolder con
`.git` lo è). Per ogni sub-repo su entrambi i lati registra: **branch** corrente, i **ref
milestone/feature** rilevanti, un **MERGE_HEAD/rebase** in corso, la **dirtiness**. Poi classifica:

- **SHARED** — stesso repo su entrambi i lati: stessa origin **oppure** storia condivisa (esiste un
  `git merge-base`) → candidato a git-merge.
- **DISTINCT** — controparte con origin diversa **e** nessuna storia condivisa → solo port manuale.

Una dest **dirty** o con un **merge in corso** → chiudila/puliscila prima (vedi *Chiudere un merge in
sicurezza*); se non si può finire in sicurezza → report e **stop**.

## 3. Trova la commit-footprint della feature

Sul SOURCE, trova i commit che compongono la **purpose** oltre la base milestone
(`git log <base>..<feature-branch>`), poi `git show --stat` per avere **file esatti + in quali repo**
la feature tocca. La purpose — non l'intero branch — definisce l'ambito.

## 4. Decisione merge-vs-port (per ogni repo toccato)

- **git merge / cherry-pick** *solo* quando il repo è lo **stesso SHARED** su entrambi i lati. Merge
  di branch intero solo se **non over-porta**; se il branch source porta anche lavoro estraneo →
  **cherry-pick** dei soli commit della feature. → non banale: **conferma** la scelta.
- **Port manuale** quando il repo è **DISTINCT** (repo diverso → nessuna storia condivisa da mergiare):
  ri-crea il cambiamento nell'albero della dest.
- Un repo **SHARED che la feature non tocca** → niente da fare lì.

### Chiudere un merge in sicurezza

Quando completi un merge, finalizzalo come **un singolo commit di merge a due genitori**
(`git commit --no-edit`, usa `MERGE_MSG`) — **mai** spezzarlo in commit ordinari: appiattirebbe il
merge e **distruggerebbe il link a due genitori**. Se ci sono **path non risolti** (conflitti), la
risoluzione è dell'utente → report e stop; non fare stage/resolve/commit al suo posto. **Mai**
`reset --hard`, `push --force`, o rebase di commit già pushati.

## 5. Mappa i path + enumera i call site nella dest

Mappa ogni path source toccato al suo equivalente nella dest (progetto/cartella omonimi sotto la root
dest; il layer applicativo spesso differisce — es. multi-cella `AB/`+`C/` vs `HMI/` singolo). **Grep
la dest** per il/i simbolo/i che la feature cambia/rimuove → enumera i **call site reali** da migrare.

## 6. Classifica ogni edit — banale vs non banale

- **Banale/dipendente → automatico:** file con eredità condivisa che portano quasi identici; rename
  meccanici; file nuovi le cui dipendenze esistono già nella dest.
- **Non banale → conferma (`AskUserQuestion`):** un file condiviso che è **divergente** nella dest (va
  ri-applicato **semanticamente**, non testualmente); un call site della dest **senza** controparte
  source; la scelta merge-vs-cherry-pick; la **cancellazione** di un tipo migrato-via.

## 7. Piano + gate di approvazione (prima di qualsiasi edit)

Presenta il piano completo — decisione merge/port per-repo, i gruppi di file (auto vs conferma), e il
passo di verifica — e **gate** (`Proceed` / correggi / solo-piano). Read-only fino a qui.

Struttura minima del piano (e del report finale allo Step 9):

```
## Riconciliazione: <purpose>   (SOURCE → DEST)
### <repo> — [SHARED merge | SHARED cherry-pick | DISTINCT port | nessuna azione]
- File auto: <elenco>
- File da confermare: <elenco + perché>
### Verifica
- build dest 0 errori nuovi · 0 riferimenti residui · edit lasciati unstaged
```

## 8. Esegui (dopo approvazione)

- **Baseline di build della dest** — prima di editare, builda la dest e registra errori/warning
  preesistenti, così a fine lavoro distingui i problemi **nuovi** da quelli già presenti.
- **Pre-check dipendenze di build** — prima di aggiungere file portati, verifica che i tipi/extension
  che richiedono esistano già sul branch della dest (evita sorprese di build rotta).
- **Auto-applica** il gruppo banale; per ogni **file condiviso divergente**, diffa la versione dest e
  ri-applica l'**intento** del cambiamento (non patchare alla cieca un diff stale).
- **Conferma ogni sito non banale** man mano che lo raggiungi, poi applica.
- **Attenzione alle firme delle factory** old→new: l'ordine degli argomenti può cambiare nella
  migrazione → passa **argomenti nominati** per stare al sicuro.
- **Rimanda la cancellazione** di un tipo migrato-via finché **tutti** i caller (inclusi quelli gated)
  sono migrati.
- Path merge/cherry-pick: finalizza come un solo commit gated a due genitori (vedi sopra).

## 9. Verifica + report

- **Builda la dest** (`dotnet build <dest .sln/.slnx>`), confrontando con la baseline dello Step 8:
  attesi 0 errori **nuovi**. Se la build fallisce, riporta gli errori, **lascia gli edit unstaged** e
  non auto-riparare oltre l'intento della feature (niente rifacimenti fuori ambito).
- **Zero riferimenti residui** a un simbolo rimosso (una nota doc `<c>…</c>` è innocua).
- **Lascia tutti gli edit unstaged** — riporta il change set (`git status --porcelain`) per la review.
- **Riporta la divergenza** creata tra le due solution, per agevolare il sync successivo.

## Note

- Read-only fino al gate dello Step 7; tutto ciò che segue è gated e lasciato unstaged per la review.
- Multi-repo: una feature può attraversare più repo con verdetti merge/port diversi — decidi per-repo.
- Se la feature SOURCE è **non committata**, un git merge non può trasportarla → committala prima sul
  source (chiedi), o ripiega sul port manuale.
