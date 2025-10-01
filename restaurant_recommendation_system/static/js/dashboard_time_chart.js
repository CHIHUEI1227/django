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
    var months = [...new Set(timeStats.map(item => item.month.substring(0,7)))];
    var datasets = mealTimes.map(mt => ({
        label: mealTimeLabels[mt],
        data: months.map(m => {
            var found = timeStats.find(item => item.month.substring(0,7) === m && item.meal_time === mt);
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
    var ctx = document.getElementById('mealTimeChart').getContext('2d');
    new Chart(ctx, {
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
});