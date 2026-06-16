# Manuale Operativo - Sistema HMI Sistec AM

## Sommario

- [1. Premessa](#1-premessa)
- [2. Comandi software](#2-comandi-software)
  - [2.1 Simboli](#21-simboli)
  - [2.2 Autenticazione](#22-autenticazione)
- [3. Controllo del pannello](#3-controllo-del-pannello)
  - [3.1 Layout generale](#31-layout-generale)
  - [3.2 Menù laterale](#32-menù-laterale)
  - [3.3 Layout impianto](#33-layout-impianto)
  - [3.4 Spazio dati](#34-spazio-dati)
  - [3.5 Informazioni di sistema](#35-informazioni-di-sistema)
  - [3.6 Pagine standard](#36-pagine-standard)
- [4. Pannello di controllo principale](#4-pannello-di-controllo-principale)
  - [4.1 Layout generale](#41-layout-generale)
  - [4.2 Zona 1](#42-zona-1)
  - [4.3 Zona 2](#43-zona-2)
  - [4.4 Zona 3](#44-zona-3)
  - [4.5 Zona 4](#45-zona-4)
  - [4.6 Zona 5](#46-zona-5)
  - [4.7 Zona 6](#47-zona-6)
- [5. Avvio della produzione](#5-avvio-della-produzione)
  - [5.1 Diagnostica iniziale](#51-diagnostica-iniziale)
  - [5.2 Configurazione della lavorazione](#52-configurazione-della-lavorazione)
  - [5.3 Avvio ordine](#53-avvio-ordine)
  - [5.4 Selezione baie](#54-selezione-baie)
  - [5.5 Inizio del ciclo](#55-inizio-del-ciclo)
  - [5.6 Arresto del ciclo](#56-arresto-del-ciclo)
  - [5.7 Ripristino del ciclo](#57-ripristino-del-ciclo)
  - [5.8 Arresto della produzione](#58-arresto-della-produzione)
  - [5.9 Spegnimento del pannello operatore](#59-spegnimento-del-pannello-operatore)

---

## 1. Premessa

Questo allegato costituisce il manuale operativo dell'interfaccia HMI (Human Machine Interface) e ha lo scopo di fornire una guida completa per la supervisione, il controllo e la diagnosi del sistema automatizzato.

L'interfaccia HMI, qui definita anche come **pannello di controllo** o **pannello operatore**, rappresenta lo strumento principale attraverso il quale l'operatore interagisce con il PLC e gli altri dispositivi dell'impianto, consentendo la gestione delle lavorazioni, il monitoraggio degli stati operativi e l'individuazione di eventuali anomalie.

All'interno dell'allegato vengono descritte:

- La struttura e la navigazione dell'interfaccia;
- I principali comandi software;
- Le procedure operative per l'avvio, la gestione e l'arresto della produzione;
- Gli strumenti di diagnostica, le segnalazioni e gli allarmi dell'impianto.

## 2. Comandi software

I comandi software sono definiti come tutti quei dispositivi che interagiscono con il processo produttivo e in cui la funzione di comando è delegata alle istruzioni del programma.

### 2.1 Simboli

L'accesso alle diverse funzioni dell'applicazione (quali navigazione, controlli manuali, richieste e visualizzazioni) avviene selezionando le aree sensibili della pagina principale e/o le icone che rappresentano le singole funzioni.

Alcune funzioni potrebbero non essere disponibili, ad esempio se il livello di accesso dell'utente non è sufficiente o se non sono soddisfatte le condizioni necessarie al loro utilizzo.

Le icone delle funzioni non disponibili sono visualizzate in scala di grigi, mentre le icone delle funzioni attive sono mostrate a colori.

| Icona disabilitata | Icona abilitata |
| --- | --- |
| ![Icona disabilitata](src/img/iconaDisabilitata.png) | ![Icona abilitata](src/img/iconaAbilitata.png) |

Un pulsante **attivo** ha la sua immagine a colori brillanti.

In ogni sezione verranno descritti i simboli specifici e utili per la pagina.

### 2.2 Autenticazione

Nell'applicazione sono definiti quattro livelli utente, con password distinte:

- **Operatore**: utente di livello base, con privilegi minimi;
- **Manutentore**: utente di livello intermedio;
- **Esperto**: utente di livello avanzato, con tutti i privilegi;
- **Sistec**: utente riservato ai soli tecnici Sistec.

![Finestra di accesso](src/img/finestraDiAccesso.png)

*Immagine: Finestra di accesso.*

## 3. Controllo del pannello

Il pannello di controllo, o pannello operatore, rappresenta l'interfaccia dell'operatore con il PLC di gestione dell'impianto e consente all'operatore di inviare e ricevere informazioni di processo.

### 3.1 Layout generale

![Layout generale](src/img/LayoutGenerale.png)

*Immagine: Layout Generale.*

I pannelli operatore sono caratterizzati da un layout generale condiviso, la cui struttura rimane invariata mentre i contenuti variano in base allo specifico pannello e alle operazioni eseguite. Tale layout è composto da:

1. **MENU LATERALE**: ogni voce di questo menu modifica il contenuto degli spazi **SPAZIO DATI** e **LAYOUT IMPIANTO**. Le diverse combinazioni dei contenuti di questi due spazi definiscono le cosiddette pagine standard. Di conseguenza, ogni icona del menu laterale è associata a una specifica pagina standard;
2. **SPAZIO DATI**: in questo spazio saranno presenti i comandi software associati alle pagine standard o al contenuto selezionato nel **LAYOUT IMPIANTO**;
3. **LAYOUT IMPIANTO**: in questo spazio viene visualizzato il layout grafico in pianta dell'impianto. Questo layout è interattivo e consente di selezionare le zone e gli elementi specifici dell'impianto. A seconda della zona o dell'elemento selezionato cambierà anche il contenuto di **SPAZIO DATI**;
4. **INFORMAZIONI DI SISTEMA**: in questo spazio vengono visualizzati gli stati più rilevanti del sistema come quelli dei dispositivi di sicurezza, dei robot e la comunicazione tra i dispositivi. Il contenuto di questo spazio è fisso e specifico per ciascun pannello operatore.

### 3.2 Menù laterale

Cliccando le varie icone del menu laterale è possibile navigare attraverso le pagine standard dell'interfaccia. Inoltre, contiene alcune funzionalità base come la gestione degli utenti e gli strumenti per spegnere, riavviare o chiudere l'interfaccia.

| Icona | Funzione |
| --- | --- |
| ![Accedi](src/img/accedi.png) | Apre la finestra "Accedi", che consente di accedere ai 4 livelli utente. |
| ![Home](src/img/home.png) | Apre la pagina "Home", da cui è possibile creare ed eseguire un processo. |
| ![Ricetta](src/img/ricetta.png) | Apre la pagina "Ricetta" e consente di creare e gestire le ricette. |
| ![Allarmi](src/img/allarmi.png) | Apre la pagina "Allarmi e Report". |
| ![Storico eventi](src/img/eventi.png) | Apre la pagina "Storico eventi" e mostra gli allarmi e gli avvisi. |
| ![Manutenzione](src/img/manutenzioni.png) | Apre la pagina "Manutenzione" da cui è possibile gestire le manutenzioni programmate. |
| ![Impostazioni](src/img/impostazioni.png) | Apre la pagina "Impostazioni". |
| ![Minimizza](src/img/minimizza.png) | Minimizza l'HMI per accedere al sistema operativo. |
| ![Shutdown](src/img/spegni.png) | Apre la finestra "Shutdown", dalla quale è possibile chiudere l'applicazione, arrestare o riavviare l'HMI. |

Con l'apertura di ogni pagina verrà ripristinato anche il contenuto dello spazio di LAYOUT IMPIANTO, portando la vista al layout globale del sistema.

### 3.3 Layout impianto

Il sistema, nello spazio LAYOUT IMPIANTO, consente di navigare all'interno della pianta selezionando le aree evidenziate da riquadri colorati. La selezione di una di queste aree conduce alla relativa zona, in cui verrà visualizzata un'immagine di dettaglio di questa. Ogni zona può contenere simboli di attuatori o dispositivi cliccabili, associati a comandi manuali, e/o simboli non cliccabili utilizzati per indicare lo stato di sensori o riscontri.

La selezione di questi simboli porta un cambiamento nel contenuto dello SPAZIO DATI, dove compariranno le interfacce per i comandi software dei singoli elementi.

![Layout impianto delle zone](src/img/layoutImpiantoZone.png)

È possibile tornare alla zona di livello superiore, fino al layout generale, tramite il pulsante con icona triangolare presente in basso a destra.

| Icona | Funzione |
| --- | --- |
| ![Mostra nomi zone](src/img/mostraNomiZone.png) | Simbolo che permette di visualizzare il nome di tutte le zone nel layout nonché le etichette relative ai comandi manuali. |
| ![Torna alla zona precedente](src/img/tornaZonaPrecedente.png) | Simbolo che permette di tornare alla zona precedente da un comando manuale o zona fino a tornare al layout generale. |

#### 3.3.1 Attuatori e dispositivi

Di seguito è riportato l'elenco dei simboli interattivi che rappresentano attuatori o altri dispositivi.

| Icona | Funzione |
| --- | --- |
| ![Motore](src/img/motore.png) | Indica un motore. |
| ![Chiusura cilindro valvola orizzontale](src/img/valvolaChiusuraOrizzontale.png) | Indica la chiusura del cilindro della valvola con movimento orizzontale. |
| ![Apertura cilindro valvola orizzontale](src/img/valvolaAperturaOrizzontale.png) | Indica l'apertura del cilindro della valvola con movimento orizzontale. |
| ![Soffio valvola](src/img/valvolaSoffio.png) | Indica l'azione di soffio di una valvola. |
| ![Aspirazione vuoto valvola](src/img/valvolaAspirazioneVuoto.png) | Indica l'azione di aspirazione del vuoto di una valvola. |

### 3.4 Spazio dati

Interagendo con il LAYOUT IMPIANTO, ad esempio cliccando l'icona di un attuatore, questo spazio visualizza i comandi manuali o le informazioni relative al dispositivo selezionato.

Di seguito vengono descritti i comandi software comuni a tutti i pannelli operatore.

I comandi software che comprendono l'attivazione manuale di attuatori potranno essere attivati solo in condizioni specifiche. Queste condizioni, se presenti, saranno indicate nella parte inferiore dello SPAZIO DATI.

![Spazio Dati](src/img/spazioDati.png)

*Immagine: Spazio Dati.*

#### 3.4.1 Valvole

![Comando Valvola](src/img/comandoValvola.png)

*Immagine: Comando Valvola.*

Cliccando uno dei simboli associati, nello SPAZIO DATI viene visualizzata la seguente interfaccia. Tramite questa è possibile attivare manualmente il dispositivo e monitorarne i feedback.

1. **DESCRIZIONE**: descrizione del componente;
2. **STATI RISCONTRO**: riscontri legati allo scopo della valvola. Questi cambiano a seconda del tipo di valvola e al suo scopo nell'impianto;
3. **COMANDI**: pulsanti per attivare le uscite legate al dispositivo. L'icona di questi pulsanti varia in funzione del tipo di attuatore e dell'azione che esso esegue nell'impianto.

| Icona | Funzione |
| --- | --- |
| ![Movimento dal basso verso l'alto](src/img/movimentoBassoAlto.png) | Indica il movimento dal basso verso l'alto. |
| ![Movimento dall'alto verso il basso](src/img/movimentoAltoBasso.png) | Indica il movimento dall'alto verso il basso. |
| ![Movimento da sinistra verso destra](src/img/movimentoSinistraDestra.png) | Indica il movimento da sinistra verso destra. |
| ![Movimento da destra verso sinistra](src/img/movimentoDestraSinistra.png) | Indica il movimento da destra verso sinistra. |
| ![Chiusura cilindro valvola verticale](src/img/valvolaChiusuraVerticale.png) | Indica la chiusura del cilindro della valvola con movimento verticale. |
| ![Apertura cilindro valvola verticale](src/img/valvolaAperturaVerticale.png) | Indica l'apertura del cilindro della valvola con movimento verticale. |
| ![Chiusura cilindro valvola orizzontale](src/img/valvolaChiusuraOrizzontale.png) | Indica la chiusura del cilindro della valvola con movimento orizzontale. |
| ![Apertura cilindro valvola orizzontale](src/img/valvolaAperturaOrizzontale.png) | Indica l'apertura del cilindro della valvola con movimento orizzontale. |
| ![Soffio valvola](src/img/valvolaSoffio.png) | Indica l'azione di soffio di una valvola. |
| ![Aspirazione vuoto valvola](src/img/valvolaAspirazioneVuoto.png) | Indica l'azione di aspirazione del vuoto di una valvola. |

#### 3.4.2 Motore semplice

![Comando Motore Semplice](src/img/comandoMotoreSemplice.png)

*Immagine: Comando Motore Semplice.*

Cliccando uno dei simboli associati, nello SPAZIO DATI viene visualizzata la seguente interfaccia. Tramite questa è possibile attivare manualmente il dispositivo e monitorarne la velocità.

1. **DESCRIZIONE**: descrizione del componente;
2. **OVERRIDE VELOCITÀ**: tramite questo cursore è possibile regolare la velocità in percentuale rispetto a quella nominale (0-100%);
3. **VELOCITÀ CORRENTE**: indica la velocità del motore quando è in rotazione, espressa in giri al minuto (rpm);
4. **COMANDI**: pulsanti per l'avvio del motore avanti o indietro. Le loro icone possono cambiare in funzione allo scopo del motore.

| Icona | Funzione |
| --- | --- |
| ![Rotazione antioraria](src/img/rotazioneAntioraria.png) | Indica l'azione di rotazione in senso antiorario di un motore. |
| ![Rotazione oraria](src/img/rotazioneOraria.png) | Indica l'azione di rotazione in senso orario di un motore. |
| ![Movimento da sinistra a destra](src/img/movimentoSinistraDestra.png) | Indica il movimento da sinistra verso destra. |
| ![Movimento da destra a sinistra](src/img/movimentoDestraSinistra.png) | Indica il movimento da destra verso sinistra. |

#### 3.4.3 Motore controllato in posizione

![Comando Motore Controllato in Posizione](src/img/comandoMotoreControllatoPosizione.png)

*Immagine: Comando Motore Controllato in Posizione.*

Cliccando uno dei simboli associati, nello SPAZIO DATI viene visualizzata la seguente interfaccia. Da qui è possibile attivare manualmente il dispositivo, monitorarne la posizione e la velocità e regolarne i limiti.

1. **DESCRIZIONE**: descrizione del componente;
2. **OVERRIDE VELOCITÀ**: tramite questo cursore è possibile regolare la velocità in percentuale rispetto a quella nominale (0-100%);
3. **VELOCITÀ CORRENTE**: indica la velocità del motore quando è in rotazione, espressa in giri al minuto (rpm);
4. **POSIZIONE CORRENTE**: indica la posizione attuale dell'asse, espressa in millimetri (mm);
5. **STATO CORSA**: mostra lo stato dei sensori di extracorsa;
6. **COMANDI**: pulsanti per l'avvio del motore avanti o indietro. Quando l'asse raggiunge un limite software o di extracorsa, il comando verrà disabilitato automaticamente;
7. **IMPOSTA POSIZIONE ASSOLUTA**: modificando il valore all'interno della casella di testo entro i limiti indicati, e premendo l'icona di conferma, è possibile impostare la posizione assoluta dell'asse;
8. **POSIZIONE DI DESTINAZIONE**: modificando il valore all'interno della casella di testo entro i limiti indicati, è possibile impostare la posizione di target dell'asse. Al rilascio del pulsante di conferma verrà eseguito un movimento automatico verso la posizione di target;
9. **REGOLAZIONE FINECORSA**: modificando i valori all'interno delle caselle di testo entro i limiti indicati, è possibile regolare i finecorsa software dell'asse.

#### 3.4.4 Override robot

![Comando Motori Coordinati](src/img/comandoOverrideRobot.png)

*Immagine: Comando Motori Coordinati.*

Cliccando uno dei simboli associati, nello SPAZIO DATI viene visualizzata la seguente interfaccia. Tramite questa è possibile monitorare e regolare l'override della velocità di un robot.

1. **DESCRIZIONE**: descrizione del robot;
2. **OVERRIDE VELOCITÀ**: tramite questo cursore è possibile pre-impostare il valore dell'override;
3. **VELOCITÀ CORRENTE**: indica il valore corrente dell'override di velocità;
4. **COMANDO SET OVERRIDE**: una volta regolata la velocità tramite cursore, è possibile applicare il valore impostato tramite questo pulsante.

#### 3.4.5 Stato della sequenza

![Stato della Sequenza](src/img/statoSequenza.png)

*Immagine: Stato della Sequenza.*

La visualizzazione offre una descrizione sintetica sullo stato corrente della sequenza a livello di processo, e consente di eseguire un ripristino per riportare la sequenza alle condizioni iniziali dopo un'interruzione.

1. **DESCRIZIONE**: descrizione della sequenza e dei dispositivi coinvolti;
2. **STATO DELLA SEQUENZA**: identificativo dello stato attuale. Questo valore varia tra le sequenze dell'impianto e rappresenta il passo logico gestito dal PLC (Init, Run, Move, End, …);
3. **COMANDO DI RESET**: comando di ripristino della sequenza. È abilitato solo se l'impianto è in modalità manuale e il livello attuale dell'utente è ESPERTO.

Attivando il COMANDO DI RESET compare un pop-up di conferma dell'azione.

![Pop-up Conferma Reset Sequenza](src/img/popupResetSequenza.png)

*Immagine: Pop-up Conferma Reset Sequenza.*

#### 3.4.6 Stato comunicazione robot

In ogni zona in cui è presente un robot, compare nello SPAZIO DATI la sezione Stato della comunicazione. Qui viene visualizzato lo stato corrente della comunicazione con il robot ed è possibile ripristinarla manualmente nel caso in cui non sia attiva.

![Stato di Comunicazione Robot](src/img/statoComunicazioneRobot.png)

*Immagine: Stato di Comunicazione Robot.*

1. **STATO**: questo indicatore cambia colore a seconda dello stato della comunicazione con il robot;
   - **VERDE**: comunicazione attiva;
   - **GIALLO**: comunicazione in fase di inizializzazione;
   - **ROSSO**: comunicazione interrotta;
   - **GRIGIO**: informazione assente.
2. **RIAVVIO COMUNICAZIONE**: permette di riavviare la comunicazione con il robot.

### 3.5 Informazioni di sistema

Le seguenti icone sono visibili nella sezione INFORMAZIONI DI SISTEMA, e danno informazioni riguardanti lo stato fisico dell'impianto quali:

- Stato delle sicurezze;
- Modalità di Lavoro;
- Stato dei dispositivi di sicurezza.

![Informazioni di Sistema](src/img/informazioniSistema.png)

*Immagine: Informazioni di Sistema.*

#### 3.5.1 Stati principali

| Icona | Funzione |
| --- | --- |
| ![Sistema in emergenza](src/img/statoEmergenza.png) | Sistema in emergenza. |
| ![Sistema in allarme](src/img/statoAllarme.png) | Sistema in allarme. |
| ![Sistema in allerta](src/img/statoAllerta.png) | Sistema in allerta. |
| ![Sistema in manuale](src/img/statoManuale.png) | Sistema in manuale. |
| ![Sistema automatico](src/img/statoAutomatico.png) | Sistema automatico. |
| ![Sistema automatico fermo](src/img/statoAutomaticoFermo.png) | Sistema automatico fermo. Questo stato si verifica quando si verifica un fermo impianto o quando un processo è terminato. |
| ![Pulsanti di emergenza premuti](src/img/sicurezzaEmergenzePremute.png) | Stato di sicurezza: Pulsanti di emergenza premuti. |
| ![Richieste di apertura cancello](src/img/sicurezzaRichiestaCancello.png) | Stato di sicurezza: Richieste di apertura cancello. |
| ![Barriere fotoelettriche](src/img/sicurezzaBarriere.png) | Stato di sicurezza: barriere fotoelettriche. |
| ![Cancelli perimetrali aperti](src/img/sicurezzaCancelliAperti.png) | Stato di sicurezza: Cancelli perimetrali aperti. |
| ![Tacito segnalazione acustica](src/img/tacitoSegnalazione1.png) ![Tacito segnalazione acustica](src/img/tacitoSegnalazione2.png) | Stato del tacito della segnalazione acustica. |

#### 3.5.2 Comunicazione con la pressa

| Icona | Funzione |
| --- | --- |
| ![Comunicazione attiva](src/img/comPressaAttiva.png) | Comunicazione attiva con il dispositivo. |
| ![Connesso e in attesa](src/img/comPressaAttesa.png) | Dispositivo connesso e in attesa. |
| ![Non connesso](src/img/comPressaNonConnesso.png) | Dispositivo non connesso. |
| ![Stato sconosciuto](src/img/comPressaSconosciuto.png) | Stato della comunicazione sconosciuto. |
| ![In connessione](src/img/comPressaConnessione.png) | Dispositivo in fase di connessione. |

#### 3.5.3 Comunicazione con i robot

| Icona | Funzione |
| --- | --- |
| ![Comunicazione attiva](src/img/comRobotAttiva.png) | Comunicazione attiva con il dispositivo. |
| ![Connesso e in attesa](src/img/comRobotAttesa.png) | Dispositivo connesso e in attesa. |
| ![Non connesso](src/img/comRobotNonConnesso.png) | Dispositivo non connesso. |
| ![Stato sconosciuto](src/img/comRobotSconosciuto.png) | Stato della comunicazione sconosciuto. |
| ![In connessione](src/img/comRobotConnessione.png) | Dispositivo in fase di connessione. |

#### 3.5.4 Comunicazione con i PLC

| Icona | Funzione |
| --- | --- |
| ![Comunicazione attiva](src/img/comPlcAttiva.png) | Comunicazione attiva con il dispositivo. |
| ![Connesso e in attesa](src/img/comPlcAttesa.png) | Dispositivo connesso e in attesa. |
| ![Non connesso](src/img/comPlcNonConnesso.png) | Dispositivo non connesso. |
| ![Stato sconosciuto](src/img/comPlcSconosciuto.png) | Stato della comunicazione sconosciuto. |
| ![In connessione](src/img/comPlcConnessione.png) | Dispositivo in fase di connessione. |

#### 3.5.5 Comunicazione con la punzonatrice

| Icona | Funzione |
| --- | --- |
| ![Comunicazione attiva](src/img/comPunzonatriceAttiva.png) | Comunicazione attiva con il dispositivo. |
| ![Connesso e in attesa](src/img/comPunzonatriceAttesa.png) | Dispositivo connesso e in attesa. |
| ![Non connesso](src/img/comPunzonatriceNonConnesso.png) | Dispositivo non connesso. |
| ![Stato sconosciuto](src/img/comPunzonatriceSconosciuto.png) | Stato della comunicazione sconosciuto. |
| ![In connessione](src/img/comPunzonatriceConnessione.png) | Dispositivo in fase di connessione. |

#### 3.5.6 Stato del robot

Viene visualizzata la casella che mostra il nome del robot e una copia degli indicatori di stato principali del robot presenti nel relativo terminale. Per una descrizione più dettagliata, fare riferimento al manuale d'uso del terminale del robot.

![Stato del Robot](src/img/statoRobot.png)

*Immagine: Stato del Robot.*

#### 3.5.7 Modalità operativa

L'impianto supporta due modalità operative:

- **MODALITÀ A – FULL AUTOMATIC**: l'impianto è impostato per ricevere i pezzi dalla punzonatrice esterna, piegarli e pallettizzarli.
- **MODALITÀ B – LOAD FROM INPUT BAY**: l'impianto è impostato per prelevare i pezzi dallo sfogliatore, piegarli e pallettizzarli.

Il cambio di modalità viene effettuato utilizzando il selettore su pulsantiera (Sezione E – "PULSANTIERA PULPITO DI COMANDO" del manuale), e ogni cambio dovrà essere confermato da pannello operatore.

![Controllo Modalità Operativa](src/img/controlloModalitaOperativa.png)

*Immagine: Controllo Modalità Operativa.*

Questo controllo nella sezione INFORMAZIONI DI SISTEMA permette di visualizzare la modalità operativa attiva, quella selezionata da selettore e di confermare la modalità selezionata da pulsantiera per renderla attiva.

1. **MODALITÀ ATTIVA**: visualizzazione della modalità attiva;
2. **MODALITÀ SELEZIONATA**: visualizzazione della modalità selezionata ma non ancora confermata;
3. **PULSANTE DI CONFERMA**: utilizzato per confermare la modalità selezionata e renderla attiva;
4. **STATO MODALITÀ**: descrive lo stato di conferma della modalità e, quando confermata, ne mostra la descrizione.

##### Procedura di cambio modalità

All'avvio dell'impianto nessuna modalità è attiva ed è necessario confermarla.

![Nessuna Modalità Attiva](src/img/nessunaModalitaAttiva.png)

*Immagine: Nessuna Modalità Attiva.*

Per confermare la modalità, utilizzare il PULSANTE DI CONFERMA.

![Nessuna Modalità Attiva](src/img/nessunaModalitaAttiva2.png)

*Immagine: Nessuna Modalità Attiva.*

Se la procedura di conferma è andata a buon fine la modalità selezionata apparirà come attiva e il PULSANTE DI CONFERMA non sarà più visibile.

![Modalità Attivata](src/img/modalitaAttivata.png)

*Immagine: Modalità Attivata.*

#### 3.5.8 Comandi richiesta di scarico

Nella sezione INFORMAZIONI DI SISTEMA sono presenti i comandi di richiesta scarico stazione. Questi comandi permettono di ruotare le tre stazioni in modo da consentirne il carico e lo scarico.

![Comandi Richiesta Scarico](src/img/comandiRichiestaScarico.png)

*Immagine: Comandi Richiesta Scarico.*

A seconda dello stato del comando i componenti visivi del controllo assumeranno diversi stati.

1. **STATO DEL COMANDO**: cambia colore a seconda dello stato del comando:
   - **GRIGIO**: comando non attivo;
   - **GIALLO/ROSSO (lampeggiante)**: la richiesta è stata attivata e il sistema è in attesa che il robot completi la lavorazione o che la stazione ruoti in posizione;
   - **VERDE**: il processo di richiesta è terminato e la stazione si trova nella posizione corretta di carico/scarico;
2. **DESCRIZIONE DELLO STATO**: descrive lo stato attuale del comando.

Questi comandi sono disponibili solo se vengono soddisfatti i seguenti requisiti:

- **Modalità**: l'impianto deve essere in modalità Manuale o Automatico con ciclo attivo;
- **Autenticazione**: l'utente deve essere loggato almeno come Operatore.

Alla pressione del pulsante appare un pop-up di conferma del comando.

![Pop-up Conferma Richiesta Scarico](src/img/popupConfermaRichiestaScarico.png)

*Immagine: Pop-up Conferma Richiesta Scarico.*

Una volta che il comando viene attivato la richiesta di scarico verrà inviata. Se la richiesta è stata inviata con successo allora lo STATO DEL COMANDO inizierà a lampeggiare.

![Comando in fase di avvio](src/img/richiestaScaricoAvvio.png) ![Comando in attesa di completamento](src/img/richiestaScaricoAttesa.png)

*Immagine: Comando in Fase di Avvio e in Attesa di Completamento.*

Quando il sistema ha completato la richiesta e la stazione si trova nella posizione di scarico/carico finale, lo STATO DEL COMANDO assume colore VERDE.

![Comando Completato](src/img/richiestaScaricoCompletato.png)

*Immagine: Comando Completato.*

![Comando richiesta scarico in manuale](src/img/richiestaScaricoManuale.png)

Quando il comando viene eseguito in modalità Manuale, il processo di rotazione della stazione inizierà solo quando la modalità dell'impianto passa in Automatico e il ciclo viene avviato.

### 3.6 Pagine standard

Di seguito vengono descritte le pagine standard. Ogni icona del MENU LATERALE è associata a una specifica pagina standard.

#### 3.6.1 Allarmi e segnalazioni

![Pagina Allarmi e Segnalazioni](src/img/paginaAllarmiSegnalazioni.png)

*Immagine: Pagina Allarmi e Segnalazioni.*

Qui sono riportati tutti gli allarmi e segnalazioni dell'impianto. È possibile filtrare le due tipologie tramite gli appositi pulsanti:

| Icona | Funzione |
| --- | --- |
| ![Filtra allarmi](src/img/filtraAllarmi.png) | Filtra gli allarmi dell'impianto. |
| ![Filtra segnalazioni](src/img/filtraSegnalazioni.png) | Filtra le segnalazioni dell'impianto. |

#### 3.6.2 Storico eventi

![Pagina Storico Eventi](src/img/paginaStoricoEventi.png)

*Immagine: Pagina Storico Eventi.*

Tutti gli allarmi e segnalazioni che non sono più attivi vengono registrati nello STORICO EVENTI. Sono mostrati in una tabella ordinata per orario. Utilizzando i filtri presenti nella pagina è possibile visualizzare nella tabella solo le informazioni desiderate.

- **Giorno**: in cui è avvenuta la segnalazione;
- **Dalle/Alle**: orario degli eventi;
- **Filtro zona**: zona dell'impianto.

| Icona | Funzione |
| --- | --- |
| ![Filtra per intervallo di tempo](src/img/filtraIntervalloTempo.png) | Filtra gli elementi a seconda dell'intervallo di tempo selezionato. |

#### 3.6.3 Manutenzione

![Pagina Manutenzione](src/img/paginaManutenzione.png)

*Immagine: Pagina Manutenzione.*

In questa pagina vengono elencate le manutenzioni ordinarie. Il limite entro il quale eseguire le manutenzioni può essere impostato a seconda del tipo di manutenzione, quantità di tempo, oppure distanza in chilometri. Ogni manutenzione presenta un titolo descrittivo, al fianco del quale è presente un contatore che misura da quanto non è stata eseguita la manutenzione.

1. **DESCRIZIONE**: descrizione della manutenzione e del componente interessato;
2. **CONTATORE**: valore corrente dello stato di usura del componente;
3. **STATO**: indica lo stato della manutenzione tramite i colori:
   - **VERDE**: Manutenzione eseguita;
   - **GIALLO**: Avviso manutenzione in scadenza;
   - **ROSSO**: Manutenzione scaduta.
4. **COMANDO EFFETTUA MANUTENZIONE**: premendo questo pulsante appare il pop-up che permette di confermare l'esecuzione della manutenzione;
5. **ULTIMA MANUTENZIONE**: indica il valore di usura di quando è stata eseguita l'ultima manutenzione;
6. **PROSSIMA MANUTENZIONE**: indica tra quanto si dovrà effettuare la manutenzione.

![Pop-up manutenzione](src/img/popupManutenzione.png)

*Immagine: Pop-up manutenzione.*

#### 3.6.4 Impostazioni

![Pagina Impostazioni](src/img/paginaImpostazioni.png)

*Immagine: Pagina Impostazioni.*

Nella pagina Impostazioni è possibile accedere ai parametri di configurazione del sistema e visualizzare lo stato della comunicazione tra HMI e PLC. Questa comunicazione può essere interrotta e successivamente ripristinata per il campo PLC.

Sono inoltre disponibili le impostazioni per la regolazione della velocità di lavorazione automatica.

| Icona | Funzione |
| --- | --- |
| ![Gestione utenti](src/img/gestioneUtenti.png) | **Gestione utenti**: pulsante che consente di aggiungere o rimuovere utenti, nonché di modificare il livello utente. |
| ![Impostazioni HMI avanzate](src/img/impostazioniAvanzate.png) | **Impostazioni HMI avanzate**: pulsante a discrezione esclusiva dell'utente Sistec. |
| ![Import-export csv](src/img/importExportCsv.png) | **Import-export csv**: permette di aprire il popup contenente i pulsanti per l'importazione e/o l'esportazione delle ricette dal database. |
| ![Reset](src/img/reset.png) | **Reset**: riavvia le sequenze PLC e la comunicazione bus EtherCAT. |
| ![Sospendi](src/img/sospendi.png) ![Avvia](src/img/avvia.png) | **Avvia/Sospendi**: sospende la comunicazione OPCUA tra HMI e PLC. Il pulsante assume la simbologia di "Avvia" quando la comunicazione è attiva. |
| ![Stato del polling del MES](src/img/statoPollingMes.png) | **Stato del polling del MES**: pulsante che abilita il polling per ricevere e leggere le informazioni relative alle nuove produzioni in arrivo dal MES. |
| ![Cancella](src/img/cancellaTracking.png) | **Cancella**: ripristina tutti i tracking cancellando i dati della produzione al loro interno. |
| ![Italia](src/img/linguaItaliana.png) | **Italia**: imposta la lingua del programma in italiano. |
| ![USA](src/img/linguaInglese.png) | **USA**: imposta la lingua del programma in inglese. |
