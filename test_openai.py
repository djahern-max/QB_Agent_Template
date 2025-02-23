from dotenv import load_dotenv
import os
from openai import OpenAI


def test_openai_connection():
    try:
        # Load environment variables
        load_dotenv()

        # Initialize OpenAI client
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Basic connection test
        print("\n🔄 Testing Basic Connection:")
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": "Simple test: Say 'Connection successful!'"}
            ],
        )
        print("✅ Connection successful")
        print(f"Response: {response.choices[0].message.content}\n")

        # Financial analysis test
        print("\n🔄 Testing Financial Analysis Capabilities:")
        financial_prompt = """
        Please explain what a debt to equity ratio is, including:
        1. How it's calculated
        2. What it indicates about a company's financial health
        3. What's considered a good ratio
        4. How it varies by industry
        """

        response = client.chat.completions.create(
            model="gpt-4", messages=[{"role": "user", "content": financial_prompt}]
        )

        print("✅ Financial Analysis Response:")
        print(f"{response.choices[0].message.content}")

    except Exception as e:
        print("❌ Connection failed")
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    test_openai_connection()
