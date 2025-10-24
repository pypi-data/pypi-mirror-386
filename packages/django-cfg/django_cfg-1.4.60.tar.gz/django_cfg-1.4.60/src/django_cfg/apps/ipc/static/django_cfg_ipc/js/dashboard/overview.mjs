/**
 * RPC Overview Dashboard Module
 * Handles overview, requests, notifications, and methods tabs
 */
export class OverviewModule {
    constructor(api, dashboard) {
        this.api = api;
        this.dashboard = dashboard;
    }

    /**
     * Load data based on current tab
     */
    async loadData(tabName) {
        switch (tabName) {
            case 'overview':
                await this.loadOverviewStats();
                break;
            case 'requests':
                await this.loadRecentRequests();
                break;
            case 'notifications':
                await this.loadNotificationStats();
                break;
            case 'methods':
                await this.loadMethodStats();
                break;
        }
    }

    /**
     * Load overview statistics
     */
    async loadOverviewStats() {
        try {
            const stats = await this.api.ipcAdminApiMonitorOverviewRetrieve();

            if (stats) {
                // Update stats cards
                this.updateElement('total-requests', stats.total_requests_today || 0);
                this.updateElement('active-methods-count', stats.active_methods?.length || 0);
                this.updateElement('avg-response-time', (stats.avg_response_time_ms || 0).toFixed(0));
                this.updateElement('success-rate', (stats.success_rate || 0).toFixed(1));

                // Update top method (XSS-safe)
                if (stats.top_method) {
                    const topMethodElement = document.getElementById('top-method');
                    if (topMethodElement) {
                        const code = document.createElement('code');
                        code.className = 'bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded text-blue-600 dark:text-blue-300';
                        code.textContent = stats.top_method;
                        topMethodElement.innerHTML = '';
                        topMethodElement.appendChild(code);
                    }
                }
            }
        } catch (error) {
            console.error('Error loading overview stats:', error);
        }
    }

    /**
     * Load recent RPC requests
     */
    async loadRecentRequests() {
        try {
            const data = await this.api.ipcAdminApiMonitorRequestsRetrieve({ count: 50 });

            if (data) {
                const requests = data.requests || [];
                this.renderRequestsTable(requests);
            }
        } catch (error) {
            console.error('Error loading recent requests:', error);
        }
    }

    /**
     * Render requests table
     */
    renderRequestsTable(requests) {
        const tbody = document.getElementById('requests-table-body');
        if (!tbody) return;

        if (requests.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="4" class="px-4 py-8 text-center text-gray-500 dark:text-gray-400">
                        No recent requests found
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = requests.map(req => `
            <tr class="hover:bg-gray-50 dark:hover:bg-gray-700">
                <td class="px-4 py-3 text-sm">
                    ${this.formatTimestamp(req.timestamp)}
                </td>
                <td class="px-4 py-3">
                    <code class="text-sm bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">${this.escapeHtml(req.method || 'unknown')}</code>
                </td>
                <td class="px-4 py-3 text-sm font-mono">
                    ${this.escapeHtml((req.correlation_id || '').substring(0, 8))}...
                </td>
                <td class="px-4 py-3 text-sm">
                    <details class="cursor-pointer">
                        <summary class="text-blue-600 dark:text-blue-400 hover:underline">View</summary>
                        <pre class="mt-2 text-xs bg-gray-100 dark:bg-gray-900 p-2 rounded overflow-auto max-h-40">${this.escapeHtml(JSON.stringify(req.params || {}, null, 2))}</pre>
                    </details>
                </td>
            </tr>
        `).join('');
    }

    /**
     * Load notification statistics
     */
    async loadNotificationStats() {
        try {
            const stats = await this.api.ipcAdminApiMonitorNotificationsRetrieve();

            if (stats) {
                this.renderNotificationStats(stats);
            }
        } catch (error) {
            console.error('Error loading notification stats:', error);
        }
    }

    /**
     * Render notification statistics
     */
    renderNotificationStats(stats) {
        const container = document.getElementById('notification-stats-content');
        if (!container) return;

        const byType = stats.by_type || {};
        const total = stats.total_sent || 0;

        container.innerHTML = `
            <div class="space-y-4">
                <div class="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded">
                    <span>Total Sent</span>
                    <span class="text-2xl font-bold">${total}</span>
                </div>
                <div class="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded">
                    <span>Delivery Rate</span>
                    <span class="text-2xl font-bold text-green-600 dark:text-green-400">${stats.delivery_rate || 0}%</span>
                </div>
                <div>
                    <h4 class="text-md font-semibold mb-3">By Type</h4>
                    <div class="space-y-2">
                        ${Object.entries(byType).map(([type, count]) => `
                            <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded">
                                <span>${this.escapeHtml(type)}</span>
                                <span class="font-medium">${count}</span>
                            </div>
                        `).join('') || '<p class="text-gray-500 dark:text-gray-400">No data available</p>'}
                    </div>
                </div>
                ${stats.recent && stats.recent.length > 0 ? `
                    <div>
                        <h4 class="text-md font-semibold mb-3">Recent Notifications</h4>
                        <div class="space-y-2">
                            ${stats.recent.slice(0, 5).map(notif => `
                                <div class="p-3 bg-gray-50 dark:bg-gray-700 rounded">
                                    <div class="flex justify-between items-start">
                                        <span class="text-sm">${this.escapeHtml(notif.type || 'unknown')}</span>
                                        <span class="text-xs text-gray-500 dark:text-gray-400">${this.formatTimestamp(notif.timestamp)}</span>
                                    </div>
                                    ${notif.message ? `<p class="text-xs text-gray-600 dark:text-gray-400 mt-1">${this.escapeHtml(notif.message)}</p>` : ''}
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
    }

    /**
     * Load method statistics
     */
    async loadMethodStats() {
        try {
            const data = await this.api.ipcAdminApiMonitorMethodsRetrieve();

            if (data) {
                const methods = data.methods || [];
                this.renderMethodsTable(methods);
            }
        } catch (error) {
            console.error('Error loading method stats:', error);
        }
    }

    /**
     * Render methods table
     */
    renderMethodsTable(methods) {
        const tbody = document.getElementById('methods-table-body');
        if (!tbody) return;

        if (methods.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="4" class="px-4 py-8 text-center text-gray-500 dark:text-gray-400">
                        No method data available
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = methods.map(method => `
            <tr class="hover:bg-gray-50 dark:hover:bg-gray-700">
                <td class="px-4 py-3">
                    <code class="text-sm bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">${this.escapeHtml(method.method)}</code>
                </td>
                <td class="px-4 py-3 text-sm font-medium">${method.count}</td>
                <td class="px-4 py-3 text-sm">${method.percentage}%</td>
                <td class="px-4 py-3 text-sm">${method.avg_time_ms || method.avg_time || 0}ms</td>
            </tr>
        `).join('');
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
     * Helper: Format ISO timestamp to local time
     */
    formatTimestamp(isoString) {
        try {
            const date = new Date(isoString);
            return date.toLocaleTimeString();
        } catch {
            return 'N/A';
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
