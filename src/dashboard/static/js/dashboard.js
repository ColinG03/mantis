// Mantis Dashboard JavaScript

// Static Dashboard (no real-time updates)
class DashboardManager {
    constructor() {
        this.charts = {};
        this.allBugRows = [];
        this.uniquePages = new Set();
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initializeCharts();
        this.initializePageFilter();
    }

    setupEventListeners() {
        console.log('Dashboard initialized for static report viewing');
        
        // Page filter event listener
        const pageFilter = document.getElementById('page-filter');
        if (pageFilter) {
            pageFilter.addEventListener('change', (e) => {
                this.filterBugsByPage(e.target.value);
            });
        }
    }

    initializeCharts() {
        // Initialize charts if they exist on the page
        try {
            if (document.getElementById('severityChart')) {
                this.initializeSeverityChart();
            }
            if (document.getElementById('typeChart')) {
                this.initializeTypeChart();
            }
        } catch (error) {
            console.log('Charts not available on this page:', error.message);
        }
    }

    initializeSeverityChart() {
        const ctx = document.getElementById('severityChart');
        if (!ctx) return;

        // Get data from page (rendered by template)
        const severityData = window.dashboardData ? window.dashboardData.severityData : {};

        this.charts.severity = new Chart(ctx.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: Object.keys(severityData).map(s => s.charAt(0).toUpperCase() + s.slice(1)),
                datasets: [{
                    data: Object.values(severityData),
                    backgroundColor: ['#1b4332', '#2d5a3d', '#52b788', '#95d5b2']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } }
            }
        });
    }

    initializeTypeChart() {
        const ctx = document.getElementById('typeChart');
        if (!ctx) return;

        // Get data from page (rendered by template)
        const typeData = window.dashboardData ? window.dashboardData.typeData : {};

        this.charts.type = new Chart(ctx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: Object.keys(typeData),
                datasets: [{
                    label: 'Bug Count',
                    data: Object.values(typeData),
                    backgroundColor: ['#40916c', '#74c69d', '#2d5a3d']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } },
                plugins: { legend: { display: false } }
            }
        });
    }

    initializePageFilter() {
        // Collect all unique pages from bug rows
        const bugRows = document.querySelectorAll('.bug-row');
        this.allBugRows = Array.from(bugRows);
        
        bugRows.forEach(row => {
            const pageUrl = row.getAttribute('data-page-url');
            if (pageUrl) {
                this.uniquePages.add(pageUrl);
            }
        });

        // Populate the page filter dropdown
        const pageFilter = document.getElementById('page-filter');
        if (pageFilter && this.uniquePages.size > 0) {
            // Sort pages alphabetically
            const sortedPages = Array.from(this.uniquePages).sort();
            
            sortedPages.forEach(pageUrl => {
                const option = document.createElement('option');
                option.value = pageUrl;
                option.textContent = this.formatPageUrl(pageUrl);
                pageFilter.appendChild(option);
            });
        }
    }

    formatPageUrl(url) {
        try {
            const urlObj = new URL(url);
            // Show just the path and filename, or domain if it's the root
            return urlObj.pathname === '/' ? urlObj.hostname : urlObj.pathname;
        } catch (e) {
            // If URL parsing fails, return the original URL truncated
            return url.length > 50 ? url.substring(0, 47) + '...' : url;
        }
    }

    filterBugsByPage(selectedPage) {
        const bugRows = document.querySelectorAll('.bug-row');
        const bugDetailsRows = document.querySelectorAll('.bug-details-row');
        const noBugsRow = document.getElementById('no-bugs-row');
        let visibleCount = 0;

        // Show/hide bug rows based on selected page
        bugRows.forEach(row => {
            const pageUrl = row.getAttribute('data-page-url');
            const shouldShow = selectedPage === 'all' || pageUrl === selectedPage;
            
            row.style.display = shouldShow ? '' : 'none';
            if (shouldShow) {
                visibleCount++;
            }
        });

        // Show/hide corresponding bug details rows
        bugDetailsRows.forEach(row => {
            const pageUrl = row.getAttribute('data-page-url');
            const shouldShow = selectedPage === 'all' || pageUrl === selectedPage;
            
            row.style.display = shouldShow ? '' : 'none';
        });

        // Update bug count badge
        const bugCountBadge = document.getElementById('bug-count-badge');
        if (bugCountBadge) {
            bugCountBadge.textContent = visibleCount;
        }

        // Show/hide "no bugs" message
        if (noBugsRow) {
            noBugsRow.style.display = visibleCount === 0 ? '' : 'none';
        }

        // Update the "no bugs" message text if filtering
        if (visibleCount === 0 && selectedPage !== 'all') {
            const noBugsCell = noBugsRow?.querySelector('td');
            if (noBugsCell) {
                noBugsCell.innerHTML = '<i class="fas fa-filter"></i> No bugs found for the selected page...';
            }
        } else if (visibleCount === 0 && selectedPage === 'all') {
            const noBugsCell = noBugsRow?.querySelector('td');
            if (noBugsCell) {
                noBugsCell.innerHTML = '<i class="fas fa-search"></i> No bugs found yet...';
            }
        }
    }
}

// Screenshot Modal Functions
function openScreenshotModal(imageSrc) {
    const modal = document.getElementById('screenshotModal');
    const modalImage = document.getElementById('modalImage');
    
    modalImage.src = imageSrc;
    modal.style.display = 'block';
    
    // Prevent body scrolling when modal is open
    document.body.style.overflow = 'hidden';
}

function closeScreenshotModal() {
    const modal = document.getElementById('screenshotModal');
    modal.style.display = 'none';
    
    // Restore body scrolling
    document.body.style.overflow = 'auto';
}

// Close modal when ESC key is pressed
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeScreenshotModal();
    }
});

// Prevent modal from closing when clicking on the image itself
document.addEventListener('DOMContentLoaded', function() {
    const modalImage = document.getElementById('modalImage');
    if (modalImage) {
        modalImage.addEventListener('click', function(event) {
            event.stopPropagation();
        });
    }
});

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('🌐 DOM loaded, initializing static dashboard...');
    window.dashboard = new DashboardManager();
    console.log('✅ Static dashboard initialized');
});