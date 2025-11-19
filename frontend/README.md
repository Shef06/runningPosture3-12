# Frontend - Jump Analyzer Pro

Interfaccia utente Svelte per l'applicazione di analisi biomeccanica della corsa.

## Installazione

1. Installa le dipendenze:
```bash
npm install
```

## Avvio

```bash
npm run dev
```

L'applicazione sarà disponibile su `http://localhost:3000`

## Build per Produzione

```bash
npm run build
npm run preview
```

## Struttura

- `src/routes/+page.svelte` - Pagina principale
- `src/lib/components/BaselineUploader.svelte` - Componente per caricare i 5 video di baseline
- `src/lib/components/AnalysisUploader.svelte` - Componente per analizzare un nuovo video
- `src/routes/styles.css` - Stili globali

## Funzionalità

### BaselineUploader
- Permette di selezionare 5 video contemporaneamente
- Mostra l'elenco dei file selezionati
- Invia i video al backend per creare la baseline
- Mostra feedback sull'addestramento del modello

### AnalysisUploader
- Permette di selezionare un singolo video
- Mostra un'anteprima del video
- Invia il video al backend per l'analisi
- Visualizza l'anomaly score e il livello di anomalia con interpretazione

## Note

Assicurati che il backend Flask sia in esecuzione su `http://localhost:5000` prima di utilizzare l'applicazione.

