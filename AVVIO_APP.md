# Guida all'Avvio dell'Applicazione

L'applicazione si avvia automaticamente in modalità BUILD se trova i file buildati, altrimenti in modalità DEV.

## Modalità BUILD (Automatica - File Statici)

**Comportamento predefinito**: Quando avvii il backend, se trova i file buildati del frontend, li serve automaticamente e apre il browser.

### Passi:

1. **Build del frontend** (se non già fatto):
   ```bash
   cd frontend
   npm run build
   ```

2. **Avvia il backend**:
   ```bash
   cd backend
   python app.py
   ```

Il backend cercherà automaticamente i file buildati. Se li trova:
- Servirà i file statici del frontend
- Aprira il browser automaticamente su `http://localhost:5000`

## Modalità DEV (Sviluppo)

Se i file buildati non vengono trovati, il backend si avvia in modalità DEV.

### Passi:

1. **Avvia il backend**:
   ```bash
   cd backend
   python app.py
   ```

2. **In un altro terminale, avvia il frontend**:
   ```bash
   cd frontend
   npm run dev
   ```

Il backend sarà disponibile su `http://localhost:5000` e il frontend su `http://localhost:3000`.

## Note

- La modalità BUILD cerca automaticamente i file buildati in diverse posizioni possibili:
  - `frontend/dist/` (priorità - Svelte puro con Vite)
  - `frontend/build/`
  - `frontend/.svelte-kit/output/client/` (per compatibilità con vecchi build)
  - `frontend/.svelte-kit/output/prerendered/` (per compatibilità con vecchi build)

- Se la directory di build non viene trovata, il backend si avvierà comunque in modalità DEV.

- Il progetto usa **Svelte puro** (non SvelteKit), quindi i file buildati vengono generati in `frontend/dist/` quando esegui `npm run build`.

