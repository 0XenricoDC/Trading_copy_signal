# 📚 GUIDA COMPLETA TRADECOPY - Per Principianti Assoluti

> **Versione:** 1.0
> **Data:** Gennaio 2025
> **Livello:** Da Zero a Operativo

---

## 📋 INDICE

1. [Cos'è TradeCopy?](#1-cosè-tradecopy)
2. [Requisiti del Sistema](#2-requisiti-del-sistema)
3. [Installazione Software Necessari](#3-installazione-software-necessari)
4. [Configurazione Completa (.env)](#4-configurazione-completa-env)
5. [Struttura del Progetto Spiegata](#5-struttura-del-progetto-spiegata)
6. [Avvio del Sistema Passo per Passo](#6-avvio-del-sistema-passo-per-passo)
7. [Utilizzo della Web App](#7-utilizzo-della-web-app)
8. [Risoluzione Problemi Comuni](#8-risoluzione-problemi-comuni)
9. [Glossario Tecnico](#9-glossario-tecnico)

---

## 1. COS'È TRADECOPY?

### 🎯 In Parole Semplici

TradeCopy è un sistema che:
1. **Legge** segnali di trading da canali Telegram o FX Blue
2. **Interpreta** questi segnali (es: "BUY EURUSD @ 1.0850")
3. **Esegue** automaticamente gli ordini sui tuoi conti MetaTrader 5

### 🔄 Come Funziona (Schema Semplificato)

```
📱 Canale Telegram          🌐 FX Blue          👤 Tu (Manuale)
     "BUY GOLD"                Trade               Dashboard
          ↓                      ↓                    ↓
          └──────────────────────┴────────────────────┘
                                 ↓
                    ┌────────────────────────┐
                    │    🧠 TradeCopy        │
                    │   (Analizza e Decide)  │
                    └────────────────────────┘
                                 ↓
            ┌────────────────────┼────────────────────┐
            ↓                    ↓                    ↓
        💰 MT5 #1           💰 MT5 #2           💰 MT5 #N
       (Conto Demo)        (Conto Live)        (Altri conti)
```

### 💡 Caratteristiche Principali

| Funzionalità | Descrizione |
|--------------|-------------|
| Multi-Account | Gestisce 50+ conti MT5 contemporaneamente |
| Multi-TP | Divide gli ordini per più Take Profit |
| Real-time | Aggiornamenti in tempo reale via WebSocket |
| Sicuro | Password MT5 criptate, autenticazione JWT |
| Web Dashboard | Interfaccia grafica per gestire tutto |

---

## 2. REQUISITI DEL SISTEMA

### 💻 Hardware Minimo

| Componente | Minimo | Consigliato |
|------------|--------|-------------|
| CPU | 2 core | 4+ core |
| RAM | 4 GB | 8+ GB |
| Disco | 20 GB liberi | SSD 50+ GB |
| Internet | Stabile | Fibra/Bassa latenza |

### 🖥️ Sistema Operativo

> ⚠️ **IMPORTANTE**: MetaTrader 5 funziona SOLO su Windows!

- **Windows 10/11** (64-bit) - **OBBLIGATORIO** per MT5
- Docker Desktop per Windows (con WSL2)

### 📦 Software da Installare

1. **Docker Desktop** - Per eseguire database e servizi
2. **MetaTrader 5** - Per eseguire i trade
3. **Git** - Per scaricare il progetto (opzionale)
4. **Python 3.11+** - Solo se vuoi eseguire senza Docker
5. **Node.js 20+** - Solo per sviluppo frontend

---

## 3. INSTALLAZIONE SOFTWARE NECESSARI

### 3.1 Installare Docker Desktop

Docker è come una "scatola magica" che contiene tutto il necessario per far funzionare il programma senza installare mille cose.

#### Passo 1: Scarica Docker
1. Vai su: https://www.docker.com/products/docker-desktop/
2. Clicca "Download for Windows"
3. Salva il file `Docker Desktop Installer.exe`

#### Passo 2: Installa Docker
1. Doppio click sul file scaricato
2. Segui le istruzioni (clicca "Next" → "Next" → "Install")
3. **IMPORTANTE**: Quando chiede di abilitare WSL2, accetta!
4. Riavvia il computer quando richiesto

#### Passo 3: Verifica Installazione
1. Apri il Prompt dei Comandi (cerca "cmd" nel menu Start)
2. Scrivi: `docker --version`
3. Dovresti vedere qualcosa come: `Docker version 24.x.x`

```
✅ Se vedi la versione → Docker è installato correttamente
❌ Se vedi un errore → Riavvia il PC e riprova
```

### 3.2 Installare MetaTrader 5

#### Passo 1: Scarica MT5
1. Vai sul sito del tuo broker (es: IC Markets, Pepperstone, etc.)
2. Cerca "Download MetaTrader 5"
3. Oppure vai su: https://www.metatrader5.com/en/download

#### Passo 2: Installa MT5
1. Esegui il file scaricato
2. Segui le istruzioni di installazione
3. Alla fine, MT5 si aprirà automaticamente

#### Passo 3: Accedi al Tuo Conto
1. Inserisci le credenziali del tuo broker:
   - **Login**: Il numero del tuo conto (es: 12345678)
   - **Password**: La password del conto
   - **Server**: Il server del broker (es: "ICMarkets-Demo")
2. Clicca "Login"

> 💡 **Suggerimento**: Inizia SEMPRE con un conto DEMO per testare!

### 3.3 Configurare Python (Solo se Non Usi Docker)

> ℹ️ Questa sezione è opzionale se usi Docker

#### Windows:
1. Scarica da: https://www.python.org/downloads/
2. **IMPORTANTE**: Durante l'installazione, spunta "Add Python to PATH"
3. Verifica: apri cmd e scrivi `python --version`

---

## 4. CONFIGURAZIONE COMPLETA (.env)

### 🔑 Cos'è il File .env?

Il file `.env` è come un "foglio di istruzioni" che dice al programma:
- Come connettersi al database
- Come accedere a Telegram
- Quali chiavi di sicurezza usare

### 📝 Crea il Tuo File .env

#### Passo 1: Copia il Template
```bash
# Nel terminale, vai nella cartella docker:
cd C:\Users\gaiad\OneDrive\Desktop\coding\tradeCopy\docker

# Copia il file di esempio:
copy .env.example .env
```

#### Passo 2: Apri il File .env con un Editor
Puoi usare Notepad, ma consiglio **VS Code** o **Notepad++**

### 📋 GUIDA DETTAGLIATA A OGNI VARIABILE

---

#### 🗄️ CONFIGURAZIONE DATABASE

```env
POSTGRES_USER=tradecopy
POSTGRES_PASSWORD=tradecopy_secret
POSTGRES_DB=tradecopy
```

| Variabile | Cos'è | Cosa Scrivere | Esempio |
|-----------|-------|---------------|---------|
| `POSTGRES_USER` | Nome utente del database | Un nome a tua scelta | `tradecopy` |
| `POSTGRES_PASSWORD` | Password del database | **Password SICURA!** | `MiaPassword123!Forte` |
| `POSTGRES_DB` | Nome del database | Lascia così | `tradecopy` |

> ⚠️ **ATTENZIONE SICUREZZA**: Per un sistema in produzione (soldi veri), usa password di almeno 32 caratteri con lettere, numeri e simboli!

**Come Generare una Password Sicura:**
1. Vai su: https://passwordsgenerator.net/
2. Imposta lunghezza: 32
3. Copia la password generata

---

#### 🔐 CONFIGURAZIONE SICUREZZA

```env
SECRET_KEY=your-super-secret-key-change-in-production-min-32-chars
FERNET_KEY=your-fernet-key-generate-with-cryptography
```

##### SECRET_KEY - Chiave per i Token di Accesso

**Cos'è:** Una chiave segreta usata per creare i "biglietti d'ingresso" (token JWT) che permettono agli utenti di accedere.

**Come Generarla:**

**Metodo 1 - Online (più semplice):**
1. Vai su: https://generate-secret.vercel.app/32
2. Copia la stringa generata

**Metodo 2 - Con Python:**
```python
# Apri il terminale e scrivi:
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Esempio di SECRET_KEY valida:**
```
SECRET_KEY=<genera-una-chiave-casuale>
```

##### FERNET_KEY - Chiave per Criptare le Password MT5

**Cos'è:** Una chiave speciale che cripta (nasconde) le password dei tuoi conti MT5 nel database. Anche se qualcuno accede al database, non può leggere le password.

**Come Generarla:**

**Metodo 1 - Con Python (consigliato):**
```python
# Apri il terminale e scrivi:
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**Metodo 2 - Online:**
1. Vai su: https://fernetkeygen.com/
2. Copia la chiave generata

**Esempio di FERNET_KEY valida:**
```
FERNET_KEY=<genera-con-Fernet.generate_key()>
```

> ⚠️ **IMPORTANTE**: La FERNET_KEY ha un formato specifico (finisce sempre con `=`). Non inventarla, generala sempre!

---

#### 📱 CONFIGURAZIONE TELEGRAM

```env
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_SESSION_STRING=
```

Questa è la parte più importante! Telegram richiede credenziali speciali per leggere i messaggi dai canali.

##### Come Ottenere TELEGRAM_API_ID e TELEGRAM_API_HASH

**Passo 1: Vai su my.telegram.org**
1. Apri il browser
2. Vai su: https://my.telegram.org
3. Inserisci il tuo numero di telefono (con prefisso, es: +39 333 1234567)
4. Riceverai un codice su Telegram - inseriscilo

**Passo 2: Crea un'App**
1. Clicca su "API development tools"
2. Compila il form:
   - **App title**: `TradeCopy` (o quello che vuoi)
   - **Short name**: `tradecopy`
   - **Platform**: `Desktop`
   - **Description**: `Trade copying system`
3. Clicca "Create application"

**Passo 3: Copia le Credenziali**
Vedrai una pagina con:
- `api_id`: Un numero (es: `12345678`)
- `api_hash`: Una stringa (es: `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`)

**Esempio Configurazione:**
```env
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
```

##### Come Ottenere TELEGRAM_SESSION_STRING

La Session String è come un "ricordo" del tuo login Telegram, così il bot non deve chiederti il codice ogni volta.

**Metodo - Prima Esecuzione:**
1. Lascia `TELEGRAM_SESSION_STRING=` vuoto
2. Avvia il sistema (vedi sezione 6)
3. Guarda i log del container telegram:
   ```bash
   docker-compose logs telegram_listener
   ```
4. Vedrai un messaggio tipo:
   ```
   Session string: 1BVtsOKABu2....[stringa molto lunga]....==
   Save this session string to TELEGRAM_SESSION_STRING env var
   ```
5. Copia quella stringa INTERA
6. Incollala nel file .env:
   ```env
   TELEGRAM_SESSION_STRING=1BVtsOKABu2....[stringa molto lunga]....==
   ```
7. Riavvia il sistema

---

#### 🔧 ALTRE CONFIGURAZIONI

```env
DEBUG=true
REDIS_URL=redis://redis:6379/0
MT5_PATH=C:\Program Files\MetaTrader 5\terminal64.exe
```

| Variabile | Cos'è | Valore Consigliato |
|-----------|-------|-------------------|
| `DEBUG` | Mostra info dettagliate | `true` per test, `false` per produzione |
| `REDIS_URL` | Indirizzo del cache Redis | Lascia così (Docker lo gestisce) |
| `MT5_PATH` | Percorso di MT5 sul tuo PC | Il percorso dove hai installato MT5 |

**Come Trovare MT5_PATH:**
1. Trova l'icona di MetaTrader 5 sul desktop
2. Click destro → "Apri percorso file"
3. Copia il percorso completo del file `terminal64.exe`

---

### 📄 FILE .env COMPLETO DI ESEMPIO

```env
# ============================================
# TRADECOPY - CONFIGURAZIONE COMPLETA
# ============================================

# --- DATABASE ---
# Credenziali per PostgreSQL (il database)
POSTGRES_USER=tradecopy
POSTGRES_PASSWORD=CambiaQuesta!Password123Sicura
POSTGRES_DB=tradecopy

# --- SICUREZZA ---
# Chiave per firmare i token di accesso (min 32 caratteri)
SECRET_KEY=<genera-una-chiave-casuale>

# Chiave per criptare le password MT5 (genera con Fernet!)
FERNET_KEY=<genera-con-Fernet.generate_key()>

# --- TELEGRAM ---
# Ottieni da https://my.telegram.org
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6

# Lascia vuoto al primo avvio, poi copia dai log
TELEGRAM_SESSION_STRING=

# --- IMPOSTAZIONI ---
DEBUG=true
REDIS_URL=redis://redis:6379/0

# --- METATRADER 5 ---
# Percorso di MT5 (solo per esecuzione locale senza Docker)
MT5_PATH=C:\Program Files\MetaTrader 5\terminal64.exe
```

---

## 5. STRUTTURA DEL PROGETTO SPIEGATA

### 📁 Panoramica Cartelle

```
tradeCopy/
│
├── 📂 backend/          ← Il "cervello" del sistema (API)
│   ├── app/
│   │   ├── main.py      ← Punto di avvio del server
│   │   ├── config.py    ← Legge le impostazioni (.env)
│   │   ├── api/v1/      ← Tutti gli endpoint (URL)
│   │   ├── models/      ← Struttura del database
│   │   └── schemas/     ← Validazione dati
│   └── alembic/         ← Migrazioni database
│
├── 📂 workers/          ← I "lavoratori" che eseguono i trade
│   ├── celery_app.py    ← Configurazione coda lavori
│   ├── mt5/             ← Connessione a MetaTrader
│   ├── parsers/         ← Analizza i segnali
│   └── tasks/           ← Compiti da eseguire
│
├── 📂 telegram_listener/ ← Ascolta i canali Telegram
│   ├── main.py          ← Avvio listener
│   └── handlers/        ← Gestisce i messaggi
│
├── 📂 frontend/         ← L'interfaccia web (Dashboard)
│   ├── src/pages/       ← Le pagine della web app
│   └── src/components/  ← Componenti riutilizzabili
│
├── 📂 fxblue_bridge/    ← Integrazione FX Blue (Expert Advisor)
│   ├── TradeCopyReceiver.mq5
│   └── TradeCopySender.mq5
│
├── 📂 docker/           ← Configurazione Docker
│   ├── docker-compose.yml
│   └── .env.example
│
└── 📄 README.md         ← Documentazione base
```

### 🔍 Spiegazione Dettagliata di Ogni Componente

#### 1. Backend (FastAPI) - Il Cervello 🧠

**Cos'è:** Un server web che:
- Gestisce gli utenti (login, registrazione)
- Salva e recupera dati dal database
- Comunica con il frontend
- Riceve segnali e li passa ai worker

**File Importanti:**
- `main.py` - Avvia il server sulla porta 8000
- `config.py` - Legge tutte le variabili dal file .env
- `api/v1/auth.py` - Login e registrazione
- `api/v1/channels.py` - Gestione canali Telegram
- `api/v1/mt5_accounts.py` - Gestione conti MT5
- `api/v1/trades.py` - Storico dei trade

#### 2. Workers (Celery) - I Lavoratori 👷

**Cos'è:** Processi in background che:
- Analizzano i segnali ricevuti
- Si connettono ai conti MT5
- Eseguono gli ordini di trading
- Sincronizzano saldi e posizioni

**File Importanti:**
- `celery_app.py` - Configura la coda dei lavori
- `mt5/connector.py` - Si connette a MetaTrader
- `mt5/executor.py` - Esegue i trade
- `parsers/regex_parser.py` - Capisce i segnali testuali

#### 3. Telegram Listener - Le Orecchie 👂

**Cos'è:** Un client Telegram che:
- Si connette come il tuo account
- Monitora i canali che specifichi
- Rileva i nuovi messaggi
- Passa i segnali al backend

**File Importanti:**
- `main.py` - Avvia il client Telethon
- `handlers/signal_handler.py` - Processa i messaggi

#### 4. Frontend (React) - La Faccia 😊

**Cos'è:** Un sito web dove puoi:
- Vedere la dashboard con statistiche
- Aggiungere canali Telegram
- Configurare conti MT5
- Monitorare i trade

**Pagine Principali:**
- Dashboard - Panoramica generale
- Channels - Gestisci canali Telegram
- Accounts - Gestisci conti MT5
- Subscriptions - Collega canali a conti
- Trades - Storico operazioni

#### 5. FX Blue Bridge - Il Ponte 🌉

**Cos'è:** Expert Advisor per MetaTrader che:
- Riceve segnali da FX Blue
- Invia i tuoi trade a FX Blue

**File:**
- `TradeCopyReceiver.mq5` - Riceve da FX Blue
- `TradeCopySender.mq5` - Invia a FX Blue

---

## 6. AVVIO DEL SISTEMA PASSO PER PASSO

### 🚀 Metodo 1: Con Docker (CONSIGLIATO)

#### Passo 1: Apri il Terminale
1. Premi `Win + R`
2. Scrivi `cmd` e premi Invio
3. Naviga alla cartella del progetto:
```bash
cd C:\Users\gaiad\OneDrive\Desktop\coding\tradeCopy\docker
```

#### Passo 2: Verifica il File .env
```bash
# Assicurati che esista il file .env
dir .env
```
Se non esiste, crealo (vedi sezione 4).

#### Passo 3: Avvia i Servizi
```bash
docker-compose up -d
```

**Cosa succede:**
- Docker scarica le immagini necessarie (la prima volta ci vuole un po')
- Avvia tutti i container
- Il flag `-d` lo fa girare in background

#### Passo 4: Verifica che Tutto Funzioni
```bash
# Vedi lo stato dei container
docker-compose ps
```

Dovresti vedere qualcosa tipo:
```
NAME                      STATUS
tradecopy_postgres        Up
tradecopy_redis           Up
tradecopy_api             Up
tradecopy_celery_worker   Up
tradecopy_celery_beat     Up
tradecopy_telegram        Up
tradecopy_frontend        Up
```

> ✅ Se tutti dicono "Up" → Tutto OK!
> ❌ Se qualcuno dice "Exited" → C'è un problema (vedi log)

#### Passo 5: Esegui le Migrazioni Database
```bash
docker-compose exec api alembic upgrade head
```

Questo crea le tabelle nel database.

#### Passo 6: Accedi alla Web App
1. Apri il browser
2. Vai su: http://localhost:3000
3. Registra un nuovo account
4. Inizia a configurare!

### 📊 Comandi Utili Docker

```bash
# Vedere i log di un servizio
docker-compose logs api
docker-compose logs telegram_listener
docker-compose logs celery_worker

# Seguire i log in tempo reale
docker-compose logs -f api

# Riavviare un servizio
docker-compose restart api

# Fermare tutto
docker-compose down

# Fermare e cancellare i dati
docker-compose down -v
```

---

## 7. UTILIZZO DELLA WEB APP

### 7.1 Primo Accesso

1. **Vai su:** http://localhost:3000
2. **Clicca:** "Sign up" o "Registrati"
3. **Inserisci:**
   - Email (anche inventata per test)
   - Password (min 8 caratteri)
4. **Clicca:** "Create account"

### 7.2 Aggiungere un Canale Telegram

1. **Vai su:** Menu → Channels
2. **Clicca:** "Add Channel"
3. **Inserisci:**
   - **Channel ID**: L'ID numerico del canale (vedi sotto come trovarlo)
   - **Channel Name**: Un nome a tua scelta
4. **Clicca:** "Add"

**Come Trovare l'ID di un Canale Telegram:**
1. Vai su Telegram
2. Cerca il bot `@getidsbot`
3. Inoltra un messaggio dal canale al bot
4. Il bot ti risponderà con l'ID (es: `-1001234567890`)

### 7.3 Aggiungere un Conto MT5

1. **Vai su:** Menu → MT5 Accounts
2. **Clicca:** "Add Account"
3. **Inserisci:**
   - **Name**: Nome descrittivo (es: "Conto Demo IC Markets")
   - **Login**: Numero del conto MT5
   - **Password**: Password del conto
   - **Server**: Nome del server broker
   - **Is Demo**: Spunta se è un conto demo
4. **Clicca:** "Add Account"
5. **Test:** Clicca l'icona "🔄" per testare la connessione

### 7.4 Creare una Subscription (Collegamento)

Una subscription collega un canale a un conto MT5.

1. **Vai su:** Menu → Subscriptions
2. **Clicca:** "New Subscription"
3. **Scegli:**
   - **Channel**: Il canale da monitorare
   - **MT5 Account**: Il conto su cui eseguire
   - **Lot Size**: Dimensione dei lotti (es: 0.01)
   - **TP Strategy**: Come dividere i Take Profit
4. **Clicca:** "Create"

### 7.5 Monitorare i Trade

1. **Dashboard**: Vedi statistiche generali
2. **Signals**: Vedi i segnali ricevuti
3. **Trades**: Vedi i trade eseguiti

---

## 8. RISOLUZIONE PROBLEMI COMUNI

### ❌ "Docker non parte"

**Sintomo:** `docker-compose up` dà errore

**Soluzioni:**
1. Assicurati che Docker Desktop sia avviato (icona nella tray)
2. Riavvia Docker Desktop
3. Riavvia il computer
4. Verifica WSL2: `wsl --status`

### ❌ "Container api esce subito"

**Sintomo:** Il container api dice "Exited"

**Debug:**
```bash
docker-compose logs api
```

**Cause Comuni:**
- File .env mancante o con errori
- SECRET_KEY o FERNET_KEY non valide
- Errore di sintassi nel .env

### ❌ "Telegram non si connette"

**Sintomo:** telegram_listener continua a riavviarsi

**Debug:**
```bash
docker-compose logs telegram_listener
```

**Cause Comuni:**
- TELEGRAM_API_ID/HASH errati
- Numero di telefono già usato in altra app
- Necessita di inserire codice di verifica

**Soluzione per il Codice:**
1. Ferma il container: `docker-compose stop telegram_listener`
2. Esegui manualmente per inserire il codice:
   ```bash
   docker-compose run telegram_listener python -m telegram_listener.main
   ```
3. Inserisci il codice quando richiesto
4. Copia la session string dai log
5. Aggiorna .env e riavvia

### ❌ "MT5 non si connette"

**Sintomo:** Test connessione fallisce

**Cause Comuni:**
- Login/Password/Server errati
- MT5 non installato (per worker locali)
- Broker non supporta API

**Verifica Credenziali:**
1. Apri MetaTrader 5 manualmente
2. Prova a fare login con le stesse credenziali
3. Verifica il nome esatto del server

### ❌ "Frontend non carica"

**Sintomo:** http://localhost:3000 non risponde

**Soluzioni:**
1. Attendi 1-2 minuti (il build iniziale è lento)
2. Verifica: `docker-compose logs frontend`
3. Prova: `docker-compose restart frontend`

---

## 9. GLOSSARIO TECNICO

| Termine | Spiegazione Semplice |
|---------|---------------------|
| **API** | Un "cameriere" che porta richieste dal frontend al backend |
| **Backend** | Il "cervello" nascosto che fa i calcoli |
| **Celery** | Un sistema per eseguire lavori in background |
| **Container** | Una "scatola" isolata dove gira un programma |
| **Database** | Un "archivio" dove si salvano tutti i dati |
| **Docker** | Un programma che crea e gestisce container |
| **Endpoint** | Un indirizzo URL specifico dell'API |
| **ENV / .env** | File con le "impostazioni segrete" |
| **FastAPI** | Il framework Python usato per creare l'API |
| **Fernet** | Un metodo per criptare (nascondere) le password |
| **Frontend** | La parte visibile del sito web |
| **JWT** | Un "biglietto" digitale per accedere al sistema |
| **Lot** | L'unità di misura per la dimensione di un trade |
| **Migration** | Aggiornamento della struttura del database |
| **MT5** | MetaTrader 5, il programma per fare trading |
| **PostgreSQL** | Il tipo di database usato |
| **React** | Il framework usato per creare il frontend |
| **Redis** | Un database veloce usato come "memoria temporanea" |
| **REST** | Lo stile di comunicazione dell'API |
| **Session String** | Un "ricordo" del login Telegram |
| **Subscription** | Il collegamento tra un canale e un conto |
| **Take Profit (TP)** | Il prezzo a cui chiudere in profitto |
| **Stop Loss (SL)** | Il prezzo a cui chiudere in perdita |
| **WebSocket** | Una connessione "sempre aperta" per aggiornamenti real-time |
| **Worker** | Un processo che esegue lavori in background |

---

## 📞 SUPPORTO

Se hai problemi:

1. **Controlla i log:** `docker-compose logs [servizio]`
2. **Leggi gli errori:** Spesso indicano la soluzione
3. **Cerca online:** Copia l'errore su Google
4. **GitHub Issues:** Apri una issue sul repository

---

## ✅ CHECKLIST FINALE

Prima di iniziare, assicurati di aver:

- [ ] Installato Docker Desktop
- [ ] Installato MetaTrader 5
- [ ] Creato il file .env nella cartella docker/
- [ ] Configurato POSTGRES_PASSWORD (password sicura)
- [ ] Generato SECRET_KEY (32+ caratteri)
- [ ] Generato FERNET_KEY (con Python/Fernet)
- [ ] Ottenuto TELEGRAM_API_ID da my.telegram.org
- [ ] Ottenuto TELEGRAM_API_HASH da my.telegram.org
- [ ] Eseguito `docker-compose up -d`
- [ ] Eseguito le migrazioni database
- [ ] Creato un account sulla web app
- [ ] Aggiunto almeno un canale Telegram
- [ ] Aggiunto almeno un conto MT5 (demo per test!)
- [ ] Creato una subscription

---

**Buon Trading! 📈**

*Questa guida è stata creata per rendere TradeCopy accessibile a tutti, anche a chi non ha mai programmato.*
