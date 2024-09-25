import win32com.client as win32 # component object model automation
import argparse

def ensure_excel_dispath():
    win32.gencache.EnsureDispatch('Excel.Application')

def password_excel(filename, pwd): 
    # excel = win32.gencache.EnsureDispatch('Excel.Application')  # starts instance of excel and COM object for excel created
    ensure_excel_dispath()

    excel = win32.Dispatch("Excel.Application")
    excel.DisplayAlerts = False
    excel.Visible= False # Run in Background
    try:
        wb = excel.Workbooks.Open(filename, ReadOnly= False, Password= '')
        print("Workbook is not password protected")
        wb.Password=pwd
        wb.Save()
        wb.Close(True)
        print("Workbook is now password protected")
    except Exception as e:
        if 'password' in str(e).lower():
            print("Workbook is already password protected")
    finally:
        for workbook in excel.Workbooks:
            workbook.Close(SaveChanges=False)
        excel.Application.Quit()
        del excel   
def main():
    parser = argparse.ArgumentParser(description="check and set password for Excel")
    parser.add_argument("--filepath", help= "Path to workbook")
    parser.add_argument("--password", help="Password to be set to workbook")
    args=parser.parse_args()
    filepath=args.filepath
    password=args.password
    password_excel(filename=filepath, pwd= password)

if __name__ == "__main__":
    
    main()

'''
python.exe ExcelOperation.py --filepath "C:/code/test.xlsx" --password "pass"
Workbook is not password protected
Workbook is now password protected

python.exe ExcelOperation.py --filepath "C:/code/test.xlsx" --password "pass"
Workbook is already password protected

'''