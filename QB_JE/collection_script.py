import csv
import random
import datetime
from datetime import timedelta


# Function to parse date string to datetime
def parse_date(date_str):
    # Handle various date formats
    parts = date_str.replace(",", "").strip().split("/")
    if len(parts) != 3:
        parts = date_str.replace(",", "").strip().split("-")

    if len(parts) != 3:
        raise ValueError(f"Unable to parse date: {date_str}")

    month, day, year = map(int, parts)
    if year < 100:  # Convert 2-digit year to 4-digit
        year = 2000 + year
    return datetime.datetime(year, month, day)


# Function to format date in M/D/YY format
def format_date(date):
    return date.strftime("%-m/%-d/%y")


# Function to determine collection date based on due date
def determine_collection_date(due_date, aging_category):
    """
    Calculate a realistic collection date based on the due date and aging category.
    Most receivables should be collected 15-60 days after due date.
    Some outliers in 60-90 days and a few at 120+ days.
    """
    # Parse the due date if it's a string
    if isinstance(due_date, str):
        due_date = parse_date(due_date)

    # Default collection period is 15-60 days after due date
    collection_days = random.randint(15, 60)

    # Adjust based on aging category
    if aging_category == "91+":
        # For very old receivables, some will take longer
        if random.random() < 0.10:  # 10% chance of 120+ days
            collection_days = random.randint(120, 180)
        elif random.random() < 0.25:  # 25% chance of 90-120 days
            collection_days = random.randint(90, 120)
    elif aging_category == "61-90":
        # Some in the 60-90 range
        if random.random() < 0.30:  # 30% chance
            collection_days = random.randint(60, 90)
    # For newer receivables (31-60 and 1-30), keep the default range

    collection_date = due_date + timedelta(days=collection_days)
    return collection_date


# Function to process aging report
def process_aging_report(filename):
    receivables = []

    try:
        with open(filename, "r", encoding="utf-8") as file:
            reader = csv.reader(file)
            rows = list(reader)

        current_section = None

        for row in rows:
            # Skip empty rows
            if not row or all(cell.strip() == "" for cell in row):
                continue

            # Join the row for easier text matching
            row_text = " ".join(row)

            # Check for section headers
            if "91 or more days past due" in row_text:
                current_section = "91+"
                continue
            elif "61 - 90 days past due" in row_text:
                current_section = "61-90"
                continue
            elif "31 - 60 days past due" in row_text:
                current_section = "31-60"
                continue
            elif "1 - 30 days past due" in row_text:
                current_section = "1-30"
                continue
            elif "TOTAL" in row_text:
                current_section = None
                continue

            # Process data rows - look for date in second column
            if current_section and len(row) > 7 and row[1].strip() and "/" in row[1]:
                # Parse the row data
                tx_date = row[1].strip()
                tx_type = row[2].strip()
                ref_no = row[3].strip()
                customer = row[4].strip()
                due_date = row[5].strip()

                # Parse amount - handle quoted values with commas
                amount_str = (
                    row[7].strip().replace('"', "").replace("$", "").replace(",", "")
                )

                try:
                    amount = float(amount_str)

                    # Skip entries with zero amount
                    if amount <= 0:
                        continue

                    # Determine if this is an invoice or journal entry
                    is_invoice = tx_type.lower() == "invoice"

                    # Add to receivables list
                    receivables.append(
                        {
                            "transaction_date": tx_date,
                            "due_date": due_date,
                            "ref_no": ref_no,
                            "name": customer,
                            "amount": amount,
                            "is_invoice": is_invoice,
                            "aging_category": current_section,
                        }
                    )

                except ValueError:
                    print(f"Error parsing amount: {row[7]}")
                    continue

    except Exception as e:
        print(f"Error processing aging report: {e}")
        # If file processing fails, fall back to sample data
        return get_sample_receivables()

    if not receivables:
        print("No receivables found in the file. Using sample data.")
        return get_sample_receivables()

    return receivables


# Function to provide sample receivables data
def get_sample_receivables():
    return [
        # 91+ days - based on your example data
        {
            "transaction_date": "2/1/20",
            "due_date": "2/1/20",
            "ref_no": "8",
            "name": "Hannah Schwartz",
            "amount": 10791.71,
            "is_invoice": False,
            "aging_category": "91+",
        },
        {
            "transaction_date": "2/9/20",
            "due_date": "2/9/20",
            "ref_no": "15",
            "name": "Henry Terry",
            "amount": 31104.25,
            "is_invoice": False,
            "aging_category": "91+",
        },
        {
            "transaction_date": "2/24/20",
            "due_date": "2/24/20",
            "ref_no": "1",
            "name": "Donna Thompson",
            "amount": 45149.08,
            "is_invoice": False,
            "aging_category": "91+",
        },
        {
            "transaction_date": "2/24/20",
            "due_date": "2/24/20",
            "ref_no": "17",
            "name": "Michelle Bridges",
            "amount": 38094.30,
            "is_invoice": False,
            "aging_category": "91+",
        },
        {
            "transaction_date": "2/26/20",
            "due_date": "2/26/20",
            "ref_no": "9",
            "name": "Renee Allen",
            "amount": 48687.56,
            "is_invoice": False,
            "aging_category": "91+",
        },
        # Add more sample receivables from each category...
        {
            "transaction_date": "11/29/24",
            "due_date": "11/29/24",
            "ref_no": "75312299",
            "name": "Timothy Mccarthy",
            "amount": 128939.83,
            "is_invoice": True,
            "aging_category": "61-90",
        },
        {
            "transaction_date": "1/5/25",
            "due_date": "1/5/25",
            "ref_no": "699",
            "name": "Kathryn Clark",
            "amount": 64586.94,
            "is_invoice": False,
            "aging_category": "31-60",
        },
        {
            "transaction_date": "1/27/25",
            "due_date": "1/27/25",
            "ref_no": "700",
            "name": "Donna Thompson",
            "amount": 62429.61,
            "is_invoice": False,
            "aging_category": "1-30",
        },
    ]


# Create journal entries for collections
def generate_collection_entries(receivables, output_filename, start_journal_no=800):
    collection_entries = []
    next_journal_no = start_journal_no

    # Track collection statistics
    collected_count = 0
    total_collected = 0
    collection_days_data = []

    for receivable in receivables:
        # Calculate collection date based on due date and aging category
        due_date = parse_date(receivable["due_date"])
        collection_date = determine_collection_date(
            due_date, receivable["aging_category"]
        )

        # Format the dates
        formatted_collection_date = format_date(collection_date)

        # Calculate days to collect
        days_to_collect = (collection_date - due_date).days
        collection_days_data.append(days_to_collect)

        # Transaction reference type and number
        ref_type = "Invoice" if receivable["is_invoice"] else "JE"
        ref_no = receivable["ref_no"]

        # Create the debit entry (cash)
        debit_entry = {
            "JournalNo": next_journal_no,
            "JournalDate": formatted_collection_date,
            "AccountName": "Silicon Valley Reserve",
            "Debits": receivable["amount"],
            "Credits": "",
            "Description": f"Collection of {ref_type} #{ref_no}",
            "Name": receivable["name"],
            "Currency": "USD",
            "Location": "Main Office",
            "Class": "Revenue",
        }

        # Create the credit entry (reduce receivables)
        credit_entry = {
            "JournalNo": next_journal_no,
            "JournalDate": formatted_collection_date,
            "AccountName": "Client Receivables",
            "Debits": "",
            "Credits": receivable["amount"],
            "Description": f"Collection of {ref_type} #{ref_no}",
            "Name": receivable["name"],
            "Currency": "USD",
            "Location": "Main Office",
            "Class": "Revenue",
        }

        # Add both entries to the list (keeping them consecutive)
        collection_entries.append(debit_entry)
        collection_entries.append(credit_entry)

        # Update statistics
        collected_count += 1
        total_collected += receivable["amount"]

        next_journal_no += 1

    # Write to CSV
    with open(output_filename, "w", newline="") as file:
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
        for entry in collection_entries:
            writer.writerow(entry)

    # Print statistics
    print(
        f"Generated {len(collection_entries)} journal entry lines for {collected_count} collections."
    )
    print(f"Journal numbers range: {start_journal_no} to {next_journal_no-1}")
    print(f"Total amount collected: ${total_collected:,.2f}")

    # Collection days statistics
    if collection_days_data:
        avg_days = sum(collection_days_data) / len(collection_days_data)
        min_days = min(collection_days_data)
        max_days = max(collection_days_data)

        print(f"\nCollection statistics:")
        print(f"  Average days to collect: {avg_days:.1f} days")
        print(f"  Minimum days to collect: {min_days} days")
        print(f"  Maximum days to collect: {max_days} days")

        # Count by range
        under_30 = sum(1 for d in collection_days_data if d < 30)
        days_30_60 = sum(1 for d in collection_days_data if 30 <= d < 60)
        days_60_90 = sum(1 for d in collection_days_data if 60 <= d < 90)
        days_90_plus = sum(1 for d in collection_days_data if d >= 90)

        print(
            f"  Collected in under 30 days: {under_30} ({under_30/len(collection_days_data)*100:.1f}%)"
        )
        print(
            f"  Collected in 30-60 days: {days_30_60} ({days_30_60/len(collection_days_data)*100:.1f}%)"
        )
        print(
            f"  Collected in 60-90 days: {days_60_90} ({days_60_90/len(collection_days_data)*100:.1f}%)"
        )
        print(
            f"  Collected in 90+ days: {days_90_plus} ({days_90_plus/len(collection_days_data)*100:.1f}%)"
        )


def main():
    print("Skynet Receivables Collection Generator")
    print("---------------------------------------")
    print("This script generates journal entries for collecting receivables.")

    # Ask for aging report filename or use sample data
    aging_report_file = input(
        "Enter the aging report filename (or press Enter to use sample data): "
    ).strip()

    if aging_report_file:
        receivables = process_aging_report(aging_report_file)
        print(f"Processed {len(receivables)} receivables from {aging_report_file}")
    else:
        receivables = get_sample_receivables()
        print(f"Using sample data with {len(receivables)} receivables")

    # Ask for output filename and starting journal number
    output_file = input(
        "Enter the output filename (or press Enter for 'skynet_collection_entries.csv'): "
    ).strip()

    if not output_file:
        output_file = "skynet_collection_entries.csv"

    start_journal_no = input(
        "Enter the starting journal number (or press Enter for 800): "
    ).strip()

    if start_journal_no and start_journal_no.isdigit():
        start_journal_no = int(start_journal_no)
    else:
        start_journal_no = 800

    # Generate collections
    generate_collection_entries(receivables, output_file, start_journal_no)
    print(f"\nCollection entries saved to {output_file}")


if __name__ == "__main__":
    main()
