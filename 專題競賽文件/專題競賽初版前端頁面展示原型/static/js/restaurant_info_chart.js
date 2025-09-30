// Chart.js 指標圖表初始化
window.addEventListener('DOMContentLoaded', function() {
  const ctx = document.getElementById('indicatorChart').getContext('2d');
  new Chart(ctx, {
    type: 'radar',
    data: {
      labels: ['食物', '價錢', '服務', '環境'],
      datasets: [{
        label: '指標分數',
        data: [4, 4, 5, 4], // 假資料
        backgroundColor: 'rgba(54, 162, 235, 0.2)',
        borderColor: 'rgba(54, 162, 235, 1)',
        borderWidth: 2
      }]
    },
    options: {
      scales: {
        r: {
          min: 0,
          max: 5,
          ticks: { stepSize: 1 }
        }
      }
    }
  });
});
