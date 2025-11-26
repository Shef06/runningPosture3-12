<script>
    import { onMount, afterUpdate } from 'svelte';
    import Chart from 'chart.js/auto';
  
    export let data = [];
    export let labels = [];
    export let threshold = null;
    export let baselineMean = null;  // Media baseline
    export let baselineStd = null;   // Deviazione standard baseline
    export let title = "Grafico";
    export let color = "#3b82f6";
    export let onClick = null;  // Funzione callback per il click

    let chartCanvas;
    let chartInstance;

    function initChart() {
      if (chartInstance) chartInstance.destroy();
      if (!chartCanvas) return;

      const datasets = [{
        label: title,
        data: data,
        borderColor: color,
        backgroundColor: color + '20',
        borderWidth: 2,
        tension: 0.4,
        pointRadius: 0,
        fill: true
      }];

      // Linea baseline (media) - priorità su threshold se entrambi presenti
      const baselineValue = baselineMean !== null ? baselineMean : threshold;
      
      if (baselineValue !== null) {
        // Linea media baseline
        datasets.push({
          label: 'Baseline (Media)',
          data: new Array(data.length).fill(baselineValue),
          borderColor: '#10b981',
          borderWidth: 2,
          borderDash: [5, 5],
          pointRadius: 0,
          fill: false
        });

        // Linee ±1σ e ±2σ se disponibili
        if (baselineStd !== null) {
          // +1σ
          datasets.push({
            label: 'Baseline +1σ',
            data: new Array(data.length).fill(baselineValue + baselineStd),
            borderColor: '#f59e0b',
            borderWidth: 1,
            borderDash: [3, 3],
            pointRadius: 0,
            fill: false
          });

          // -1σ
          datasets.push({
            label: 'Baseline -1σ',
            data: new Array(data.length).fill(baselineValue - baselineStd),
            borderColor: '#f59e0b',
            borderWidth: 1,
            borderDash: [3, 3],
            pointRadius: 0,
            fill: false
          });

          // +2σ
          datasets.push({
            label: 'Baseline +2σ',
            data: new Array(data.length).fill(baselineValue + 2 * baselineStd),
            borderColor: '#ef4444',
            borderWidth: 1,
            borderDash: [2, 2],
            pointRadius: 0,
            fill: false
          });

          // -2σ
          datasets.push({
            label: 'Baseline -2σ',
            data: new Array(data.length).fill(baselineValue - 2 * baselineStd),
            borderColor: '#ef4444',
            borderWidth: 1,
            borderDash: [2, 2],
            pointRadius: 0,
            fill: false
          });
        }
      }
  
      chartInstance = new Chart(chartCanvas, {
        type: 'line',
        data: { labels, datasets },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: { intersect: false, mode: 'index' },
          plugins: { 
            legend: { labels: { color: '#94a3b8' } },
            tooltip: { enabled: true }
          },
          scales: {
            y: { 
              grid: { color: 'rgba(255,255,255,0.05)' }, 
              ticks: { color: '#94a3b8' },
              beginAtZero: true
            },
            x: { 
              grid: { display: false },
              ticks: { display: false }
            }
          }
        }
      });
    }
  
    onMount(initChart);
    afterUpdate(() => {
      if (data && chartCanvas) initChart();
    });
  </script>
  
  <div 
    class="chart-container" 
    class:clickable={onClick !== null}
    on:click={onClick || (() => {})}
    role={onClick ? "button" : undefined}
    tabindex={onClick ? 0 : undefined}
    on:keydown={(e) => {
      if (onClick && (e.key === 'Enter' || e.key === ' ')) {
        e.preventDefault();
        onClick();
      }
    }}
  >
    <canvas bind:this={chartCanvas}></canvas>
    {#if onClick}
      <div class="chart-overlay">
        <span class="expand-hint">👆 Clicca per ingrandire</span>
      </div>
    {/if}
  </div>
  
  <style>
    .chart-container {
      position: relative;
      height: 250px;
      width: 100%;
      background: rgba(15, 23, 42, 0.3);
      border-radius: 12px;
      padding: 1rem;
      border: 1px solid rgba(255, 255, 255, 0.05);
      transition: all 0.3s ease;
    }

    .chart-container.clickable {
      cursor: pointer;
    }

    .chart-container.clickable:hover {
      border-color: rgba(59, 130, 246, 0.5);
      background: rgba(15, 23, 42, 0.4);
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
    }

    .chart-overlay {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      background: rgba(0, 0, 0, 0.3);
      border-radius: 12px;
      opacity: 0;
      transition: opacity 0.3s ease;
      pointer-events: none;
    }

    .chart-container.clickable:hover .chart-overlay {
      opacity: 1;
    }

    .expand-hint {
      background: rgba(59, 130, 246, 0.9);
      color: white;
      padding: 0.5rem 1rem;
      border-radius: 8px;
      font-size: 0.85rem;
      font-weight: 600;
      backdrop-filter: blur(8px);
    }
  </style>