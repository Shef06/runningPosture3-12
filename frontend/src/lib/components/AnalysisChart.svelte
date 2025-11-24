<script>
    import { onMount, afterUpdate } from 'svelte';
    import Chart from 'chart.js/auto';
  
    export let data = [];
    export let labels = [];
    export let threshold = null;
    export let title = "Grafico";
    export let color = "#3b82f6";
  
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
  
      if (threshold !== null) {
        datasets.push({
          label: 'Baseline (Soglia)',
          data: new Array(data.length).fill(threshold),
          borderColor: '#ef4444',
          borderWidth: 2,
          borderDash: [5, 5],
          pointRadius: 0,
          fill: false
        });
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
  
  <div class="chart-container">
    <canvas bind:this={chartCanvas}></canvas>
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
    }
  </style>