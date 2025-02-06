import os
import pandas as pd
import pyodbc
import json
def readConfigFile(configfilename):
    with open(configfilename,'r') as file:
        config = json.load(file)
        return config
config = readConfigFile('configFile.json')
driver=config["sourceDB"]["driver"]
server=config["sourceDB"]["server"]
database=config["sourceDB"]["database"]
uid=config["sourceDB"]["username"]
pwd=config["sourceDB"]["password"]
conn = pyodbc.connect(f'Driver={driver};SERVER={server};DATABASE={database};UID={uid};PWD={pwd}')
cursor = conn.cursor()
cursor.fast_executemany = True # enable fast bult insert
folderpath = config["output"]["folder"]
tablename='claimtrackingReport_staging'
for files in os.listdir(folderpath):
    if files.endswith(".xlsx"):
        filepath = os.path.join(folderpath, files)
        print("Processing file: ",filepath)
        df = pd.read_excel(filepath, engine="openpyxl")
        df["filename"] = files
        df = df.astype(str)
        df = df.where(pd.notna(df), None)
        df.replace({pd.NA: None, '' : None}, inplace= True)
        df= df.map(lambda x: None if (x=='' or pd.isna(x)) else x)
        data_tuples = list(df.itertuples(index=False, name=None)) # convert DF to list of tuples
        placeholder = ', '.join(['?']* len(df.columns))
        sql = f"insert into {tablename} ({', '.join(df.columns)}) values ({placeholder})"     
        try:
            if data_tuples:
                cursor.executemany(sql,data_tuples)
                conn.commit()
        except Exception as e:
            print(f"error inserting row from {files} : {e}")
            conn.rollback()
        
cursor.close()
conn.close()
print("Data inserted successfully")
