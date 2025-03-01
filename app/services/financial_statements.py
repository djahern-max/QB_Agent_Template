# app/services/financial_statements.py
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from sqlalchemy.orm import Session

from ..services.quickbooks import QuickbooksService
from ..models import FinancialAnalysis
import traceback

logger = logging.getLogger(__name__)


class FinancialStatementsService:
    def __init__(self, quickbooks_service: QuickbooksService):
        self.qb_service = quickbooks_service

    async def get_profit_and_loss(
        self, realm_id: str, start_date: str, end_date: str
    ) -> Dict[str, Any]:
        """
        Generate a Profit and Loss statement for the specified period using QBO Report API.

        Args:
            realm_id: QuickBooks realm ID
            start_date: Start date in format YYYY-MM-DD
            end_date: End date in format YYYY-MM-DD

        Returns:
            Dict containing the formatted P&L statement
        """
        try:
            # Call the QBO ProfitAndLoss report endpoint
            report_data = await self.qb_service.get_report(
                realm_id=realm_id,
                report_type="ProfitAndLoss",
                params={
                    "start_date": start_date,
                    "end_date": end_date,
                    "minorversion": "75",  # Use the version from your API call
                },
            )

            # Process the report response into our standardized format
            # This will depend on the exact structure of QBO's response
            formatted_data = self._format_profit_and_loss(
                report_data, start_date, end_date
            )
            return formatted_data

        except Exception as e:
            logger.error(f"Error generating Profit & Loss statement: {str(e)}")
            raise

    async def get_balance_sheet(self, realm_id: str, as_of_date: str) -> Dict[str, Any]:
        """
        Generate a Balance Sheet as of the specified date using QBO Report API.

        Args:
            realm_id: QuickBooks realm ID
            as_of_date: Date for the balance sheet in format YYYY-MM-DD

        Returns:
            Dict containing the formatted Balance Sheet
        """
        try:
            # Log the parameters
            logger.debug(
                f"Getting balance sheet for realm_id={realm_id}, as_of_date={as_of_date}"
            )

            # Call the QBO BalanceSheet report endpoint
            report_data = await self.qb_service.get_report(
                realm_id=realm_id,
                report_type="BalanceSheet",
                params={
                    "as_of": as_of_date,  # Use "as_of" parameter
                    "minorversion": "75",
                },
            )

            # Process the report response into our standardized format
            formatted_data = self._format_balance_sheet(report_data, as_of_date)
            return formatted_data

        except Exception as e:
            logger.error(f"Error generating Balance Sheet: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise


async def get_cash_flow_statement(
    self, realm_id: str, start_date: str, end_date: str
) -> Dict[str, Any]:
    """
    Generate a Statement of Cash Flows for the specified period using QBO Report API.

    Args:
        realm_id: QuickBooks realm ID
        start_date: Start date in format YYYY-MM-DD
        end_date: End date in format YYYY-MM-DD

    Returns:
        Dict containing the formatted Statement of Cash Flows
    """
    try:
        # Log the parameters
        logger.debug(
            f"Getting cash flow for realm_id={realm_id}, start_date={start_date}, end_date={end_date}"
        )

        # Try with "StatementOfCashFlows" first
        try:
            report_data = await self.qb_service.get_report(
                realm_id=realm_id,
                report_type="StatementOfCashFlows",
                params={
                    "start_date": start_date,
                    "end_date": end_date,
                    "minorversion": "75",
                },
            )
        except Exception as e1:
            logger.warning(
                f"Error with StatementOfCashFlows, trying CashFlow: {str(e1)}"
            )
            # Fall back to "CashFlow" if the first attempt fails
            report_data = await self.qb_service.get_report(
                realm_id=realm_id,
                report_type="CashFlow",
                params={
                    "start_date": start_date,
                    "end_date": end_date,
                    "minorversion": "75",
                },
            )

        # Process the report response into our standardized format
        formatted_data = self._format_cash_flow(report_data, start_date, end_date)
        return formatted_data

    except Exception as e:
        logger.error(f"Error generating Cash Flow Statement: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

    def _format_profit_and_loss(
        self, report_data: Dict[str, Any], start_date: str, end_date: str
    ) -> Dict[str, Any]:
        """
        Format the QuickBooks ProfitAndLoss report response into our standardized format.

        The exact implementation will depend on the structure of the QBO report response.
        This is a placeholder that should be updated once you have examined the actual response.
        """
        # Extract company name from report header
        company_name = (
            report_data.get("Header", {})
            .get("ReportName", "")
            .replace("Profit and Loss", "")
            .strip()
        )
        if not company_name:
            company_name = "Your Company"

        # Initialize sections
        income_items = []
        cogs_items = []
        expense_items = []
        other_income_items = []
        other_expense_items = []

        # Process report rows
        # The actual structure will depend on QBO's response format
        rows = report_data.get("Rows", {}).get("Row", [])

        # Track totals
        total_income = 0
        total_cogs = 0
        total_expenses = 0
        total_other_income = 0
        total_other_expense = 0

        # Extract data from rows
        # This is a simplistic example - the actual QBO response will need careful parsing
        for row in rows:
            if row.get("group") == "Income" and not row.get("Summary"):
                for detail in row.get("Rows", {}).get("Row", []):
                    if detail.get("type") == "Data":
                        amount = float(detail.get("value", 0))
                        income_items.append(
                            {
                                "id": detail.get("id", ""),
                                "name": detail.get("ColData", [{}])[0].get("value", ""),
                                "amount": amount,
                                "account_type": "Income",
                            }
                        )
                        total_income += amount

            # Continue similar parsing for other sections...

        # Calculate key figures
        gross_profit = total_income - total_cogs
        operating_income = gross_profit - total_expenses
        net_income = operating_income + total_other_income - total_other_expense

        # Return formatted data
        return {
            "statement_type": "Profit and Loss",
            "company_name": company_name,
            "period": {"start_date": start_date, "end_date": end_date},
            "income": income_items,
            "total_income": total_income,
            "cost_of_goods_sold": cogs_items,
            "total_cogs": total_cogs,
            "gross_profit": gross_profit,
            "expenses": expense_items,
            "total_expenses": total_expenses,
            "operating_income": operating_income,
            "other_income": other_income_items,
            "total_other_income": total_other_income,
            "other_expenses": other_expense_items,
            "total_other_expenses": total_other_expense,
            "net_income": net_income,
        }

    def _format_balance_sheet(
        self, report_data: Dict[str, Any], as_of_date: str
    ) -> Dict[str, Any]:
        """
        Format the QuickBooks BalanceSheet report response into our standardized format.

        The exact implementation will depend on the structure of the QBO report response.
        This is a placeholder that should be updated once you have examined the actual response.
        """
        # Implementation details would go here based on actual QBO response format
        # For now, this is a placeholder
        return {
            "statement_type": "Balance Sheet",
            "company_name": "Your Company",
            "as_of_date": as_of_date,
            "assets": [],
            "total_assets": 0,
            "liabilities": [],
            "total_liabilities": 0,
            "equity": [],
            "total_equity": 0,
            "liabilities_and_equity": 0,
        }

    def _format_cash_flow(
        self, report_data: Dict[str, Any], start_date: str, end_date: str
    ) -> Dict[str, Any]:
        """
        Format the QuickBooks CashFlow report response into our standardized format.

        The exact implementation will depend on the structure of the QBO report response.
        This is a placeholder that should be updated once you have examined the actual response.
        """
        # Implementation details would go here based on actual QBO response format
        # For now, this is a placeholder
        return {
            "statement_type": "Statement of Cash Flows",
            "company_name": "Your Company",
            "period": {"start_date": start_date, "end_date": end_date},
            "operating_activities": {"net_income": 0, "adjustments": []},
            "total_operating_cash_flow": 0,
            "investing_activities": [],
            "total_investing_cash_flow": 0,
            "financing_activities": [],
            "total_financing_cash_flow": 0,
            "net_cash_change": 0,
            "beginning_cash_balance": 0,
            "ending_cash_balance": 0,
        }

    async def analyze_financial_trends(
        self, realm_id: str, db: Session
    ) -> Dict[str, Any]:
        """
        Analyze financial trends by comparing current statements with previous periods.

        Args:
            realm_id: QuickBooks realm ID
            db: Database session

        Returns:
            Dict containing financial trends analysis
        """
        try:
            # Get current date info for default periods
            today = datetime.now()
            current_month_start = today.replace(day=1).strftime("%Y-%m-%d")
            current_month_end = today.strftime("%Y-%m-%d")

            # For previous period comparison - get previous month
            prev_month = today.replace(day=1) - timedelta(days=1)
            prev_month_start = prev_month.replace(day=1).strftime("%Y-%m-%d")
            prev_month_end = prev_month.strftime("%Y-%m-%d")

            # Get current financial statements
            current_pl = await self.get_profit_and_loss(
                realm_id, current_month_start, current_month_end
            )
            current_bs = await self.get_balance_sheet(realm_id, current_month_end)
            current_cf = await self.get_cash_flow_statement(
                realm_id, current_month_start, current_month_end
            )

            # Get previous period statements for comparison
            prev_pl = await self.get_profit_and_loss(
                realm_id, prev_month_start, prev_month_end
            )
            prev_bs = await self.get_balance_sheet(realm_id, prev_month_end)
            prev_cf = await self.get_cash_flow_statement(
                realm_id, prev_month_start, prev_month_end
            )

            # Perform trend analysis
            pl_trends = self._analyze_pl_trends(current_pl, prev_pl)
            bs_trends = self._analyze_bs_trends(current_bs, prev_bs)
            cf_trends = self._analyze_cf_trends(current_cf, prev_cf)

            # Create financial analysis record
            analysis = FinancialAnalysis(
                realm_id=realm_id,
                summary=self._generate_summary(pl_trends, bs_trends, cf_trends),
                positive_insights=self._extract_positive_insights(
                    pl_trends, bs_trends, cf_trends
                ),
                concerns=self._extract_concerns(pl_trends, bs_trends, cf_trends),
                recommendations=self._generate_recommendations(
                    pl_trends, bs_trends, cf_trends
                ),
                analysis_date=today,
            )

            # Save to database
            db.add(analysis)
            db.commit()

            # Return consolidated trends
            return {
                "profit_loss_trends": pl_trends,
                "balance_sheet_trends": bs_trends,
                "cash_flow_trends": cf_trends,
                "summary": analysis.summary,
                "positive_insights": analysis.positive_insights,
                "concerns": analysis.concerns,
                "recommendations": analysis.recommendations,
                "analysis_date": analysis.analysis_date.isoformat(),
            }

        except Exception as e:
            logger.error(f"Error analyzing financial trends: {str(e)}")
            raise

    def _analyze_pl_trends(
        self, current_pl: Dict[str, Any], prev_pl: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze trends in Profit & Loss statements"""
        trends = {}

        try:
            # Get key metrics from current P&L
            current_total_income = self._extract_pl_value(current_pl, "total_income")
            current_total_cogs = self._extract_pl_value(current_pl, "total_cogs")
            current_gross_profit = self._extract_pl_value(current_pl, "gross_profit")
            current_total_expenses = self._extract_pl_value(
                current_pl, "total_expenses"
            )
            current_net_income = self._extract_pl_value(current_pl, "net_income")

            # Get key metrics from previous P&L
            prev_total_income = self._extract_pl_value(prev_pl, "total_income")
            prev_total_cogs = self._extract_pl_value(prev_pl, "total_cogs")
            prev_gross_profit = self._extract_pl_value(prev_pl, "gross_profit")
            prev_total_expenses = self._extract_pl_value(prev_pl, "total_expenses")
            prev_net_income = self._extract_pl_value(prev_pl, "net_income")

            # Calculate changes (percentage)
            trends["revenue_change"] = self._calculate_percentage_change(
                current_total_income, prev_total_income
            )
            trends["cogs_change"] = self._calculate_percentage_change(
                current_total_cogs, prev_total_cogs
            )
            trends["gross_profit_change"] = self._calculate_percentage_change(
                current_gross_profit, prev_gross_profit
            )
            trends["expenses_change"] = self._calculate_percentage_change(
                current_total_expenses, prev_total_expenses
            )
            trends["net_income_change"] = self._calculate_percentage_change(
                current_net_income, prev_net_income
            )

            # Calculate current ratios
            if current_total_income > 0:
                trends["gross_margin"] = (
                    current_gross_profit / current_total_income
                ) * 100
                trends["net_margin"] = (current_net_income / current_total_income) * 100
            else:
                trends["gross_margin"] = 0
                trends["net_margin"] = 0

            # Compare with previous ratios
            if prev_total_income > 0:
                prev_gross_margin = (prev_gross_profit / prev_total_income) * 100
                prev_net_margin = (prev_net_income / prev_total_income) * 100
                trends["gross_margin_change"] = (
                    trends["gross_margin"] - prev_gross_margin
                )
                trends["net_margin_change"] = trends["net_margin"] - prev_net_margin
            else:
                trends["gross_margin_change"] = 0
                trends["net_margin_change"] = 0

            return trends
        except Exception as e:
            logger.error(f"Error analyzing P&L trends: {str(e)}")
            return {"error": str(e)}

    def _analyze_bs_trends(
        self, current_bs: Dict[str, Any], prev_bs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze trends in Balance Sheet statements"""
        trends = {}

        try:
            # Extract key metrics from Balance Sheets
            current_total_assets = self._extract_bs_value(current_bs, "total_assets")
            current_current_assets = self._extract_bs_value(
                current_bs, "current_assets"
            )
            current_total_liabilities = self._extract_bs_value(
                current_bs, "total_liabilities"
            )
            current_current_liabilities = self._extract_bs_value(
                current_bs, "current_liabilities"
            )
            current_total_equity = self._extract_bs_value(current_bs, "total_equity")

            prev_total_assets = self._extract_bs_value(prev_bs, "total_assets")
            prev_current_assets = self._extract_bs_value(prev_bs, "current_assets")
            prev_total_liabilities = self._extract_bs_value(
                prev_bs, "total_liabilities"
            )
            prev_current_liabilities = self._extract_bs_value(
                prev_bs, "current_liabilities"
            )
            prev_total_equity = self._extract_bs_value(prev_bs, "total_equity")

            # Calculate changes
            trends["total_assets_change"] = self._calculate_percentage_change(
                current_total_assets, prev_total_assets
            )
            trends["total_liabilities_change"] = self._calculate_percentage_change(
                current_total_liabilities, prev_total_liabilities
            )
            trends["equity_change"] = self._calculate_percentage_change(
                current_total_equity, prev_total_equity
            )

            # Calculate key ratios
            trends["current_ratio"] = current_current_assets / max(
                current_current_liabilities, 1
            )
            trends["debt_to_equity"] = current_total_liabilities / max(
                current_total_equity, 1
            )

            # Compare with previous ratios
            prev_current_ratio = prev_current_assets / max(prev_current_liabilities, 1)
            prev_debt_to_equity = prev_total_liabilities / max(prev_total_equity, 1)

            trends["current_ratio_change"] = (
                trends["current_ratio"] - prev_current_ratio
            )
            trends["debt_to_equity_change"] = (
                trends["debt_to_equity"] - prev_debt_to_equity
            )

            return trends
        except Exception as e:
            logger.error(f"Error analyzing Balance Sheet trends: {str(e)}")
            return {"error": str(e)}

    def _analyze_cf_trends(
        self, current_cf: Dict[str, Any], prev_cf: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze trends in Cash Flow statements"""
        trends = {}

        try:
            # Extract key metrics
            current_operating_cash = self._extract_cf_value(
                current_cf, "total_operating_cash_flow"
            )
            current_investing_cash = self._extract_cf_value(
                current_cf, "total_investing_cash_flow"
            )
            current_financing_cash = self._extract_cf_value(
                current_cf, "total_financing_cash_flow"
            )
            current_net_cash = self._extract_cf_value(current_cf, "net_cash_change")

            prev_operating_cash = self._extract_cf_value(
                prev_cf, "total_operating_cash_flow"
            )
            prev_investing_cash = self._extract_cf_value(
                prev_cf, "total_investing_cash_flow"
            )
            prev_financing_cash = self._extract_cf_value(
                prev_cf, "total_financing_cash_flow"
            )
            prev_net_cash = self._extract_cf_value(prev_cf, "net_cash_change")

            # Calculate changes
            trends["operating_cash_change"] = self._calculate_percentage_change(
                current_operating_cash, prev_operating_cash
            )
            trends["investing_cash_change"] = self._calculate_percentage_change(
                current_investing_cash, prev_investing_cash
            )
            trends["financing_cash_change"] = self._calculate_percentage_change(
                current_financing_cash, prev_financing_cash
            )
            trends["net_cash_change"] = self._calculate_percentage_change(
                current_net_cash, prev_net_cash
            )

            return trends
        except Exception as e:
            logger.error(f"Error analyzing Cash Flow trends: {str(e)}")
            return {"error": str(e)}

    def _calculate_percentage_change(self, current: float, previous: float) -> float:
        """Calculate percentage change between two values"""
        if previous == 0:
            return 0.0
        return ((current - previous) / abs(previous)) * 100

    def _extract_pl_value(self, pl_data: Dict[str, Any], key: str) -> float:
        """Extract numerical value from P&L data safely"""
        try:
            value = pl_data.get(key, 0)
            return float(value) if value is not None else 0.0
        except (ValueError, TypeError):
            return 0.0

    def _extract_bs_value(self, bs_data: Dict[str, Any], key: str) -> float:
        """Extract numerical value from Balance Sheet data safely"""
        try:
            value = bs_data.get(key, 0)
            return float(value) if value is not None else 0.0
        except (ValueError, TypeError):
            return 0.0

    def _extract_cf_value(self, cf_data: Dict[str, Any], key: str) -> float:
        """Extract numerical value from Cash Flow data safely"""
        try:
            value = cf_data.get(key, 0)
            return float(value) if value is not None else 0.0
        except (ValueError, TypeError):
            return 0.0

    def _generate_summary(self, pl_trends, bs_trends, cf_trends) -> str:
        """Generate an overall summary of financial health"""
        # Example summary generation
        revenue_change = pl_trends.get("revenue_change", 0)
        net_income_change = pl_trends.get("net_income_change", 0)
        current_ratio = bs_trends.get("current_ratio", 0)
        operating_cash = cf_trends.get("operating_cash_change", 0)

        summary_parts = []

        # Revenue analysis
        if revenue_change > 10:
            summary_parts.append("Revenue is growing strongly.")
        elif revenue_change > 0:
            summary_parts.append("Revenue is showing moderate growth.")
        elif revenue_change < -10:
            summary_parts.append("Revenue has declined significantly.")
        elif revenue_change < 0:
            summary_parts.append("Revenue has slightly decreased.")
        else:
            summary_parts.append("Revenue has remained stable.")

        # Profitability analysis
        if net_income_change > 10:
            summary_parts.append("Profitability has improved significantly.")
        elif net_income_change > 0:
            summary_parts.append("Profitability has slightly improved.")
        elif net_income_change < -10:
            summary_parts.append("Profitability has declined significantly.")
        elif net_income_change < 0:
            summary_parts.append("Profitability has slightly decreased.")
        else:
            summary_parts.append("Profitability has remained stable.")

        # Liquidity analysis
        if current_ratio >= 2:
            summary_parts.append("Liquidity position is strong.")
        elif current_ratio >= 1:
            summary_parts.append("Liquidity position is adequate.")
        else:
            summary_parts.append("Liquidity position needs attention.")

        # Cash flow analysis
        if operating_cash > 10:
            summary_parts.append("Operating cash flow has improved significantly.")
        elif operating_cash > 0:
            summary_parts.append("Operating cash flow has slightly improved.")
        elif operating_cash < -10:
            summary_parts.append("Operating cash flow has declined significantly.")
        elif operating_cash < 0:
            summary_parts.append("Operating cash flow has slightly decreased.")
        else:
            summary_parts.append("Operating cash flow has remained stable.")

        return " ".join(summary_parts)

    def _extract_positive_insights(self, pl_trends, bs_trends, cf_trends) -> str:
        """Extract positive insights from the financial analysis"""
        insights = []

        # Check for positive trends
        if pl_trends.get("revenue_change", 0) > 0:
            insights.append(f"Revenue increased by {pl_trends['revenue_change']:.1f}%")

        if pl_trends.get("net_income_change", 0) > 0:
            insights.append(
                f"Net income improved by {pl_trends['net_income_change']:.1f}%"
            )

        if pl_trends.get("gross_margin_change", 0) > 0:
            insights.append(
                f"Gross margin improved by {pl_trends['gross_margin_change']:.1f} percentage points"
            )

        if bs_trends.get("current_ratio", 0) > 1.5:
            insights.append("Strong short-term liquidity position")

        if cf_trends.get("operating_cash_change", 0) > 0:
            insights.append("Improving operating cash flow")

        return (
            ", ".join(insights)
            if insights
            else "No significant positive trends identified."
        )

    def _extract_concerns(self, pl_trends, bs_trends, cf_trends) -> str:
        """Extract areas of concern from the financial analysis"""
        concerns = []

        # Check for negative trends
        if pl_trends.get("revenue_change", 0) < 0:
            concerns.append(
                f"Revenue decreased by {abs(pl_trends['revenue_change']):.1f}%"
            )

        if pl_trends.get("net_income_change", 0) < 0:
            concerns.append(
                f"Net income decreased by {abs(pl_trends['net_income_change']):.1f}%"
            )

        if pl_trends.get("expenses_change", 0) > pl_trends.get("revenue_change", 0):
            concerns.append("Expenses growing faster than revenue")

        if bs_trends.get("current_ratio", 0) < 1:
            concerns.append(
                "Current ratio below 1.0 indicates potential liquidity issues"
            )

        if bs_trends.get("debt_to_equity", 0) > 2:
            concerns.append("High debt-to-equity ratio may indicate excessive leverage")

        if cf_trends.get("operating_cash_change", 0) < 0:
            concerns.append("Declining operating cash flow")

        return (
            ", ".join(concerns) if concerns else "No significant concerns identified."
        )

    def _generate_recommendations(self, pl_trends, bs_trends, cf_trends) -> str:
        """Generate recommendations based on financial analysis"""
        recommendations = []

        # Revenue recommendations
        if pl_trends.get("revenue_change", 0) < 0:
            recommendations.append("Focus on sales growth initiatives")

        # Expense recommendations
        if pl_trends.get("expenses_change", 0) > pl_trends.get("revenue_change", 0):
            recommendations.append("Implement cost control measures")

        # Margin recommendations
        if pl_trends.get("gross_margin_change", 0) < 0:
            recommendations.append("Review pricing strategy and cost of goods sold")

        # Liquidity recommendations
        if bs_trends.get("current_ratio", 0) < 1:
            recommendations.append("Improve working capital management")

        # Leverage recommendations
        if bs_trends.get("debt_to_equity", 0) > 2:
            recommendations.append("Consider debt reduction strategies")

        # Cash flow recommendations
        if cf_trends.get("operating_cash_change", 0) < 0:
            recommendations.append("Focus on improving cash conversion cycle")

        return (
            ", ".join(recommendations)
            if recommendations
            else "Continue monitoring financial performance."
        )
