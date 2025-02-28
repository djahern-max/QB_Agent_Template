# app/services/financial_trends.py
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from .quickbooks import QuickBooksService

logger = logging.getLogger(__name__)


class FinancialTrendsService:
    def __init__(self, qb_service: QuickBooksService):
        self.qb_service = qb_service

    async def get_monthly_profit_loss_trend(
        self, realm_id: str, months: int = 6
    ) -> Dict[str, Any]:
        """
        Get monthly Profit & Loss data for trend analysis

        Args:
            realm_id: QuickBooks realm ID
            months: Number of months to analyze (default: 6)

        Returns:
            Dict containing monthly P&L trend data
        """
        try:
            # Generate list of month periods to analyze
            end_date = datetime.now()
            periods = []

            for i in range(months):
                # Calculate period start/end
                current_month_end = (
                    end_date.replace(day=1) - timedelta(days=1) if i > 0 else end_date
                )
                current_month_start = current_month_end.replace(day=1)

                # Format dates for API
                start_date_str = current_month_start.strftime("%Y-%m-%d")
                end_date_str = current_month_end.strftime("%Y-%m-%d")

                # Add to periods list
                periods.append(
                    {
                        "month": current_month_start.strftime("%b %Y"),
                        "start_date": start_date_str,
                        "end_date": end_date_str,
                    }
                )

                # Move to previous month
                end_date = current_month_start - timedelta(days=1)

            # Reverse chronological order to have oldest first
            periods.reverse()

            # Get P&L data for each period
            trend_data = []
            for period in periods:
                report_data = await self.qb_service.get_report(
                    realm_id=realm_id,
                    report_type="ProfitAndLoss",
                    params={
                        "start_date": period["start_date"],
                        "end_date": period["end_date"],
                        "minorversion": "65",
                    },
                )

                # Extract key metrics from the report
                metrics = self._extract_pl_metrics(report_data)
                metrics["period"] = period["month"]

                trend_data.append(metrics)

            # Calculate growth rates and additional insights
            trend_analysis = self._analyze_pl_trends(trend_data)

            return {"trend_data": trend_data, "analysis": trend_analysis}

        except Exception as e:
            logger.error(f"Error getting P&L trend data: {str(e)}")
            raise

    def _extract_pl_metrics(self, pl_report: Dict[str, Any]) -> Dict[str, float]:
        """
        Extract key metrics from a Profit & Loss report
        """
        metrics = {
            "total_revenue": 0,
            "total_expenses": 0,
            "gross_profit": 0,
            "net_income": 0,
        }

        try:
            # Extract data from QuickBooks report structure
            rows = pl_report.get("Rows", {}).get("Row", [])

            for row in rows:
                if row.get("group") == "Income" and row.get("Summary"):
                    metrics["total_revenue"] = float(
                        row["Summary"]["ColData"][1]["value"]
                    )
                elif row.get("group") == "GrossProfit" and row.get("Summary"):
                    metrics["gross_profit"] = float(
                        row["Summary"]["ColData"][1]["value"]
                    )
                elif row.get("group") == "Expenses" and row.get("Summary"):
                    metrics["total_expenses"] = float(
                        row["Summary"]["ColData"][1]["value"]
                    )
                elif row.get("group") == "NetIncome" and row.get("Summary"):
                    metrics["net_income"] = float(row["Summary"]["ColData"][1]["value"])

            # Calculate margins
            if metrics["total_revenue"] > 0:
                metrics["gross_margin"] = (
                    metrics["gross_profit"] / metrics["total_revenue"]
                ) * 100
                metrics["net_margin"] = (
                    metrics["net_income"] / metrics["total_revenue"]
                ) * 100
            else:
                metrics["gross_margin"] = 0
                metrics["net_margin"] = 0

            return metrics

        except Exception as e:
            logger.error(f"Error extracting P&L metrics: {str(e)}")
            return metrics

    def _analyze_pl_trends(self, trend_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze profit & loss trends to identify patterns and insights
        """
        if not trend_data or len(trend_data) < 2:
            return {"status": "insufficient_data"}

        analysis = {
            "revenue_growth": [],
            "expense_growth": [],
            "profit_growth": [],
            "overall_trend": "",
            "insights": [],
        }

        # Calculate period-over-period growth
        for i in range(1, len(trend_data)):
            current = trend_data[i]
            previous = trend_data[i - 1]

            # Skip if previous revenue is zero (avoid division by zero)
            if previous["total_revenue"] == 0:
                continue

            revenue_growth = (
                (current["total_revenue"] - previous["total_revenue"])
                / previous["total_revenue"]
            ) * 100
            expense_growth = (
                (
                    (current["total_expenses"] - previous["total_expenses"])
                    / previous["total_expenses"]
                )
                * 100
                if previous["total_expenses"] > 0
                else 0
            )
            profit_growth = (
                (
                    (current["net_income"] - previous["net_income"])
                    / previous["net_income"]
                )
                * 100
                if previous["net_income"] > 0
                else 0
            )

            analysis["revenue_growth"].append(
                {"period": current["period"], "growth": revenue_growth}
            )

            analysis["expense_growth"].append(
                {"period": current["period"], "growth": expense_growth}
            )

            analysis["profit_growth"].append(
                {"period": current["period"], "growth": profit_growth}
            )

        # Determine overall trend
        if len(analysis["revenue_growth"]) > 0:
            avg_revenue_growth = sum(
                item["growth"] for item in analysis["revenue_growth"]
            ) / len(analysis["revenue_growth"])
            avg_profit_growth = (
                sum(item["growth"] for item in analysis["profit_growth"])
                / len(analysis["profit_growth"])
                if analysis["profit_growth"]
                else 0
            )

            if avg_revenue_growth > 10 and avg_profit_growth > 10:
                analysis["overall_trend"] = "strong_growth"
                analysis["insights"].append(
                    "Your business is showing strong growth in both revenue and profit."
                )
            elif avg_revenue_growth > 5:
                analysis["overall_trend"] = "moderate_growth"
                analysis["insights"].append("Your business is showing moderate growth.")
            elif avg_revenue_growth < 0:
                analysis["overall_trend"] = "decline"
                analysis["insights"].append(
                    "Your revenue has been declining. Consider reviewing your sales strategy."
                )
            else:
                analysis["overall_trend"] = "stable"
                analysis["insights"].append(
                    "Your business appears stable with minimal growth."
                )

        # Add additional insights
        latest = trend_data[-1]
        if latest["gross_margin"] < 30:
            analysis["insights"].append(
                "Your gross margin is below industry average. Consider ways to reduce direct costs."
            )

        if len(trend_data) >= 3:
            # Check for expense trend
            recent_expenses = [data["total_expenses"] for data in trend_data[-3:]]
            if recent_expenses[2] > recent_expenses[1] > recent_expenses[0]:
                analysis["insights"].append(
                    "Your expenses have been consistently increasing. Review your cost structure."
                )

        return analysis
