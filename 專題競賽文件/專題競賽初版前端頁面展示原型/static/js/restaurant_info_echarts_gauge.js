// ECharts 半圓形儀表板評論指標
window.addEventListener('DOMContentLoaded', function() {
  // 1~5分制，分數可自訂
  const indicatorData = [
    { label: '食物', value: 4, color: '#ff6384' },
    { label: '價錢', value: 4, color: '#4bc0c0' },
    { label: '服務', value: 5, color: '#36a2eb' },
    { label: '環境', value: 5, color: '#9966ff' }
  ];
  const container = document.getElementById('gauge-indicators');
  container.innerHTML = '';
  indicatorData.forEach((item, idx) => {
    const div = document.createElement('div');
  div.style.width = '180px';
  div.style.height = '120px';
  div.style.display = 'inline-block';
  div.style.margin = '0 12px';
  div.style.textAlign = 'center';
    container.appendChild(div);
    const chart = echarts.init(div);
    chart.setOption({
      series: [{
        type: 'gauge',
        startAngle: 180,
        endAngle: 0,
        min: 1,
        max: 5,
        splitNumber: 4,
        axisLine: {
          lineStyle: {
            width: 18,
            color: [
              [ (item.value-1)/4, item.color ],
              [ 1, '#eaeaea' ]
            ]
          }
        },
        splitLine: { show: false },
        axisTick: { show: false },
        axisLabel: { show: false },
        pointer: { show: false },
        progress: { show: false },
        detail: {
          valueAnimation: true,
          fontSize: 28,
          offsetCenter: [0, '25%'],
          color: '#222',
          formatter: value => value.toFixed(1)
        },
        data: [{ value: item.value }],
        title: {
          show: false
        }
      }]
    });
    // 指標文字
    const label = document.createElement('div');
    label.textContent = item.label;
    label.style.marginTop = '2px';
    label.style.fontSize = '16px';
    label.style.color = '#444';
    label.style.fontWeight = '500';
    div.appendChild(label);
  });
});
