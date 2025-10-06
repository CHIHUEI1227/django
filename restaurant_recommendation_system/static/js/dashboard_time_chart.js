document.addEventListener("DOMContentLoaded", function() {
    var timeStats = JSON.parse(document.getElementById('time-stats-data').textContent);
    var mealTimes = ["breakfast", "lunch", "afternoon_tea", "dinner", "late_night"];
    var mealTimeLabels = {
        "breakfast": "早餐",
        "lunch": "午餐",
        "afternoon_tea": "下午茶",
        "dinner": "晚餐",
        "late_night": "消夜"
    };

    // 取得所有月份（yyyy-mm）
    function getMonths(data) {
        return [...new Set(data.map(item => item.month.substring(0,7)))];
    }

    // 篩選資料
    function filterStats(range) {
        const now = new Date();
        let filtered;
        if (range === "week") {
            // 近一週
            const weekAgo = new Date(now);
            weekAgo.setDate(now.getDate() - 6);
            filtered = timeStats.filter(item => {
                const d = new Date(item.month);
                return d >= weekAgo && d <= now;
            });
        } else if (range === "month") {
            // 近一個月
            const monthAgo = new Date(now);
            monthAgo.setMonth(now.getMonth() - 1);
            filtered = timeStats.filter(item => {
                const d = new Date(item.month);
                return d >= monthAgo && d <= now;
            });
        } else if (range === "year") {
            // 近一年
            const yearAgo = new Date(now);
            yearAgo.setFullYear(now.getFullYear() - 1);
            filtered = timeStats.filter(item => {
                const d = new Date(item.month);
                return d >= yearAgo && d <= now;
            });
        } else {
            // 全部
            filtered = timeStats;
        }
        return filtered;
    }

    // 畫圖
    var ctx = document.getElementById('mealTimeChart').getContext('2d');
    var chart;

    function renderChart(range) {
        var filteredStats = filterStats(range);
        var months = getMonths(filteredStats);
        var datasets = mealTimes.map(mt => ({
            label: mealTimeLabels[mt],
            data: months.map(m => {
                var found = filteredStats.find(item => item.month.substring(0,7) === m && item.meal_time === mt);
                return found ? found.count : 0;
            }),
            backgroundColor: {
                "breakfast": "#ffd166",
                "lunch": "#06d6a0",
                "afternoon_tea": "#118ab2",
                "dinner": "#ef476f",
                "late_night": "#073b4c"
            }[mt]
        }));
        if (chart) chart.destroy();
        chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: months,
                datasets: datasets
            },
            options: {
                plugins: {
                    title: { display: false }
                },
                responsive: true,
                scales: {
                    x: { stacked: true },
                    y: { stacked: true, beginAtZero: true }
                }
            }
        });
    }

    // 綁定按鈕
    document.querySelectorAll('[data-range]').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('[data-range]').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            renderChart(this.dataset.range);
        });
    });

    // 預設顯示全部
    renderChart('all');
});