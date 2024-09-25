
# pip install openpysl msoffcryto-tool # password activity in excel

import msoffcrypto
import openpyxl
import argparse
import os


def remove_password(protected_file, password):
    temp_file = 'temp_unprotected.xlsx'
    with open(protected_file,'rb') as file:
        with open(temp_file, 'wb') as decrypted:
            office_file=msoffcrypto.OfficeFile(file)
            office_file.load_key(password=password)
            office_file.decrypt(decrypted)

    wb= openpyxl.load_workbook(temp_file)
    wb.save(protected_file)
    os.remove(temp_file)

def list_files_in_folder(folder_path, password):
    file_list = os.listdir(folder_path)
    files= [f for f in file_list if os.path.isfile(os.path.join(folder_path,f))]
    for short_filename in files:
        full_filename = os.path.join(folder_path,short_filename)
        print(full_filename)
        remove_password(full_filename, password)
        print(f"Removed password for {full_filename}")


parser = argparse.ArgumentParser(description='Positional Argument involved are:')
parser.add_argument('folderpath', type=str)
parser.add_argument('password', type=str)
args = parser.parse_args()

list_files_in_folder(args.folderpath, args.password)

