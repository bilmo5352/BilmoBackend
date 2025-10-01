// API Configuration
const API_BASE_URL = 'http://127.0.0.1:5000/';
const SMART_API_BASE_URL = 'http://127.0.0.1:5000'; // New smart API endpoint

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
const dealsButton = document.getElementById('amazonDealsButton');
const flipkartDealsButton = document.getElementById('flipkartDealsButton');
const myntraDealsButton = document.getElementById('myntraDealsButton');
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
        button.addEventListener('click', async () => {
            currentPlatform = button.dataset.platform;
            updatePlatformButtons();
            
            if (searchInput.value.trim()) {
                handleSearch();
            }
        });
    });
    
    // Deals button event listeners
    if (dealsButton) {
        dealsButton.addEventListener('click', async () => {
            await loadAmazonDeals();
        });
    }
    
        if (flipkartDealsButton) {
            flipkartDealsButton.addEventListener('click', async () => {
                await loadFlipkartDeals();
            });
        }
        
        if (myntraDealsButton) {
            myntraDealsButton.addEventListener('click', async () => {
                await loadMyntraDeals();
            });
        }
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
                // Handle Myntra's structure
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
    
    // Handle different image structures
    let imageUrl = '';
    let imageAlt = '';
    
    console.log('🔍 Creating product card for:', product.title || product.name);
    console.log('🔍 Product structure:', product);
    
    if (product.image_url) {
        // Direct image_url field
        imageUrl = product.image_url;
        imageAlt = product.image_alt || product.title || product.name || 'Product Image';
        console.log('✅ Using image_url:', imageUrl);
    } else if (product.images && Array.isArray(product.images) && product.images.length > 0) {
        // Images array structure from smart API
        imageUrl = product.images[0].url || '';
        imageAlt = product.images[0].alt || product.title || product.name || 'Product Image';
        console.log('✅ Using images[0].url:', imageUrl);
    } else if (product.image) {
        // Fallback to image field
        imageUrl = product.image;
        imageAlt = product.title || product.name || 'Product Image';
        console.log('✅ Using image:', imageUrl);
    } else {
        console.log('❌ No image found for product:', product.title || product.name);
    }
    
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

async function loadMyntraDeals() {
    setDealsButtonLoading(true, myntraDealsButton);
    setLoading(true, 'Loading Myntra deals from collection...');
    hideMessages();
    hideResults();
    
    try {
        console.log('👗 Loading Myntra deals from unified collection...');
        
        // First try to get from unified collection
        const unifiedResponse = await fetch(`${SMART_API_BASE_URL}/deals/unified?platform=Myntra`, {
            method: 'GET',
            mode: 'cors',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const unifiedResult = await unifiedResponse.json();
        console.log('👗 Unified collection response:', unifiedResult);
        
        // If found in unified collection, display it
        if (unifiedResult.success && unifiedResult.data) {
            displayMyntraDeals(unifiedResult.data);
            showSuccess(`Found ${unifiedResult.data.total_sections || 0} Myntra sections with ${unifiedResult.data.total_items || 0} deals from collection!`);
            setDealsButtonLoading(false, myntraDealsButton);
            setLoading(false);
            return;
        }
        
        // If not found, scrape fresh
        console.log('🕷️ No cached data, scraping fresh Myntra homepage...');
        setLoading(true, 'Scraping Myntra Homepage...');
        
        const response = await fetch(`${SMART_API_BASE_URL}/myntra/deals`, {
            method: 'GET',
            mode: 'cors',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const result = await response.json();
        console.log('👗 Myntra deals response:', result);
        
        if (result.success && result.data) {
            displayMyntraDeals(result.data);
            showSuccess(`Found ${result.data.total_sections || 0} sections with ${result.data.total_items || 0} deals!`);
        } else {
            showError(result.error || 'Failed to load Myntra deals');
        }
    } catch (error) {
        console.error('Myntra deals error:', error);
        showError('Failed to load Myntra deals: ' + error.message);
    } finally {
        setDealsButtonLoading(false, myntraDealsButton);
        setLoading(false);
    }
}

function displayMyntraDeals(dealsData) {
    console.log('👗 Displaying Myntra homepage sections:', dealsData);
    
    const sections = dealsData.sections || [];
    
    if (sections.length === 0) {
        showError('No Myntra deals sections found');
        return;
    }
    
    // Create results display
    resultsCount.textContent = `Found ${sections.length} Myntra sections with ${dealsData.total_items || 0} deals`;
    
    // Create sections display
    let sectionsHTML = '';
    
    sections.forEach((section, sectionIndex) => {
        const items = section.items || [];
        
        sectionsHTML += `
            <div class="deals-section-display">
                <h3 class="section-title">${section.section_title}</h3>
                <div class="deals-grid">
        `;
        
        items.forEach((item, itemIndex) => {
            const title = item.title || 'No title';
            const price = item.price || 'Price not available';
            const discount = item.discount || '';
            const image = item.image || '';
            const link = item.link || '#';
            
            sectionsHTML += `
                <div class="deal-card">
                    <a href="${link}" target="_blank" class="deal-link">
                        ${image ? `<img src="${image}" alt="${title}" class="deal-image" loading="lazy">` : ''}
                        <div class="deal-info">
                            <h4 class="deal-title">${title}</h4>
                            <div class="deal-price">${price}</div>
                            ${discount ? `<div class="deal-discount">${discount}</div>` : ''}
                        </div>
                    </a>
                </div>
            `;
        });
        
        sectionsHTML += `
                </div>
            </div>
        `;
    });
    
    productsGrid.innerHTML = sectionsHTML;
    showResults();
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
        Myntra: '#f43397',
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

function showSuccess(message) {
    // Create success message element if it doesn't exist
    let successDiv = document.getElementById('success');
    if (!successDiv) {
        successDiv = document.createElement('div');
        successDiv.id = 'success';
        successDiv.className = 'success-message';
        successDiv.style.cssText = `
            background: #d4edda;
            color: #155724;
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
            border: 1px solid #c3e6cb;
            display: none;
        `;
        errorDiv.parentNode.insertBefore(successDiv, errorDiv.nextSibling);
    }
    
    successDiv.textContent = message;
    successDiv.style.display = 'block';
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        successDiv.style.display = 'none';
    }, 5000);
}

function hideMessages() {
    hideError();
    const successDiv = document.getElementById('success');
    if (successDiv) {
        successDiv.style.display = 'none';
    }
}

function showResults() {
    resultsDiv.style.display = 'block';
}

function hideResults() {
    resultsDiv.style.display = 'none';
}

// Amazon Deals Functions
async function loadAmazonDeals() {
    setDealsButtonLoading(true);
    setLoading(true, 'Loading Amazon deals from collection...');
    hideMessages();
    hideResults();
    
    try {
        console.log('🛒 Loading Amazon deals from unified collection...');
        
        // First try to get from unified collection
        const unifiedResponse = await fetch(`${SMART_API_BASE_URL}/deals/unified?platform=Amazon`, {
            method: 'GET',
            mode: 'cors',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const unifiedResult = await unifiedResponse.json();
        console.log('🛒 Unified collection response:', unifiedResult);
        
        // If found in unified collection, display it
        if (unifiedResult.success && unifiedResult.data) {
            displayAmazonDeals(unifiedResult.data);
            showSuccess(`Found ${unifiedResult.data.total_sections || 0} Amazon sections with ${unifiedResult.data.total_items || 0} deals from collection!`);
            setDealsButtonLoading(false);
            setLoading(false);
            return;
        }
        
        // If not found, scrape fresh
        console.log('🕷️ No cached data, scraping fresh Amazon homepage...');
        setLoading(true, 'Scraping Amazon Homepage...');
        
        const response = await fetch(`${SMART_API_BASE_URL}/amazon/deals`, {
            method: 'GET',
            mode: 'cors',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const result = await response.json();
        console.log('🛒 Amazon deals response:', result);
        
        if (result.success && result.data) {
            displayAmazonDeals(result.data);
            showSuccess(`Found ${result.data.total_sections || 0} sections with ${result.data.total_items || 0} deals!`);
        } else {
            showError(result.error || 'Failed to load Amazon deals');
        }
    } catch (error) {
        console.error('Amazon deals error:', error);
        showError('Failed to load Amazon deals: ' + error.message);
    } finally {
        setDealsButtonLoading(false);
        setLoading(false);
    }
}

async function loadFlipkartDeals() {
    setDealsButtonLoading(true, flipkartDealsButton);
    setLoading(true, 'Loading Flipkart deals from collection...');
    hideMessages();
    hideResults();
    
    try {
        console.log('🛍️ Loading Flipkart deals from unified collection...');
        
        // First try to get from unified collection
        const unifiedResponse = await fetch(`${SMART_API_BASE_URL}/deals/unified?platform=Flipkart`, {
            method: 'GET',
            mode: 'cors',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const unifiedResult = await unifiedResponse.json();
        console.log('🛍️ Unified collection response:', unifiedResult);
        
        // If found in unified collection, display it
        if (unifiedResult.success && unifiedResult.data) {
            displayFlipkartDeals(unifiedResult.data);
            showSuccess(`Found ${unifiedResult.data.total_sections || 0} Flipkart sections with ${unifiedResult.data.total_items || 0} deals from collection!`);
            setDealsButtonLoading(false, flipkartDealsButton);
            setLoading(false);
            return;
        }
        
        // If not found, scrape fresh
        console.log('🕷️ No cached data, scraping fresh Flipkart homepage...');
        setLoading(true, 'Scraping Flipkart Homepage...');
        
        const response = await fetch(`${SMART_API_BASE_URL}/flipkart/deals`, {
            method: 'GET',
            mode: 'cors',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const result = await response.json();
        console.log('🛍️ Flipkart deals response:', result);
        
        if (result.success && result.data) {
            displayFlipkartDeals(result.data);
            showSuccess(`Found ${result.data.total_sections || 0} sections with ${result.data.total_items || 0} deals!`);
        } else {
            showError(result.error || 'Failed to load Flipkart deals');
        }
    } catch (error) {
        console.error('Flipkart deals error:', error);
        showError('Failed to load Flipkart deals: ' + error.message);
    } finally {
        setDealsButtonLoading(false, flipkartDealsButton);
        setLoading(false);
    }
}

function setDealsButtonLoading(loading, button = dealsButton) {
    if (button) {
        if (loading) {
            button.classList.add('loading');
            button.disabled = true;
        } else {
            button.classList.remove('loading');
            button.disabled = false;
        }
    }
}

function displayFlipkartDeals(dealsData) {
    console.log('🛍️ Displaying Flipkart homepage sections:', dealsData);
    
    const sections = dealsData.sections || [];
    
    if (sections.length === 0) {
        showError('No Flipkart deals sections found');
        return;
    }
    
    // Debug: Log sample items
    if (sections.length > 0 && sections[0].items && sections[0].items.length > 0) {
        console.log('📦 Sample Flipkart item:', sections[0].items[0]);
    }
    
    // Create results display
    resultsCount.textContent = `Found ${sections.length} Flipkart sections with ${dealsData.total_items || 0} deals`;
    
    // Create sections display
    let sectionsHTML = '';
    
    sections.forEach((section, sectionIndex) => {
        const items = section.items || [];
        
        sectionsHTML += `
            <div class="deals-section-display">
                <h3 class="section-title">${section.section_title}</h3>
                <div class="deals-grid">
        `;
        
        items.forEach((item, itemIndex) => {
            const title = item.title || 'No title';
            const price = item.price || 'Price not available';
            const discount = item.discount || '';
            const image = item.image || '';
            const link = item.link || '#';
            
            sectionsHTML += `
                <div class="deal-card">
                    <a href="${link}" target="_blank" class="deal-link">
                        ${image ? `<img src="${image}" alt="${title}" class="deal-image" loading="lazy">` : ''}
                        <div class="deal-info">
                            <h4 class="deal-title">${title}</h4>
                            <div class="deal-price">${price}</div>
                            ${discount ? `<div class="deal-discount">${discount}</div>` : ''}
                        </div>
                    </a>
                </div>
            `;
        });
        
        sectionsHTML += `
                </div>
            </div>
        `;
    });
    
    productsGrid.innerHTML = sectionsHTML;
    showResults();
}

function displayAmazonDeals(dealsData) {
    console.log('🛒 Displaying Amazon homepage sections:', dealsData);
    
    const sections = dealsData.sections || [];
    
    if (sections.length === 0) {
        showError('No Amazon sections found at the moment.');
        return;
    }
    
    const totalItems = dealsData.total_items || sections.reduce((sum, s) => sum + s.item_count, 0);
    
    // Update results display
    resultsCount.textContent = `Amazon Homepage - ${sections.length} Sections • ${totalItems} Items`;
    
    // Update source and timing info
    const resultsSource = document.getElementById('resultsSource');
    const processingTime = document.getElementById('processingTime');
    
    if (dealsData.source === 'cache') {
        resultsSource.innerHTML = `📦 From cache ${dealsData.cache_age ? `(${dealsData.cache_age})` : ''}`;
        resultsSource.className = 'results-source cache-source';
    } else {
        resultsSource.innerHTML = `🕷️ Fresh web scraping → 💾 Saved to MongoDB`;
        resultsSource.className = 'results-source fresh-source';
    }
    
    if (dealsData.timestamp) {
        const timestamp = new Date(dealsData.timestamp);
        processingTime.textContent = `🕐 ${timestamp.toLocaleTimeString()}`;
    }
    
    // Create grouped sections display
    productsGrid.innerHTML = createGroupedSectionsHTML(sections);
    
    showResults();
}

function createGroupedSectionsHTML(sections) {
    let html = '';
    
    sections.forEach((section, sectionIndex) => {
        html += `
            <div class="section-group" style="grid-column: 1 / -1; margin-bottom: 30px;">
                <div class="section-header" style="margin-bottom: 15px; padding: 15px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 8px; color: white;">
                    <h2 style="margin: 0; font-size: 24px; font-weight: 600;">
                        ${section.section_title}
                    </h2>
                    <p style="margin: 5px 0 0 0; opacity: 0.9; font-size: 14px;">
                        ${section.item_count} items
                    </p>
                </div>
                <div class="section-items" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px;">
                    ${section.items.map(item => createSectionItemCard(item)).join('')}
                </div>
            </div>
        `;
    });
    
    return html;
}

function createSectionItemCard(item) {
    const imageUrl = item.image || '';
    const title = item.title || 'Product Title Not Available';
    const price = item.price || '';
    const discount = item.discount || '';
    const link = item.link || '#';
    
    return `
        <div class="product-card" style="background: white; border-radius: 8px; padding: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); transition: transform 0.2s, box-shadow 0.2s;" onmouseover="this.style.transform='translateY(-5px)'; this.style.boxShadow='0 4px 16px rgba(0,0,0,0.2)';" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 8px rgba(0,0,0,0.1)';">
            <div class="product-platform platform-amazon" style="background-color: #ff9900; color: white; padding: 5px 10px; border-radius: 4px; font-size: 11px; font-weight: bold; display: inline-block; margin-bottom: 10px;">
                AMAZON
            </div>
            
            ${imageUrl ? `
                <img 
                    src="${imageUrl}" 
                    alt="${title}"
                    class="product-image"
                    style="width: 100%; height: 200px; object-fit: contain; margin-bottom: 10px; border-radius: 4px;"
                    onerror="this.style.display='none'"
                />
            ` : ''}
            
            <h3 class="product-title" style="font-size: 14px; font-weight: 500; color: #333; margin: 10px 0; line-height: 1.4; height: 40px; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;">
                ${title}
            </h3>
            
            ${price ? `
                <div class="product-price" style="font-size: 20px; font-weight: bold; color: #B12704; margin: 10px 0;">
                    ${price}
                </div>
            ` : ''}
            
            ${discount ? `
                <div class="product-discount" style="color: #007600; font-weight: 600; font-size: 14px; margin: 5px 0;">
                    ${discount}
                </div>
            ` : ''}
            
            ${link !== '#' ? `
                <a href="${link}" target="_blank" rel="noopener noreferrer" class="product-link" style="display: inline-block; background: #ff9900; color: white; padding: 10px 20px; border-radius: 4px; text-decoration: none; margin-top: 10px; font-size: 14px; font-weight: 500; transition: background 0.2s;" onmouseover="this.style.background='#e88c00'" onmouseout="this.style.background='#ff9900'">
                    View on Amazon 🔗
                </a>
            ` : ''}
        </div>
    `;
}

async function loadMyntraDeals() {
    setDealsButtonLoading(true, myntraDealsButton);
    setLoading(true, 'Loading Myntra deals from collection...');
    hideMessages();
    hideResults();
    
    try {
        console.log('👗 Loading Myntra deals from unified collection...');
        
        // First try to get from unified collection
        const unifiedResponse = await fetch(`${SMART_API_BASE_URL}/deals/unified?platform=Myntra`, {
            method: 'GET',
            mode: 'cors',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const unifiedResult = await unifiedResponse.json();
        console.log('👗 Unified collection response:', unifiedResult);
        
        // If found in unified collection, display it
        if (unifiedResult.success && unifiedResult.data) {
            displayMyntraDeals(unifiedResult.data);
            showSuccess(`Found ${unifiedResult.data.total_sections || 0} Myntra sections with ${unifiedResult.data.total_items || 0} deals from collection!`);
            setDealsButtonLoading(false, myntraDealsButton);
            setLoading(false);
            return;
        }
        
        // If not found, scrape fresh
        console.log('🕷️ No cached data, scraping fresh Myntra homepage...');
        setLoading(true, 'Scraping Myntra Homepage...');
        
        const response = await fetch(`${SMART_API_BASE_URL}/myntra/deals`, {
            method: 'GET',
            mode: 'cors',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const result = await response.json();
        console.log('👗 Myntra deals response:', result);
        
        if (result.success && result.data) {
            displayMyntraDeals(result.data);
            showSuccess(`Found ${result.data.total_sections || 0} sections with ${result.data.total_items || 0} deals!`);
        } else {
            showError(result.error || 'Failed to load Myntra deals');
        }
    } catch (error) {
        console.error('Myntra deals error:', error);
        showError('Failed to load Myntra deals: ' + error.message);
    } finally {
        setDealsButtonLoading(false, myntraDealsButton);
        setLoading(false);
    }
}

function displayMyntraDeals(dealsData) {
    console.log('👗 Displaying Myntra homepage sections:', dealsData);
    
    const sections = dealsData.sections || [];
    
    if (sections.length === 0) {
        showError('No Myntra deals sections found');
        return;
    }
    
    // Create results display
    resultsCount.textContent = `Found ${sections.length} Myntra sections with ${dealsData.total_items || 0} deals`;
    
    // Create sections display
    let sectionsHTML = '';
    
    sections.forEach((section, sectionIndex) => {
        const items = section.items || [];
        
        sectionsHTML += `
            <div class="deals-section-display">
                <h3 class="section-title">${section.section_title}</h3>
                <div class="deals-grid">
        `;
        
        items.forEach((item, itemIndex) => {
            const title = item.title || 'No title';
            const price = item.price || 'Price not available';
            const discount = item.discount || '';
            const image = item.image || '';
            const link = item.link || '#';
            
            sectionsHTML += `
                <div class="deal-card">
                    <a href="${link}" target="_blank" class="deal-link">
                        ${image ? `<img src="${image}" alt="${title}" class="deal-image" loading="lazy">` : ''}
                        <div class="deal-info">
                            <h4 class="deal-title">${title}</h4>
                            <div class="deal-price">${price}</div>
                            ${discount ? `<div class="deal-discount">${discount}</div>` : ''}
                        </div>
                    </a>
                </div>
            `;
        });
        
        sectionsHTML += `
                </div>
            </div>
        `;
    });
    
    productsGrid.innerHTML = sectionsHTML;
    showResults();
}

function createDealCard(deal) {
    const imageUrl = deal.image || '';
    const title = deal.title || 'Deal Title Not Available';
    const price = deal.price || '';
    const discount = deal.discount || '';
    const link = deal.link || '#';
    const dealType = deal.deal_type || 'Deal';
    
    return `
        <div class="product-card">
            <div class="product-platform platform-amazon" style="background-color: #ff9900">
                ${dealType.toUpperCase()}
            </div>
            
            ${imageUrl ? `
                <img 
                    src="${imageUrl}" 
                    alt="${title}"
                    class="product-image"
                    onerror="this.style.display='none'"
                />
            ` : ''}
            
            <h3 class="product-title">${title}</h3>
            
            ${price ? `<div class="product-price">${price}</div>` : ''}
            
            ${discount ? `
                <div class="product-discount" style="color: #28a745; font-weight: bold;">
                    ${discount}
                </div>
            ` : ''}
            
            ${link !== '#' ? `
                <a href="${link}" target="_blank" rel="noopener noreferrer" class="product-link">
                    View Deal 🔗
                </a>
            ` : ''}
        </div>
    `;
}

async function loadMyntraDeals() {
    setDealsButtonLoading(true, myntraDealsButton);
    setLoading(true, 'Loading Myntra deals from collection...');
    hideMessages();
    hideResults();
    
    try {
        console.log('👗 Loading Myntra deals from unified collection...');
        
        // First try to get from unified collection
        const unifiedResponse = await fetch(`${SMART_API_BASE_URL}/deals/unified?platform=Myntra`, {
            method: 'GET',
            mode: 'cors',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const unifiedResult = await unifiedResponse.json();
        console.log('👗 Unified collection response:', unifiedResult);
        
        // If found in unified collection, display it
        if (unifiedResult.success && unifiedResult.data) {
            displayMyntraDeals(unifiedResult.data);
            showSuccess(`Found ${unifiedResult.data.total_sections || 0} Myntra sections with ${unifiedResult.data.total_items || 0} deals from collection!`);
            setDealsButtonLoading(false, myntraDealsButton);
            setLoading(false);
            return;
        }
        
        // If not found, scrape fresh
        console.log('🕷️ No cached data, scraping fresh Myntra homepage...');
        setLoading(true, 'Scraping Myntra Homepage...');
        
        const response = await fetch(`${SMART_API_BASE_URL}/myntra/deals`, {
            method: 'GET',
            mode: 'cors',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const result = await response.json();
        console.log('👗 Myntra deals response:', result);
        
        if (result.success && result.data) {
            displayMyntraDeals(result.data);
            showSuccess(`Found ${result.data.total_sections || 0} sections with ${result.data.total_items || 0} deals!`);
        } else {
            showError(result.error || 'Failed to load Myntra deals');
        }
    } catch (error) {
        console.error('Myntra deals error:', error);
        showError('Failed to load Myntra deals: ' + error.message);
    } finally {
        setDealsButtonLoading(false, myntraDealsButton);
        setLoading(false);
    }
}

function displayMyntraDeals(dealsData) {
    console.log('👗 Displaying Myntra homepage sections:', dealsData);
    
    const sections = dealsData.sections || [];
    
    if (sections.length === 0) {
        showError('No Myntra deals sections found');
        return;
    }
    
    // Create results display
    resultsCount.textContent = `Found ${sections.length} Myntra sections with ${dealsData.total_items || 0} deals`;
    
    // Create sections display
    let sectionsHTML = '';
    
    sections.forEach((section, sectionIndex) => {
        const items = section.items || [];
        
        sectionsHTML += `
            <div class="deals-section-display">
                <h3 class="section-title">${section.section_title}</h3>
                <div class="deals-grid">
        `;
        
        items.forEach((item, itemIndex) => {
            const title = item.title || 'No title';
            const price = item.price || 'Price not available';
            const discount = item.discount || '';
            const image = item.image || '';
            const link = item.link || '#';
            
            sectionsHTML += `
                <div class="deal-card">
                    <a href="${link}" target="_blank" class="deal-link">
                        ${image ? `<img src="${image}" alt="${title}" class="deal-image" loading="lazy">` : ''}
                        <div class="deal-info">
                            <h4 class="deal-title">${title}</h4>
                            <div class="deal-price">${price}</div>
                            ${discount ? `<div class="deal-discount">${discount}</div>` : ''}
                        </div>
                    </a>
                </div>
            `;
        });
        
        sectionsHTML += `
                </div>
            </div>
        `;
    });
    
    productsGrid.innerHTML = sectionsHTML;
    showResults();
}
