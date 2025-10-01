document.addEventListener("DOMContentLoaded", function() {
    var typeStats = JSON.parse(document.getElementById('type-stats-month-data').textContent);
    // 甜甜圈圖：前5名
    var top5 = typeStats.slice(0, 5);
    var donutLabels = top5.map(item => item.restaurant_type || "未分類");
    var donutData = top5.map(item => item.count);
    var donutColors = ["#457b9d", "#a8dadc", "#f4a261", "#e76f51", "#2a9d8f"];
    var ctxDonut = document.getElementById('typeDonutChart').getContext('2d');
    new Chart(ctxDonut, {
        type: 'doughnut',
        data: {
            labels: donutLabels,
            datasets: [{
                data: donutData,
                backgroundColor: donutColors
            }]
        },
        options: {
            plugins: {
                legend: { position: 'bottom' }
            }
        }
    });

    // 橫條圖：所有類型
    var barLabels = typeStats.map(item => item.restaurant_type || "未分類");
    var barData = typeStats.map(item => item.count);
    var ctxBar = document.getElementById('typeBarChart').getContext('2d');
    new Chart(ctxBar, {
        type: 'bar',
        data: {
            labels: barLabels,
            datasets: [{
                label: "次數",
                data: barData,
                backgroundColor: "#457b9d"
            }]
        },
        options: {
            indexAxis: 'y',
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: { beginAtZero: true }
            }
        }
    });
});