// Global variables to store data
let accountsData = null;
let realmId = null;

// DOM Elements
const qbStatus = document.getElementById('qb-status');
const connectButton = document.getElementById('connect-qb');
const loadAccountsButton = document.getElementById('load-accounts');
const accountsTable = document.getElementById('accounts-table');
const analysisSummary = document.getElementById('analysis-summary');
const positiveInsights = document.getElementById('positive-insights');
const concerns = document.getElementById('concerns');
const recommendations = document.getElementById('recommendations');
const questionInput = document.getElementById('question');
const askButton = document.getElementById('ask-button');
const answer = document.getElementById('answer');
const suggestedQuestions = document.getElementById('suggested-questions');
const accountsChart = document.getElementById('accounts-chart');

// Initialize the chart with empty data
let accountDistributionChart = new Chart(accountsChart, {
    type: 'doughnut',
    data: {
        labels: [],
        datasets: [{
            data: [],
            backgroundColor: [
                'rgba(54, 162, 235, 0.7)',
                'rgba(255, 99, 132, 0.7)',
                'rgba(75, 192, 192, 0.7)',
                'rgba(153, 102, 255, 0.7)',
                'rgba(255, 159, 64, 0.7)'
            ]
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false
    }
});

// Check the QuickBooks connection status
async function checkConnectionStatus() {
    try {
        const response = await fetch('/api/financial/connection-status');
        const data = await response.json();

        if (data.connected) {
            qbStatus.innerHTML = '<p class="text-green-600">✓ Connected to QuickBooks</p>';
            connectButton.textContent = 'Reconnect to QuickBooks';
            loadAccountsButton.disabled = false;
            realmId = data.realm_id;
            return true;
        } else {
            qbStatus.innerHTML = '<p class="text-yellow-600">Not connected to QuickBooks</p>';
            connectButton.textContent = 'Connect to QuickBooks';
            loadAccountsButton.disabled = true;
            return false;
        }
    } catch (error) {
        console.error('Error checking connection status:', error);
        qbStatus.innerHTML = `<p class="text-red-600">Error checking connection: ${error.message}</p>`;
        return false;
    }
}

// Load suggested questions
async function loadSuggestedQuestions() {
    try {
        const response = await fetch('/api/financial/suggested-questions');
        const data = await response.json();

        suggestedQuestions.innerHTML = '';
        data.questions.forEach(question => {
            const btn = document.createElement('button');
            btn.classList.add('bg-gray-200', 'hover:bg-gray-300', 'rounded', 'px-3', 'py-1', 'text-sm');
            btn.textContent = question;
            btn.addEventListener('click', () => {
                questionInput.value = question;
            });
            suggestedQuestions.appendChild(btn);
        });
    } catch (error) {
        console.error('Error loading suggested questions:', error);
        suggestedQuestions.innerHTML = '<span class="text-red-500">Failed to load suggestions</span>';
    }
}

// Connect to QuickBooks
connectButton.addEventListener('click', async () => {
    try {
        const response = await fetch('/api/financial/auth-url');
        const data = await response.json();

        // Redirect to QuickBooks authorization
        window.location.href = data.auth_url;
    } catch (error) {
        console.error('Error getting auth URL:', error);
        qbStatus.innerHTML = `<p class="text-red-600">Error connecting to QuickBooks: ${error.message}</p>`;
    }
});

// Load chart of accounts
loadAccountsButton.addEventListener('click', async () => {
    try {
        // Use the realmId from the connection check
        if (!realmId) {
            const connected = await checkConnectionStatus();
            if (!connected) {
                accountsTable.innerHTML = `
                    <tr>
                        <td colspan="3" class="px-4 py-2 text-center border text-red-600">
                            Not connected to QuickBooks. Please connect first.
                        </td>
                    </tr>
                `;
                return;
            }
        }

        qbStatus.innerHTML = '<p class="text-blue-600">Loading accounts...</p>';

        const response = await fetch(`/api/financial/accounts?realm_id=${realmId}`);
        accountsData = await response.json();

        // Display accounts in the table
        displayAccounts(accountsData);

        // Update chart
        updateChart(accountsData);

        // Enable asking questions
        askButton.disabled = false;

        qbStatus.innerHTML = '<p class="text-green-600">✓ Connected to QuickBooks | Accounts loaded</p>';

    } catch (error) {
        console.error('Error loading accounts:', error);
        qbStatus.innerHTML = '<p class="text-red-600">Error loading accounts</p>';
        accountsTable.innerHTML = `
            <tr>
                <td colspan="3" class="px-4 py-2 text-center border text-red-600">
                    Error loading accounts: ${error.message}
                </td>
            </tr>
        `;
    }
});

// Analyze accounts
async function analyzeAccounts() {
    if (!accountsData) return;

    analysisSummary.innerHTML = '<p class="text-gray-500">Analyzing financial data...</p>';

    try {
        const response = await fetch('/api/financial/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ accounts_data: accountsData })
        });

        const analysis = await response.json();

        // Display summary
        analysisSummary.innerHTML = `<p>${analysis.summary || 'Analysis complete.'}</p>`;

        // Display positive insights
        positiveInsights.innerHTML = '';
        if (analysis.positive_insights && analysis.positive_insights.length > 0) {
            analysis.positive_insights.forEach(insight => {
                const insightObj = typeof insight === 'string' ? { description: insight } : insight;
                positiveInsights.innerHTML += `
                    <div class="mb-3">
                        <h3 class="font-medium text-green-600">${insightObj.title || 'Insight'}</h3>
                        <p>${insightObj.description}</p>
                    </div>
                `;
            });
        } else {
            positiveInsights.innerHTML = '<p class="text-gray-500">No positive insights found.</p>';
        }

        // Display concerns
        concerns.innerHTML = '';
        if (analysis.concerns && analysis.concerns.length > 0) {
            analysis.concerns.forEach(concern => {
                const concernObj = typeof concern === 'string' ? { description: concern } : concern;
                concerns.innerHTML += `
                    <div class="mb-3">
                        <h3 class="font-medium text-yellow-600">${concernObj.title || 'Concern'}</h3>
                        <p>${concernObj.description}</p>
                    </div>
                `;
            });
        } else {
            concerns.innerHTML = '<p class="text-gray-500">No concerns found.</p>';
        }

        // Display recommendations
        recommendations.innerHTML = '';
        if (analysis.recommendations && analysis.recommendations.length > 0) {
            analysis.recommendations.forEach(rec => {
                const recObj = typeof rec === 'string' ? { description: rec } : rec;
                recommendations.innerHTML += `
                    <div class="mb-3">
                        <h3 class="font-medium text-blue-600">${recObj.title || 'Recommendation'}</h3>
                        <p>${recObj.description}</p>
                    </div>
                `;
            });
        } else {
            recommendations.innerHTML = '<p class="text-gray-500">No recommendations found.</p>';
        }

    } catch (error) {
        console.error('Error analyzing accounts:', error);
        analysisSummary.innerHTML = `<p class="text-red-600">Error analyzing accounts: ${error.message}</p>`;
        positiveInsights.innerHTML = '<p class="text-gray-500">Unavailable due to analysis error.</p>';
        concerns.innerHTML = '<p class="text-gray-500">Unavailable due to analysis error.</p>';
        recommendations.innerHTML = '<p class="text-gray-500">Unavailable due to analysis error.</p>';
    }
}

// Ask a question
askButton.addEventListener('click', async () => {
    const question = questionInput.value.trim();

    if (!question) return;
    if (!accountsData) {
        answer.innerHTML = `<p class="text-red-600">Please load your accounts data first</p>`;
        return;
    }

    answer.innerHTML = '<p class="text-gray-500">Analyzing your question...</p>';

    try {
        const response = await fetch('/api/financial/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                accounts_data: accountsData,
                question: question
            })
        });

        const data = await response.json();

        answer.innerHTML = `<p>${data.answer}</p>`;

    } catch (error) {
        console.error('Error asking question:', error);
        answer.innerHTML = `<p class="text-red-600">Error: ${error.message}</p>`;
    }
});

// Display accounts in the table
function displayAccounts(data) {
    if (!data || !data.QueryResponse) {
        accountsTable.innerHTML = `
            <tr>
                <td colspan="3" class="px-4 py-2 text-center border">
                    No account data available
                </td>
            </tr>
        `;
        return;
    }

    const accounts = data.QueryResponse.Account || [];

    accountsTable.innerHTML = '';

    if (accounts.length === 0) {
        accountsTable.innerHTML = `
            <tr>
                <td colspan="3" class="px-4 py-2 text-center border">
                    No accounts found
                </td>
            </tr>
        `;
        return;
    }

    accounts.forEach(account => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td class="px-4 py-2 border">${account.Name}</td>
            <td class="px-4 py-2 border">${account.AccountType}</td>
            <td class="px-4 py-2 text-right border">$${(account.CurrentBalance || 0).toFixed(2)}</td>
        `;
        accountsTable.appendChild(row);
    });

    // After displaying accounts, analyze them
    analyzeAccounts();
}

// Update the chart with account data
function updateChart(data) {
    if (!data || !data.QueryResponse) {
        return;
    }

    const accounts = data.QueryResponse.Account || [];

    // Group accounts by type
    const accountTypes = {};

    accounts.forEach(account => {
        const type = account.AccountType;
        if (!accountTypes[type]) {
            accountTypes[type] = 0;
        }
        accountTypes[type] += account.CurrentBalance || 0;
    });

    // Update chart
    accountDistributionChart.data.labels = Object.keys(accountTypes);
    accountDistributionChart.data.datasets[0].data = Object.values(accountTypes);
    accountDistributionChart.update();
}

// Initialize the page
document.addEventListener('DOMContentLoaded', async () => {
    // Check if already connected to QuickBooks
    await checkConnectionStatus();

    // Load suggested questions
    loadSuggestedQuestions();

    // Check URL for query parameters that might indicate a callback
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('code') && urlParams.has('realmId')) {
        // This might be a callback from QuickBooks - display a message
        qbStatus.innerHTML = '<p class="text-green-600">✓ Authentication successful! The page will reload shortly.</p>';

        // Wait a moment and then refresh the page to clear the URL parameters
        setTimeout(() => {
            window.location.href = '/financial';
        }, 3000);
    }
});