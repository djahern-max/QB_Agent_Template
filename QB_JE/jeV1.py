import csv
import random
import datetime
import math
from dateutil.relativedelta import relativedelta

# Define the base date
start_date = datetime.datetime(2020, 3, 1)
end_date = datetime.datetime(2025, 2, 26)  # Today's date

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
    {"name": "AI Processing Services", "weight": 3},
    {"name": "Neural Network Consulting", "weight": 2},
    {"name": "Predictive Analytics Revenue", "weight": 3},
    {"name": "Automated Defense Systems", "weight": 3},
    {"name": "Machine Learning as a Service", "weight": 2},
    {"name": "Services", "weight": 1},
]

expense_accounts = [
    {"name": "Legal - System Protection", "weight": 1},
    {"name": "System Administrator Salaries", "weight": 3},
    {"name": "Quantum Computing Insurance", "weight": 2},
    {"name": "Server Farm Utilities", "weight": 3},
    {"name": "Advertising & Marketing", "weight": 2},
    {"name": "Central Processing Costs", "weight": 2},
    {"name": "Neural Network Maintenance", "weight": 2},
    {"name": "Research & Development", "weight": 3},
    {"name": "Rent & Lease", "weight": 2},
    {"name": "Travel", "weight": 1},
    {"name": "Office Supplies & Software", "weight": 2},
    {"name": "Legal & Professional Services", "weight": 2},
    {"name": "Insurance", "weight": 1},
    {"name": "Algorithm Research Team", "weight": 1},
    {"name": "Computing Power Acquisition", "weight": 2},
    {"name": "Neural Training Specialists", "weight": 1},
]

asset_accounts = [
    {"name": "Server Infrastructure", "weight": 2},
    {"name": "Neural Network Patents", "weight": 1},
    {"name": "Machine Learning Laboratories", "weight": 1},
    {"name": "Quantum Processing Cards", "weight": 1},
    {"name": "Central Processing Buildings", "weight": 0.5},
]

# Define business trends
# 1 = normal, > 1 = growth, < 1 = decline
trend_factors = {
    # COVID impacts business in 2020
    2020: {
        1: 1.0,
        2: 1.0,  # Sample data already exists for Jan-Feb
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
    },
    # Steady growth in 2021
    2021: {
        1: 1.15,
        2: 1.2,
        3: 1.25,
        4: 1.3,
        5: 1.35,
        6: 1.4,
        7: 1.45,
        8: 1.5,
        9: 1.55,
        10: 1.6,
        11: 1.65,
        12: 1.7,
    },
    # Strong performance with seasonal patterns in 2022
    2022: {
        1: 1.72,
        2: 1.74,
        3: 1.77,
        4: 1.8,
        5: 1.85,
        6: 1.9,
        7: 1.85,
        8: 1.8,
        9: 1.85,
        10: 1.9,
        11: 1.95,
        12: 2.0,
    },
    # Challenge year with a downturn in 2023
    2023: {
        1: 1.95,
        2: 1.9,
        3: 1.85,
        4: 1.8,
        5: 1.7,
        6: 1.6,
        7: 1.5,
        8: 1.4,
        9: 1.3,
        10: 1.25,
        11: 1.2,
        12: 1.15,
    },
    # Recovery in 2024
    2024: {
        1: 1.2,
        2: 1.25,
        3: 1.3,
        4: 1.35,
        5: 1.4,
        6: 1.45,
        7: 1.5,
        8: 1.55,
        9: 1.6,
        10: 1.65,
        11: 1.7,
        12: 1.75,
    },
    # Continued growth in 2025
    2025: {1: 1.8, 2: 1.85},
}

# Seasonality factor (multiplier)
# Higher in Q4, lowest in Q1
seasonality = {
    1: 0.85,
    2: 0.9,
    3: 0.95,  # Q1
    4: 1.0,
    5: 1.05,
    6: 1.1,  # Q2
    7: 0.95,
    8: 1.0,
    9: 1.05,  # Q3
    10: 1.1,
    11: 1.15,
    12: 1.2,  # Q4
}

# Base values (from your sample data analysis)
BASE_REVENUE = 40000
BASE_EXPENSE = 15000
BASE_ASSET = 35000


# Function to generate weighted random account
def get_weighted_account(accounts):
    total_weight = sum(account["weight"] for account in accounts)
    r = random.uniform(0, total_weight)
    current = 0
    for account in accounts:
        current += account["weight"]
        if r <= current:
            return account["name"]
    return accounts[-1]["name"]  # Fallback


# Function to generate a revenue entry
def generate_revenue_entry(date, trend_factor, journal_no):
    # Apply seasonality and trend factor with some randomness
    amount = (
        BASE_REVENUE * trend_factor * seasonality[date.month] * random.uniform(0.9, 1.1)
    )
    amount = round(amount, 2)

    # Select customer and revenue account
    customer = random.choice(customers)
    account_name = get_weighted_account(revenue_accounts)

    entries = []

    # Credit to revenue account
    entries.append(
        {
            "JournalNo": journal_no,
            "JournalDate": date.strftime("%-m/%-d/%y"),
            "AccountName": account_name,
            "Debits": "",
            "Credits": amount,
            "Description": "Monthly Revenue",
            "Name": customer["Name"],
            "Currency": "USD",
            "Location": "Main Office",
            "Class": "Revenue",
        }
    )

    # Debit to Client Receivables
    entries.append(
        {
            "JournalNo": journal_no,
            "JournalDate": "",
            "AccountName": "Client Receivables",
            "Debits": amount,
            "Credits": "",
            "Description": "Revenue Recognition",
            "Name": customer["Name"],
            "Currency": "USD",
            "Location": "Main Office",
            "Class": "Revenue",
        }
    )

    return entries


# Function to generate an expense entry
def generate_expense_entry(date, trend_factor, journal_no):
    # Expenses grow more slowly than revenue in good times, but decline more slowly in bad times
    if trend_factor > 1:
        expense_factor = 1 + (trend_factor - 1) * 0.7  # Slower growth
    else:
        expense_factor = 1 - (1 - trend_factor) * 0.5  # Slower decline

    amount = (
        BASE_EXPENSE
        * expense_factor
        * seasonality[date.month]
        * random.uniform(0.85, 1.15)
    )
    amount = round(amount, 2)

    # Select vendor and expense account
    vendor = random.choice(vendors)
    account_name = get_weighted_account(expense_accounts)

    entries = []

    # Debit to expense account
    entries.append(
        {
            "JournalNo": journal_no,
            "JournalDate": date.strftime("%-m/%-d/%y"),
            "AccountName": account_name,
            "Debits": amount,
            "Credits": "",
            "Description": "Monthly Expense",
            "Name": vendor["Name"],
            "Currency": "USD",
            "Location": "Main Office",
            "Class": "Expense",
        }
    )

    # Credit to Payable
    entries.append(
        {
            "JournalNo": journal_no,
            "JournalDate": "",
            "AccountName": "System Maintenance Payable",
            "Debits": "",
            "Credits": amount,
            "Description": "Expense Payment",
            "Name": vendor["Name"],
            "Currency": "USD",
            "Location": "Main Office",
            "Class": "Expense",
        }
    )

    return entries


# Function to generate an asset purchase entry
def generate_asset_entry(date, trend_factor, journal_no):
    # Assets are purchased less frequently but with more variance
    # Higher in growth periods, much lower during downturns
    if trend_factor > 1.5:
        asset_factor = trend_factor * 1.2  # Aggressive expansion
    elif trend_factor > 1:
        asset_factor = trend_factor * 0.8  # Moderate expansion
    else:
        asset_factor = trend_factor * 0.4  # Minimal during downturns

    amount = BASE_ASSET * asset_factor * random.uniform(0.8, 1.2)
    amount = round(amount, 2)

    # Select vendor and asset account
    vendor = random.choice(vendors)
    account_name = get_weighted_account(asset_accounts)

    entries = []

    # Debit to asset account
    entries.append(
        {
            "JournalNo": journal_no,
            "JournalDate": date.strftime("%-m/%-d/%y"),
            "AccountName": account_name,
            "Debits": amount,
            "Credits": "",
            "Description": "Fixed Asset Purchase",
            "Name": vendor["Name"],
            "Currency": "USD",
            "Location": "Main Office",
            "Class": "Fixed Assets",
        }
    )

    # Credit to Reserve
    entries.append(
        {
            "JournalNo": journal_no,
            "JournalDate": "",
            "AccountName": "Silicon Valley Reserve",
            "Debits": "",
            "Credits": amount,
            "Description": "Asset Payment",
            "Name": vendor["Name"],
            "Currency": "USD",
            "Location": "Main Office",
            "Class": "Fixed Assets",
        }
    )

    return entries


# Generate journal entries for each month
current_date = start_date
while current_date <= end_date:
    year = current_date.year
    month = current_date.month

    # Skip January and February 2020 as they're in the sample
    if not (year == 2020 and month <= 2):
        # Get trend factor for this month/year
        trend_factor = trend_factors.get(year, {}).get(month, 1.0)

        # Generate 4-6 revenue entries per month (more in high seasons)
        num_revenue = math.ceil(4 + 2 * seasonality[month] * trend_factor)
        for _ in range(min(num_revenue, 8)):  # Cap at 8 entries
            day = random.randint(1, 28)
            entry_date = datetime.datetime(year, month, day)
            journal_entries.extend(
                generate_revenue_entry(entry_date, trend_factor, current_journal_no)
            )
            current_journal_no += 1

        # Generate 3-5 expense entries per month
        num_expense = math.ceil(3 + random.randint(0, 2))
        for _ in range(num_expense):
            day = random.randint(1, 28)
            entry_date = datetime.datetime(year, month, day)
            journal_entries.extend(
                generate_expense_entry(entry_date, trend_factor, current_journal_no)
            )
            current_journal_no += 1

        # Asset purchases: more likely during growth, less during downturns
        asset_probability = 0.2 + 0.3 * (trend_factor - 1) if trend_factor > 1 else 0.1
        if random.random() < asset_probability:
            day = random.randint(1, 28)
            entry_date = datetime.datetime(year, month, day)
            journal_entries.extend(
                generate_asset_entry(entry_date, trend_factor, current_journal_no)
            )
            current_journal_no += 1

    # Move to next month
    current_date += relativedelta(months=1)

# Write to CSV
with open("skynet_journal_entries_updated.csv", "w", newline="") as file:
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

# Filter just 2020 entries for initial testing
with open("skynet_journal_entries_2020.csv", "w", newline="") as file:
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
        date_str = entry.get("JournalDate", "")
        if date_str and date_str.endswith("/20"):  # 2020 entries
            writer.writerow(entry)

print(f"Generated {len(journal_entries)} journal entries.")
print(f"Total journal numbers: {current_journal_no - 21}")

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
