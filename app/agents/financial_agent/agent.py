# app/agents/financial_agent/agent.py
import os
import json
import re
from typing import Dict, Any
from openai import OpenAI
from fastapi import Depends
from sqlalchemy.orm import Session

from ...database import get_db


class FinancialAnalysisAgent:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.openai_api_key)

    async def analyze_accounts(self, accounts_data: Dict) -> Dict:
        """
        Analyze chart of accounts data with GPT-4

        Parameters:
        - accounts_data: Dictionary containing the chart of accounts from QuickBooks

        Returns:
        - Dictionary containing the analysis
        """
        try:
            # Format accounts data for the prompt
            accounts_summary = self._format_accounts_for_analysis(accounts_data)

            # Create prompt for GPT-4
            prompt = f"""
            As a financial analyst, review the following chart of accounts and provide insights:
            
            # Chart of Accounts
            {accounts_summary}
            
            Please provide:
            1. 3 positive insights about the financial situation
            2. 3 areas of concern or potential issues
            3. 3 actionable recommendations
            4. A brief summary of the overall financial health
            
            Format your response as JSON with the following structure:
            {{
                "positive_insights": [
                    {{
                        "title": "Brief Title",
                        "description": "Detailed explanation"
                    }}
                ],
                "concerns": [
                    {{
                        "title": "Brief Title",
                        "description": "Detailed explanation"
                    }}
                ],
                "recommendations": [
                    {{
                        "title": "Brief Title",
                        "description": "Detailed explanation"
                    }}
                ],
                "summary": "Overall financial health summary in 3-4 sentences"
            }}
            """

            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial analysis AI specialized in providing insights from accounting data.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=1000,
            )

            # Extract response
            response_content = response.choices[0].message.content

            # Parse JSON
            try:
                analysis = json.loads(response_content)
                return analysis
            except json.JSONDecodeError:
                return {
                    "error": "Could not parse GPT response as JSON",
                    "raw_response": response_content,
                }

        except Exception as e:
            return {"error": f"Analysis failed: {str(e)}"}

    async def ask_question(self, accounts_data: Dict, question: str) -> Dict:
        """
        Ask a specific question about the financial data

        Parameters:
        - accounts_data: Dictionary containing the chart of accounts
        - question: Question to ask about the data

        Returns:
        - Dictionary containing the answer
        """
        try:
            # Format accounts data for the prompt
            accounts_summary = self._format_accounts_for_analysis(accounts_data)

            # Create prompt
            prompt = f"""
            As a financial analyst, use the following chart of accounts to answer this question:
            
            # Question
            {question}
            
            # Chart of Accounts
            {accounts_summary}
            
            Provide a comprehensive answer with any relevant calculations, explanations, and insights.
            """

            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial analysis AI specialized in providing insights from accounting data.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=800,
            )

            # Extract response
            answer = response.choices[0].message.content

            return {"question": question, "answer": answer}

        except Exception as e:
            return {"error": f"Failed to answer question: {str(e)}"}

    def _format_accounts_for_analysis(self, accounts_data: Dict) -> str:
        """Format account data for GPT analysis"""
        formatted_accounts = []

        # Handle different possible structures of input data
        accounts = accounts_data.get("accounts", [])
        if not accounts and "QueryResponse" in accounts_data:
            accounts = accounts_data.get("QueryResponse", {}).get("Account", [])

        for account in accounts:
            # Handle different possible formats
            if isinstance(account, dict):
                name = account.get("Name", account.get("name", "Unnamed Account"))
                account_type = account.get(
                    "AccountType", account.get("type", "Unknown")
                )
                balance = account.get("CurrentBalance", account.get("balance", 0))
            else:
                continue

            formatted_accounts.append(
                f"- {name} ({account_type}): ${float(balance):,.2f}"
            )

        return "\n".join(formatted_accounts)

    async def forecast_cash_flow(self, accounts_data: Dict) -> Dict:
        """
        Generate a cash flow forecast based on account data

        Parameters:
        - accounts_data: Dictionary containing the accounts data from QuickBooks

        Returns:
        - Dictionary containing the forecast and recommendations
        """
        try:
            # Format accounts data for the prompt
            accounts_summary = self._format_accounts_for_analysis(accounts_data)

            # Create prompt for GPT-4
            prompt = f"""
            As a financial analyst specialized in cash flow management, review the following chart of accounts and provide a 90-day cash flow forecast:
            
            # Chart of Accounts
            {accounts_summary}
            
            Based on this financial data, please provide:
            1. A 90-day cash flow forecast broken down by month (next 3 months)
            2. Key factors that will likely impact cash flow in the next 90 days
            3. Three actionable recommendations to improve cash flow
            4. Potential cash flow risks to be aware of
            
            Format your response as JSON with the following structure:
            {{
                "forecast": {{
                    "month1": {{
                        "inflow": [estimated inflow in dollars],
                        "outflow": [estimated outflow in dollars],
                        "net_change": [net cash flow]
                    }},
                    "month2": {{
                        "inflow": [estimated inflow in dollars],
                        "outflow": [estimated outflow in dollars],
                        "net_change": [net cash flow]
                    }},
                    "month3": {{
                        "inflow": [estimated inflow in dollars],
                        "outflow": [estimated outflow in dollars],
                        "net_change": [net cash flow]
                    }}
                }},
                "impact_factors": [
                    {{
                        "title": "Brief Title",
                        "description": "Detailed explanation"
                    }}
                ],
                "recommendations": [
                    {{
                        "title": "Brief Title",
                        "description": "Detailed explanation"
                    }}
                ],
                "risks": [
                    {{
                        "title": "Brief Title",
                        "description": "Detailed explanation"
                    }}
                ]
            }}
            """

            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial analysis AI specialized in cash flow forecasting and management.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=1200,
            )

            # Extract response
            response_content = response.choices[0].message.content

            # Parse JSON
            try:
                forecast = json.loads(response_content)
                return forecast
            except json.JSONDecodeError:
                return {
                    "error": "Could not parse GPT response as JSON",
                    "raw_response": response_content,
                }

        except Exception as e:
            return {"error": f"Forecasting failed: {str(e)}"}

    async def analyze_profit_loss(self, profit_loss_data: Dict) -> Dict:
        """
        Analyze profit & loss statement with GPT-4

        Parameters:
        - profit_loss_data: Dictionary containing the P&L data from QuickBooks

        Returns:
        - Dictionary containing the analysis
        """
        try:
            # Format the data for the prompt
            pl_summary = self._format_pl_for_analysis(profit_loss_data)

            # Create prompt for GPT-4
            prompt = f"""
            As a financial analyst, review the following Profit & Loss statement and provide insights:
            
            # Profit & Loss Statement
            {pl_summary}
            
            Please provide:
            1. A concise summary of the financial position (2-3 sentences)
            2. 5 key insights about the data, focusing on revenue, expenses, and profitability
            3. 3 actionable recommendations based on this P&L statement
            
            Format your response as JSON with the following structure:
            {{
                "summary": "Overall financial summary in 2-3 sentences",
                "insights": [
                    "Insight 1",
                    "Insight 2",
                    "Insight 3",
                    "Insight 4",
                    "Insight 5"
                ],
                "recommendations": [
                    "Recommendation 1",
                    "Recommendation 2",
                    "Recommendation 3"
                ]
            }}
            """

            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial analysis AI specialized in providing insights from financial statements.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=1000,
            )

            # Extract and parse response
            response_content = response.choices[0].message.content

            try:
                analysis = json.loads(response_content)
                return analysis
            except json.JSONDecodeError:
                return {
                    "error": "Could not parse GPT response as JSON",
                    "raw_response": response_content,
                }

        except Exception as e:
            return {"error": f"Analysis failed: {str(e)}"}

    def _format_pl_for_analysis(self, profit_loss_data: Dict) -> str:
        """Format P&L data for GPT analysis"""
        formatted_lines = []

        # Header information
        header = profit_loss_data.get("Header", {})
        formatted_lines.append(
            f"Period: {header.get('StartPeriod', 'N/A')} to {header.get('EndPeriod', 'N/A')}"
        )
        formatted_lines.append(f"Basis: {header.get('ReportBasis', 'N/A')}")
        formatted_lines.append("")

        # Process rows
        rows = profit_loss_data.get("Rows", {}).get("Row", [])

        if not rows:
            return "No financial data available."

        # Process sections (Income, COGS, Expenses, etc.)
        for section in rows:
            # Get section header
            header_data = section.get("Header", {}).get("ColData", [])
            if header_data and len(header_data) > 0:
                section_name = header_data[0].get("value", "")
                if section_name:
                    formatted_lines.append(f"## {section_name}")
                    formatted_lines.append("")

            # Process line items within the section
            section_rows = section.get("Rows", {}).get("Row", [])
            if section_rows:
                for item in section_rows:
                    if item.get("type") == "Data" and "ColData" in item:
                        col_data = item.get("ColData", [])
                        if len(col_data) >= 2:
                            name = col_data[0].get("value", "Unknown")
                            amount = col_data[1].get("value", "0.00")
                            formatted_lines.append(f"- {name}: ${amount}")

                formatted_lines.append("")

            # Process section summary
            summary = section.get("Summary", {})
            if summary and "ColData" in summary:
                col_data = summary.get("ColData", [])
                if len(col_data) >= 2:
                    label = col_data[0].get("value", "Total")
                    value = col_data[1].get("value", "0.00")
                    formatted_lines.append(f"**{label}**: ${value}")
                    formatted_lines.append("")

        # Add overall summary from the last section (usually Net Income)
        if rows and "Summary" in rows[-1]:
            net_summary = rows[-1].get("Summary", {}).get("ColData", [])
            if len(net_summary) >= 2:
                label = net_summary[0].get("value", "")
                value = net_summary[1].get("value", "")
                if label and value:
                    formatted_lines.append(f"## {label}: ${value}")

        return "\n".join(formatted_lines)

    def _format_bs_for_analysis(self, balance_sheet_data: Dict) -> str:
        """Format Balance Sheet data for GPT analysis"""
        # Extract relevant information
        formatted_lines = []

        # Header information
        header = balance_sheet_data.get("Header", {})
        formatted_lines.append(f"As of date: {header.get('EndPeriod', 'N/A')}")
        formatted_lines.append(f"Basis: {header.get('ReportBasis', 'N/A')}")
        formatted_lines.append("")

        # Process rows
        rows = balance_sheet_data.get("Rows", {}).get("Row", [])

        # Extract key sections
        for row in rows:
            group = row.get("group", "")
            summary = row.get("Summary", {})

            if group in ["Assets", "Liabilities", "Equity"]:
                # Add section header
                if group == "Assets":
                    formatted_lines.append("## ASSETS")
                elif group == "Liabilities":
                    formatted_lines.append("## LIABILITIES")
                elif group == "Equity":
                    formatted_lines.append("## EQUITY")

                # Add details if this is a section with rows
                if "Rows" in row and "Row" in row["Rows"]:
                    for detail in row["Rows"]["Row"]:
                        if detail.get("type") == "Data" and "ColData" in detail:
                            name = detail["ColData"][0].get("value", "Unknown")
                            amount = detail["ColData"][1].get("value", "0.00")
                            formatted_lines.append(f"{name}: {amount}")

                # Add summary line
                if summary and "ColData" in summary:
                    label = summary["ColData"][0].get("value", "Total")
                    value = summary["ColData"][1].get("value", "0.00")
                    formatted_lines.append(f"{label}: {value}")

                # Add spacing between sections
                formatted_lines.append("")

        return "\n".join(formatted_lines)

    async def analyze_cash_flow(self, cash_flow_data: Dict) -> Dict:
        """
        Analyze cash flow statement with GPT-4

        Parameters:
        - cash_flow_data: Dictionary containing the Cash Flow data from QuickBooks

        Returns:
        - Dictionary containing the analysis
        """
        try:
            # Format the data for the prompt
            cf_summary = self._format_cf_for_analysis(cash_flow_data)

            # Create prompt for GPT-4
            prompt = f"""
            As a financial analyst, review the following Cash Flow statement and provide insights:
            
            # Cash Flow Statement
            {cf_summary}
            
            Please provide:
            1. A concise summary of the cash position (2-3 sentences)
            2. 5 key insights about the cash flow, focusing on operating, investing, and financing activities
            3. 3 actionable recommendations to improve cash flow
            
            Format your response as JSON with the following structure:
            {{
                "summary": "Overall cash flow summary in 2-3 sentences",
                "insights": [
                    "Insight 1",
                    "Insight 2",
                    "Insight 3",
                    "Insight 4",
                    "Insight 5"
                ],
                "recommendations": [
                    "Recommendation 1",
                    "Recommendation 2",
                    "Recommendation 3"
                ]
            }}
            """

            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial analysis AI specialized in providing insights from financial statements.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=1000,
            )

            # Extract and parse response
            response_content = response.choices[0].message.content

            try:
                analysis = json.loads(response_content)
                return analysis
            except json.JSONDecodeError:
                return {
                    "error": "Could not parse GPT response as JSON",
                    "raw_response": response_content,
                }

        except Exception as e:
            return {"error": f"Analysis failed: {str(e)}"}

    def _format_cf_for_analysis(self, cash_flow_data: Dict) -> str:
        """Format Cash Flow data for GPT analysis"""
        # Extract relevant information
        formatted_lines = []

        # Header information
        header = cash_flow_data.get("Header", {})
        formatted_lines.append(
            f"Period: {header.get('StartPeriod', 'N/A')} to {header.get('EndPeriod', 'N/A')}"
        )
        formatted_lines.append(f"Basis: {header.get('ReportBasis', 'N/A')}")
        formatted_lines.append("")

        # Process rows
        rows = cash_flow_data.get("Rows", {}).get("Row", [])

        # Extract key sections
        for row in rows:
            group = row.get("group", "")
            summary = row.get("Summary", {})

            if group in ["Operating", "Investing", "Financing", "Cash"]:
                # Add section header
                if group == "Operating":
                    formatted_lines.append("## OPERATING ACTIVITIES")
                elif group == "Investing":
                    formatted_lines.append("## INVESTING ACTIVITIES")
                elif group == "Financing":
                    formatted_lines.append("## FINANCING ACTIVITIES")
                elif group == "Cash":
                    formatted_lines.append("## CASH SUMMARY")

                # Add details if this is a section with rows
                if "Rows" in row and "Row" in row["Rows"]:
                    for detail in row["Rows"]["Row"]:
                        if detail.get("type") == "Data" and "ColData" in detail:
                            name = detail["ColData"][0].get("value", "Unknown")
                            amount = detail["ColData"][1].get("value", "0.00")
                            formatted_lines.append(f"{name}: {amount}")

                # Add summary line
                if summary and "ColData" in summary:
                    label = summary["ColData"][0].get("value", "Total")
                    value = summary["ColData"][1].get("value", "0.00")
                    formatted_lines.append(f"{label}: {value}")

                # Add spacing between sections
                formatted_lines.append("")

        return "\n".join(formatted_lines)

    def extract_json_from_text(self, text):
        """
        Attempts to extract and parse JSON from a text response that might
        contain additional text or markdown formatting.
        """
        # First try direct parsing
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try to find JSON within the text using regex
        json_pattern = r'```json\s*([\s\S]*?)\s*```|{\s*"[^"]+"\s*:[\s\S]*}'
        matches = re.findall(json_pattern, text)

        for match in matches:
            # Remove any markdown formatting
            potential_json = match.strip().replace("```json", "").replace("```", "")
            try:
                return json.loads(potential_json)
            except json.JSONDecodeError:
                continue

        # If we can't extract clean JSON, create a structured response from the text
        return {
            "summary": "Analysis completed but response format was non-standard.",
            "insights": [
                text.strip()[:500] + "..." if len(text) > 500 else text.strip()
            ],
            "recommendations": ["Please retry the analysis or contact support."],
        }

    # Then modify the analyze_profit_loss method
    async def analyze_profit_loss(self, profit_loss_data: Dict) -> Dict:
        """
        Analyze profit & loss statement with GPT-4

        Parameters:
        - profit_loss_data: Dictionary containing the P&L data from QuickBooks

        Returns:
        - Dictionary containing the analysis
        """
        try:
            # Format the data for the prompt
            pl_summary = self._format_pl_for_analysis(profit_loss_data)

            # Create prompt for GPT-4
            prompt = f"""
            As a financial analyst, review the following Profit & Loss statement and provide insights:
            
            # Profit & Loss Statement
            {pl_summary}
            
            Based on the detailed line items and totals above, please provide:
            1. A concise summary of the financial position (2-3 sentences)
            2. 5 key insights about the data, focusing on:
            - Revenue mix and concentration (examine each revenue stream)
            - Expense patterns and efficiency
            - Gross margin and profitability metrics
            - Any unusual patterns or outliers
            - Overall business financial health

            3. 3 actionable recommendations based on this P&L statement, considering:
            - The business's technology focus
            - Revenue diversification opportunities
            - Expense management and efficiency improvements
            - Growth opportunities based on the highest-performing revenue streams

            Format your response as JSON with the following structure:
            {{
                "summary": "Overall financial summary in 2-3 sentences",
                "insights": [
                    "Specific insight 1 about revenue streams and their relative contribution",
                    "Specific insight 2 about expense patterns and areas of concern",
                    "Specific insight 3 about profitability metrics compared to industry standards",
                    "Specific insight 4 about potential growth opportunities based on performance",
                    "Specific insight 5 about overall financial health and risk assessment"
                ],
                "recommendations": [
                    "Specific recommendation 1 with clear actionable steps",
                    "Specific recommendation 2 with clear actionable steps",
                    "Specific recommendation 3 with clear actionable steps"
                ]
            }}

            IMPORTANT: Response must be valid JSON that can be parsed. Do not include any explanatory text outside the JSON structure.
            """

            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial analysis AI specialized in providing insights from financial statements. Always reply with valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=1000,
            )

            # Extract response
            response_content = response.choices[0].message.content

            try:
                # Try to parse as JSON first
                analysis = json.loads(response_content)
                return analysis
            except json.JSONDecodeError:
                # Use our helper function to extract JSON
                # Use our helper function to extract JSON
                analysis = self.extract_json_from_text(
                    response_content
                )  # CORRECT - with 'self'

                # If we still couldn't parse JSON, create a fallback
                if not analysis:
                    return {
                        "error": "Could not parse GPT response as JSON",
                        "summary": "Analysis completed, but results need manual review.",
                        "insights": [
                            "Raw analysis needs to be reviewed by a human analyst."
                        ],
                        "recommendations": [
                            "Try again with a different report format."
                        ],
                        "raw_response": response_content[
                            :1000
                        ],  # Limiting to first 1000 chars
                    }

                return analysis

        except Exception as e:
            return {
                "error": f"Analysis failed: {str(e)}",
                "summary": "An error occurred during analysis.",
                "insights": [],
                "recommendations": ["Please try again later."],
            }

    async def analyze_balance_sheet(self, balance_sheet_data: Dict) -> Dict:
        """
        Analyze balance sheet with GPT-4

        Parameters:
        - balance_sheet_data: Dictionary containing the Balance Sheet data from QuickBooks

        Returns:
        - Dictionary containing the analysis
        """
        try:
            # Format the data for the prompt
            bs_summary = self._format_bs_for_analysis(balance_sheet_data)

            # Create prompt for GPT-4
            prompt = f"""
            As a financial analyst, review the following Balance Sheet and provide insights:
            
            # Balance Sheet
            {bs_summary}
            
            Please provide:
            1. A concise summary of the financial position (2-3 sentences)
            2. 5 key insights about the balance sheet, focusing on assets, liabilities, and equity
            3. 3 actionable recommendations based on this Balance Sheet
            
            Format your response as JSON with the following structure:
            {{
                "summary": "Overall financial summary in 2-3 sentences",
                "insights": [
                    "Insight 1",
                    "Insight 2",
                    "Insight 3",
                    "Insight 4",
                    "Insight 5"
                ],
                "recommendations": [
                    "Recommendation 1",
                    "Recommendation 2",
                    "Recommendation 3"
                ]
            }}

            IMPORTANT: Response must be valid JSON that can be parsed. Do not include any explanatory text outside the JSON structure.
            """

            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial analysis AI specialized in providing insights from financial statements. Always reply with valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=1000,
                # Remove response_format parameter to avoid 400 error
            )

            # Extract and parse response
            response_content = response.choices[0].message.content

            try:
                # Try to parse as JSON first
                analysis = json.loads(response_content)
                return analysis
            except json.JSONDecodeError:
                # Use our helper function to extract JSON
                analysis = self.extract_json_from_text(response_content)

                # If we still couldn't parse JSON, create a fallback
                if not analysis:
                    return {
                        "error": "Could not parse GPT response as JSON",
                        "summary": "Analysis completed, but results need manual review.",
                        "insights": [
                            "Raw analysis needs to be reviewed by a human analyst."
                        ],
                        "recommendations": [
                            "Try again with a different report format."
                        ],
                        "raw_response": response_content[
                            :1000
                        ],  # Limiting to first 1000 chars
                    }

                return analysis

        except Exception as e:
            return {
                "error": f"Analysis failed: {str(e)}",
                "summary": "An error occurred during analysis.",
                "insights": [],
                "recommendations": ["Please try again later."],
            }

    def _format_bs_for_analysis(self, balance_sheet_data: Dict) -> str:
        """Format Balance Sheet data for GPT analysis"""
        # Extract relevant information
        formatted_lines = []

        try:
            # Header information
            header = balance_sheet_data.get("Header", {})
            formatted_lines.append(f"As of date: {header.get('EndPeriod', 'N/A')}")
            formatted_lines.append(f"Basis: {header.get('ReportBasis', 'N/A')}")
            formatted_lines.append("")

            # Process rows
            rows = balance_sheet_data.get("Rows", {}).get("Row", [])

            if not rows:
                formatted_lines.append(
                    "## NOTE: This balance sheet appears to be empty or contains insufficient data."
                )
                return "\n".join(formatted_lines)

            # Extract key sections
            for row in rows:
                group = row.get("group", "")
                summary = row.get("Summary", {})

                if group in ["Assets", "Liabilities", "Equity"]:
                    # Add section header
                    if group == "Assets":
                        formatted_lines.append("## ASSETS")
                    elif group == "Liabilities":
                        formatted_lines.append("## LIABILITIES")
                    elif group == "Equity":
                        formatted_lines.append("## EQUITY")

                    # Add details if this is a section with rows
                    if "Rows" in row and "Row" in row["Rows"]:
                        for detail in row["Rows"]["Row"]:
                            if detail.get("type") == "Data" and "ColData" in detail:
                                name = detail["ColData"][0].get("value", "Unknown")
                                amount = detail["ColData"][1].get("value", "0.00")
                                formatted_lines.append(f"{name}: {amount}")

                    # Add summary line
                    if summary and "ColData" in summary:
                        label = summary["ColData"][0].get("value", "Total")
                        value = summary["ColData"][1].get("value", "0.00")
                        formatted_lines.append(f"{label}: {value}")

                    # Add spacing between sections
                    formatted_lines.append("")
        except Exception as e:
            formatted_lines.append(
                f"## ERROR: Failed to format balance sheet: {str(e)}"
            )
            formatted_lines.append(
                "The balance sheet data may be incomplete or in an unexpected format."
            )

        return "\n".join(formatted_lines)
