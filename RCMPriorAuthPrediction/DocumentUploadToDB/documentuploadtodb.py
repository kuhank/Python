import pyodbc
import io
import base64
import pandas as pd
import openpyxl
import os
from dotenv import load_dotenv

load_dotenv()


# helper
def move_Prog_notes_ForAI(sourcefolder, DestFolder, RegexPattern):
    import shutil
    import re

    if not os.path.exists(DestFolder):
        os.makedirs(DestFolder)

    for filename in os.listdir(sourcefolder):
        if re.match(RegexPattern, filename):
            shutil.move(
                os.path.join(sourcefolder, filename), os.path.join(DestFolder, filename)
            )
            print(f"Moved file: {filename} to {DestFolder}")


def delete_other_files(sourcefolder, Keep_Pattern):
    import os
    import re

    for filename in os.listdir(sourcefolder):
        if not re.match(Keep_Pattern, filename):
            os.remove(os.path.join(sourcefolder, filename))
            print(f"Deleted file: {filename}")


def main():
    OUTPUT_EXCEL = os.getenv("OUTPUT_EXCEL")
    df = pd.read_excel(OUTPUT_EXCEL)
    SQL_SERVER = os.getenv("SQL_SERVER")
    SQL_DATABASE = os.getenv("SQL_DATABASE")
    SQL_USERNAME = os.getenv("SQL_USERNAME")
    SQL_PASSWORD = os.getenv("SQL_PASSWORD")
    conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={SQL_SERVER};"
        f"DATABASE={SQL_DATABASE};"
        f"UID={SQL_USERNAME};"
        f"PWD={SQL_PASSWORD};"
        "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    )

    cursor = conn.cursor()

    # Loop through DataFrame rows
    for index, row in df.iterrows():
        doc_path = row["filename"]
        db_path = row["filename"]
        doc_type = row["filename"]
        order_id = int(row["max_order_id"])
        fullpath = row["full_path"]

        # Read and encode the PDF
        with open(f"{fullpath}", "rb") as file:
            pdf_data = file.read()
            mem_stream = io.BytesIO(file.read())
            base64_data = base64.b64encode(pdf_data)
            encoded = base64.b64encode(file.read())
            pdf_bytes = mem_stream.getvalue()

        # Insert into SQL
        cursor.execute(
            """
            INSERT INTO tbl_order_documents ( document, [Document Type], [order id], [update time], [isactive], documentpath)
            VALUES (?,  ?, ?, GETDATE(), ?, ?)
                    """,
            pdf_data,
            doc_type,
            order_id,
            1,
            db_path,
        )

    # Commit and close
    conn.commit()
    cursor.close()
    conn.close()
    print("Documents uploaded successfully.")
    postUploadProcessing()


def postUploadProcessing():
    sourcefolder = r"C:\\code\\AIModel2\\new\\documentUpload\\pdffiles\\"
    DestFolder = r"C:\\code\\AIModel2\\new\\documentUpload\\BackupFileforAI\\"
    RegexPattern = r"progress_notes_.*_1\.pdf$"
    move_Prog_notes_ForAI(sourcefolder, DestFolder, RegexPattern)
    print("File movement completed.")
    Keep_Pattern = "^progress_notes_.*_1\.pdf$"
    sourcefolder_ForDeletion = r"C:\\code\\AIModel2\\new\\documentUpload\\pdffiles\\"
    delete_other_files(sourcefolder_ForDeletion, Keep_Pattern)
    print("File deletion completed.")
    return


if __name__ == "__main__":
    main()

# ==============================
