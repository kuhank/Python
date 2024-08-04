# pip install office365-REST-Python-Client
import argparse
from office365.runtime.auth.authentication_context import AuthenticationContext
from office365.sharepoint.client_context import ClientContext
from office365.sharepoint.files.file import File
from office365.sharepoint.folders.folder import Folder
import os
def upload_files_to_sharepoint(site_url, username, password, target_folder_url, local_path):
    site_url = site_url
    Username = username
    password = password
    target_folder_url = target_folder_url
    local_path = local_path   
    ctxauth=AuthenticationContext(site_url)
    if ctxauth.acquire_token_for_user(username=Username, password=password):
        ctx=ClientContext(site_url,ctxauth)
        try:
            folder = ctx.web.get_folder_by_server_relative_url(target_folder_url)
            ctx.load(folder)
            ctx.execute_query()
            print("Target folder exists")
        except Exception as e:
            print(f"Error: {e}")
            print(F"Targer folder '{target_folder_url}' does not exist")
            exit()         
        try:
            with open(local_path,'rb') as file_content:
                content = file_content.read()
                target_url = f"{target_folder_url}/{os.path.basename(local_path)}"
                upload_file = folder.files.add(target_url, file_content, overwrite=True)
                ctx.execute_query()
                print("File has been successfully uploaded")
        except Exception as e:
            print(f"Error Uploading File : {e}")

    else:
        print(ctxauth.get_last_error()) 
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--site_url', type =str, required=True)
    parser.add_argument('--username', type =str, required=True)
    parser.add_argument('--password', type =str, required=True)
    parser.add_argument('--target_folder_url', type =str, required=True)
    parser.add_argument('--local_path', type =str, required=True)

    args=parser.parse_args()

    upload_files_to_sharepoint(args.site_url, args.username, args.password, args.target_folder_url, args.local_path)

'''

python SharepointConnection.py --site_url "https://company.sharepoint.com/sites/mysite" --username "yourusername@yourdomain.com" --password "apppassword" --target_folder_url "/sites/mysite/Shared Documents/Testing" --local_path "Drive:\\folder\\filename"

'''