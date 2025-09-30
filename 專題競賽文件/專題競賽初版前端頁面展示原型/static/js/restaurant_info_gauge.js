// Chart.js 半圓形儀表板評論指標
window.addEventListener('DOMContentLoaded', function() {
  const indicatorData = [
    { label: '食物', value: 80, color: '#ff6384' },
    { label: '價錢', value: 90, color: '#4bc0c0' },
    { label: '服務', value: 90, color: '#36a2eb' },
    { label: '環境', value: 90, color: '#9966ff' }
  ];
  const container = document.getElementById('gauge-indicators');
  indicatorData.forEach((item, idx) => {
    const canvas = document.createElement('canvas');
    canvas.width = 160;
    canvas.height = 100;
    canvas.style.margin = '0 16px';
    container.appendChild(canvas);
    new Chart(canvas.getContext('2d'), {
      type: 'doughnut',
      data: {
        datasets: [{
          data: [item.value, 100-item.value],
          backgroundColor: [item.color, '#eaeaea'],
          borderWidth: 0
        }]
      },
      options: {
        rotation: -Math.PI,
        circumference: Math.PI,
        cutout: '70%',
        plugins: {
          legend: { display: false },
          tooltip: { enabled: false },
          datalabels: { display: false }
        },
        elements: {
          arc: { roundedCornersFor: 'end' }
        }
      },
      plugins: [{
        id: 'centerText',
        afterDraw: chart => {
          const ctx = chart.ctx;
          ctx.save();
          ctx.font = 'bold px Noto Sans TC, Arial';
          ctx.fillStyle = '#222';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillText(item.value + '%', canvas.width/2, canvas.height/2);
          ctx.font = '14px Noto Sans TC, Arial';
          ctx.fillStyle = '#444';
          ctx.fillText(item.label, canvas.width/2, canvas.height/2+28);
          ctx.restore();
        }
      }]
    });
  });
});
