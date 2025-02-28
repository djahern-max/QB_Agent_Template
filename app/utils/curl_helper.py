# app/utils/curl_helper.py
from fastapi import FastAPI
from typing import Dict, List, Optional
import json


def generate_curl_commands(
    app: FastAPI, base_url: str = "https://clarity.ryze.ai"
) -> Dict[str, List[str]]:
    """
    Generate curl commands for all routes in the application

    Parameters:
    - app: FastAPI application instance
    - base_url: Base URL for the application

    Returns:
    - Dictionary with route categories and corresponding curl commands
    """
    curl_commands = {
        "Authentication": [],
        "Data Retrieval": [],
        "Analysis": [],
        "Utility": [],
    }

    # Process all routes
    for route in app.routes:
        if not hasattr(route, "methods") or not route.methods:
            continue

        path = route.path
        methods = route.methods

        # Skip OPTIONS methods (used for CORS)
        if "OPTIONS" in methods and len(methods) == 1:
            continue

        # Generate curl commands based on HTTP method and path pattern
        for method in methods:
            if method == "OPTIONS":
                continue

            # Create basic curl command
            command = f"curl -X {method} {base_url}{path}"

            # Add appropriate headers and data based on method
            if method in ["POST", "PUT", "PATCH"]:
                command += ' -H "Content-Type: application/json"'

                # Add sample data based on endpoint
                if "analyze" in path:
                    sample_data = {"accounts_data": {"QueryResponse": {"Account": []}}}
                    command += f" -d '{json.dumps(sample_data)}'"
                elif "ask" in path:
                    sample_data = {
                        "accounts_data": {"QueryResponse": {"Account": []}},
                        "question": "What is my current financial health?",
                    }
                    command += f" -d '{json.dumps(sample_data)}'"

            # Add example parameters for GET endpoints with required parameters
            if method == "GET":
                if "callback" in path and "{" not in path:
                    command += "?code=EXAMPLE_CODE&realmId=EXAMPLE_REALM_ID"
                elif "get_accounts" in path or path == "/clarity.ryze.ai":
                    command += "?realm_id=EXAMPLE_REALM_ID"

            # Categorize the commands
            if "auth" in path or "callback" in path:
                curl_commands["Authentication"].append(
                    {"description": route.name or path, "command": command}
                )
            elif "analyze" in path or "ask" in path:
                curl_commands["Analysis"].append(
                    {"description": route.name or path, "command": command}
                )
            elif "accounts" in path or "get" in path:
                curl_commands["Data Retrieval"].append(
                    {"description": route.name or path, "command": command}
                )
            else:
                curl_commands["Utility"].append(
                    {"description": route.name or path, "command": command}
                )

    return curl_commands


def print_curl_commands(curl_commands: Dict[str, List[str]]) -> None:
    """
    Print curl commands in a readable format

    Parameters:
    - curl_commands: Dictionary with route categories and corresponding curl commands
    """
    print("\n===== CURL COMMANDS FOR API TESTING =====\n")

    for category, commands in curl_commands.items():
        if not commands:
            continue

        print(f"\n== {category} ==\n")

        for cmd in commands:
            print(f"# {cmd['description']}")
            print(f"{cmd['command']}\n")


# Example usage
if __name__ == "__main__":
    from app.main import app

    # Change this to your actual base URL
    base_url = "https://clarity.ryze.ai"

    curl_commands = generate_curl_commands(app, base_url)
    print_curl_commands(curl_commands)
