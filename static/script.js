let currentData = [];
let isListening = false;

const translations = {
    hi: {
        subtitle: 'अपने डेटा से सवाल पूछो, SQL + चार्ट पाओ',
        shop: 'दुकान',
        history: 'इतिहास',
        upload: 'CSV Upload',
        voice: 'बोलो',
        clear: 'साफ करें',
        analyze: 'विश्लेषण',
        samples: 'नमूना सवाल:',
        placeholder: 'अपना सवाल यहाँ लिखो... जैसे: Top 5 products by sales',
        analyzing: 'विश्लेषण हो रहा है...',
        result: 'परिणाम',
        rows: 'पंक्तियाँ',
        export: 'CSV Export',
        insights: 'जानकारी',
        sql: 'SQL क्वेरी',
        chart: 'चार्ट',
        data: 'डेटा',
        historyTitle: 'सवालों का इतिहास',
        close: 'बंद करें',
        noHistory: 'अभी कोई इतिहास नहीं',
        errorWrite: 'पहले सवाल लिखो',
        errorSomething: 'कुछ गलत हो गया',
        errorNetwork: 'Network error: ',
        errorExport: 'Export के लिए कोई डेटा नहीं',
        errorExportFail: 'Export failed: ',
        errorClear: 'Clear failed: ',
        errorVoice: 'इस browser में voice support नहीं है। Chrome use करेंे',
        errorVoiceFail: 'Voice recognition failed. Try again.',
        uploading: 'अपलोड हो रहा है...',
        uploaded: 'अपलोड हो गया: ',
        error: 'Error: ',
        confirmClear: 'सारा इतिहास मिट जाएगा। पक्का?',
        cleared: 'इतिहास साफ हो गया',
        listening: 'सुन रहा हूँ...',
        ai: 'AI',
        rule: 'Rule'
    },
    en: {
        subtitle: 'Ask questions in natural language, get SQL + charts',
        shop: 'Shop',
        history: 'History',
        upload: 'CSV Upload',
        voice: 'Voice',
        clear: 'Clear',
        analyze: 'Analyze',
        samples: 'Sample questions:',
        placeholder: 'Type your question here... e.g. Top 5 products by sales',
        analyzing: 'Analyzing...',
        result: 'Result',
        rows: 'rows',
        export: 'Export CSV',
        insights: 'Insights',
        sql: 'SQL Query',
        chart: 'Chart',
        data: 'Data',
        historyTitle: 'Query History',
        close: 'Close',
        noHistory: 'No history yet',
        errorWrite: 'Please write a question first',
        errorSomething: 'Something went wrong',
        errorNetwork: 'Network error: ',
        errorExport: 'No data to export',
        errorExportFail: 'Export failed: ',
        errorClear: 'Clear failed: ',
        errorVoice: 'Voice not supported in this browser. Use Chrome.',
        errorVoiceFail: 'Voice recognition failed. Try again.',
        uploading: 'Uploading...',
        uploaded: 'Uploaded: ',
        error: 'Error: ',
        confirmClear: 'All history will be deleted. Sure?',
        cleared: 'History cleared',
        listening: 'Listening...',
        ai: 'AI',
        rule: 'Rule'
    }
};

function setLanguage(lang) {
    localStorage.setItem('lang', lang);
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (translations[lang] && translations[lang][key]) {
            el.textContent = translations[lang][key];
        }
    });
    const ph = document.querySelector('[data-i18n-ph="placeholder"]');
    if (ph && translations[lang]) {
        ph.placeholder = translations[lang].placeholder;
    }
    const voiceBtn = document.getElementById('voiceBtn');
    if (voiceBtn && !isListening) {
        voiceBtn.textContent = translations[lang].voice;
    }
    const langSelect = document.getElementById('langSelect');
    if (langSelect) langSelect.value = lang;
}

(function initLang() {
    const saved = localStorage.getItem('lang') || 'hi';
    setLanguage(saved);
})();

function setQuestion(q) {
    document.getElementById('question').value = q;
    document.getElementById('question').focus();
}

async function askQuestion() {
    const question = document.getElementById('question').value.trim();
    if (!question) {
        showError('पहले सवाल लिखो');
        return;
    }

    showLoading(true);
    hideResult();
    hideError();

    try {
        const res = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question })
        });
        const data = await res.json();

        if (!data.success) {
            showError(data.error || 'कुछ गलत हो गया');
            showLoading(false);
            return;
        }

        currentData = data.data || [];
        showResult(data);
    } catch (err) {
        showError('Network error: ' + err.message);
    }
    showLoading(false);
}

function showResult(data) {
    const result = document.getElementById('result');
    result.classList.remove('hidden');

    document.getElementById('rowCount').textContent = data.row_count + ' पंक्तियाँ';
    const methodBadge = document.getElementById('methodBadge');
    if (data.method === 'openai') {
        methodBadge.textContent = 'AI';
        methodBadge.style.background = '#34d399';
    } else {
        methodBadge.textContent = 'Rule';
        methodBadge.style.background = '#818cf8';
    }

    document.getElementById('insightsText').textContent = data.insights || 'कोई जानकारी नहीं';
    document.getElementById('sqlCode').textContent = data.sql;

    const chartSection = document.getElementById('chartSection');
    if (data.chart) {
        document.getElementById('chartImg').src = 'data:image/png;base64,' + data.chart;
        chartSection.classList.remove('hidden');
    } else {
        chartSection.classList.add('hidden');
    }

    const table = document.getElementById('resultTable');
    const thead = table.querySelector('thead');
    const tbody = table.querySelector('tbody');
    thead.innerHTML = '';
    tbody.innerHTML = '';

    if (data.data && data.data.length > 0) {
        const cols = Object.keys(data.data[0]);
        const headerRow = document.createElement('tr');
        cols.forEach(col => {
            const th = document.createElement('th');
            th.textContent = col;
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);

        data.data.forEach(row => {
            const tr = document.createElement('tr');
            cols.forEach(col => {
                const td = document.createElement('td');
                td.textContent = row[col];
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });
    }
}

function showLoading(show) {
    document.getElementById('loading').classList.toggle('hidden', !show);
}

function hideResult() {
    document.getElementById('result').classList.add('hidden');
}

function showError(msg) {
    const el = document.getElementById('error');
    el.textContent = msg;
    el.classList.remove('hidden');
}

function hideError() {
    document.getElementById('error').classList.add('hidden');
}

async function exportCSV() {
    if (!currentData || currentData.length === 0) {
        showError('Export के लिए कोई डेटा नहीं');
        return;
    }
    try {
        const res = await fetch('/api/export', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ data: currentData })
        });
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'query_result.csv';
        a.click();
        window.URL.revokeObjectURL(url);
    } catch (err) {
        showError('Export failed: ' + err.message);
    }
}

async function toggleHistory() {
    const panel = document.getElementById('historyPanel');
    panel.classList.toggle('hidden');
    if (!panel.classList.contains('hidden')) {
        await loadHistory();
    }
}

async function loadHistory() {
    try {
        const res = await fetch('/api/history');
        const data = await res.json();
        const list = document.getElementById('historyList');
        list.innerHTML = '';

        if (data.history && data.history.length > 0) {
            data.history.forEach(item => {
                const div = document.createElement('div');
                div.className = 'history-item';
                div.innerHTML = `<div class="q">${item.question}</div>
                    <div class="meta">${item.row_count} पंक्तियाँ - ${new Date(item.created_at).toLocaleString()}</div>
                    <div class="insights">${item.insights || ''}</div>`;
                div.onclick = () => {
                    setQuestion(item.question);
                    toggleHistory();
                };
                list.appendChild(div);
            });
        } else {
            list.innerHTML = '<p style="color:#64748b">अभी कोई इतिहास नहीं</p>';
        }
    } catch (err) {
        console.error('History load failed:', err);
    }
}

async function clearHistory() {
    if (!confirm('सारा इतिहास मिट जाएगा। पक्का?')) return;
    try {
        await fetch('/api/clear_history', { method: 'POST' });
        showError('इतिहास साफ हो गया');
        setTimeout(hideError, 2000);
    } catch (err) {
        showError('Clear failed: ' + err.message);
    }
}

async function uploadFile(input) {
    const file = input.files[0];
    if (!file) return;

    const status = document.getElementById('uploadStatus');
    status.innerHTML = 'अपलोड हो रहा है...';
    status.classList.remove('hidden');

    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await fetch('/api/upload', { method: 'POST', body: formData });
        const data = await res.json();

        if (data.success) {
            status.innerHTML = `अपलोड हो गया: ${data.filename} (${data.rows} पंक्तियाँ, ${data.columns.length} कॉलम)`;
            status.style.borderColor = '#34d399';
            status.style.color = '#a7f3d0';
        } else {
            status.innerHTML = 'Error: ' + data.error;
            status.style.borderColor = '#ef4444';
            status.style.color = '#fca5a5';
        }
    } catch (err) {
        status.innerHTML = 'Upload failed: ' + err.message;
        status.style.borderColor = '#ef4444';
        status.style.color = '#fca5a5';
    }
    input.value = '';
}

function toggleVoice() {
    const btn = document.getElementById('voiceBtn');

    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        showError('इस browser में voice support नहीं है। Chrome use करें।');
        return;
    }

    if (isListening) {
        isListening = false;
        btn.classList.remove('active');
        btn.textContent = 'बोलो';
        return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.lang = 'hi-IN';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    isListening = true;
    btn.classList.add('active');
    btn.textContent = 'सुन रहा हूँ...';

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        document.getElementById('question').value = transcript;
        isListening = false;
        btn.classList.remove('active');
        btn.textContent = 'बोलो';
    };

    recognition.onerror = () => {
        isListening = false;
        btn.classList.remove('active');
        btn.textContent = 'बोलो';
        showError('Voice recognition failed. Try again.');
    };

    recognition.onend = () => {
        isListening = false;
        btn.classList.remove('active');
        btn.textContent = 'बोलो';
    };

    recognition.start();
}

document.getElementById('question').addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        askQuestion();
    }
});
