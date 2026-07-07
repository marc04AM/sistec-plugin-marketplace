---
name: translate
description: Genera l'INSERT MySQL per la tabella language_spv a partire dal MissingTranslations.csv di una HMI. Per ogni chiave ricava StringName (esatta, incluso l'eventuale '#' iniziale) e i testi Italian/English leggendo il call-site nel codice, preserva i placeholder string.Format, e scrive un .sql idempotente pronto da eseguire. Usala quando c'è un MissingTranslations.csv da riversare in language_spv.
disable-model-invocation: true
---

# translate — MissingTranslations.csv → INSERT `language_spv`

Converte le traduzioni mancanti loggate da una HMI (`MissingTranslations.csv`) in un `.sql` pronto:
un `INSERT` idempotente nella tabella canonica `language_spv`. **Genera solo il file** — non si
connette al database; l'esecuzione la fai tu.

## 1. Risolvi il CSV

- Path dato → quello.
- Nessun path → il `MissingTranslations.csv` **più recente** (per data di modifica) sotto la cartella
  di lavoro (tipicamente `**/bin/**/MissingTranslations.csv`). Nessuno trovato → segnala e fermati.

## 2. Parsa → chiavi distinte

Colonne del CSV: `Timestamp;Locale;Key;DefaultText;Module;Method`. Collassa a **una riga per `Key`
distinta** (una chiave si logga una volta per locale). Tieni `DefaultText`, `Module`, `Method`:
puntano al call-site per lo Step 3.

## 3. Ricava Italian + English dal call-site (il punto)

Per ogni chiave, `grep` il sorgente a `Module`/`Method` (e la chiamata `GetOrDefault(key, default)`)
per leggere il testo inteso e il suo significato, poi produci un valore **Italian** e uno **English**
puliti:

- il `DefaultText` senza `#` è il fallback dell'autore — di solito giusto per una lingua; fornisci tu
  la traduzione naturale dell'altra;
- disambigua dal contesto (titolo vs corpo, header di colonna, membro enum, unità di misura);
- **preserva i placeholder `string.Format`** (`{0}`, `{1}`, …) verbatim in entrambe le lingue;
- **segnala ogni valore indovinato** (nessun default leggibile nel codice) perché l'utente lo verifichi.

### Regola di correttezza n.1 — `StringName` = chiave esatta

La HMI risolve un termine con un **hit esatto di dizionario, senza strippare il `#`**. Quindi
`StringName` **deve** essere la chiave grezza: le chiavi scritte con `#` iniziale nel codice
(`"#ProductionLog"`) si salvano **con** il `#`; quelle senza (`plc_PLC_0`) senza. Sbagliare qui = il
termine non si risolve mai a runtime. Il `#` nella colonna `DefaultText` del CSV è invece solo il
marcatore "non tradotto" — **non** fa parte della chiave.

## 4. Scrivi il `.sql`

Un unico `INSERT` multi-riga, **idempotente**, in **UTF-8** (testo IT accentato):

```sql
INSERT INTO language_spv (StringName, Italian, English) VALUES
  ('#ProductionLog', 'Log di produzione', 'Production log'),
  ('#JobSplit',      'Divisione lavoro {0}', 'Job split {0}')
ON DUPLICATE KEY UPDATE Italian = VALUES(Italian), English = VALUES(English);
```

- `StringName` = chiave esatta (incl. `#`); lascia `TimeStamp`/`Other` ai loro default.
- La coda `ON DUPLICATE KEY UPDATE … = VALUES(…)` rende l'INSERT rieseguibile senza errori di chiave
  duplicata e vale **sia su MySQL 5.7 sia 8.x** — nessun rilevamento di versione.
- **Escape gli apici singoli** nei testi (`'` → `''`): l'italiano ne è pieno (`l'operatore` → `l''operatore`).
- Intestazione a commento: CSV sorgente, tabella, e le regole (chiave-esatta, marcatore `#`,
  idempotenza). Raggruppa le tuple per area con un commento per gruppo; marca con un commento le righe
  il cui valore è **indovinato**.
- Output di default: `<dir-del-csv>\MissingTranslations.sql` (o il path indicato).

## 5. Report

Path del `.sql`, conteggi (chiavi distinte / indovinate), l'elenco dei valori indovinati da vetare, e
il comando per eseguirlo:

```
mysql -h <host> -u <user> -p <db> --default-character-set=utf8mb4 < <out>
```
