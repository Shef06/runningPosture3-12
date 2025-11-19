import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import { readFileSync, writeFileSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Plugin per iniettare il JavaScript inline nell'HTML
function inlineScriptPlugin() {
  return {
    name: 'inline-script',
    closeBundle() {
      const distPath = join(__dirname, 'dist');
      const htmlPath = join(distPath, 'index.html');
      const jsPath = join(distPath, 'assets', 'bundle.js');
      
      try {
        let html = readFileSync(htmlPath, 'utf-8');
        
        // Trova e inietta tutti i file CSS inline
        const cssMatches = html.match(/<link[^>]*href="([^"]*\.css)"[^>]*>/g);
        if (cssMatches) {
          cssMatches.forEach(linkTag => {
            const hrefMatch = linkTag.match(/href="([^"]+)"/);
            if (hrefMatch) {
              const cssPath = join(distPath, hrefMatch[1].replace(/^\.\//, ''));
              try {
                const css = readFileSync(cssPath, 'utf-8');
                html = html.replace(linkTag, `<style>${css}</style>`);
              } catch (e) {
                console.warn(`CSS file not found: ${cssPath}`);
              }
            }
          });
        }
        
        // Leggi e inietta il JavaScript inline
        try {
          if (!existsSync(jsPath)) {
            console.warn(`File JavaScript non trovato: ${jsPath}`);
            return;
          }
          
          let js = readFileSync(jsPath, 'utf-8');
          
          // Escapa solo i caratteri che possono causare problemi in HTML
          // 1. Escapa </script> per evitare chiusura prematura del tag (CRITICO)
          // Usa una regex più robusta che matcha </script> anche con spazi o altri caratteri
          js = js.replace(/<\/\s*script\s*>/gi, '<\\/script>');
          // Anche varianti senza spazio
          js = js.replace(/<\/script>/gi, '<\\/script>');
          
          // 2. Escapa <! per evitare che venga interpretato come commento HTML
          js = js.replace(/<!\[CDATA\[/g, '<\\![CDATA[');
          
          // 3. Per &, NON escappiamo perché dentro <script> non è necessario
          // Tuttavia, alcuni browser potrebbero interpretare & seguito da lettere come entità HTML
          // Soluzione: NON escappiamo & affatto - il browser moderno dovrebbe gestirlo correttamente
          
          // NOTA: Dentro un tag <script>, il contenuto non dovrebbe essere interpretato come HTML
          // Quindi & non dovrebbe essere un problema. Se il browser lo interpreta comunque,
          // potrebbe essere un bug del browser o un problema con il modo in cui iniettiamo il codice.
          
          // 4. Correggi eventuali &amp; seguiti da numeri o caratteri non validi (da build precedenti)
          // Questi dovrebbero essere & normali, non &amp;
          js = js.replace(/&amp;(?=[0-9&=\|^<>])/g, '&');
          // Correggi anche &amp;&amp; che dovrebbe essere &&
          js = js.replace(/&amp;&amp;/g, '&&');
          
          // Trova il tag script da sostituire
          const scriptPattern = /<script[^>]*src="[^"]*bundle\.js"[^>]*><\/script>/i;
          const scriptMatch = html.match(scriptPattern);
          
          if (scriptMatch) {
            // Usa replace con una funzione per costruire il nuovo tag in modo sicuro
            // Assicurati che il JavaScript non contenga </script> non escapato
            html = html.replace(scriptPattern, () => {
              // Verifica che non ci siano </script> non escapati nel JavaScript
              if (js.includes('</script>') && !js.includes('<\\/script>')) {
                console.warn('ATTENZIONE: Trovato </script> non escapato nel JavaScript!');
              }
              return '<script type="text/javascript">\n' + js + '\n</script>';
            });
          } else {
            // Fallback: prova pattern alternativi
            html = html.replace(
              /<script[^>]*src="[^"]*bundle\.js"[^>]*><\/script>/gi,
              () => '<script type="text/javascript">' + js + '</script>'
            );
          }
          
          // Rimuovi altri script esterni se presenti
          html = html.replace(
            /<script[^>]*src="[^"]*assets\/[^"]*\.js"[^>]*><\/script>/gi,
            ''
          );
          
          writeFileSync(htmlPath, html, 'utf-8');
          console.log('✓ JavaScript e CSS iniettati inline nell\'HTML');
        } catch (e) {
          console.error('Errore nell\'iniezione del JavaScript:', e);
          console.error('Percorso JS:', jsPath);
        }
      } catch (e) {
        console.error('Errore nella lettura dell\'HTML:', e);
      }
    }
  };
}

export default defineConfig({
  plugins: [
    svelte({
      compilerOptions: {
        // Disabilita features che potrebbero usare import.meta
        generate: 'dom'
      }
    }), 
    inlineScriptPlugin()
  ],
  base: './', // Usa percorsi relativi per funzionare con file://
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    // Configurazione per funzionare con file://
    rollupOptions: {
      output: {
        // Usa formato IIFE per compatibilità con file://
        format: 'iife',
        name: 'JumpAnalyzerApp',
        // Single bundle file
        entryFileNames: 'assets/bundle.js',
        chunkFileNames: 'assets/bundle.js',
        assetFileNames: 'assets/[name].[ext]',
        // Inlinea i dynamic imports
        inlineDynamicImports: true,
        // Rimuovi import.meta e altri costrutti ES6
        generatedCode: {
          constBindings: true
        }
      },
      // Plugin per rimuovere import.meta
      plugins: [{
        name: 'remove-import-meta',
        renderChunk(code) {
          // Sostituisci import.meta.url con una stringa vuota o valore di fallback
          return code.replace(/import\.meta\.url/g, '""');
        }
      }]
    },
    chunkSizeWarningLimit: 10000 // Aumentato perché tutto sarà in un file
  }
});

