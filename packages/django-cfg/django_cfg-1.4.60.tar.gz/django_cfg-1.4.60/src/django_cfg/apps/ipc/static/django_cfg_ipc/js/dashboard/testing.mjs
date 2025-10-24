/**
 * RPC Testing Tools Module
 * Handles test client and load testing functionality
 */
export class TestingModule {
    constructor(api, dashboard) {
        this.api = api;
        this.dashboard = dashboard;
        this.loadTestInterval = null;
        this.isLoadTestRunning = false;
    }

    /**
     * Initialize testing tools
     */
    init() {
        this.setupEventListeners();
    }

    /**
     * Setup event listeners for testing tools
     */
    setupEventListeners() {
        // Test RPC Client
        const sendTestBtn = document.getElementById('send-test-rpc-btn');
        const clearTestBtn = document.getElementById('clear-test-rpc-btn');

        if (sendTestBtn) {
            sendTestBtn.addEventListener('click', () => this.sendTestRequest());
        }

        if (clearTestBtn) {
            clearTestBtn.addEventListener('click', () => this.clearTestForm());
        }

        // Load Testing
        const startLoadTestBtn = document.getElementById('start-load-test-btn');
        const stopLoadTestBtn = document.getElementById('stop-load-test-btn');

        if (startLoadTestBtn) {
            startLoadTestBtn.addEventListener('click', () => this.startLoadTest());
        }

        if (stopLoadTestBtn) {
            stopLoadTestBtn.addEventListener('click', () => this.stopLoadTest());
        }
    }

    /**
     * Send a single test RPC request
     */
    async sendTestRequest() {
        try {
            const method = document.getElementById('test-rpc-method')?.value;
            const timeout = parseInt(document.getElementById('test-rpc-timeout')?.value || '10');
            const paramsText = document.getElementById('test-rpc-params')?.value || '{}';

            // Validate input
            if (!method) {
                this.showTestResponse('Please select a method', 'error');
                return;
            }

            let params = {};
            try {
                params = JSON.parse(paramsText);
            } catch (e) {
                this.showTestResponse('Invalid JSON in parameters: ' + e.message, 'error');
                return;
            }

            // Auto-add timestamp if not present (required by WebSocket server)
            if (!params.timestamp) {
                params.timestamp = new Date().toISOString();
            }

            // Show loading state
            this.showTestResponse('Sending request...', 'info');

            // Send test request via API
            const response = await this.api.ipcAdminApiTestSendCreate({
                method,
                params,
                timeout
            });

            // Display response
            this.displayTestResponse(response);

        } catch (error) {
            this.showTestResponse('Request failed: ' + error.message, 'error');
        }
    }

    /**
     * Display test response
     */
    displayTestResponse(response) {
        const resultDiv = document.getElementById('test-rpc-result');
        if (!resultDiv) return;

        const isSuccess = response.success;
        const statusClass = isSuccess ? 'text-green-600' : 'text-red-600';
        const statusIcon = isSuccess ? 'check_circle' : 'error';

        resultDiv.innerHTML = `
            <div class="p-4 bg-gray-50 dark:bg-gray-700 rounded">
                <!-- Status -->
                <div class="flex items-center mb-3">
                    <span class="material-icons ${statusClass} mr-2">${statusIcon}</span>
                    <h4 class="font-semibold ${statusClass}">
                        ${isSuccess ? 'Success' : 'Failed'}
                    </h4>
                </div>

                <!-- Timing -->
                <div class="mb-3 text-sm">
                    <strong>Duration:</strong> ${response.duration_ms?.toFixed(2) || 'N/A'} ms
                </div>

                <!-- Correlation ID -->
                <div class="mb-3 text-sm">
                    <strong>Correlation ID:</strong>
                    <code class="bg-gray-200 dark:bg-gray-600 px-2 py-1 rounded text-xs">
                        ${this.escapeHtml(response.correlation_id || 'N/A')}
                    </code>
                </div>

                <!-- Response/Error -->
                <div class="mt-3">
                    <strong class="text-sm">${isSuccess ? 'Response:' : 'Error:'}</strong>
                    <pre class="mt-2 text-xs bg-gray-100 dark:bg-gray-900 p-3 rounded overflow-auto max-h-60">${
                        this.escapeHtml(JSON.stringify(isSuccess ? response.response : response.error, null, 2))
                    }</pre>
                </div>
            </div>
        `;

        resultDiv.classList.remove('hidden');
    }

    /**
     * Show test response message
     */
    showTestResponse(message, type = 'info') {
        const resultDiv = document.getElementById('test-rpc-result');
        if (!resultDiv) return;

        const colors = {
            info: 'text-blue-600 dark:text-blue-400',
            error: 'text-red-600 dark:text-red-400',
            success: 'text-green-600 dark:text-green-400'
        };

        const icons = {
            info: 'info',
            error: 'error',
            success: 'check_circle'
        };

        resultDiv.innerHTML = `
            <div class="p-4 bg-gray-50 dark:bg-gray-700 rounded">
                <div class="flex items-center">
                    <span class="material-icons ${colors[type]} mr-2">${icons[type]}</span>
                    <span class="${colors[type]}">${this.escapeHtml(message)}</span>
                </div>
            </div>
        `;

        resultDiv.classList.remove('hidden');
    }

    /**
     * Clear test form
     */
    clearTestForm() {
        const methodSelect = document.getElementById('test-rpc-method');
        const paramsTextarea = document.getElementById('test-rpc-params');
        const timeoutInput = document.getElementById('test-rpc-timeout');
        const resultDiv = document.getElementById('test-rpc-result');

        if (methodSelect) methodSelect.value = '';
        if (paramsTextarea) paramsTextarea.value = '{}';
        if (timeoutInput) timeoutInput.value = '10';
        if (resultDiv) resultDiv.classList.add('hidden');
    }

    /**
     * Start load test
     */
    async startLoadTest() {
        try {
            const method = document.getElementById('load-test-method')?.value;
            const totalRequests = parseInt(document.getElementById('load-test-total')?.value || '100');
            const concurrency = parseInt(document.getElementById('load-test-concurrency')?.value || '10');
            const paramsText = document.getElementById('load-test-params')?.value || '{}';

            // Validate input
            if (!method) {
                window.showNotification?.('Please select a method', 'error');
                return;
            }

            if (totalRequests < 1 || totalRequests > 10000) {
                window.showNotification?.('Total requests must be between 1 and 10,000', 'error');
                return;
            }

            if (concurrency < 1 || concurrency > 100) {
                window.showNotification?.('Concurrency must be between 1 and 100', 'error');
                return;
            }

            // Parse params
            let params = {};
            try {
                params = JSON.parse(paramsText);
            } catch (e) {
                window.showNotification?.('Invalid JSON in parameters: ' + e.message, 'error');
                return;
            }

            // Auto-add timestamp if not present
            if (!params.timestamp) {
                params.timestamp = new Date().toISOString();
            }

            // Start load test
            const response = await this.api.ipcAdminApiTestLoadStartCreate({
                method,
                total_requests: totalRequests,
                concurrency,
                params: params
            });

            if (response && response.test_id) {
                this.isLoadTestRunning = true;
                this.toggleLoadTestButtons(true);
                this.startLoadTestPolling();
                window.showNotification?.('Load test started', 'success');
            }

        } catch (error) {
            window.showNotification?.('Failed to start load test: ' + error.message, 'error');
        }
    }

    /**
     * Stop load test
     */
    async stopLoadTest() {
        try {
            await this.api.ipcAdminApiTestLoadStopCreate({
                method: '',
                params: {},
                timeout: 10
            });

            this.isLoadTestRunning = false;
            this.stopLoadTestPolling();
            this.toggleLoadTestButtons(false);
            window.showNotification?.('Load test stopped', 'info');

        } catch (error) {
            window.showNotification?.('Failed to stop load test: ' + error.message, 'error');
        }
    }

    /**
     * Toggle load test buttons
     */
    toggleLoadTestButtons(isRunning) {
        const startBtn = document.getElementById('start-load-test-btn');
        const stopBtn = document.getElementById('stop-load-test-btn');

        if (startBtn) {
            startBtn.disabled = isRunning;
            startBtn.classList.toggle('opacity-50', isRunning);
            startBtn.classList.toggle('cursor-not-allowed', isRunning);
        }

        if (stopBtn) {
            stopBtn.disabled = !isRunning;
            stopBtn.classList.toggle('opacity-50', !isRunning);
            stopBtn.classList.toggle('cursor-not-allowed', !isRunning);
        }
    }

    /**
     * Start polling for load test status
     */
    startLoadTestPolling() {
        // Initial update
        this.updateLoadTestStatus();

        // Poll every 500ms
        if (this.loadTestInterval) {
            clearInterval(this.loadTestInterval);
        }

        this.loadTestInterval = setInterval(() => {
            this.updateLoadTestStatus();
        }, 500);
    }

    /**
     * Stop polling for load test status
     */
    stopLoadTestPolling() {
        if (this.loadTestInterval) {
            clearInterval(this.loadTestInterval);
            this.loadTestInterval = null;
        }
    }

    /**
     * Update load test status
     */
    async updateLoadTestStatus() {
        try {
            const status = await this.api.ipcAdminApiTestLoadStatusRetrieve();

            if (status) {
                // Update progress bar
                const progressBar = document.getElementById('load-test-progress');
                if (progressBar) {
                    const percentage = status.total > 0 ? (status.progress / status.total * 100) : 0;
                    progressBar.style.width = percentage + '%';
                }

                // Update progress text
                const progressText = document.getElementById('load-test-progress-text');
                if (progressText) {
                    progressText.textContent = `${status.progress} / ${status.total}`;
                }

                // Update stats
                this.updateElement('load-test-success', status.success_count);
                this.updateElement('load-test-failed', status.failed_count);
                this.updateElement('load-test-avg-time', status.avg_duration_ms?.toFixed(2) || '0');
                this.updateElement('load-test-rps', status.rps?.toFixed(2) || '0');

                // Check if test is complete
                if (!status.running && this.isLoadTestRunning) {
                    this.isLoadTestRunning = false;
                    this.stopLoadTestPolling();
                    this.toggleLoadTestButtons(false);
                    window.showNotification?.('Load test completed', 'success');
                }
            }

        } catch (error) {
            console.error('Error updating load test status:', error);
        }
    }

    /**
     * Helper: Update element text content
     */
    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }

    /**
     * Helper: Escape HTML to prevent XSS
     */
    escapeHtml(unsafe) {
        const div = document.createElement('div');
        div.textContent = unsafe;
        return div.innerHTML;
    }
}
