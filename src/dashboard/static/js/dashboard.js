// Mantis Dashboard JavaScript

// Static Dashboard (no real-time updates)
class DashboardManager {
    constructor() {
        this.charts = {};
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initializeCharts();
    }

    setupEventListeners() {
        console.log('Dashboard initialized for static report viewing');
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
                    backgroundColor: ['#dc3545', '#fd7e14', '#ffc107', '#6c757d']
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
                    backgroundColor: ['#0d6efd', '#198754', '#dc3545']
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