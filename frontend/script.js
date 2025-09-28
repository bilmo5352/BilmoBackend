// API Configuration
const API_BASE_URL = 'http://localhost:5000';
const SMART_API_BASE_URL = 'http://localhost:5000'; // New smart API endpoint

// Global Variables
let currentPlatform = 'all';
let searchHistory = JSON.parse(localStorage.getItem('searchHistory') || '[]');

// DOM Elements
const searchForm = document.getElementById('searchForm');
const searchInput = document.getElementById('searchInput');
const searchButton = document.getElementById('searchButton');
const searchIcon = document.getElementById('searchIcon');
const searchText = document.getElementById('searchText');
const platformButtons = document.querySelectorAll('.platform-button');
const searchHistoryDiv = document.getElementById('searchHistory');
const historyButtons = document.querySelector('.history-buttons');
const errorDiv = document.getElementById('error');
const loadingDiv = document.getElementById('loading');
const resultsDiv = document.getElementById('results');
const resultsCount = document.getElementById('resultsCount');
const productsGrid = document.getElementById('productsGrid');

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    updateSearchHistory();
    setupEventListeners();
    testConnection();
});

// Test API connection on page load
async function testConnection() {
    try {
        const response = await fetch(`${SMART_API_BASE_URL}/status`, { 
            method: 'GET',
            mode: 'cors',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        if (response.ok) {
            const data = await response.json();
            console.log('✅ Smart API connection successful:', data);
            
            // Load search history from server
            await loadServerSearchHistory();
        } else {
            console.log('⚠️ API responded but with error status');
        }
    } catch (error) {
        console.log('❌ API connection failed:', error.message);
        showError('Cannot connect to the server. Please make sure the Smart API is running on port 5000.');
    }
}

// Load search history from server
async function loadServerSearchHistory() {
    try {
        const response = await fetch(`${SMART_API_BASE_URL}/history?limit=10`, {
            method: 'GET',
            mode: 'cors',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success && data.searches) {
                const serverHistory = data.searches.map(search => search._id);
                // Merge with local history, server takes priority
                searchHistory = [...new Set([...serverHistory, ...searchHistory])].slice(0, 10);
                localStorage.setItem('searchHistory', JSON.stringify(searchHistory));
                updateSearchHistory();
            }
        }
    } catch (error) {
        console.log('Could not load server search history:', error.message);
    }
}

// Event Listeners
function setupEventListeners() {
    searchForm.addEventListener('submit', handleSearch);
    
    // Add force search button event listener
    const forceSearchButton = document.getElementById('forceSearchButton');
    if (forceSearchButton) {
        forceSearchButton.addEventListener('click', handleSearch);
    }
    
    platformButtons.forEach(button => {
        button.addEventListener('click', () => {
            currentPlatform = button.dataset.platform;
            updatePlatformButtons();
            if (searchInput.value.trim()) {
                handleSearch();
            }
        });
    });
}

// Search Functions
async function handleSearch(event) {
    if (event) event.preventDefault();
    
    const query = searchInput.value.trim();
    if (!query) return;
    
    setLoading(true);
    hideError();
    hideResults();
    
    try {
        // Check if force refresh is requested
        const forceFresh = event && event.target && event.target.dataset.forceFresh === 'true';
        
        // Use the new smart API endpoint
        const searchData = {
            query: query,
            force_refresh: forceFresh || false
        };
        
        console.log('🔍 Making search request:', searchData);
        
        // Convert to GET request with query parameters
        const params = new URLSearchParams({
            q: query,
            force_refresh: forceFresh || false
        });
        
        const response = await fetch(`${SMART_API_BASE_URL}/search?${params}`, { 
            method: 'GET',
            mode: 'cors'
        });
        
        const data = await response.json();
        console.log('🔍 Smart API Response:', data);
        
        if (data.success) {
            displayResults(data);
            addToHistory(query);
        } else {
            showError(data.error || 'Search failed');
        }
    } catch (error) {
        console.error('Search error:', error);
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            showError('Cannot connect to the server. Please make sure the Smart API is running on port 5000.');
        } else {
            showError(error.message || 'An error occurred during search');
        }
    } finally {
        setLoading(false);
    }
}

// Display Functions
function displayResults(data) {
    console.log('🔍 Received data:', data);
    
    let products = [];
    
    // Ensure data.results exists
    if (!data.results || !Array.isArray(data.results)) {
        console.log('❌ No valid results found');
        showError(`No results found for "${data.query}". Try a different search term.`);
        return;
    }
    
    const resultsArray = data.results;
    console.log('🔍 Processing results from', resultsArray.length, 'platforms');
    
    if (currentPlatform === 'all') {
        // Show products from all platforms
        resultsArray.forEach((platformData, index) => {
            console.log(`🔍 Processing platform ${index}:`, platformData.site);
            
            // Handle different product structures
            let platformProducts = [];
            
            if (platformData.products && Array.isArray(platformData.products)) {
                platformProducts = platformData.products;
            } else if (platformData.basic_products && Array.isArray(platformData.basic_products)) {
                // Handle Meesho's structure
                platformProducts = platformData.basic_products;
            }
            
            if (platformProducts.length > 0) {
                console.log(`✅ Adding ${platformProducts.length} products from ${platformData.site}`);
                products.push(...platformProducts.map(product => ({
                    ...product,
                    platform: platformData.site?.toLowerCase() || 'unknown',
                    site: platformData.site
                })));
            } else {
                console.log(`⚠️ No products found for ${platformData.site}`);
            }
        });
    } else {
        // Show products from specific platform
        const platformResult = resultsArray.find(r => 
            r && r.site && r.site.toLowerCase() === currentPlatform
        );
        if (platformResult) {
            if (platformResult.products && Array.isArray(platformResult.products)) {
                products = platformResult.products.map(product => ({
                    ...product,
                    platform: currentPlatform,
                    site: platformResult.site
                }));
            } else if (platformResult.basic_products && Array.isArray(platformResult.basic_products)) {
                products = platformResult.basic_products.map(product => ({
                    ...product,
                    platform: currentPlatform,
                    site: platformResult.site
                }));
            }
        }
    }
    
    console.log('🔍 Final products count:', products.length);
    
    if (products.length === 0) {
        console.log('❌ No products to display');
        showError(`No products found for "${data.query}". Try a different search term.`);
        return;
    }
    
    // Update results display
    resultsCount.textContent = `Found ${products.length} products for "${data.query}"`;
    
    // Update source and timing info
    const resultsSource = document.getElementById('resultsSource');
    const processingTime = document.getElementById('processingTime');
    
    if (data.source === 'cache') {
        resultsSource.innerHTML = `📦 From cache ${data.cache_age ? `(${data.cache_age})` : ''}`;
        resultsSource.className = 'results-source cache-source';
    } else {
        resultsSource.innerHTML = `🕷️ Fresh web scraping → 💾 Saved to MongoDB`;
        resultsSource.className = 'results-source fresh-source';
    }
    
    if (data.processing_time) {
        processingTime.textContent = `⏱️ ${data.processing_time}`;
    }
    
    productsGrid.innerHTML = products.map(product => createProductCard(product)).join('');
    
    showResults();
}

function createProductCard(product) {
    const platformColor = getPlatformColor(product.platform);
    const imageUrl = product.image_url || product.image || '';
    const imageAlt = product.image_alt || product.title || product.name || 'Product Image';
    const title = product.title || product.name || 'Product Name Not Available';
    const price = product.price || 'Price not available';
    const rating = product.rating || '';
    const reviews = product.reviews_count || product.reviews || '';
    const link = product.link || '#';
    
    return `
        <div class="product-card">
            <div class="product-platform platform-${product.platform}" style="background-color: ${platformColor}">
                ${product.platform?.toUpperCase() || 'UNKNOWN'}
            </div>
            
            ${imageUrl ? `
                <img 
                    src="${imageUrl}" 
                    alt="${imageAlt}"
                    class="product-image"
                    onerror="this.style.display='none'"
                />
            ` : ''}
            
            <h3 class="product-title">${title}</h3>
            
            <div class="product-price">${price}</div>
            
            ${rating ? `
                <div class="product-rating">
                    <span>⭐</span>
                    <span>${rating}</span>
                    ${reviews ? `<span>(${reviews})</span>` : ''}
                </div>
            ` : ''}
            
            ${link !== '#' ? `
                <a href="${link}" target="_blank" rel="noopener noreferrer" class="product-link">
                    View Product 🔗
                </a>
            ` : ''}
        </div>
    `;
}

// Platform Functions
function updatePlatformButtons() {
    platformButtons.forEach(button => {
        button.classList.toggle('active', button.dataset.platform === currentPlatform);
    });
}

function getPlatformColor(platform) {
    const colors = {
        amazon: '#ff9900',
        flipkart: '#2874f0',
        meesho: '#f43397',
        myntra: '#ff3f6c'
    };
    return colors[platform] || '#667eea';
}

// Search History Functions
function addToHistory(query) {
    searchHistory = [query, ...searchHistory.filter(item => item !== query)].slice(0, 10);
    localStorage.setItem('searchHistory', JSON.stringify(searchHistory));
    updateSearchHistory();
}

function updateSearchHistory() {
    if (searchHistory.length === 0) {
        searchHistoryDiv.style.display = 'none';
        return;
    }
    
    searchHistoryDiv.style.display = 'block';
    historyButtons.innerHTML = searchHistory.slice(0, 5).map(item => 
        `<button class="platform-button" onclick="searchFromHistory('${item}')">${item}</button>`
    ).join('');
}

function searchFromHistory(query) {
    searchInput.value = query;
    handleSearch();
}

// UI State Functions
function setLoading(loading) {
    const forceSearchButton = document.getElementById('forceSearchButton');
    const loadingSubtitle = document.querySelector('.loading-subtitle');
    
    if (loading) {
        loadingDiv.style.display = 'block';
        searchButton.disabled = true;
        if (forceSearchButton) forceSearchButton.disabled = true;
        searchIcon.textContent = '⏳';
        searchText.textContent = 'Searching...';
        
        // Update loading message
        loadingDiv.querySelector('p').textContent = 'Smart search in progress...';
        if (loadingSubtitle) {
            loadingSubtitle.textContent = 'Checking cache → Web scraping if needed → Saving to MongoDB';
        }
    } else {
        loadingDiv.style.display = 'none';
        searchButton.disabled = false;
        if (forceSearchButton) forceSearchButton.disabled = false;
        searchIcon.textContent = '🔍';
        searchText.textContent = 'Search';
    }
}

function showError(message) {
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
}

function hideError() {
    errorDiv.style.display = 'none';
}

function showResults() {
    resultsDiv.style.display = 'block';
}

function hideResults() {
    resultsDiv.style.display = 'none';
}
