# pip install office365-REST-Python-Client

from office365.runtime.auth.authentication_context import AuthenticationContext
from office365.sharepoint.client_context import ClientContext
from office365.sharepoint.files.file import File
from office365.sharepoint.folders.folder import Folder
import os

site_url = "https://company.sharepoint.com/sites/mysite"
Username = "username"
password = "pwd"
target_folder_url = '/sites/mysite/Shared Documents/folder'
document_library = 'Documents'

local_path = r'Drive:\\folder\\filename'


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
            # upload_file= File.save_binary(ctx, target_url, content=content)
            upload_file = folder.files.add(target_url, file_content, overwrite=True)
            ctx.execute_query()
            print("File has been successfully uploaded")
    except Exception as e:
        print(f"Error Uploading File : {e}")

else:
    print(ctxauth.get_last_error())
  