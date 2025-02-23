#!/usr/bin/env python3
import os
from typing import List, Dict
import re
from datetime import datetime


class ReadmeUpdater:
    def __init__(self, project_root: str = "."):
        self.project_root = project_root
        self.exclude_patterns = [
            "__pycache__",
            ".git",
            "venv",
            ".env",
            ".pyc",
            ".DS_Store",
        ]

    def generate_tree(self, startpath: str = "app") -> str:
        """Generate a tree-like directory structure."""
        tree = []
        for root, dirs, files in os.walk(os.path.join(self.project_root, startpath)):
            # Skip excluded directories
            dirs[:] = [
                d for d in dirs if not any(pat in d for pat in self.exclude_patterns)
            ]
            files = [
                f for f in files if not any(pat in f for pat in self.exclude_patterns)
            ]

            level = root.replace(os.path.join(self.project_root, startpath), "").count(
                os.sep
            )
            indent = "    " * level

            if not any(pat in os.path.basename(root) for pat in self.exclude_patterns):
                if level > 0:  # Don't add the root directory
                    tree.append(f"{indent}├── {os.path.basename(root)}/")

                for i, file in enumerate(sorted(files)):
                    is_last = (i == len(files) - 1) and not dirs
                    prefix = "└── " if is_last else "├── "
                    tree.append(f"{indent}{prefix}{file}")

        return "\n".join(["app/"] + tree)

    def check_implementation_status(self) -> Dict[str, bool]:
        """Check which components have been implemented."""
        status = {
            "Project Structure": True,  # Always True as it's the base
            "Base Agent Implementation": os.path.exists(
                os.path.join(self.project_root, "app/core/base_agent.py")
            ),
            "Financial Analysis Agent": os.path.exists(
                os.path.join(self.project_root, "app/agents/financial_agent/agent.py")
            ),
            "QuickBooks Integration": os.path.exists(
                os.path.join(
                    self.project_root, "app/integrations/quickbooks/connector.py"
                )
            ),
            "Middleware Components": all(
                [
                    os.path.exists(
                        os.path.join(self.project_root, f"app/middleware/{f}")
                    )
                    for f in ["rate_limiter.py", "caching.py", "token_handler.py"]
                ]
            ),
            "Testing Suite": os.path.exists(
                os.path.join(self.project_root, "tests/test_financial_agent.py")
            ),
        }
        return status

    def check_component_status(self) -> Dict[str, Dict[str, bool]]:
        """Check detailed status of each component."""
        return {
            "Phase 1: Core Implementation": {
                "Project Structure Setup": True,
                "Base Agent Implementation": os.path.exists("app/core/base_agent.py"),
                "Financial Analysis Agent": os.path.exists(
                    "app/agents/financial_agent/agent.py"
                ),
                "Basic API Endpoints": os.path.exists("app/main.py"),
            },
            "Phase 2: QuickBooks Integration": {
                "OAuth Flow Implementation": os.path.exists(
                    "app/integrations/quickbooks/connector.py"
                ),
                "Data Fetcher Development": os.path.exists(
                    "app/integrations/quickbooks/data_fetcher.py"
                ),
                "Account Management": os.path.exists(
                    "app/integrations/quickbooks/account_manager.py"
                ),
                "Financial Data Processing": os.path.exists(
                    "app/integrations/quickbooks/data_processor.py"
                ),
            },
            "Phase 3: Advanced Features": {
                "Middleware Components": os.path.exists(
                    "app/middleware/rate_limiter.py"
                ),
                "Caching System": os.path.exists("app/middleware/caching.py"),
                "Rate Limiting": os.path.exists("app/middleware/rate_limiter.py"),
                "Token Management": os.path.exists("app/middleware/token_handler.py"),
            },
            "Phase 4: Testing & Documentation": {
                "Unit Tests": os.path.exists("tests/unit"),
                "Integration Tests": os.path.exists("tests/integration"),
                "API Documentation": os.path.exists("docs/api.md"),
                "User Guides": os.path.exists("docs/user_guide.md"),
            },
        }

    def update_implementation_section(self, content: str) -> str:
        """Update the implementation status section in the README."""
        status = self.check_implementation_status()
        status_section = "\n".join(
            f'- [{"x" if implemented else " "}] {component}'
            for component, implemented in status.items()
        )

        pattern = r"(## Development Status\n).*?(\n\n|$)"
        replacement = f"\\1{status_section}\n\n"
        return re.sub(pattern, replacement, content, flags=re.DOTALL)

    def update_tree_section(self, content: str) -> str:
        """Update the project structure tree in the README."""
        tree = self.generate_tree()
        pattern = r"(```\n)app/.*?(```)"
        replacement = f"\\1{tree}\\2"
        return re.sub(pattern, replacement, content, flags=re.DOTALL)

    def update_phase_status(self, content: str) -> str:
        """Update the status of each development phase."""
        status = self.check_component_status()

        # Update each phase in the roadmap
        for phase, components in status.items():
            phase_section = "\n".join(
                f'- [{"x" if implemented else " "}] {component}'
                for component, implemented in components.items()
            )

            pattern = f"(### {phase}\n).*?(\n\n|$)"
            replacement = f"\\1{phase_section}\n\n"
            content = re.sub(pattern, replacement, content, flags=re.DOTALL)

        return content

    def update_timestamp(self, content: str) -> str:
        """Update the last modified timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if "*Note: This README" in content:
            pattern = r"\*Note: This README.*\*"
            replacement = f"*Note: This README serves as a living document and development guide. Last updated: {timestamp}*"
            return re.sub(pattern, replacement, content)
        return content

    def update_readme(self):
        """Update the README.md file with current project structure and status."""
        readme_path = os.path.join(self.project_root, "README.md")

        try:
            with open(readme_path, "r") as f:
                content = f.read()

            # Perform all updates
            content = self.update_tree_section(content)
            content = self.update_implementation_section(content)
            content = self.update_phase_status(content)
            content = self.update_timestamp(content)

            with open(readme_path, "w") as f:
                f.write(content)

            print("✅ README.md has been successfully updated!")

        except FileNotFoundError:
            print(
                "❌ Error: README.md not found. Please ensure it exists in the project root."
            )
        except Exception as e:
            print(f"❌ Error updating README: {str(e)}")


if __name__ == "__main__":
    updater = ReadmeUpdater()
    updater.update_readme()
