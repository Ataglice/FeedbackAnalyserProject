document.addEventListener("DOMContentLoaded", function() {
    
    // 1. Извлечение данных из DOM
    const rawTrendData = document.getElementById('trendData').textContent;
    const rawDistData = document.getElementById('distributionData').textContent;
    
    const trendData = JSON.parse(rawTrendData);
    const distData = JSON.parse(rawDistData);

    // Глобальные настройки для темной темы
    Chart.defaults.color = '#8e8e93';
    Chart.defaults.font.family = 'system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif';

    // 2. Инициализация линейного графика (Area Chart)
    const ctxTrend = document.getElementById('trendChart').getContext('2d');
    
    // Создание градиентов
    const gradientPos = ctxTrend.createLinearGradient(0, 0, 0, 300);
    gradientPos.addColorStop(0, 'rgba(212, 175, 55, 0.4)'); 
    gradientPos.addColorStop(1, 'rgba(212, 175, 55, 0.0)');

    const gradientNeg = ctxTrend.createLinearGradient(0, 0, 0, 300);
    gradientNeg.addColorStop(0, 'rgba(155, 114, 203, 0.4)'); 
    gradientNeg.addColorStop(1, 'rgba(155, 114, 203, 0.0)');

    new Chart(ctxTrend, {
        type: 'line',
        data: {
            labels: trendData.labels,
            datasets: [
                {
                    label: 'Положительные',
                    data: trendData.positive,
                    borderColor: '#d4af37',
                    backgroundColor: gradientPos,
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4, // Плавность кривой
                    pointRadius: 0
                },
                {
                    label: 'Отрицательные',
                    data: trendData.negative,
                    borderColor: '#9b72cb',
                    backgroundColor: gradientNeg,
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom', labels: { usePointStyle: true, boxWidth: 8 } }
            },
            scales: {
                x: { grid: { display: false }, border: { display: false } },
                y: { grid: { color: '#333' }, border: { display: false }, beginAtZero: true }
            }
        }
    });

    // 3. Инициализация кольцевой диаграммы (Donut Chart)
    const ctxDonut = document.getElementById('donutChart').getContext('2d');
    
    new Chart(ctxDonut, {
        type: 'doughnut',
        data: {
            labels: distData.labels,
            datasets: [{
                data: distData.values,
                backgroundColor: [
                    '#ffb347', // (Нейтральные)
                    '#9b72cb', // (Позитивные)
                    '#ff6b6b'  // (Негативные)
                ],
                borderWidth: 0,
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '75%', // Толщина кольца
            plugins: {
                legend: { position: 'right', labels: { usePointStyle: true, boxWidth: 8, padding: 20 } }
            }
        }
    });
});