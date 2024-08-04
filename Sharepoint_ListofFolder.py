# pip install office365-REST-Python-Client

from office365.runtime.auth.authentication_context import AuthenticationContext
from office365.sharepoint.client_context import ClientContext
from office365.sharepoint.files.file import File
from office365.sharepoint.folders.folder import Folder
import os

site_url = "https://Companyname.sharepoint.com/sites/siteName"
Username = "username"
password = "AppPassword"
document_library = 'Documents'


ctxauth=AuthenticationContext(site_url)
if ctxauth.acquire_token_for_user(username=Username, password=password):
    ctx=ClientContext(site_url,ctxauth)

    library=ctx.web.lists.get_by_title(document_library)
    folders=library.root_folder.folders

    # lists = ctx.web.lists  
    # ctx.load(lists)
    ctx.load(folders)
    try:
        ctx.execute_query()
        print(F"Foolder in '{document_library}'")
        for folder in folders:
            print(folder.properties["Name"])
        '''    
        for lst in lists:
            print(f"Name: {lst.properties['Title']}+ Type: {lst.properties['BaseTemplate']}")
        '''
    except Exception as e:
        print(f"Error {e}")  
else:
    print(ctxauth.get_last_error())
        