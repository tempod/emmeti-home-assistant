# emmeti_aqiot
Integrazione Febos Emmeti Su Home Assistant

L'integrazione importa i dati dalla webapp emmeti e crea sensori, switch, timer, sensori binari, ecc con le entità trovate e ne permette la modifica tramite l'interfaccia di Home Assistant.
# Funazioni principali
- Dati di accesso alla web app emmeti impostabili tramite interfaccia
- Timer di polling regolabile tramite interfaccia (minimo 10 secondi, 30 valore consigliato) 
- Riconnessione automatica allo scadere del token
- Invio multiplo dei dati modificati
    - data l'esterma lentazza della webapp può capitare che il comando impartito non venga recepito. L'integrazione, alla ricezione di un          errore "400" tenta nuovamente l'invio dei dati dopo due secondi. Questo per 3 volte. Così facendo dovrebbe essere garantita la               ricezione del valore
