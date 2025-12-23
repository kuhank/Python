import pyodbc
from dotenv import load_dotenv
import os
import glob
from pathlib import Path
from typing import List, Dict

import pyodbc
import pandas as pd

load_dotenv()
# ==============================
# CONFIG
# ==============================

# Folder where your PDFs live
PDF_FOLDER = os.getenv("PDF_FOLDER")

# Excel output file
OUTPUT_EXCEL = os.getenv("OUTPUT_EXCEL")


SQL_SERVER = os.getenv("SQL_SERVER")
SQL_DATABASE = os.getenv("SQL_DATABASE")
SQL_USERNAME = os.getenv("SQL_USERNAME")
SQL_PASSWORD = os.getenv("SQL_PASSWORD")

# Table / column names in SQL Server
TABLE_NAME = os.getenv("TABLE_NAME")
ACCOUNT_COL = os.getenv("ACCOUNT_COL")
ORDERID_COL = os.getenv("ORDERID_COL")

# ==============================
# HELPER: Extract account number
# ==============================


def extract_account_and_series(filename: str):
    """
    Given a filename like:
        - 'quest_Lab Documents_201497_1.pdf'
        - '2024_10_18_mr_prostate_wwo_con_X-Ray Documents_240772_1.pdf'
        - 'progress_notes_152489_10.pdf'
    We assume:
        "<anything>_<account_number>_<series>.pdf"

    Returns: (account_number, series_number) or (None, None) if pattern invalid.
    """
    base = os.path.basename(filename)
    name, ext = os.path.splitext(base)

    # Only handle PDFs, just in case
    if ext.lower() != ".pdf":
        return None, None

    parts = name.split("_")
    if len(parts) < 3:
        # Not enough parts to contain account + series
        return None, None

    account_str = parts[-2]  # second-to-last token
    series_str = parts[-1]  # last token

    # Basic sanity check: account should be digits
    if not account_str.isdigit():
        return None, None

    # series can be digits, but we won't enforce strongly
    return account_str, series_str


# ==============================
# HELPER: Query SQL Server
# ==============================


def get_max_order_ids_for_accounts(accounts: List[str]) -> pd.DataFrame:
    """
    Given a list of account numbers (strings), query tbl_order to get:
        account_number, max(order_id)

    Returns a DataFrame with columns:
        [ACCOUNT_COL, 'max_order_id']
    """
    if not accounts:
        return pd.DataFrame(columns=[ACCOUNT_COL, "max_order_id"])

    # Remove duplicates to reduce query size
    unique_accounts = sorted(set(accounts))

    # Build connection string
    conn_str = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={SQL_SERVER};"
        f"DATABASE={SQL_DATABASE};"
        f"UID={SQL_USERNAME};"
        f"PWD={SQL_PASSWORD};"
        "TrustServerCertificate=yes;"
    )

    conn = pyodbc.connect(conn_str)
    try:
        # We'll do IN (?) param list; for very large lists you may want to chunk.
        # Simple version assuming list is reasonable in size.
        placeholders = ", ".join(["?"] * len(unique_accounts))
        sql = f"""
            SELECT
                {ACCOUNT_COL} AS account_number,
                MAX({ORDERID_COL}) AS max_order_id
            FROM {TABLE_NAME}
            WHERE {ACCOUNT_COL} IN ({placeholders})
            GROUP BY {ACCOUNT_COL}
        """

        df_orders = pd.read_sql(sql, conn, params=unique_accounts)
        return df_orders

    finally:
        conn.close()


# ==============================
# MAIN LOGIC
# ==============================


def main():
    # 1. Find all PDF files
    pdf_pattern = os.path.join(PDF_FOLDER, "*.pdf")
    pdf_files = glob.glob(pdf_pattern)

    records: List[Dict] = []

    # 2. Extract account + series per file
    for filepath in pdf_files:
        account, series = extract_account_and_series(filepath)
        if account is None:
            # Skip files that don't match pattern
            # (you could also log these if you want)
            continue

        records.append(
            {
                "filename": os.path.basename(filepath),
                "full_path": filepath,
                "account_number": account,
                "series_number": series,
            }
        )

    if not records:
        print("No files matched the pattern for account_number extraction.")
        return

    df_files = pd.DataFrame(records)

    # 3. Get max(order_id) from SQL Server for extracted accounts
    account_list = df_files["account_number"].tolist()
    df_orders = get_max_order_ids_for_accounts(account_list)

    # 4. Merge file info with order info
    df_merged = df_files.merge(
        df_orders,
        how="left",
        left_on="account_number",
        right_on="account_number",
    )

    # 5. Write to Excel
    output_folder = os.path.dirname(OUTPUT_EXCEL)
    if output_folder and not os.path.exists(output_folder):
        os.makedirs(output_folder, exist_ok=True)

    df_merged.to_excel(OUTPUT_EXCEL, index=False)
    print(f"Successfully wrote output to: {OUTPUT_EXCEL}")


if __name__ == "__main__":
    main()
