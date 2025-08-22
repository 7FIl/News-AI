document.addEventListener('DOMContentLoaded', function() {
    // --- DOM Elements ---
    const analyzeBtn = document.getElementById('analyze-btn');
    const newsText = document.getElementById('news-text');
    
    // --- Main Function ---
    async function handleAnalysis() {
        // MODIFIED: Get elements inside the function to ensure they exist
        const resultsSection = document.getElementById('results-section');
        const overallVerdictEl = document.getElementById('overall-verdict');
        const countsContainer = document.getElementById('counts-container');
        const summaryEl = document.getElementById('summary');
        const detailsContainer = document.getElementById('details-container');

        // MODIFIED: Add a check to ensure all result elements are present before fetching
        if (!resultsSection || !overallVerdictEl || !countsContainer || !summaryEl || !detailsContainer) {
            alert('Terjadi galat pada halaman: Elemen hasil tidak ditemukan. Coba lakukan hard refresh (Ctrl+Shift+R).');
            return;
        }

        const text = newsText.value.trim();
        if (!text) {
            alert('Silakan masukkan teks berita yang ingin Anda analisis.');
            return;
        }

        setLoadingState(true);
        
        const controller = new AbortController();
        const timeoutId = setTimeout(() => {
            controller.abort();
        }, 60000);

        try {
            const response = await fetch('/check-news', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content: text }),
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: 'An unknown server error occurred.' }));
                throw new Error(`HTTP error! status: ${response.status} - ${errorData.error}`);
            }

            const data = await response.json();
            displayResults(data, { resultsSection, overallVerdictEl, countsContainer, summaryEl, detailsContainer });

        } catch (error) {
            if (error.name === 'AbortError') {
                alert('Analisis melewati batas waktu 60 detik. Server mungkin kelebihan beban atau artikel terlalu panjang. Silakan coba lagi.');
            } else {
                console.error('Analysis Error:', error);
                alert(`Terjadi kesalahan saat menganalisis berita: ${error.message}`);
            }
            resultsSection.classList.add('hidden');
        } finally {
            setLoadingState(false);
        }
    }

    // --- UI Helper Functions ---

    function setLoadingState(isLoading) {
        if (isLoading) {
            analyzeBtn.disabled = true;
            analyzeBtn.innerHTML = `
                <svg class="animate-spin -ml-1 mr-2 h-5 w-5 text-white inline-block" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Menganalisis...`;
        } else {
            analyzeBtn.disabled = false;
            analyzeBtn.innerHTML = `
                Analisis dengan AI
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 inline-block ml-2" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M10.293 5.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L12.586 11H5a1 1 0 110-2h7.586l-2.293-2.293a1 1 0 010-1.414z" clip-rule="evenodd" />
                </svg>`;
        }
    }

    function displayResults(data, elements) {
        const { resultsSection, overallVerdictEl, countsContainer, summaryEl, detailsContainer } = elements;

        summaryEl.textContent = data.summary || 'Tidak ada ringkasan yang tersedia.';
        
        const verdict = data.overall_verdict || 'INCONCLUSIVE';
        overallVerdictEl.textContent = verdict;
        overallVerdictEl.className = `text-center text-5xl font-bold mb-4 ${getVerdictColor(verdict)}`;

        countsContainer.innerHTML = '';
        if (data.counts) {
            countsContainer.innerHTML = `
                <span class="text-green-400 font-semibold">✓ ${data.counts.accurate} Akurat</span>
                <span class="text-yellow-400 font-semibold">! ${data.counts.misleading} Menyesatkan</span>
                <span class="text-red-400 font-semibold">✗ ${data.counts.false} Salah</span>
                <span class="text-gray-400 font-semibold">? ${data.counts.unverifiable} Tidak Terverifikasi</span>
            `;
        }

        detailsContainer.innerHTML = '';
        if (data.details && data.details.length > 0) {
            data.details.forEach(item => {
                const detailCard = createDetailCard(item);
                detailsContainer.appendChild(detailCard);
            });
        } else {
            detailsContainer.innerHTML = '<p class="text-gray-500">Tidak ada detail klaim yang ditemukan.</p>';
        }

        resultsSection.classList.remove('hidden');
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    function createDetailCard(item) {
        const card = document.createElement('div');
        card.className = 'bg-primary-dark p-4 rounded-lg border border-gray-700';

        const verdictColor = getVerdictColor(item.verdict);

        card.innerHTML = `
            <div class="flex justify-between items-start">
                <p class="text-gray-300 flex-1 pr-4"><strong>Klaim:</strong> ${item.claim}</p>
                <span class="font-bold px-2 py-1 rounded-md text-sm ${verdictColor}">${item.verdict}</span>
            </div>
            <p class="text-gray-400 mt-2 text-sm"><strong>Penjelasan:</strong> ${item.explanation}</p>
            ${item.sources && item.sources.length > 0 ? `
            <div class="mt-3">
                <p class="text-sm text-gray-500">Sumber:</p>
                <ul class="list-disc list-inside text-sm">
                    ${item.sources.map(src => `<li><a href="${src}" target="_blank" rel="noopener noreferrer" class="text-purple-400 hover:underline">${src}</a></li>`).join('')}
                </ul>
            </div>
            ` : ''}
        `;
        return card;
    }

    function getVerdictColor(verdict) {
        if (!verdict) return 'text-gray-400';
        const v = verdict.toUpperCase();
        if (v.includes('FALSE')) return 'text-red-400';
        if (v.includes('ACCURATE') || v.includes('TRUE')) return 'text-green-400';
        if (v.includes('MISLEADING') || v.includes('MIXED')) return 'text-yellow-400';
        return 'text-gray-400';
    }
    
    // Add event listener to the analyze button
    if (analyzeBtn) {
        analyzeBtn.addEventListener('click', handleAnalysis);
    } else {
        console.error('Tombol analisis tidak ditemukan. Pastikan ID "analyze-btn" ada di HTML.');
    }
});
