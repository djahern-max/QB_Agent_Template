from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict
import openai


class FinancialAnalysisAgent:
    def __init__(self, api_key: str, qb_service: Any):
        self.api_key = api_key
        self.qb_service = qb_service
        self.openai_client = openai.OpenAI()

    def process_input(self, input_data: Dict) -> Dict:
        """Process input data and generate financial analysis"""
        if "realm_id" not in input_data:
            raise ValueError("realm_id is required")

        realm_id = input_data["realm_id"]

        # Fetch QuickBooks data
        raw_data = self._fetch_quickbooks_data(realm_id)

        # Process different aspects of the data
        processed_data = {
            "financial_metrics": self._process_financial_metrics(raw_data),
            "customer_analysis": self._analyze_customers(raw_data),
            "service_metrics": self._analyze_services(raw_data),
            "cash_flow": self._analyze_cash_flow(raw_data),
            "trends": self._analyze_trends(raw_data),
        }

        return processed_data

    def _fetch_quickbooks_data(self, realm_id: str) -> Dict:
        """Fetch all required data from QuickBooks"""
        return {
            "accounts": self.qb_service.get_accounts(realm_id),
            "invoices": self.qb_service.get_invoices(realm_id),
            "company_info": self.qb_service.get_company_info(realm_id),
        }

    def _process_financial_metrics(self, data: Dict) -> Dict:
        """Calculate key financial metrics"""
        accounts = data["accounts"]["QueryResponse"]["Account"]
        invoices = data["invoices"]["QueryResponse"]["Invoice"]

        # Account balances by classification
        balances = defaultdict(float)
        for account in accounts:
            balances[account["Classification"]] += account.get("CurrentBalance", 0)

        # Invoice metrics
        current_month = datetime.now().strftime("%Y-%m")
        current_month_invoices = [
            inv for inv in invoices if inv["TxnDate"].startswith(current_month)
        ]

        total_revenue = sum(float(inv["TotalAmt"]) for inv in invoices)
        total_receivables = sum(float(inv["Balance"]) for inv in invoices)

        return {
            "balances": dict(balances),
            "revenue": {
                "total": total_revenue,
                "receivables": total_receivables,
                "current_month": sum(
                    float(inv["TotalAmt"]) for inv in current_month_invoices
                ),
            },
            "key_ratios": {
                "current_ratio": (
                    balances["Asset"] / balances["Liability"]
                    if balances["Liability"] != 0
                    else 0
                ),
                "debt_to_equity": (
                    balances["Liability"] / balances["Equity"]
                    if balances["Equity"] != 0
                    else 0
                ),
                "profit_margin": (
                    (balances["Revenue"] - balances["Expense"]) / balances["Revenue"]
                    if balances["Revenue"] != 0
                    else 0
                ),
            },
        }

    def _analyze_customers(self, data: Dict) -> Dict:
        """Analyze customer behavior and segmentation"""
        invoices = data["invoices"]["QueryResponse"]["Invoice"]

        # Customer metrics
        customer_data = defaultdict(
            lambda: {
                "total_spent": 0,
                "invoice_count": 0,
                "average_invoice": 0,
                "services_used": set(),
            }
        )

        for invoice in invoices:
            customer = invoice["CustomerRef"]["name"]
            amount = float(invoice["TotalAmt"])

            customer_data[customer]["total_spent"] += amount
            customer_data[customer]["invoice_count"] += 1

            # Track services used
            for line in invoice.get("Line", []):
                if "SalesItemLineDetail" in line:
                    service = line["SalesItemLineDetail"].get("ItemRef", {}).get("name")
                    if service:
                        customer_data[customer]["services_used"].add(service)

        # Calculate averages and convert sets to lists for JSON serialization
        for customer in customer_data:
            data = customer_data[customer]
            data["average_invoice"] = data["total_spent"] / data["invoice_count"]
            data["services_used"] = list(data["services_used"])

        return {
            "customer_metrics": dict(customer_data),
            "segments": {
                "high_value": [
                    customer
                    for customer, data in customer_data.items()
                    if data["total_spent"] > 1000
                ],
                "regular": [
                    customer
                    for customer, data in customer_data.items()
                    if data["invoice_count"] > 3
                ],
            },
        }

    def _analyze_services(self, data: Dict) -> Dict:
        """Analyze service popularity and profitability"""
        invoices = data["invoices"]["QueryResponse"]["Invoice"]

        service_metrics = defaultdict(
            lambda: {"revenue": 0, "frequency": 0, "average_price": 0}
        )

        for invoice in invoices:
            for line in invoice.get("Line", []):
                if "SalesItemLineDetail" in line:
                    service = line["SalesItemLineDetail"].get("ItemRef", {}).get("name")
                    if service:
                        amount = float(line.get("Amount", 0))
                        service_metrics[service]["revenue"] += amount
                        service_metrics[service]["frequency"] += 1

        # Calculate averages
        for service in service_metrics:
            metrics = service_metrics[service]
            metrics["average_price"] = metrics["revenue"] / metrics["frequency"]

        return dict(service_metrics)

    def _analyze_cash_flow(self, data: Dict) -> Dict:
        """Analyze cash flow patterns"""
        invoices = data["invoices"]["QueryResponse"]["Invoice"]

        monthly_cash_flow = defaultdict(lambda: {"incoming": 0, "receivables": 0})

        for invoice in invoices:
            month = invoice["TxnDate"][:7]  # YYYY-MM
            amount = float(invoice["TotalAmt"])
            balance = float(invoice["Balance"])

            monthly_cash_flow[month]["incoming"] += amount
            monthly_cash_flow[month]["receivables"] += balance

        return {
            "monthly_flow": dict(monthly_cash_flow),
            "total_receivables": sum(
                flow["receivables"] for flow in monthly_cash_flow.values()
            ),
        }

    def _analyze_trends(self, data: Dict) -> Dict:
        """Analyze trends in revenue and services"""
        invoices = data["invoices"]["QueryResponse"]["Invoice"]

        # Sort invoices by date
        sorted_invoices = sorted(invoices, key=lambda x: x["TxnDate"])

        monthly_trends = defaultdict(
            lambda: {"revenue": 0, "invoice_count": 0, "new_customers": set()}
        )

        seen_customers = set()

        for invoice in sorted_invoices:
            month = invoice["TxnDate"][:7]  # YYYY-MM
            customer = invoice["CustomerRef"]["name"]
            amount = float(invoice["TotalAmt"])

            monthly_trends[month]["revenue"] += amount
            monthly_trends[month]["invoice_count"] += 1

            if customer not in seen_customers:
                monthly_trends[month]["new_customers"].add(customer)
                seen_customers.add(customer)

        # Convert sets to counts for JSON serialization
        for month in monthly_trends:
            monthly_trends[month]["new_customers"] = len(
                monthly_trends[month]["new_customers"]
            )

        return dict(monthly_trends)

    def generate_response(self, processed_data: Dict) -> Dict:
        """Generate AI analysis of the processed data"""
        # Prepare a focused prompt with key insights
        prompt = self._prepare_analysis_prompt(processed_data)

        # Get AI analysis
        response = self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a financial analysis expert."},
                {"role": "user", "content": prompt},
            ],
        )

        return {
            "analysis": response.choices[0].message.content,
            "metrics": processed_data["financial_metrics"],
            "recommendations": self._generate_recommendations(processed_data),
        }

    def _prepare_analysis_prompt(self, data: Dict) -> str:
        """Prepare a focused prompt for GPT-4"""
        metrics = data["financial_metrics"]
        trends = data["trends"]

        return f"""Analyze these key financial metrics for a landscaping business:

Financial Overview:
- Total Revenue: ${metrics['revenue']['total']:,.2f}
- Current Month Revenue: ${metrics['revenue']['current_month']:,.2f}
- Outstanding Receivables: ${metrics['revenue']['receivables']:,.2f}
- Profit Margin: {metrics['key_ratios']['profit_margin']:.1%}

Customer Insights:
- High Value Customers: {len(data['customer_analysis']['segments']['high_value'])}
- Regular Customers: {len(data['customer_analysis']['segments']['regular'])}

Top Services by Revenue:
{self._format_top_services(data['service_metrics'], limit=3)}

Provide concise insights on:
1. Overall financial health
2. Key areas for improvement
3. Specific action items for growth

Keep response focused and actionable."""

    def _format_top_services(self, service_metrics: Dict, limit: int) -> str:
        """Format top services by revenue"""
        sorted_services = sorted(
            service_metrics.items(), key=lambda x: x[1]["revenue"], reverse=True
        )[:limit]

        return "\n".join(
            f"- {service}: ${metrics['revenue']:,.2f} ({metrics['frequency']} orders)"
            for service, metrics in sorted_services
        )

    def _generate_recommendations(self, data: Dict) -> List[Dict]:
        """Generate specific recommendations based on the data"""
        metrics = data["financial_metrics"]
        receivables_ratio = (
            metrics["revenue"]["receivables"] / metrics["revenue"]["total"]
        )

        recommendations = []

        # Financial health recommendations
        if receivables_ratio > 0.2:
            recommendations.append(
                {
                    "category": "Cash Flow",
                    "priority": "High",
                    "recommendation": "Implement stricter payment collection policies",
                    "impact": f"${metrics['revenue']['receivables']:,.2f} in outstanding receivables",
                }
            )

        # Customer recommendations
        customer_segments = data["customer_analysis"]["segments"]
        if len(customer_segments["high_value"]) < 5:
            recommendations.append(
                {
                    "category": "Customer Growth",
                    "priority": "Medium",
                    "recommendation": "Develop premium service packages for high-value customer acquisition",
                    "impact": "Potential 20% revenue increase",
                }
            )

        return recommendations
