let emotionChart = null;

async function loadHistory() {
    try {
        const response = await fetch('/history');
        const data = await response.json();
        
        updateStats(data);
        updateChart(data.history);
        updateHistoryList(data.history);
    } catch (error) {
        console.error('Error loading history:', error);
    }
}

function updateStats(data) {
    document.getElementById('avgScore').textContent = 
        data.avg_score ? `${data.avg_score}점` : '-';
    document.getElementById('entryCount').textContent = 
        data.count ? `${data.count}개` : '-';
    document.getElementById('posRatio').textContent = 
        data.sentiment_ratio ? `${data.sentiment_ratio.긍정}%` : '-';
}

function updateChart(history) {
    const ctx = document.getElementById('emotionChart').getContext('2d');
    
    if (emotionChart) {
        emotionChart.destroy();
    }

    const chartData = prepareChartData(history);
    
    emotionChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: chartData.labels,
            datasets: [{
                label: '감정 점수',
                data: chartData.scores,
                borderColor: '#7c3aed',
                tension: 0.4,
                fill: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    min: 0,
                    max: 100,
                    ticks: {
                        callback: value => `${value}점`
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: context => `${context.parsed.y}점`
                    }
                }
            }
        }
    });
}

function prepareChartData(history) {
    const sorted = [...history].sort((a, b) => new Date(a.date) - new Date(b.date));
    return {
        labels: sorted.map(h => h.date),
        scores: sorted.map(h => h.score)
    };
}

function updateHistoryList(history) {
    const container = document.getElementById('historyList');
    container.innerHTML = history
        .sort((a, b) => new Date(b.date) - new Date(a.date))
        .map(entry => `
            <div class="result-item">
                <h3>${entry.date} - ${entry.today_state}</h3>
                <p>${entry.today_message}</p>
                <p><strong>감정 점수:</strong> ${entry.score}점</p>
            </div>
        `)
        .join('');
}

document.addEventListener('DOMContentLoaded', loadHistory);
