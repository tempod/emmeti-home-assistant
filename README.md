# Emmeti AQ-IoT per Home Assistant

[![Release](https://img.shields.io/github/v/release/tempod/emmeti-home-assistant)](https://github.com/tempod/emmeti-home-assistant/releases)
[![Validate](https://github.com/tempod/emmeti-home-assistant/actions/workflows/validate.yml/badge.svg)](https://github.com/tempod/emmeti-home-assistant/actions/workflows/validate.yml)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz)
[![License](https://img.shields.io/github/license/tempod/emmeti-home-assistant)](LICENSE)

Integrazione **non ufficiale** per gli impianti Emmeti Febos, basata sulla webapp Emmeti AQ-IoT.

Legge periodicamente i dati dell'impianto e crea le entità corrispondenti in Home Assistant: temperature, umidità, potenze, setpoint, fasce orarie e comandi. I parametri modificabili nella webapp lo sono anche da Home Assistant, quindi puoi usarli in automazioni, scene e dashboard.

![plancia](plancia.png)

---

## Indice

- [Requisiti](#requisiti)
- [Installazione](#installazione)
- [Configurazione](#configurazione)
- [Trovare i codici dei gruppi](#trovare-i-codici-dei-gruppi)
- [Modificare gruppi e polling](#modificare-gruppi-e-polling)
- [Entità create](#entità-create)
- [Registri non mappati](#registri-non-mappati)
- [Corrispondenza fra entità e registri](#corrispondenza-fra-entità-e-registri)
- [Risoluzione dei problemi](#risoluzione-dei-problemi)
- [Aggiornare da una versione precedente](#aggiornare-da-una-versione-precedente)
- [Contribuire](#contribuire)
- [Immagini di brand](#immagini-di-brand)
- [Changelog](#changelog)
- [Licenza](#licenza)

---

## Requisiti

- Home Assistant 2025.2.4 o successivo
- Un account attivo sulla webapp Emmeti AQ-IoT (le stesse credenziali che usi sul sito)
- Un impianto Febos raggiungibile dalla webapp

L'integrazione comunica con i server Emmeti, non con l'impianto in locale: serve una connessione a Internet funzionante.

## Installazione

### Tramite HACS (consigliato)

1. In HACS, apri il menu in alto a destra e scegli **Repository personalizzati**
2. Incolla `https://github.com/tempod/emmeti-home-assistant`, categoria **Integrazione**
3. Cerca **Emmeti AQ-IoT** e installa
4. Riavvia Home Assistant

### Manualmente

Copia la cartella `custom_components/emmeti_aqiot` dentro la cartella `custom_components` della tua configurazione, poi riavvia Home Assistant.

## Configurazione

Vai su **Impostazioni → Dispositivi e servizi → Aggiungi integrazione** e cerca **Emmeti AQ-IoT**.

La procedura è in due passaggi.

**1. Credenziali.** Nome utente e password della webapp Emmeti, più l'intervallo di aggiornamento in secondi (10–300, valore consigliato 30). L'integrazione verifica subito le credenziali: se sono errate te lo dice qui, senza creare nulla.

**2. Gruppi.** Un elenco di codici, uno per riga. Sono l'equivalente delle zone e dei sottosistemi del tuo impianto, e vanno ricavati una volta sola dalla webapp — vedi la sezione seguente. Sono accettate anche liste separate da virgola; spazi e righe vuote vengono ignorati.

Al termine trovi un dispositivo per ogni gruppo, con le sue entità.

![gruppi](gruppi.png)

## Trovare i codici dei gruppi

L'API Emmeti **non espone un endpoint per elencare i gruppi**. L'endpoint dei dati realtime pretende la lista come parametro di ingresso e, se interrogato senza, risponde `NOT_FOUND`. I codici vanno quindi letti dalle chiamate che la webapp fa al proprio server.

Procedura:

1. Apri la webapp Emmeti in un browser da computer ed effettua l'accesso
2. Premi <kbd>F12</kbd> per aprire gli strumenti di sviluppo e vai nella scheda **Rete** (o *Network*)
3. Ricarica la pagina e attendi il caricamento della plancia
4. Cerca le richieste che contengono `realtime-data`
5. Nell'URL della richiesta trovi il parametro `input_group_list`: contiene l'elenco completo dei gruppi, separati da virgola

I codici hanno questa forma:

```
FB-AMB-DT@D13577@T44164
FB-AMB-SUMM@D13577@T44164
FB-HP-DT1@D13577@T44167
FB-HW-DT@D13577@T44165
FB-EP-SUMM@D13577@T44166
```

Il prefisso indica il sottosistema (`AMB` ambiente, `HP` pompa di calore, `HW` acqua calda sanitaria, `EP` energia), mentre le parti dopo `@` identificano il tuo impianto e il singolo dispositivo. **Sono diversi per ogni installazione**: non riutilizzare quelli di altri, creerebbero entità che non si aggiornano mai.

## Modificare gruppi e polling

**Impostazioni → Dispositivi e servizi → Emmeti AQ-IoT → Configura**

Da qui puoi cambiare l'intervallo di aggiornamento e l'elenco dei gruppi in qualsiasi momento. Aggiungi una riga per creare le entità di un nuovo gruppo, togline una per smettere di interrogarlo. Salvando, l'integrazione si ricarica da sola: non serve riavviare Home Assistant.

Se rimuovi un gruppo, le sue entità restano nel registro come *non disponibili*. Per eliminarle davvero vanno rimosse dalla pagina del dispositivo.

## Entità create

A seconda dei registri presenti in ciascun gruppo vengono create entità su cinque piattaforme:

| Piattaforma | Contenuto | Esempi |
|---|---|---|
| `sensor` | Valori in sola lettura | temperature, umidità, potenze, portata |
| `number` | Setpoint modificabili | comfort e attenuazione, temperature ACS, soglie umidità |
| `time` | Fasce orarie | inizio comfort e attenuazione, richieste ACS |
| `switch` | Comandi on/off | presenza, boost, on/off pompa di calore, freddo/caldo |
| `binary_sensor` | Stati on/off in lettura | eco acqua calda |

Alcune grandezze nascono dalla combinazione di due registri: i contatori di energia sono memorizzati a 32 bit su una coppia di registri a 16 bit, che l'integrazione ricompone in un unico sensore. Hanno `state_class` di tipo totale crescente e si possono collegare direttamente alla **dashboard Energia** di Home Assistant.

Oltre a questi, due sensori ricompongono i **contatori di energia a 32 bit** (energia prelevata dalla rete ed energia prodotta/immessa): il valore è spezzato su due registri e va ricomposto, quindi non sarebbe utilizzabile leggendoli singolarmente. Sono dichiarati con `state_class: total_increasing`, quindi si possono collegare direttamente alla **dashboard Energia** di Home Assistant.

Note sul comportamento:

- **Unità e scale automatiche.** Per i registri riconosciuti vengono impostati unità di misura, classe dispositivo e fattore di scala, così i valori compaiono già convertiti e lo storico è utilizzabile nei grafici.
- **Aggiornamento ottimistico.** Il valore che imposti viene mostrato subito, senza tornare al precedente in attesa del polling successivo. Se il server non lo conferma entro alcuni cicli, l'entità torna al valore reale.
- **Comandi ripetuti.** La webapp è lenta e talvolta risponde `400 Bad Response from device` pur avendo ricevuto una richiesta valida: in quel caso il comando viene ritentato dopo due secondi, fino a tre volte.
- **Riconnessione automatica.** Alla scadenza del token l'integrazione rifà il login da sola, sia in lettura sia in scrittura.

L'aggiornamento dei valori richiede tempo: dopo una modifica possono servire fino al doppio dell'intervallo di polling perché il dato torni dal server.

## Registri non mappati

**Non tutti i registri sono identificati.** Su una installazione tipica il server ne restituisce oltre centocinquanta, di cui una quarantina riconosciuti. I restanti sono valori grezzi di cui non si conosce ancora il significato.

Di default questi registri **non generano entità**: sarebbero un centinaio di sensori senza nome che scrivono uno stato a ogni ciclo di polling, appesantendo il database senza dare nulla in cambio. Su un impianto con otto gruppi significa oltre trecentomila righe al giorno risparmiate.

Se vuoi contribuire alla mappatura puoi attivarli da **Configura → Crea entità per i registri non identificati**. Compaiono con il codice al posto del nome e il valore non convertito, nella categoria Diagnostica in fondo alla pagina del dispositivo. Spegnendo di nuovo l'opzione le entità vengono rimosse automaticamente dal registro, senza lasciare voci orfane da cancellare a mano.

**L'opzione non serve per identificare i registri.** I due strumenti di lavoro — il log dei valori cambiati e la diagnostica scaricabile — leggono i dati grezzi e funzionano identici anche a opzione spenta.

### Identificare un registro

Attiva il log di debug in `configuration.yaml`. Ogni registro ha un proprio logger che ne porta il codice nel nome, e i logger sono gerarchici: puoi quindi scegliere quanto guardare.

**Tutti i registri, e nient'altro** — solo le righe `DELTA`, senza i messaggi di autenticazione, scrittura ed errori:

```yaml
logger:
  default: warning
  logs:
    custom_components.emmeti_aqiot.delta: debug
```

**Un solo registro**, quando ne stai inseguendo uno per ore e non vuoi il rumore degli altri:

```yaml
logger:
  default: warning
  logs:
    custom_components.emmeti_aqiot.delta.R8682: debug
```

Puoi elencarne quanti ne vuoi, uno per riga.

**Tutti tranne i più rumorosi**, accendendo il padre e zittendo i singoli figli. Corrente e sfasamento cambiano a ogni ciclo e da soli producono gran parte delle righe:

```yaml
logger:
  default: warning
  logs:
    custom_components.emmeti_aqiot.delta: debug
    custom_components.emmeti_aqiot.delta.R8112: warning
    custom_components.emmeti_aqiot.delta.R8113: warning
```

**Tutta l'integrazione**, cioè i `DELTA` più la diagnostica di funzionamento — tentativi di scrittura, rinnovi del token, letture ritentate. Serve quando indaghi un malfunzionamento, non una mappatura:

```yaml
logger:
  logs:
    custom_components.emmeti_aqiot: debug
```

A ogni ciclo l'integrazione scrive nel log **soltanto i registri il cui valore è cambiato**:

```
DELTA FB-AMB-DT@D13577@T44164 R8688 (Confort Riscaldamento): 2050 -> 2100 (+50)
DELTA FB-HP-DT1@D13577@T44167 R9034 (NON MAPPATO): 12 -> 13 (+1)
```

Il metodo è: modifica un parametro nella webapp Emmeti, poi guarda quale coppia gruppo/registro si è mossa. L'entità del salto rivela anche la scala — spostando un setpoint di 1 °C, `+10` significa decimi di grado, `+100` centesimi.

Per i registri elettrici funziona bene la prova del carico noto: accendi un forno o un bollitore per qualche minuto e osserva quali registri saltano e di quanto. È così che sono stati identificati la potenza assorbita e la corrente, distinguendole grazie al fattore di potenza che passa da 0,54 a riposo a 0,96 con un carico resistivo.

Un terzo metodo è il confronto con la webapp: la pagina *Analisi energie* impostata su un solo giorno fornisce valori in kWh che si possono confrontare con quanto sono cresciuti i contatori nello stesso intervallo. È così che sono stati riconosciuti i contatori a 32 bit.

### Segnalare un registro

Da **Impostazioni → Dispositivi e servizi → Emmeti AQ-IoT → Scarica diagnostica** ottieni un file JSON con una sezione `registri_non_mappati` già pronta, con credenziali e identificativo impianto oscurati. Allegarlo a una issue è il modo più rapido per farlo aggiungere.

## Corrispondenza fra entità e registri

Fino alla versione 1.0.x l'`entity_id` conteneva il codice del registro. Non è più così: gli identificativi ora derivano dal nome del dispositivo e dell'entità, molto più leggibili ma senza il codice. Il codice resta nell'`unique_id` e, dalla 1.3.0, è esposto anche come **attributo di stato** — lo vedi in Strumenti per sviluppatori → Stati, alle voci `registro` e `gruppo`.

Questa è la corrispondenza completa, utile per leggere il log dei `DELTA`:

| Entità | Registro | Piattaforma |
|---|---|---|
| Angolo di Sfasamento | `R8114` | `sensor` |
| Assorbimento ACS | `R8005` | `sensor` |
| Assorbimento PDC | `R8002` | `sensor` |
| Attenuazione Raffrescamento | `R8686` | `number` |
| Attenuazione Riscaldamento | `R8690` | `number` |
| Boost | `R8692` | `switch` |
| Confort Raffrescamento | `R8684` | `number` |
| Confort Riscaldamento | `R8688` | `number` |
| Corrente Assorbita | `R8112` | `sensor` |
| Deumidificatore | `R8682` | `binary_sensor` |
| Eco Hot Water | `R9073` | `binary_sensor` |
| Energia Prelevata dalla Rete | `R8106+R8107` | `sensor` |
| Energia Prodotta/Immessa | `R8101+R8102` | `sensor` |
| Freddo/Caldo | `R8683` | `switch` |
| Orario Attenuazione Raffrescamento | `R8687` | `time` |
| Orario Attenuazione Riscaldamento | `R8691` | `time` |
| Orario Confort Raffrescamento | `R8685` | `time` |
| Orario Confort Riscaldamento | `R8689` | `time` |
| Orario Richiesta 1 ACS | `R16493` | `time` |
| Orario Richiesta 2 ACS | `R16495` | `time` |
| PDC On/Off | `R16384` | `switch` |
| Portata | `R9120` | `sensor` |
| Potenza Compressore | `R9008` | `sensor` |
| Potenza Termica | `R9123` | `sensor` |
| Prelievo da Rete | `R8110` | `sensor` |
| Presenza | `R8676` | `switch` |
| Produzione Solare | `R8105` | `sensor` |
| Punto di Rugiada | `R8680` | `sensor` |
| Setpoint Umidita Raffrescamento | `R8660` | `number` |
| Setpoint Umidita Riscaldamento | `R8661` | `number` |
| Temp Mantenimento ACS | `R16497` | `number` |
| Temp Richiesta 1 ACS | `R16494` | `number` |
| Temp Richiesta 2 ACS | `R16496` | `number` |
| Temperatura Acqua Calda | `R8989` | `sensor` |
| Temperatura Attuale | `R8703` | `sensor` |
| Temperatura Attuale Acqua PDC | `R9052` | `sensor` |
| Temperatura Esterna | `R8986` | `sensor` |
| Temperatura Mandata | `R8987` | `sensor` |
| Temperatura Minima Radiante Acqua PDC | `R9042` | `sensor` |
| Temperatura Ritorno | `R8988` | `sensor` |
| Temperatura Target Acqua PDC | `R9051` | `sensor` |
| Tensione di Rete | `R8100` | `sensor` |
| Umidita Attuale | `R8704` | `sensor` |

I registri non presenti in questa tabella non sono ancora identificati: se attivi la relativa opzione compaiono come sensori diagnostici con il codice al posto del nome.

## Risoluzione dei problemi

**Credenziali non valide durante la configurazione.** Verifica di riuscire ad accedere alla webapp Emmeti con le stesse credenziali. L'integrazione usa esattamente quelle.

**`Il server ha risposto NOT_FOUND (Device)`.** Uno dei codici gruppo non è valido per il tuo impianto: un refuso, un gruppo rimosso, oppure codici copiati da un'altra installazione. Ricontrollali con la procedura F12 e correggili da **Configura**.

**Le entità restano non disponibili.** Di solito significa che il gruppo corrispondente non è più nell'elenco configurato, oppure che il server non risponde. Il log dell'integrazione riporta il motivo dell'ultimo aggiornamento fallito.

**Un valore impostato torna indietro dopo qualche secondo.** Il comando non è stato accettato dal dispositivo. Controlla il log: se compaiono ripetuti `Bad Response from device`, l'impianto sta rifiutando la scrittura, non è un problema di Home Assistant.

**I valori si aggiornano lentamente.** È il comportamento della webapp Emmeti, non dell'integrazione. Abbassare troppo l'intervallo di polling non aiuta e appesantisce solo i server.

## Aggiornare da una versione precedente

Le versioni precedenti leggevano i gruppi dal file `groups.json` incluso nell'integrazione, e tentavano una scoperta automatica che in realtà **non ha mai funzionato**: l'errore veniva silenziosamente ignorato e si ripiegava sempre su quel file, precompilato con i gruppi dell'autore.

Ora il file non esiste più e i gruppi si inseriscono dall'interfaccia. Se stavi usando una versione precedente:

- Le entità già esistenti **restano valide**: identificativi, storico e personalizzazioni sono preservati
- I nomi visualizzati cambiano, perché ora includono il nome del dispositivo come prefisso
- Se avevi modificato `groups.json`, incolla quei codici nel campo gruppi durante la configurazione o da **Configura**

Prima di aggiornare, come sempre, fai un backup.

## Contribuire

Segnalazioni, suggerimenti e pull request sono benvenuti — soprattutto per i registri non ancora identificati. Aiutiamoci a vicenda per migliorare l'integrazione, perché l'app di Emmeti fa veramente pena!

Questo progetto non è affiliato a Emmeti S.p.A. I marchi citati appartengono ai rispettivi proprietari.

## Immagini di brand

L'integrazione include le proprie immagini in `custom_components/emmeti_aqiot/brand/`. Da Home Assistant 2026.3 questi file hanno la precedenza sul CDN e non serve alcuna configurazione; su versioni precedenti vengono ignorati e resta l'icona generica, senza errori.

Sono otto file: `icon.png` / `icon@2x.png` e `logo.png` / `logo@2x.png` per il tema chiaro, con le rispettive varianti `dark_` per il tema scuro. Icona e logo portano entrambi la sigla AQ-IoT sotto il marchio; nelle varianti dark la sigla è in chiaro, così resta leggibile su entrambi i temi.

## Changelog

Le modifiche di ogni versione sono elencate in [CHANGELOG.md](CHANGELOG.md).

## Licenza

MIT — vedi [LICENSE](LICENSE).
