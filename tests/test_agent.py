import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from app.agents.financial_agent.agent import FinancialAnalysisAgent
from app.services.quickbooks import QuickBooksService

# Keep your existing mock data
MOCK_ACCOUNTS = {
    "Account": [
        {"Classification": "Asset", "AccountType": "Bank", "CurrentBalance": 50000.00},
        {
            "Classification": "Income",
            "AccountType": "Revenue",
            "CurrentBalance": 100000.00,
        },
        {
            "Classification": "Expense",
            "AccountType": "Expense",
            "CurrentBalance": 60000.00,
        },
    ]
}

MOCK_INVOICES = {
    "Invoice": [
        {
            "TxnDate": "2024-01-15",
            "TotalAmt": 5000.00,
            "Balance": 1000.00,
            "CustomerRef": {"value": "1"},
        }
    ]
}


@pytest.fixture
def mock_qb_service():
    """Create a mock QuickBooks service"""
    mock_service = Mock(spec=QuickBooksService)
    mock_service.get_accounts.return_value = MOCK_ACCOUNTS
    mock_service.get_invoices.return_value = MOCK_INVOICES
    mock_service.get_company_info.return_value = {"CompanyName": "Test Company"}
    return mock_service


@pytest.fixture
def financial_agent(mock_qb_service):
    """Create a FinancialAnalysisAgent with mock QuickBooks service"""
    return FinancialAnalysisAgent(api_key="ryze_test_key", qb_service=mock_qb_service)


def test_process_input_basics(financial_agent):
    """Test basic input processing"""
    input_data = {"realm_id": "test_realm"}
    result = financial_agent.process_input(input_data)

    assert isinstance(result, dict)
    assert "financial_metrics" in result
    assert "quickbooks_data" in result
    assert "document_analysis" in result


def test_process_accounts(financial_agent):
    """Test account processing and categorization"""
    result = financial_agent._process_accounts("test_realm")

    assert "assets" in result
    assert "income" in result
    assert "expenses" in result
    assert len(result["assets"]) == 1
    assert len(result["income"]) == 1
    assert len(result["expenses"]) == 1


def test_calculate_profit_loss(financial_agent):
    """Test profit and loss calculations"""
    result = financial_agent._calculate_profit_loss("test_realm")

    assert result["total_income"] == 100000.00
    assert result["total_expenses"] == 60000.00
    assert result["net_profit"] == 40000.00
    assert "profit_margin" in result


def test_generate_response(financial_agent):
    """Test response generation structure"""
    processed_data = financial_agent.process_input({"realm_id": "test_realm"})
    result = financial_agent.generate_response(processed_data)

    assert "analysis" in result
    assert "metrics" in result
    assert "recommendations" in result


def test_missing_realm_id(financial_agent):
    """Test error handling for missing realm_id"""
    with pytest.raises(ValueError):
        financial_agent.process_input({})
