# WiFi Sentinel

**WiFi Sentinel** è un sistema di sicurezza IoT, in esecuzione su un dispositivo a cui gli utenti possono accedere, basato su microservizi Docker, progettato per rilevare attacchi **Evil Twin** sulle reti WiFi in tempo reale.

## Autori
* **Membri:** Carotenuto Giusy, D'Urso Nicola, Maraglino Marco, Putignano Michele

---

## Prerequisiti Hardware e Software
**IMPORTANTE:** Il sistema è progettato per funzionare in ambiente **Linux**.

### Sistema Operativo
* **Consigliato:** Linux nativo (Ubuntu, Debian, Kali), ma è possibile utilizzare una Macchina Virtuale con Linux guest.

### Requisiti di Rete (Monitor Mode)
Il modulo di monitoraggio necessita di una scheda di rete capace di supportare la **Monitor Mode**.
-   **Su Linux Nativo:** È sufficiente la scheda di rete wireless integrata (se supporta monitor mode).
-   **Su Macchina Virtuale:** È **obbligatorio** utilizzare un'antenna WiFi USB esterna collegata alla VM. Le schede integrate del PC host non vengono viste come interfacce WiFi dalla VM (ma come Ethernet), quindi non possono effettuare scansioni delle reti WiFi circostanti.

### Software
* Docker Desktop o Docker Engine
* Docker Compose

---

## Architettura
Il sistema è composto da 5 microservizi containerizzati:
1.  **Sentinel-Monitor:** Modulo dedicato allo sniffing di rete, configurato per catturare i pacchetti di annuncio tramite le librerie tcpdump e scapy.
2.  **Sentinel-Core:** Il cervello del sistema. Analizza i dati via MQTT, applica le strategie di sicurezza e gestisce le notifiche.
3.  **Sentinel-Web:** Dashboard di gestione (Flask) per visualizzare allarmi, gestire la Whitelist e gli utenti.
4.  **Sentinel-DB:** Database PostgreSQL per la persistenza dei dati.
5.  **MQTT Broker:** Canale di comunicazione asincrono tra Monitor e Core.

---

## Installazione e Avvio

### Metodo 1: Avvio dall'archivio ZIP
L'archivio consegnato contiene già tutti i file di configurazione necessari, incluso il token del bot Telegram.

1.  Estrarre l'archivio `Gruppo_XX.zip`.
2.  Entrare nella cartella del codice sorgente.
3.  Avviare il sistema:
    ```bash
    docker compose up --build
    ```

### Metodo 2: Avvio da GitHub
Se si sceglie di clonare la repository pubblica, mancherà il file delle configurazioni segrete.

1.  Clonare la repository:

2.  * Recuperare il file `.env` dall'archivio ZIP consegnato.
    * Copiarlo nella cartella principale del progetto clonato.

3.  Avviare il sistema:
    ```bash
    docker compose up --build
    ```

---

## Accesso al Sistema
Una volta avviati i container, la Dashboard Web è accessibile via browser.

* **URL:** `http://localhost:5000`, oppure l'indirizzo IP della macchina virtuale
* **Username:** `admin`
* **Password:** `admin`

*(Nota: Al primo avvio, se il DB è vuoto, lo script di init crea automaticamente questo utente).*

---

## Integrazione Telegram
Il sistema utilizza un **Bot Telegram** per le notifiche in tempo reale.
1.  Accedere alla Dashboard come utente loggato.
2.  Cliccare sul pulsante **"Collega Telegram"** nella barra di navigazione.
3.  Si aprirà Telegram: cliccare su **Avvia** per completare il collegamento.

**Bot ufficiale per i test:** `@Sentinel_sapd_bot`
*Per testare la ricezione notifiche, assicurarsi che il file .env contenga il token del bot telegram corretto.*
*Il file .env deve essere quello contenuto nel progetto zippato.*

---

## Funzionamento della Detection
Il sistema implementa una verifica basata su **Whitelist BSSID**.
1.  L'admin aggiunge le reti "sicure" alla Whitelist tramite la Dashboard (o con il pulsante rapido `➕`).
2.  Se Sentinel rileva un SSID noto (presente in Whitelist) ma trasmesso da un indirizzo MAC (BSSID) sconosciuto, scatta l'allarme.
3.  Viene generato un evento **EVIL_TWIN** sulla dashboard e inviata una notifica Telegram immediata.