// Function to load portfolio data
async function loadPortfolioData() {
    try {
        const response = await fetch('/api/portfolio/value');
        const data = await response.json();
        
        // Update portfolio chart
        updatePortfolioChart(data.dates, data.values);
    } catch (error) {
        console.error('Error loading portfolio data:', error);
    }
}

// Function to load stock performance data
async function loadStockPerformance() {
    try {
        const response = await fetch('/api/stocks/performance');
        const data = await response.json();
        
        // Update stock performance chart
        updateStockPerformanceChart(data);
    } catch (error) {
        console.error('Error loading stock performance:', error);
    }
}

// Function to update portfolio stats
async function updatePortfolioStats() {
    try {
        const response = await fetch('/api/portfolio/stats');
        const data = await response.json();
        
        // Update stats display
        document.getElementById('portfolio-value').textContent = 
            `$${data.total_value.toLocaleString()}`;
        document.getElementById('total-gain').textContent = 
            `$${data.total_gain.toLocaleString()}`;
        document.getElementById('daily-change').textContent = 
            `${data.daily_change.toFixed(2)}%`;
    } catch (error) {
        console.error('Error updating stats:', error);
    }
}

// Auto-refresh data every 5 minutes
setInterval(() => {
    loadPortfolioData();
    loadStockPerformance();
    updatePortfolioStats();
}, 300000);

// Initial load
loadPortfolioData();
loadStockPerformance();
updatePortfolioStats();
