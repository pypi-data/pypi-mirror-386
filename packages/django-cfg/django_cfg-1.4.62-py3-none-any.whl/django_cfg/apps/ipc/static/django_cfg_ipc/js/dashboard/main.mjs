/**
 * Main RPC Dashboard Controller
 * Orchestrates all dashboard modules and handles tab navigation
 */
import { OverviewModule } from './overview.mjs';
import { TestingModule } from './testing.mjs';

class RPCDashboard {
    constructor() {
        this.api = window.ipcAPI;
        this.currentTab = 'overview';
        this.autoRefresh = true;
        this.refreshInterval = null;
        this.refreshRate = 5000; // 5 seconds

        // Initialize modules
        this.overviewModule = new OverviewModule(this.api, this);
        this.testingModule = new TestingModule(this.api, this);
    }

    /**
     * Initialize dashboard
     */
    init() {
        console.log('🚀 RPC Dashboard initializing...');
        this.setupEventListeners();
        this.testingModule.init();
        this.loadInitialData();
        this.startAutoRefresh();
        console.log('✅ RPC Dashboard initialized');
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Tab buttons
        const tabButtons = document.querySelectorAll('.tab-button');
        tabButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                // Use currentTarget to get the button element, not the clicked child element
                const tabName = e.currentTarget.dataset.tab;
                this.switchTab(tabName);
            });
        });

        // Auto-refresh toggle
        const autoRefreshToggle = document.getElementById('auto-refresh-toggle');
        if (autoRefreshToggle) {
            autoRefreshToggle.checked = this.autoRefresh;
            autoRefreshToggle.addEventListener('change', (e) => {
                this.autoRefresh = e.target.checked;
                if (this.autoRefresh) {
                    this.startAutoRefresh();
                } else {
                    this.stopAutoRefresh();
                }
            });
        }
    }

    /**
     * Switch tabs
     */
    switchTab(tabName) {
        console.log('Switching to tab:', tabName);

        // Update tab buttons styling
        document.querySelectorAll('.tab-button').forEach(btn => {
            if (btn.dataset.tab === tabName) {
                btn.classList.add('active', 'text-blue-600', 'dark:text-blue-400', 'border-blue-600', 'dark:border-blue-400');
                btn.classList.remove('text-gray-600', 'dark:text-gray-400', 'border-transparent');
            } else {
                btn.classList.remove('active', 'text-blue-600', 'dark:text-blue-400', 'border-blue-600', 'dark:border-blue-400');
                btn.classList.add('text-gray-600', 'dark:text-gray-400', 'border-transparent');
            }
        });

        // Update tab panels
        document.querySelectorAll('.tab-panel').forEach(panel => {
            panel.classList.add('hidden');
        });

        const activePanel = document.getElementById(`${tabName}-tab`);
        if (activePanel) {
            activePanel.classList.remove('hidden');
        }

        this.currentTab = tabName;
        this.loadTabData(tabName);
    }

    /**
     * Load initial data
     */
    async loadInitialData() {
        console.log('Loading initial data...');
        await this.loadHealthStatus();
        await this.loadTabData(this.currentTab);
    }

    /**
     * Load data for specific tab
     */
    async loadTabData(tabName) {
        console.log('Loading data for tab:', tabName);

        try {
            // Load overview stats for stat cards (always visible)
            await this.overviewModule.loadOverviewStats();

            // Load tab-specific data
            if (tabName === 'testing') {
                // Testing tab doesn't need data loading, it's interactive
            } else {
                // Overview, requests, notifications, methods tabs
                await this.overviewModule.loadData(tabName);
            }

            this.updateLastUpdate();

        } catch (error) {
            console.error('Error loading tab data:', error);
        }
    }

    /**
     * Load health status
     */
    async loadHealthStatus() {
        try {
            const health = await this.api.ipcAdminApiMonitorHealthRetrieve();

            if (health) {
                // Update health indicator
                const indicator = document.getElementById('health-indicator');
                if (indicator) {
                    const isHealthy = health.redis_connected && health.stream_exists;
                    indicator.innerHTML = `
                        <span class="pulse-dot w-2 h-2 ${isHealthy ? 'bg-green-500' : 'bg-red-500'} rounded-full"></span>
                        <span class="text-gray-700 dark:text-gray-300">${isHealthy ? 'Connected' : 'Disconnected'}</span>
                    `;
                }

                // Update system status section
                this.updateSystemStatus(health);
            }
        } catch (error) {
            console.error('Error loading health status:', error);
        }
    }

    /**
     * Update system status section
     */
    updateSystemStatus(health) {
        const statusContainer = document.getElementById('system-status');
        if (!statusContainer) return;

        statusContainer.innerHTML = `
            <!-- Redis Status -->
            <div class="flex items-start gap-3">
                <span class="material-icons flex-shrink-0 text-2xl ${health.redis_connected ? 'text-green-500' : 'text-red-500'}">
                    ${health.redis_connected ? 'check_circle' : 'cancel'}
                </span>
                <div class="min-w-0">
                    <p class="text-sm font-medium text-gray-900 dark:text-white">Redis</p>
                    <p class="text-xs text-gray-600 dark:text-gray-400">
                        ${health.redis_connected ? 'Connected (DB 2)' : 'Disconnected'}
                    </p>
                </div>
            </div>

            <!-- Stream Status -->
            <div class="flex items-start gap-3">
                <span class="material-icons flex-shrink-0 text-2xl ${health.stream_exists ? 'text-green-500' : 'text-gray-500'}">
                    ${health.stream_exists ? 'stream' : 'stream_off'}
                </span>
                <div class="min-w-0">
                    <p class="text-sm font-medium text-gray-900 dark:text-white">Request Stream</p>
                    <p class="text-xs text-gray-600 dark:text-gray-400">
                        ${health.stream_exists ? `${health.stream_length} entries` : 'Not initialized'}
                    </p>
                </div>
            </div>

            <!-- Activity Status -->
            <div class="flex items-start gap-3">
                <span class="material-icons flex-shrink-0 text-2xl ${health.recent_activity ? 'text-green-500' : 'text-yellow-500'}">
                    ${health.recent_activity ? 'notifications_active' : 'notifications_paused'}
                </span>
                <div class="min-w-0">
                    <p class="text-sm font-medium text-gray-900 dark:text-white">Recent Activity</p>
                    <p class="text-xs text-gray-600 dark:text-gray-400">
                        ${health.recent_activity ? 'Active (last 5 min)' : 'No recent activity'}
                    </p>
                </div>
            </div>
        `;
    }

    /**
     * Update last update timestamp
     */
    updateLastUpdate() {
        const element = document.getElementById('last-update');
        if (element) {
            const now = new Date();
            element.textContent = `Last updated: ${now.toLocaleTimeString()}`;
        }
    }

    /**
     * Start auto-refresh
     */
    startAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }

        this.refreshInterval = setInterval(() => {
            if (this.autoRefresh) {
                this.loadHealthStatus();
                this.loadTabData(this.currentTab);
            }
        }, this.refreshRate);
    }

    /**
     * Stop auto-refresh
     */
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }
}

/**
 * Wait for both DOM and API to be ready
 */
async function initializeDashboard() {
    console.log('DOM loaded, waiting for IpcAPI...');

    // Wait for API to be available (max 5 seconds)
    let attempts = 0;
    const maxAttempts = 100; // 100 * 50ms = 5 seconds

    while (!window.ipcAPI && attempts < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, 50));
        attempts++;
    }

    if (!window.ipcAPI) {
        console.error('❌ IpcAPI failed to load after 5 seconds');
        return;
    }

    console.log('✅ IpcAPI ready, initializing dashboard...');
    window.rpcDashboard = new RPCDashboard();
    window.rpcDashboard.init();
}

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', initializeDashboard);

// Export for debugging
export default RPCDashboard;
