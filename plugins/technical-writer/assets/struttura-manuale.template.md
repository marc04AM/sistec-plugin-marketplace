# Struttura del Manuale HMI

Indice delle sezioni del manuale, **compilato dall'utente** prima di chiedere
all'agente di generare il manuale. È l'ordine in cui le sezioni verranno redatte.

## Come compilare
- Una riga per sezione, con numerazione gerarchica (`1`, `1.1`, `1.1.1`).
- Colonna **Sezione**: titolo della voce.
- Colonna **Fonte**: il file in `ControlNarrative/` da cui attingere i contenuti.
  - Usa `src/img` se la sezione si basa solo sulle immagini/screenshot.
  - Usa `—` se la sezione è introduttiva o redazionale.
  - Lascia `TODO` se la fonte non è ancora disponibile.

> L'agente segue questo indice nell'ordine indicato e, per ogni voce, attinge
> **solo** alla fonte specificata. Le lacune vengono marcate con `<!-- TODO: ... -->`.

## Indice

| # | Sezione | Fonte |
| --- | --- | --- |
| 1 | PREMESSA | — |
|  |  |  |

<!--
Esempio di compilazione:

| # | Sezione | Fonte |
| --- | --- | --- |
| 1 | PREMESSA | — |
| 2 | COMANDI SOFTWARE | — |
| 2.1 | Autenticazione | AvvioSpegnimento.md |
| 3 | CONTROLLO DEL PANNELLO | src/img |
| 3.1 | Layout generale | src/img |
| 4 | RICETTA | Ricetta.md |
| 5 | AVVIO DELLA PRODUZIONE | AvvioSpegnimento.md |
-->
