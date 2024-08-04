# pip install office365-REST-Python-Client

from office365.runtime.auth.authentication_context import AuthenticationContext
from office365.sharepoint.client_context import ClientContext
from office365.sharepoint.files.file import File
from office365.sharepoint.folders.folder import Folder
import os

site_url = "https://Companyname.sharepoint.com/sites/siteName"
Username = "username"
password = "AppPassword"

ctxauth=AuthenticationContext(site_url)
if ctxauth.acquire_token_for_user(username=Username, password=password):
    ctx=ClientContext(site_url,ctxauth)

    lists = ctx.web.lists  
    ctx.load(lists)
    try:
        ctx.execute_query()
        for lst in lists:
            print(f"Name: {lst.properties['Title']}+ Type: {lst.properties['BaseTemplate']}")
    except Exception as e:
        
        print(f"Error {e}")  
else:
    print(ctxauth.get_last_error())

'''
Output:

Name: Access Requests+ Type: 160
Name: appdata+ Type: 125
Name: Composed Looks+ Type: 124
Name: Converted Forms+ Type: 10102
Name: DO_NOT_DELETE_SPLIST_SITECOLLECTION_AGGREGATED_CONTENTTYPES+ Type: 100
Name: Documents+ Type: 101
Name: Form Templates+ Type: 101
Name: List Template Gallery+ Type: 114
Name: Composed Looks+ Type: 124
Name: Converted Forms+ Type: 10102
Name: DO_NOT_DELETE_SPLIST_SITECOLLECTION_AGGREGATED_CONTENTTYPES+ Type: 100
Name: Documents+ Type: 101
Name: Form Templates+ Type: 101
Name: List Template Gallery+ Type: 114
Name: Converted Forms+ Type: 10102
Name: DO_NOT_DELETE_SPLIST_SITECOLLECTION_AGGREGATED_CONTENTTYPES+ Type: 100
Name: Documents+ Type: 101
Name: Form Templates+ Type: 101
Name: List Template Gallery+ Type: 114
Name: DO_NOT_DELETE_SPLIST_SITECOLLECTION_AGGREGATED_CONTENTTYPES+ Type: 100
Name: Documents+ Type: 101
Name: Form Templates+ Type: 101
Name: List Template Gallery+ Type: 114
Name: Documents+ Type: 101
Name: Form Templates+ Type: 101
Name: List Template Gallery+ Type: 114
Name: Form Templates+ Type: 101
Name: List Template Gallery+ Type: 114
Name: List Template Gallery+ Type: 114
Name: Maintenance Log Library+ Type: 175
Name: Master Page Gallery+ Type: 116
Name: Sharing Links+ Type: 3300
Name: Site Assets+ Type: 101
Name: Site Pages+ Type: 119
Name: Solution Gallery+ Type: 121
Name: Style Library+ Type: 101
Name: TaxonomyHiddenList+ Type: 100
Name: Theme Gallery+ Type: 123
Name: User Information List+ Type: 112
Name: Web Part Gallery+ Type: 113
'''