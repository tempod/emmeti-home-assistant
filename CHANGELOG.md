# Changelog

Il formato segue [Keep a Changelog](https://keepachangelog.com/it/1.1.0/) e il progetto usa il [versionamento semantico](https://semver.org/lang/it/).

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
