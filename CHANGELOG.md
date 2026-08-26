# Changelog

Il formato segue [Keep a Changelog](https://keepachangelog.com/it/1.1.0/) e il progetto usa il [versionamento semantico](https://semver.org/lang/it/).

## [1.2.0] - 2026-08-26

Identificate le grandezze elettriche del modulo FEBOS-Energy, corretta la natura di un registro e ricomposti i contatori di energia. I registri non identificati non generano più entità per impostazione predefinita.

### Cambiamenti che richiedono attenzione

- **`R8100` non è il consumo di casa: è la tensione di rete.** Su 1743 letture in una giornata resta fra 210,8 e 236,4 V, con media 225,6 e deviazione standard 3,7 V — l'andamento di una tensione, non di un consumo domestico, che varierebbe di ordini di grandezza. Il sensore cambia nome, unità e classe: automazioni e dashboard che lo usavano come potenza vanno riviste.
- **Rimosso il sensore duplicato della potenza assorbita.** `R9127` riportava la stessa grandezza di `R8110` con risoluzione dieci volte peggiore.
- **I registri non identificati non generano più entità.** Erano oltre cento sensori senza nome che scrivevano uno stato a ogni ciclo di polling; su un impianto con otto gruppi significa più di trecentomila righe al giorno nel database. Si riattivano da *Configura → Crea entità per i registri non identificati*. Spegnendo l'opzione le entità vengono rimosse automaticamente dal registro, senza lasciare voci orfane.

### Aggiunto

- **Energia prodotta/immessa** ed **energia prelevata dalla rete**, ricomposte da coppie di registri a 16 bit secondo `parola_alta × 65536 + parola_bassa`. Sono contatori totali crescenti, collegabili direttamente alla **dashboard Energia**. Verificati su due scale indipendenti: i totali storici e i consumi di una singola giornata, dove combaciano esattamente con la webapp (0,05 e 4,80 kWh).
- **Corrente assorbita** (`R8112`), che spiega un rapporto anomalo osservato in precedenza: con un forno acceso passa da 1,60 a 16,11 A, e il fattore di potenza calcolato rispetto alla potenza sale da 0,54 a 0,96 — coerente con un carico resistivo puro.
- **Tensione di rete** (`R8100`), al posto della precedente mappatura errata.
- **Angolo di sfasamento** (`R8114`), in gradi. Identificato per via fisica: il valore non supera mai 359 su oltre undicimila campioni, il suo coseno correla a +0,938 con il fattore di potenza calcolato dagli altri registri, e rispetta la disuguaglianza secondo cui il fattore di potenza reale non può superare il coseno dell'angolo. Con un carico resistivo puro passa da 337° a 351°, cioè da 0,92 a 0,99. Insieme a tensione, corrente e potenza completa il quadro elettrico del canale rete.
- **Opzione per le entità dei registri non identificati**, disattivata di default. Il log dei valori cambiati e la diagnostica scaricabile funzionano comunque, quindi il lavoro di mappatura non ne risente.

### Corretto

- **`R8707` non esiste**: era l'unico registro presente nella mappa e mai restituito dal server, quasi certamente un refuso per `R8703`. La correzione è stata verificata per via psicrometrica — il punto di rugiada calcolato da temperatura e umidità coincide con quello letto a sei centesimi di grado.
- **Messaggi di errore vuoti nel log**: i timeout producevano `Errore nel recuperare i dati:` senza alcuna causa, perché `str()` di un timeout restituisce una stringa vuota. Ora la causa è esplicita.
- **Errori di lettura transitori**: un singolo timeout rendeva non disponibili tutte le entità fino al ciclo successivo, facendo fallire le automazioni che le usavano. Ora la lettura viene ritentata.

### Verificato senza modifiche

- **`Assorbimento PDC` (`R8002`) e `Assorbimento ACS` (`R8005`)** erano già corretti. Sono potenze in watt, non energie: integrando `R8005` sulla giornata si ottengono 0,766 kWh contro i 0,76 dichiarati dalla webapp. Per avere i kWh giornalieri in Home Assistant serve un integrale di Riemann. Sono due dei quattro ingressi a impulsi del modulo FEBOS-Energy; gli altri due sono a zero.
- **`Prelievo da Rete` (`R8110`) e `Produzione Solare` (`R8105`)** erano corretti: l'integrazione di `R8110` sulla giornata dà 4,93 kWh contro i 4,80 della webapp.

### Modificato

- I dati del coordinator sono indicizzati per gruppo: con oltre centocinquanta entità la scansione lineare veniva ripetuta migliaia di volte a ogni aggiornamento.
- `actions/checkout` aggiornato alla versione 5 per il runtime Node 24.
- README ampliato con i metodi di identificazione dei registri effettivamente usati: log dei valori cambiati, prova del carico noto e confronto con la pagina *Analisi energie* della webapp.

## [1.1.0] - 2026-08-25

Revisione completa dell'integrazione: correzioni a bug che impedivano il funzionamento di alcune funzioni, allineamento alle API recenti di Home Assistant e nuove funzionalità di configurazione e diagnostica.

Le entità esistenti sono preservate: gli identificativi univoci non sono cambiati, quindi storico, personalizzazioni e appartenenza alle aree restano intatti. Cambiano i nomi visualizzati, che ora includono il nome del dispositivo come prefisso.

### Cambiamenti che richiedono attenzione

- **Rimosso `groups.json`.** I gruppi si configurano dall'interfaccia, sia in fase di installazione sia in seguito dalle opzioni. Chi aveva modificato il file deve incollare i propri codici nel campo dedicato. Il file conteneva i gruppi dell'installazione dell'autore, che su altri impianti generavano entità mai aggiornate.
- **Rimossa la scoperta automatica dei gruppi.** Non ha mai funzionato: l'endpoint interrogato richiede la lista dei gruppi come parametro e senza risponde `NOT_FOUND`. L'errore veniva silenziosamente ignorato e si ripiegava sempre su `groups.json`.
- **I nomi delle entità cambiano** per l'adozione di `has_entity_name`. Automazioni e dashboard che usano gli `entity_id` non sono interessate; vanno verificati eventuali template che filtrano per nome visualizzato.
- **I setpoint di comfort e attenuazione scrivono valori diversi da prima**, perché la scala era errata (vedi sotto). Automazioni tarate sul comportamento precedente vanno riviste.

### Corretto

- **L'options flow non era registrato**: mancava `async_get_options_flow` nel config flow, quindi il pulsante "Configura" non compariva e l'intervallo di polling non era modificabile dopo l'installazione.
- **Scala errata nei setpoint di temperatura** dei registri `R8684`, `R8686`, `R8688`, `R8690`: la lettura divideva per 100 e la scrittura moltiplicava per 10. Impostando 21 °C veniva scritto un valore rileggibile come 2,1 °C. Lettura e scrittura sono ora generate da un unico fattore di scala e non possono più divergere.
- **Errore di arrotondamento in tutte le scritture con passo 0,1**: `int(21.3 * 10)` restituisce 212 e non 213, perché il valore in virgola mobile è 212,99999. Ora si arrotonda prima di convertire.
- **Errori applicativi restituiti con status HTTP 200** non venivano riconosciuti. Il backend segnala i problemi nel corpo della risposta (`{"errCode": "NOT_FOUND", "code": -1}`); il dizionario veniva scambiato per dati validi e le piattaforme fallivano iterandolo. Ora viene riportato il messaggio del server.
- **Token scaduto durante una scrittura**: i tentativi successivi riusavano lo stesso token, fallendo tutti. Ora il login viene rifatto e il comando ritentato. Stessa gestione aggiunta in lettura.
- **Eccezione nelle entità orario** per registri fuori intervallo: un valore maggiore di 1439 o negativo faceva sollevare `ValueError` dentro una property, rendendo inutilizzabile l'entità. Ora il valore risulta sconosciuto.
- **Lettura di file bloccante nel loop degli eventi** durante la scoperta dei gruppi.
- **Accesso non protetto ai dati del coordinator** in alcune property, che poteva sollevare `TypeError` quando i dati non erano disponibili.

### Aggiunto

- **Gestione dei gruppi dall'interfaccia**: elenco modificabile in qualsiasi momento da Impostazioni → Dispositivi e servizi → Configura, con ricarica automatica dell'integrazione al salvataggio.
- **Aggiornamento ottimistico**: il valore impostato viene mostrato subito, senza tornare al precedente in attesa del polling. Se il server non lo conferma entro alcuni cicli, l'entità torna al valore reale.
- **Diagnostica scaricabile** con una sezione `registri_non_mappati` già pronta da allegare alle segnalazioni, con credenziali e identificativo impianto oscurati.
- **Log dei soli valori cambiati** in modalità debug, con nome del registro e delta, per identificare i registri sconosciuti e ricavarne la scala.
- **Traduzioni** italiano e inglese per la procedura di configurazione e le opzioni, prima assenti: i messaggi di errore comparivano come chiavi grezze.
- **Immagini di brand incluse** nell'integrazione, con varianti per tema chiaro e scuro. Da Home Assistant 2026.3 hanno la precedenza sul CDN.
- **Licenza MIT** e workflow di validazione automatica (hassfest e HACS) a ogni push.
- **Categoria diagnostica** per i registri non riconosciuti: restano attivi e con storico completo, ma non affollano più i sensori principali.
- **Campo password mascherato** nella schermata di configurazione.

### Modificato

- Compatibilità con le versioni recenti di Home Assistant: `config_entry` passato al coordinator, options flow senza il costruttore deprecato, `NumberDeviceClass` al posto della classe dei sensori, timeout `aiohttp` nella forma corrente.
- Nomi dei dispositivi leggibili ("Emmeti Ambiente DT") al posto del codice gruppo completo.
- Struttura interna riorganizzata: coordinator, classe base delle entità e utilità condivise in moduli dedicati, eliminando il codice duplicato nelle cinque piattaforme.
- README riscritto con procedura per ricavare i codici dei gruppi, tabella delle entità create e sezione di risoluzione dei problemi.

## [1.0.0]

Prima versione pubblica.
