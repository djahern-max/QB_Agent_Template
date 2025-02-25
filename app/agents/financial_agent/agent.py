# app/agents/financial_agent/agent.py
import os
import json
from typing import Dict, Any
import openai
from fastapi import Depends
from sqlalchemy.orm import Session

from ...database import get_db


class FinancialAnalysisAgent:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        # Initialize OpenAI client
        self.client = openai.OpenAI(api_key=self.openai_api_key)

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
