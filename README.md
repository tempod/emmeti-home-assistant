# emmeti_aqiot
Integrazione Febos Emmeti Su Home Assistant

L'integrazione importa i dati dalla webapp emmeti e crea sensori, switch, timer, sensori binari, ecc con le entità trovate e ne permette la modifica tramite l'interfaccia di Home Assistant.
![plancia](https://github.com/tempod/emmeti-home-assistant/blob/main/plancia.png)


# Funazioni principali
- Dati di accesso alla web app emmeti impostabili tramite interfaccia
- Timer di polling regolabile tramite interfaccia (minimo 10 secondi, 30 valore consigliato) 
- Riconnessione automatica allo scadere del token
- Invio multiplo dei dati modificati
    - data l'esterma lentazza della webapp può capitare che il comando impartito non venga recepito. L'integrazione, alla ricezione di un          errore "400" tenta nuovamente l'invio dei dati dopo due secondi. Questo per 3 volte. Così facendo dovrebbe essere garantita la               ricezione del valore
- Scansione automatica dei gruppi presenti nella webapp emmeti
    - l'integrazione esegue una scansione automatica per trovare tutti i gruppo presenti nella web app. se questa scansione non dovesse          andare a buon fine utilizza una lista di gruppi pre-inseriti. questi gruppi sono presenti nel file groups.json e presentano questa         nomenclatura "FB-AMB-DT@D13577@T44164". Se non corrispondo con la vostra installazione dovrete trovare i vostri e modificarli a         mano.
- Impostazione automatica dei registri
  - i registri trovati vengono impostati automaticamente con il sensore corretto su home assistant. Questo riguarda la MIA installazione.      Non ho avuto modo di fare test su altre instllazioni.
- l'aggiornamento dei valori richiede un po di tempo. può arrivare anche al doppio del valore di polling impostato
- NON TUTTI I REGISTRI SONO MAPPATI. Sono riuscito a identificare solo i registri della MIA installazione. Credo che i registri siano uguali per tutte le installazioni ma potrebbero cambiare i gruppi. Aprite un "ISSUE" e vedrò di aggiungerli appena posso.

# Installazione
Tramite HACS
- aggiungere il mio repository su hacs, tipo integrazione
- cercare emmeti-aqiot
- installare e riavviare home assistant
- andare su impostazioni --> dispositivi e servizi --> aggiungi integrazione --> cercare "emmeti aq-iot"
- installare e inserire le credenziali

Se tutto va a buon fine dovreste trovare tutte le entità che sono presenti sulla web app. Se questo non accade provate a cercare i vostri gruppi analizzando la web app con la funzione F12 di chrome e sostituendole con quelle presenti nel file groups.json come spiegato precedentemente (vedi immaggine gruppi.png per un chiarimento)

# AIUTO
Aiutiamoci a vicenda per migliorare l'integrazione con suggerimenti, pull request e fork perche l'app di emmeti fa veramente PENA!
