import App from './App.svelte';
import './routes/styles.css';

// Funzione helper per verificare se un errore è causato da estensioni del browser
function isExtensionError(error) {
  if (!error) return false;
  
  const errorString = typeof error === 'string' 
    ? error 
    : (error.message || error.toString() || '');
  
  const extensionErrorPatterns = [
    'message channel closed',
    'runtime.lastError',
    'Extension context invalidated',
    'A listener indicated an asynchronous response',
    'asynchronous response by returning true',
    'chrome-extension://',
    'moz-extension://',
    'safari-extension://'
  ];
  
  return extensionErrorPatterns.some(pattern => 
    errorString.toLowerCase().includes(pattern.toLowerCase())
  );
}

// Gestore globale degli errori per sopprimere errori innocui delle estensioni del browser
window.addEventListener('error', (event) => {
  if (isExtensionError(event.message) || isExtensionError(event.error)) {
    event.preventDefault();
    event.stopPropagation();
    return false;
  }
}, true); // Usa capture phase per catturare prima

// Gestore per promise rejection non gestite (errori delle estensioni)
window.addEventListener('unhandledrejection', (event) => {
  if (isExtensionError(event.reason)) {
    event.preventDefault();
    return false;
  }
});

// Gestore aggiuntivo per errori console (alcune estensioni loggano errori)
const originalConsoleError = console.error;
console.error = function(...args) {
  // Filtra errori delle estensioni dal console.error
  const hasExtensionError = args.some(arg => isExtensionError(arg));
  if (!hasExtensionError) {
    originalConsoleError.apply(console, args);
  }
};

// Assicurati che il DOM sia caricato prima di inizializzare
function initApp() {
  const target = document.getElementById('app');
  if (!target) {
    console.error('Elemento #app non trovato!');
    return;
  }
  
  const app = new App({
    target: target,
  });
  
  return app;
}

// Inizializza quando il DOM è pronto
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initApp);
} else {
  // DOM già caricato
  initApp();
}


