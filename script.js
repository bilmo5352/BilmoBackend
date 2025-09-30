// E-commerce Scraper Frontend JavaScript
const API_BASE_URL = 'http://localhost:5000';

// DOM elements
const searchForm = document.getElementById('searchForm');
const searchInput = document.getElementById('searchInput');
const searchButton = document.getElementById('searchButton');
const searchIcon = document.getElementById('searchIcon');
const searchText = document.getElementById('searchText');
const platformButtons = document.querySelectorAll('.platform-button');
const searchHistory = document.getElementById('searchHistory');
const historyButtons = document.querySelector('.history-buttons');
const errorMessage = document.getElementById('errorMessage');
const successMessage = document.getElementById('successMessage');
const loadingSection = document.getElementById('loadingSection');
const resultsSection = document.getElementById('resultsSection');
const resultsCount = document.getElementById('resultsCount');
const productsGrid = document.getElementById('productsGrid');

// State
let currentPlatform = 'all';
let searchHistoryList = [];

// Platform colors
const platformColors = {
    amazon: '#ff9900',
    flipkart: '#2874f0',
    meesho: '#f43397',
    myntra: '#ff3f6c'
};

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    loadSearchHistory();
    setupEventListeners();
});

function setupEventListeners() {
    // Search form
    searchForm.addEventListener('submit', handleSearch);
    
    // Platform buttons
    platformButtons.forEach(button => {
        button.addEventListener('click', function() {
            const platform = this.dataset.platform;
            selectPlatform(platform);
            
            // If there's a search query, search immediately
            if (searchInput.value.trim()) {
                handleSearch(new Event('submit'));
            }
        });
    });
}

function selectPlatform(platform) {
    // Update active button
    platformButtons.forEach(btn => btn.classList.remove('active'));
    document.querySelector(`[data-platform="${platform}"]`).classList.add('active');
    
    currentPlatform = platform;
}

async function handleSearch(e) {
    e.preventDefault();
    
    const query = searchInput.value.trim();
    if (!query) return;
    
    setLoading(true);
    hideMessages();
    
    try {
        const timestamp = Date.now();
        const url = currentPlatform === 'all' 
            ? `${API_BASE_URL}/search?q=${encodeURIComponent(query)}&force_refresh=true&_t=${timestamp}`
            : `${API_BASE_URL}/search/${currentPlatform}?q=${encodeURIComponent(query)}&force_refresh=true&_t=${timestamp}`;
        
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            },
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayResults(data);
            addToSearchHistory(query);
            
            // Show different messages based on data source
            if (data.source === 'mongodb_cache') {
                showSuccess(`Found ${data.total_results || 0} products for "${query}" (from MongoDB cache)`);
            } else {
                showSuccess(`Found ${data.total_results || 0} products for "${query}" (scraped from web)`);
            }
        } else {
            showError(data.error || 'Search failed');
        }
    } catch (error) {
        console.error('Search error:', error);
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            showError('Cannot connect to the server. Please make sure the Flask API is running on port 5000.');
        } else {
            showError(error.message || 'An error occurred during search');
        }
    } finally {
        setLoading(false);
    }
}

function displayResults(data) {
    resultsSection.style.display = 'block';
    
    // Show data source information
    let sourceInfo = '';
    if (data.source === 'mongodb_cache') {
        sourceInfo = ` (from MongoDB cache)`;
    } else if (data.source === 'web_scraping') {
        sourceInfo = ` (scraped from web)`;
    }
    
    resultsCount.textContent = `Found ${data.total_results || 0} products for "${data.query}"${sourceInfo}`;
    
    let products = [];
    
    // Handle both array and object formats for results
    let resultsData = data.results;
    if (Array.isArray(resultsData)) {
        // Convert array format to object format for consistency
        resultsData = {};
        resultsData.forEach(result => {
            if (result.site) {
                resultsData[result.site] = result;
            }
        });
    }
    
    if (currentPlatform === 'all') {
        // Collect products from all platforms
        Object.entries(resultsData || {}).forEach(([platform, platformData]) => {
            if (platformData.products && Array.isArray(platformData.products)) {
                products.push(...platformData.products.map(product => ({
                    ...product,
                    platform: platform
                })));
            }
        });
    } else {
        // Get products from specific platform
        const platformData = resultsData?.[currentPlatform];
        if (platformData?.products) {
            products = platformData.products.map(product => ({
                ...product,
                platform: currentPlatform
            }));
        }
    }
    
    if (products.length === 0) {
        productsGrid.innerHTML = `
            <div class="error" style="grid-column: 1 / -1; text-align: center; padding: 40px;">
                No products found for "${data.query}". Try a different search term.
            </div>
        `;
        return;
    }
    
    // Display products
    productsGrid.innerHTML = products.map(product => createProductCard(product)).join('');
}

function createProductCard(product) {
    const platformColor = platformColors[product.platform] || '#667eea';
    
    // Handle different image structures
    let imageUrl = '';
    let imageAlt = '';
    
    if (product.image_url) {
        // Direct image_url field
        imageUrl = product.image_url;
        imageAlt = product.image_alt || product.title || product.name || 'Product Image';
    } else if (product.images && Array.isArray(product.images) && product.images.length > 0) {
        // Images array structure from smart API
        imageUrl = product.images[0].url || '';
        imageAlt = product.images[0].alt || product.title || product.name || 'Product Image';
    } else if (product.image) {
        // Fallback to image field
        imageUrl = product.image;
        imageAlt = product.title || product.name || 'Product Image';
    }
    
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
                >
            ` : ''}
            
            <h3 class="product-title">
                ${product.title || product.name || 'Product Name Not Available'}
            </h3>
            
            ${product.price ? `
                <div class="product-price">
                    ₹${product.price}
                </div>
            ` : ''}
            
            ${product.rating ? `
                <div class="product-rating">
                    ⭐ ${product.rating}
                    ${product.reviews_count ? `<span>(${product.reviews_count} reviews)</span>` : ''}
                </div>
            ` : ''}
            
            ${product.link ? `
                <a 
                    href="${product.link}" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    class="product-link"
                >
                    View Product 🔗
                </a>
            ` : ''}
        </div>
    `;
}

function setLoading(loading) {
    if (loading) {
        searchButton.disabled = true;
        searchIcon.textContent = '⏳';
        searchText.textContent = 'Searching...';
        loadingSection.style.display = 'block';
        resultsSection.style.display = 'none';
    } else {
        searchButton.disabled = false;
        searchIcon.textContent = '🔍';
        searchText.textContent = 'Search';
        loadingSection.style.display = 'none';
    }
}

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.style.display = 'block';
    successMessage.style.display = 'none';
}

function showSuccess(message) {
    successMessage.textContent = message;
    successMessage.style.display = 'block';
    errorMessage.style.display = 'none';
}

function hideMessages() {
    errorMessage.style.display = 'none';
    successMessage.style.display = 'none';
}

function addToSearchHistory(query) {
    // Remove if already exists
    searchHistoryList = searchHistoryList.filter(item => item !== query);
    
    // Add to beginning
    searchHistoryList.unshift(query);
    
    // Keep only last 10
    searchHistoryList = searchHistoryList.slice(0, 10);
    
    // Save to localStorage
    localStorage.setItem('searchHistory', JSON.stringify(searchHistoryList));
    
    // Update UI
    updateSearchHistoryUI();
}

function loadSearchHistory() {
    const saved = localStorage.getItem('searchHistory');
    if (saved) {
        try {
            searchHistoryList = JSON.parse(saved);
            updateSearchHistoryUI();
        } catch (e) {
            console.error('Error loading search history:', e);
        }
    }
}

function updateSearchHistoryUI() {
    if (searchHistoryList.length === 0) {
        searchHistory.style.display = 'none';
        return;
    }
    
    searchHistory.style.display = 'block';
    historyButtons.innerHTML = searchHistoryList.slice(0, 5).map(query => `
        <button class="platform-button" onclick="searchFromHistory('${query}')">
            ${query}
        </button>
    `).join('');
}

function searchFromHistory(query) {
    searchInput.value = query;
    handleSearch(new Event('submit'));
}

// Handle Enter key in search input
searchInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        handleSearch(e);
    }
});

// Auto-focus search input
searchInput.focus();
