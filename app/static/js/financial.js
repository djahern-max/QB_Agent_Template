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

        // Open QuickBooks authorization in a new window
        window.open(data.auth_url, '_blank');

        qbStatus.innerHTML = '<p class="text-yellow-600">Authorization window opened. Please complete the authorization process.</p>';

        // In a real app, you'd implement a way to detect when auth is complete
        // For now, we'll just enable the load button
        qbStatus.innerHTML = '<p class="text-green-600">✓ Connected to QuickBooks</p>';
        loadAccountsButton.disabled = false;

    } catch (error) {
        console.error('Error getting auth URL:', error);
        qbStatus.innerHTML = `<p class="text-red-600">Error connecting to QuickBooks: ${error.message}</p>`;
    }
});

// Load chart of accounts
loadAccountsButton.addEventListener('click', async () => {
    try {
        // For demo, we'll use a hardcoded realm ID
        // In a real app, you'd get this from your auth process
        realmId = '9130355986898714'; // Replace with your actual realm ID or get it from auth

        const response = await fetch(`/api/financial/accounts?realm_id=${realmId}`);
        accountsData = await response.json();

        // Display accounts in the table
        displayAccounts(accountsData);

        // Update chart
        updateChart(accountsData);

        // Enable asking questions
        askButton.disabled = false;

    } catch (error) {
        console.error('Error loading accounts:', error);
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
        analysisSummary.innerHTML = `<p>${analysis.summary}</p>`;

        // Display positive insights
        positiveInsights.innerHTML = '';
        if (analysis.positive_insights) {
            analysis.positive_insights.forEach(insight => {
                positiveInsights.innerHTML += `
                    <div class="mb-3">
                        <h3 class="font-medium text-green-600">${insight.title}</h3>
                        <p>${insight.description}</p>
                    </div>
                `;
            });
        }

        // Display concerns
        concerns.innerHTML = '';
        if (analysis.concerns) {
            analysis.concerns.forEach(concern => {
                concerns.innerHTML += `
                    <div class="mb-3">
                        <h3 class="font-medium text-yellow-600">${concern.title}</h3>
                        <p>${concern.description}</p>
                    </div>
                `;
            });
        }

        // Display recommendations
        recommendations.innerHTML = '';
        if (analysis.recommendations) {
            analysis.recommendations.forEach(rec => {
                recommendations.innerHTML += `
                    <div class="mb-3">
                        <h3 class="font-medium text-blue-600">${rec.title}</h3>
                        <p>${rec.description}</p>
                    </div>
                `;
            });
        }

    } catch (error) {
        console.error('Error analyzing accounts:', error);
        analysisSummary.innerHTML = `<p class="text-red-600">Error analyzing accounts: ${error.message}</p>`;
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
    const accounts = data.QueryResponse?.Account || [];

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
    const accounts = data.QueryResponse?.Account || [];

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
document.addEventListener('DOMContentLoaded', () => {
    // Load suggested questions
    loadSuggestedQuestions();

    // Check if already connected to QuickBooks
    // You could add an API endpoint to check this
});