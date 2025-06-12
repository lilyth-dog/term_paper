document.addEventListener('DOMContentLoaded', () => {
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('diaryDate').value = today;
});

async function analyzeDiary() {
    const content = document.getElementById('diaryContent').value;
    const date = document.getElementById('diaryDate').value;
    const resultDiv = document.getElementById('result');
    
    if (!content.trim()) {
        alert('일기를 입력해주세요.');
        return;
    }

    try {
        resultDiv.innerHTML = '<p class="loading">분석 중...</p>';
        resultDiv.classList.remove('hidden');

        const response = await fetch('/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                diary: content,
                date: date
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        displayResult(result);
    } catch (error) {
        console.error('Error:', error);
        resultDiv.innerHTML = `
            <div class="error-message">
                <p>분석 중 오류가 발생했습니다.</p>
                <p>${error.message}</p>
            </div>
        `;
    }
}

function displayResult(result) {
    const resultDiv = document.getElementById('result');
    resultDiv.innerHTML = `
        <h3 class="result-title">${result.today_state}</h3>
        <div class="result-section">
            <p class="result-message">${result.today_message}</p>
            <p class="result-feedback">${result.pattern_feedback}</p>
            <p class="result-empathy">${result.empathy_message}</p>
            <p class="result-action">${result.action_suggestion}</p>
            <p class="result-hope">${result.hope_message}</p>
        </div>
    `;
    resultDiv.classList.remove('hidden');
}
