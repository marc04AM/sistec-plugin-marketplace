# Audit `src/` — esito finale (20/20)

> Validati con `skill-creator` e con un filtro affinato in corso d'opera (sotto). Ogni file di
> `src/` è stato o **distillato in una skill** del marketplace, o **scartato** con motivo scritto in
> riga 1 e rinominato `<name>-TRASH.md`. Gli originali restano come provenienza (bookkeeping in
> `PORTED/` e `DISCARDED/`).
>
> **Nota di contesto:** il marketplace è **interno a Sistec** → la specificità Sistec (schema
> `language_spv`, `Sistec.Core`, convenzioni HMI) **non** squalifica un file. E i **command sono
> deprecati** → la forma giusta è **skill** (esplicita, `disable-model-invocation: true`, dove
> l'operazione va invocata a mano).

---

## 1. Il filtro (le domande che decidono)

Un file merita una skill **solo** se passa tutte e tre:

1. **Lo fa già, meglio, uno strumento deterministico?** (git, linter/analyzer, `docker compose`,
   uno script). Se sì, un'approssimazione LLM ha **valore negativo**: aggiunge non-determinismo e
   rischio, zero guadagno.
2. **È solo plan-mode / TodoWrite / comportamento nativo travestito?** Se sì, è ridondante.
3. **Claude farebbe materialmente peggio SENZA?** Deve esserci **giudizio semantico** reale che
   solo un LLM porta (interpretare un output, tradurre intento, refactor semantico).

Corollario positivo — il pattern che **vince**: uno **script bundlato raccoglie in modo
deterministico**, poi **l'LLM interpreta/decide** (dpi-anchor-fix, network-probe). O: l'LLM fa un
lavoro **puramente semantico** che nessun tool sa fare (maintain-manual, translate,
reconcile-solutions).

---

## 2. Esito per file

**Legenda:** 🟢 SKILL (distillata nel marketplace) · ⚫ DROP (fuori dal marketplace, `-TRASH`).

| File | Esito | Destinazione / Motivo |
|---|---|---|
| `dpiRepair` | 🟢 | → `hmi-developer/dpi-anchor-fix`. Script deterministico rileva il bug DPI/anchor .NET 8; l'LLM interpreta il verdetto e sceglie la config sicura sotto gate. |
| `networkProbe` | 🟢 | → `device-spy/network-probe`. Script sonda NIC/IP/salute rete; l'LLM diagnostica link-flap / conflitti IP / driver. |
| `manualize` | 🟢 | → `technical-writer/maintain-manual`. Know-how python-docx (no COM, canali commenti/tracked-changes nascosti, conteggio immagini) = puro valore riusabile. Manutiene un `.docx` esistente (controparte di `technical-writer` che *genera*). |
| `translate` | 🟢 | → `hmi-developer/translate` (esplicita). `MissingTranslations.csv` → `INSERT language_spv`. Valore: regola chiave-esatta (`#`) + inferenza IT/EN dal call-site. **Semplificata** (via connessione DB, rilevamento versione 5.7≡8, `--apply`, `--rescan`). |
| `gitReconcile` | 🟢 | → `hmi-developer/reconcile-solutions` (esplicita). Porta una feature tra due solution; merge/cherry-pick dove condiviso, **port semantico** dove divergente (ri-applica l'intento, non il diff). L'unico del cluster git con valore LLM. *(Tenuta anche col caveat branch — vedi §3 — per il caso raro di prodotti distinti.)* |
| `commentize` | 🟢→merge | **Fuso** in `hmi-developer/add-doc` (non duplicato). Recuperato solo lo scoping sul **changed-set**; scartati `/simplify` (command assente), S9-"documenta i privati", gitize-cache. `add-doc` è ora la disciplina commenti unica. |
| — | — | *(+ 5 skill già shippate: path hardcoded `C:\Users\Sistec 23\…` → fixati a `$env:CLAUDE_PLUGIN_ROOT` / relativi.)* |
| `proj` | ⚫ | Infra di sessione. Nativo CC = lanciare `claude` dentro ogni repo (la cwd È il progetto). + framework privato (`_config`, `MEMORY.md`, anchor, work-dir stale). |
| `command` | ⚫ | Meta-tooling. Nativo = creare `.claude/commands/<name>.md`; per distillare skill c'è `skill-creator`. Spawner/ledger/catalog bespoke. |
| `skillify` | ⚫ | Meta-authoring. Coperto da `skill-creator`; "recording" solo comportamentale (CC non ha hook on-disk) → fragile. |
| `skilliDo` | ⚫ | Partner-produttore di `skillify`. Stesso motivo. |
| `fetch` | ⚫ | Git puro (`fetch`, `rev-list --left-right`, `status --porcelain`, `merge --ff-only`) + predicati. Un loop/script lo fa meglio. |
| `gitAlign` | ⚫ | Git puro + predicati; l'unico valore (guard "no `--split` a merge in corso") è un **check da mettere in gitize**, non una skill. |
| `gitWipe` | ⚫ | Git puro (`for-each-ref`, `branch --merged`, `branch -d/-D`); safety net = git stesso. Distruttivo → script. |
| `merge` | ⚫ | `git merge --no-ff` in loop; l'unico bit LLM (comporre il messaggio) è il mestiere di `gitize`. "Non basta `git merge`?" |
| `feedback` | ⚫ | Versione striminzita della **plan mode** nativa. |
| `deadcode` | ⚫ | Scan LLM dell'intera codebase = spreco/contesto saturo; il dead code lo trovano **linter/analyzer** (Roslyn IDE0051/CS0169, ReSharper) in modo deterministico. |
| `issue` | ⚫ | Issue-tracker su file. Human apre su **GitHub**; l'analisi è nativa ("analizza questo problema"); i verbi CRUD = manipolazione deterministica di tabella markdown; persistenza = spec-driven/"salva un md". |
| `codesys` | ⚫ | Wrapper sottile su **`docker compose`** (up/down/restart = comandi compose 1:1) + poca glue CODESYS. Modo nativo = `docker compose`. |
| `deploy` | ⚫ | Rilascio in **produzione** (copia UNC + shortcut). Operazione rischiosa/irreversibile/deterministica → **script** (robocopy + WScript.Shell), non un LLM non-deterministico. 240 righe per un copia-incolla. |
| `port-solution` | ⚫ | Rimodella un tipo su un esemplare di un'altra solution. Ma il workflow giusto per una feature è un **branch** (contesto ampio, git merge, meno rischio API pubbliche), non copie parallele di solution. Tolto il framing "due solution" = refactor nativo. |

**Conteggio finale:** 🟢 **6** (5 skill nuove + 1 fusione) · ⚫ **14**.

---

## 3. Nota sul cluster "cross-solution" (reconcile / port)

`reconcile-solutions` e `port-solution` nascono dall'abitudine di tenere **copie parallele di
solution** (es. `5309` e `5315`) e portare pezzi tra loro. Il workflow migliore per lavorare a una
feature è un **branch** (`/development-feature`): Claude ha contesto ampio, git gestisce il merge, e
c'è meno rischio di rompere le API pubbliche.

Perciò:
- `port-solution` → **scartato**: con i branch si riduce a un refactor nativo.
- `reconcile-solutions` → **tenuto** (scelta esplicita) per il caso **raro** di prodotti **davvero
  distinti** che condividono heritage e non sono branch dello stesso repo. Nel caso comune
  (stessa famiglia, branch-milestone diversi) preferire branch + merge.

---

## 4. Difetti trasversali che sono stati corretti nel port

Ogni skill distillata è stata **de-coupled** dal workspace privato (ma **non** dalla legittima
specificità di dominio Sistec):

- via **path assoluti** stale (`C:\Users\Sistec 23\…`) → `$env:CLAUDE_PLUGIN_ROOT` / cwd-relativi;
- via direttive `P0–P15`, convenzioni `S`-series (label → regole in chiaro o rimando a
  `assets/rules/`), memory-anchor `[[…]]`, ledger di progetto attivo, cross-ref a command interni
  (`/gitize`, `/gitAlign`, `/skilliDo`);
- `description` riscritto orientato al **trigger** (o, per le operazioni deliberate/rischiose,
  `disable-model-invocation: true` per l'invocazione esplicita);
- gli **engine deterministici** (`.ps1`) bundlati come `assets/…` del plugin, non referenziati da
  path della macchina.

Barra di qualità: `hmi-developer/add-doc` (corta, generale, zero leakage), **non** il port
superficiale.
