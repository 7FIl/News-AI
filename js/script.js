// CONFIGURASI
const API_ENDPOINT = "https://api";
const DEFAULT_ERROR_MSG = "Terjadi kesalahan, silakan coba lagi";

// ELEMEN DOM UTAMA
const elements = {
  textTab: document.getElementById('text-tab'),
  linkTab: document.getElementById('link-tab'),
  textTabContent: document.getElementById('text-tab-content'),
  linkTabContent: document.getElementById('link-tab-content'),
  newsText: document.getElementById('news-text'),
  newsLink: document.getElementById('news-link'),
  analyzeBtn: document.querySelector('.check-btn'),
  analyzeLinkBtn: document.getElementById('analyze-link-btn'),
  resultContainer: document.getElementById('result-container'),
};

// STATE APLIKASI
const state = {
  currentAnalysis: null,
  isLoading: false
};

// INISIALISASI
function init() {
  setupEventListeners();
  checkForSavedResults();
}

// SETUP EVENT LISTENERS
function setupEventListeners() {
  // Tab Navigation
  elements.textTab.addEventListener('click', switchToTextTab);
  elements.linkTab.addEventListener('click', switchToLinkTab);
  
  // Analysis Buttons
  elements.analyzeBtn.addEventListener('click', analyzeText);
  elements.analyzeLinkBtn.addEventListener('click', analyzeLink);
  
  // Shared DOM Events
  document.addEventListener('click', handleDocumentClick);
}

// FUNGSI TAB NAVIGATION
function switchToTextTab() {
  elements.textTab.classList.add('active-tab');
  elements.linkTab.classList.remove('active-tab');
  elements.textTabContent.classList.remove('hidden');
  elements.linkTabContent.classList.add('hidden');
}

function switchToLinkTab() {
  elements.linkTab.classList.add('active-tab');
  elements.textTab.classList.remove('active-tab');
  elements.linkTabContent.classList.remove('hidden');
  elements.textTabContent.classList.add('hidden');
}

// FUNGSI ANALISIS TEKS
async function analyzeText() {
  const text = elements.newsText.value.trim();
  
  if (!text) {
    showAlert('error', 'Silakan masukkan teks berita');
    return;
  }

  try {
    toggleLoading(true, elements.analyzeBtn);
    
    // Simulasi API call
    const analysisResult = await mockTextAnalysisAPI(text);
    
    // Simpan hasil dan redirect
    saveAnalysisResult(analysisResult);
    window.location.href = 'compare.html';
    
  } catch (error) {
    showAlert('error', error.message || DEFAULT_ERROR_MSG);
  } finally {
    toggleLoading(false, elements.analyzeBtn);
  }
}

// FUNGSI ANALISIS LINK
async function analyzeLink() {
  const url = elements.newsLink.value.trim();
  
  if (!url) {
    showAlert('error', 'Silakan masukkan URL berita');
    return;
  }

  if (!isValidUrl(url)) {
    showAlert('error', 'Format URL tidak valid');
    return;
  }

  try {
    toggleLoading(true, elements.analyzeLinkBtn);
    
    // Simulasi API call
    const analysisResult = await mockLinkAnalysisAPI(url);
    
    // Simpan hasil dan redirect
    saveAnalysisResult(analysisResult);
    window.location.href = 'compare.html';
    
  } catch (error) {
    showAlert('error', error.message || DEFAULT_ERROR_MSG);
  } finally {
    toggleLoading(false, elements.analyzeLinkBtn);
  }
}

// HELPER FUNCTIONS
function toggleLoading(isLoading, element) {
  state.isLoading = isLoading;
  
  if (isLoading) {
    element.innerHTML = `
      <svg class="animate-spin h-5 w-5 inline-block mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      Memproses...
    `;
    element.disabled = true;
  } else {
    element.innerHTML = element === elements.analyzeBtn ? 
      'Analisis dengan AI <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 inline-block ml-2" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10.293 5.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L12.586 11H5a1 1 0 110-2h7.586l-2.293-2.293a1 1 0 010-1.414z" clip-rule="evenodd" /></svg>' : 
      'Analisis Link <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 inline-block ml-2" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M12.586 4.586a2 2 0 112.828 2.828l-3 3a2 2 0 01-2.828 0 1 1 0 00-1.414 1.414 4 4 0 005.656 0l3-3a4 4 0 00-5.656-5.656l-1.5 1.5a1 1 0 101.414 1.414l1.5-1.5zm-5 5a2 2 0 012.828 0 1 1 0 101.414-1.414 4 4 0 00-5.656 0l-3 3a4 4 0 105.656 5.656l1.5-1.5a1 1 0 10-1.414-1.414l-1.5 1.5a2 2 0 11-2.828-2.828l3-3z" clip-rule="evenodd" /></svg>';
    element.disabled = false;
  }
}

function isValidUrl(string) {
  try {
    new URL(string);
    return true;
  } catch (_) {
    return false;  
  }
}

function showAlert(type, message) {
  const alertDiv = document.createElement('div');
  alertDiv.className = `fixed top-4 right-4 p-4 rounded-lg ${type === 'error' ? 'bg-red-900 text-red-100' : 'bg-green-900 text-green-100'}`;
  alertDiv.textContent = message;
  
  document.body.appendChild(alertDiv);
  
  setTimeout(() => {
    alertDiv.classList.add('opacity-0', 'transition', 'duration-300');
    setTimeout(() => alertDiv.remove(), 300);
  }, 3000);
}

function saveAnalysisResult(result) {
  sessionStorage.setItem('analysisData', JSON.stringify(result));
}

function checkForSavedResults() {
  const savedData = sessionStorage.getItem('analysisData');
  if (savedData && window.location.pathname.includes('compare.html')) {
    state.currentAnalysis = JSON.parse(savedData);
    renderComparisonResult();
  }
}

// FUNGSI RENDER HASIL (untuk compare.html)
function renderComparisonResult() {
  if (!state.currentAnalysis) return;

  const { status, confidence, sources, matchedClaims, confusingClaims, falseClaims } = state.currentAnalysis;
  
  // Update UI elements
  document.getElementById('verification-status').textContent = status === 'hoax' ? 'HOAX' : 'VALID';
  document.getElementById('verification-status').className = status === 'hoax' ? 
    'fact-check-badge bg-red-900 bg-opacity-30 text-red-300' : 
    'fact-check-badge bg-green-900 bg-opacity-30 text-green-300';
  
  document.getElementById('confidence-score').textContent = `${confidence}%`;
  document.getElementById('trust-score').style.width = `${confidence}%`;
  
  // Render klaim-klaim
  renderClaimsList(falseClaims, 'false-claims-list', 'text-red-400');
  renderClaimsList(confusingClaims, 'confusing-claims-list', 'text-yellow-400');
  renderClaimsList(matchedClaims, 'matched-claims-list', 'text-green-400');
}

function renderClaimsList(claims, elementId, textColorClass) {
  const container = document.getElementById(elementId);
  if (!container) return;
  
  container.innerHTML = claims.map(claim => 
    `<li class="flex items-start mb-2">
      <span class="${textColorClass} mr-2">•</span>
      <span>${claim}</span>
     </li>`
  ).join('');
}

// MOCK API FUNCTIONS (akan diganti dengan API sebenarnya)
async function mockTextAnalysisAPI(text) {
  return new Promise(resolve => {
    setTimeout(() => {
      resolve({
        status: Math.random() > 0.5 ? 'hoax' : 'valid',
        confidence: Math.floor(Math.random() * 30) + 70, // 70-100%
        sources: Math.floor(Math.random() * 10) + 5, // 5-15 sumber
        matchedClaims: ['Klaim tentang kondisi ekonomi', 'Data tanggal kejadian'],
        confusingClaims: ['Pernyataan tentang kebijakan baru'],
        falseClaims: ['Informasi kesehatan presiden', 'Jadwal pengunduran diri'],
        analyzedText: text,
        date: new Date().toISOString()
      });
    }, 1500);
  });
}

async function mockLinkAnalysisAPI(url) {
  return new Promise(resolve => {
    setTimeout(() => {
      resolve({
        status: Math.random() > 0.7 ? 'hoax' : 'valid',
        confidence: Math.floor(Math.random() * 40) + 60, // 60-100%
        sources: Math.floor(Math.random() * 15) + 5, // 5-20 sumber
        matchedClaims: ['Lokasi kejadian', 'Nama institusi terkait'],
        confusingClaims: ['Motif pelaku'],
        falseClaims: ['Jumlah korban', 'Tanggal kejadian sebenarnya'],
        analyzedUrl: url,
        date: new Date().toISOString()
      });
    }, 2000);
  });
}

// HANDLERS
function handleDocumentClick(e) {
  // Handle click events yang bersifat global
}

// START APP
document.addEventListener('DOMContentLoaded', init);
