import csv
import random
import datetime
import math
from dateutil.relativedelta import relativedelta

# Define the base date
start_date = datetime.datetime(2020, 3, 1)
end_date = datetime.datetime(2020, 12, 31)  # Just 2020 for now

# Lists to store data
journal_entries = []
current_journal_no = 21  # Starting after your sample entries

# Load the customer data
customers = []
with open("Alternative_Futuristic_Customer_Data.csv", "r", encoding="utf-8") as file:
    reader = csv.DictReader(file)
    for row in reader:
        customers.append(row)

# Load the vendor data
vendors = []
with open("Generated_Vendor_List.csv", "r", encoding="utf-8") as file:
    reader = csv.DictReader(file)
    for row in reader:
        vendors.append(row)

# Define account categories using ONLY accounts that exist in QuickBooks
revenue_accounts = [
    "AI Processing Services",
    "Neural Network Consulting",
    "Predictive Analytics Revenue",
    "Automated Defense Systems",
    "Machine Learning as a Service",
    "Services",
]

expense_accounts = [
    "Legal - System Protection",
    "System Administrator Salaries",
    "Quantum Computing Insurance",
    "Server Farm Utilities",
    "Advertising & Marketing",
    "Central Processing Costs",
    "Neural Network Maintenance",
    "Research & Development",
    "Rent & Lease",
    "Travel",
    "Office Supplies & Software",
    "Legal & Professional Services",
    "Insurance",
]

asset_accounts = [
    "Server Infrastructure",
    "Neural Network Patents",
    "Machine Learning Laboratories",
    "Quantum Processing Cards",
    "Central Processing Buildings",
]

# Define business trends (simplified for 2020)
# 1 = normal, > 1 = growth, < 1 = decline
trend_factors = {
    3: 0.8,
    4: 0.7,
    5: 0.7,
    6: 0.8,  # COVID impact
    7: 0.85,
    8: 0.9,
    9: 0.95,
    10: 1.0,
    11: 1.05,
    12: 1.1,  # Recovery begins
}

# Generate journal entries for each month
current_date = start_date
while current_date <= end_date:
    month = current_date.month

    # Get trend factor for this month
    trend_factor = trend_factors.get(month, 1.0)

    # Number of entries to generate this month
    num_revenue_entries = math.ceil(3 + 2 * trend_factor)
    num_expense_entries = math.ceil(3 + trend_factor)
    num_asset_entries = 1 if random.random() < (0.2 + 0.3 * trend_factor) else 0

    # Generate revenue entries
    for _ in range(num_revenue_entries):
        day = random.randint(1, 28)
        entry_date = datetime.datetime(2020, month, day)
        date_str = entry_date.strftime("%-m/%-d/%y")

        # Calculate amount with some randomness
        amount = round(40000 * trend_factor * random.uniform(0.9, 1.1), 2)

        # Select customer and revenue account
        customer = random.choice(customers)
        account = random.choice(revenue_accounts)

        # First line - Credit to revenue account
        journal_entries.append(
            {
                "JournalNo": current_journal_no,
                "JournalDate": date_str,
                "AccountName": account,
                "Debits": "",
                "Credits": amount,
                "Description": "Monthly Revenue",
                "Name": customer["Name"],
                "Currency": "USD",
                "Location": "Main Office",
                "Class": "Revenue",
            }
        )

        # Second line - Debit to Silicon Valley Reserve (cash)
        journal_entries.append(
            {
                "JournalNo": current_journal_no,
                "JournalDate": "",
                "AccountName": "Silicon Valley Reserve",
                "Debits": amount,
                "Credits": "",
                "Description": "Cash Receipt",
                "Name": customer["Name"],
                "Currency": "USD",
                "Location": "Main Office",
                "Class": "Revenue",
            }
        )

        current_journal_no += 1

    # Generate expense entries
    for _ in range(num_expense_entries):
        day = random.randint(1, 28)
        entry_date = datetime.datetime(2020, month, day)
        date_str = entry_date.strftime("%-m/%-d/%y")

        # Calculate amount with some randomness
        expense_factor = (
            1 + (trend_factor - 1) * 0.7
            if trend_factor > 1
            else 1 - (1 - trend_factor) * 0.5
        )
        amount = round(15000 * expense_factor * random.uniform(0.85, 1.15), 2)

        # Select vendor and expense account
        vendor = random.choice(vendors)
        account = random.choice(expense_accounts)

        # First line - Debit to expense account
        journal_entries.append(
            {
                "JournalNo": current_journal_no,
                "JournalDate": date_str,
                "AccountName": account,
                "Debits": amount,
                "Credits": "",
                "Description": "Monthly Expense",
                "Name": vendor["Name"],
                "Currency": "USD",
                "Location": "Main Office",
                "Class": "Expense",
            }
        )

        # Second line - Credit to Silicon Valley Reserve (cash)
        journal_entries.append(
            {
                "JournalNo": current_journal_no,
                "JournalDate": "",
                "AccountName": "Silicon Valley Reserve",
                "Debits": "",
                "Credits": amount,
                "Description": "Cash Payment",
                "Name": vendor["Name"],
                "Currency": "USD",
                "Location": "Main Office",
                "Class": "Expense",
            }
        )

        current_journal_no += 1

    # Generate asset entries
    for _ in range(num_asset_entries):
        day = random.randint(1, 28)
        entry_date = datetime.datetime(2020, month, day)
        date_str = entry_date.strftime("%-m/%-d/%y")

        # Calculate amount with some randomness
        asset_factor = trend_factor * 0.8 if trend_factor > 1 else trend_factor * 0.4
        amount = round(35000 * asset_factor * random.uniform(0.8, 1.2), 2)

        # Select vendor and asset account
        vendor = random.choice(vendors)
        account = random.choice(asset_accounts)

        # First line - Debit to asset account
        journal_entries.append(
            {
                "JournalNo": current_journal_no,
                "JournalDate": date_str,
                "AccountName": account,
                "Debits": amount,
                "Credits": "",
                "Description": "Fixed Asset Purchase",
                "Name": vendor["Name"],
                "Currency": "USD",
                "Location": "Main Office",
                "Class": "Fixed Assets",
            }
        )

        # Second line - Credit to Silicon Valley Reserve (cash)
        journal_entries.append(
            {
                "JournalNo": current_journal_no,
                "JournalDate": "",
                "AccountName": "Silicon Valley Reserve",
                "Debits": "",
                "Credits": amount,
                "Description": "Cash Payment",
                "Name": vendor["Name"],
                "Currency": "USD",
                "Location": "Main Office",
                "Class": "Fixed Assets",
            }
        )

        current_journal_no += 1

    # Move to next month
    current_date += relativedelta(months=1)

# Verify that all journal entries have exactly 2 lines
journal_counts = {}
for entry in journal_entries:
    journal_no = entry["JournalNo"]
    journal_counts[journal_no] = journal_counts.get(journal_no, 0) + 1

for journal_no, count in journal_counts.items():
    if count != 2:
        print(f"Warning: Journal #{journal_no} has {count} lines instead of 2")

# Verify that all debits and credits balance
for journal_no in journal_counts.keys():
    entries = [e for e in journal_entries if e["JournalNo"] == journal_no]

    total_debits = sum(float(e["Debits"]) if e["Debits"] else 0 for e in entries)
    total_credits = sum(float(e["Credits"]) if e["Credits"] else 0 for e in entries)

    if abs(total_debits - total_credits) > 0.01:
        print(
            f"Warning: Journal #{journal_no} is unbalanced: Debits={total_debits}, Credits={total_credits}"
        )

# Write to CSV
with open("skynet_cash_based_journal_entries_2020.csv", "w", newline="") as file:
    fieldnames = [
        "JournalNo",
        "JournalDate",
        "AccountName",
        "Debits",
        "Credits",
        "Description",
        "Name",
        "Currency",
        "Location",
        "Class",
    ]
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    for entry in journal_entries:
        writer.writerow(entry)

print(f"Generated {len(journal_entries)} journal entry lines")
print(f"Total journal entries: {len(journal_counts)}")
print(
    f"Journal numbers range: {min(journal_counts.keys())} to {max(journal_counts.keys())}"
)

# Calculate summary statistics for verification
total_revenue = sum(
    float(entry["Credits"])
    for entry in journal_entries
    if entry["Class"] == "Revenue" and entry["Credits"]
)

total_expenses = sum(
    float(entry["Debits"])
    for entry in journal_entries
    if entry["Class"] == "Expense" and entry["Debits"]
)

total_assets = sum(
    float(entry["Debits"])
    for entry in journal_entries
    if entry["Class"] == "Fixed Assets" and entry["Debits"]
)

print(f"Total Revenue: ${total_revenue:,.2f}")
print(f"Total Expenses: ${total_expenses:,.2f}")
print(f"Total Assets: ${total_assets:,.2f}")
print(f"Net Income: ${total_revenue - total_expenses:,.2f}")
