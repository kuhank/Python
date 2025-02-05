import pandas as pd
import re
import json
import os

def checking_dataIntegrity(df):

    #insert row number in the dataframe

    df.insert(0, "rownumber", range(1,len(df)+1))

    patient_df=df[0].str.extract(pat_pattern)
    claim_df=df[12].str.extract(claimid_pattern)  

    patient_df.dropna(inplace=True)
    claim_df.dropna(inplace=True)

    patient_df["rownumber"] = patient_df.index + 1
    claim_df["rownumber"] = claim_df.index + 1

    print("Patient details count: ", patient_df.shape[0])
    print("claim details count: ", claim_df.shape[0])
    
    if patient_df.shape[0] == claim_df.shape[0]:
        print("Pattern check completed, successfully extracted all the data")
    else:
        claim_rowno_list = set(claim_df["rownumber"])
        patient_rowno_list = set(patient_df["rownumber"])
        missingInPatient = claim_rowno_list - patient_rowno_list
        missingInclaim = patient_rowno_list - claim_rowno_list

        print("missingInPatient : ",missingInPatient)
        print("missingInclaim : ",missingInclaim)

def data_processing(df):
 
    # Variable declaration

    previous_row_data=None
    second_prev_data=None
    extracted_data = []
    cptdetails_data=[]
    DOSRange_data_list = []
    previous_row_data_provider=None
    previous_row_data_facility=None


    for index,row in df.iterrows():  
        claimdata = str(row[12]) if pd.notna(row[12]) else ""
        dosdata = str(row[0]) if pd.notna(row[0]) else ""
        patientdata = str(row[0]) if pd.notna(row[0]) else ""
        DOSRangedata = str(row[9]) if pd.notna(row[9]) else ""
        claimPatternMatch = re.match(claimid_pattern,claimdata)
        patientPatternMatch = re.match(pat_pattern,patientdata)
        date_match = re.match(date_pattern,dosdata)
        dosrange_match = re.match(DOSRange_pattern,DOSRangedata)

        if dosrange_match:
            provider_name = row[4] if pd.notna(row[4]) else previous_row_data_provider
            location = row[0] if pd.notna(row[0]) else previous_row_data_facility
            DOSRange_data_list.append({"rownumber": index,
            "DOSRange": row[9],
            "RenderingProvider": provider_name,
            "location": location
            }
            )
        if date_match:
            cptdetails_data.append({"rownumber":index,
                                    "cpt":str(row[1]),
                                    "Mods":str(row[2]) if pd.notna(row[2]) else "",
                                    "dos":str(row[0]),
                                    "reportingcode":row[14]})
        if patientPatternMatch:
            FirstName, LastName, SSN, PatientID, otherdetails = patientPatternMatch.groups()
        else:
            FirstName, LastName, SSN, PatientID, otherdetails = None,None,None,None,None # (np.nan)*5
        if claimPatternMatch:
            insurance_name = previous_row_data if previous_row_data else second_prev_data
            extracted_data.append({"rownumber":index,
                                "insurancedetails":insurance_name,
                                "patientdetails":row[0],
                                "PatientDOB":row[4],
                                "PolicyNumber":row[6],
                                "ClaimAge":row[14],
                                "ispatientPatternMatch": bool(patientPatternMatch),
                                "claimdetails":row[12],
                                'FirstName':FirstName,
                                'LastName':LastName,
                                'SSN': SSN, 
                                'PatientID': PatientID,
                                'otherdetails': otherdetails
            }
                                )
        second_prev_data=previous_row_data
        previous_row_data=row[0] if pd.notna(row[0]) else None
        

        previous_row_data_provider=row[4]
        previous_row_data_facility=row[0]

    combined_data=[]
    for i , claimdata in enumerate(extracted_data):
        claim_rownumber = claimdata["rownumber"]

        next_claim_rownumber = extracted_data[i+1]["rownumber"] if i+1 < len(extracted_data) else float ('inf')
        relatedcptdetails = [cpt for cpt in cptdetails_data if claim_rownumber <= cpt["rownumber"] < next_claim_rownumber]
        relatedDOSRangeDetails = [dosrange for dosrange in DOSRange_data_list if claim_rownumber <= dosrange["rownumber"] < next_claim_rownumber]
        

        if not relatedcptdetails:
            claim_data_copy = claimdata.copy()
            claim_data_copy["cpt"] = None
            claim_data_copy["Mods"] = None
            claim_data_copy["dos"] = None
            claim_data_copy["reportingcode"] = None
            claim_data_copy["cptrownumber"] = None
            combined_data.append(claim_data_copy)
            print("No cpt for this claimid: ", claim_data_copy["claimdetails"])

        for cpt in relatedcptdetails:
            claim_data_copy = claimdata.copy()
            claim_data_copy["cpt"] = cpt.get("cpt", None)
            claim_data_copy["Mods"] = cpt.get("Mods", None)
            claim_data_copy["dos"] = cpt.get("dos", None)
            claim_data_copy["reportingcode"] = cpt.get("reportingcode", None)
            claim_data_copy["cptrownumber"] = cpt.get("rownumber", None)
            if relatedDOSRangeDetails:
                claim_data_copy["dosrangerownumber"]= relatedDOSRangeDetails[0]["rownumber"] 
                claim_data_copy["DOSRange"]= relatedDOSRangeDetails[0]["DOSRange"] 
                claim_data_copy["RenderingProvider"]= relatedDOSRangeDetails[0]["RenderingProvider"] 
                claim_data_copy["location"]= relatedDOSRangeDetails[0]["location"]
            combined_data.append(claim_data_copy)
    
    return combined_data

def read_jsonfile(config_filepath):
    with open(config_filepath,'r') as file:
        config = json.load(file)
    return config

def getfile(folder):
    filelist = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder,f))]
    return filelist

if __name__=="__main__":

    #pattern assignment

    pat_pattern = r'([\w\s-]+), ([\w\s]+) \[(\d{3}-\d{2}-\d{4}[\s]?|None[\s])/([\s]?[\d]+[\s]?)(.*)'
    claimid_pattern = r'([\s]?\d+[\s]?)-([\s]?[A-Z][\s]?)'
    date_pattern=r'^\d{2}/\d{2}/\d{2}$'
    DOSRange_pattern=r'^[\s]?\d{2}/\d{2}/\d{2}[\s]?-[\s]?\d{2}/\d{2}/\d{2}[\s]?$'
    config = read_jsonfile('ConfigFile.json')  
    folder = config["source"]["folder"] # specify input folder from the config.json file
    filelist = getfile(folder)
    for files in filelist:
        filepath = os.path.join(folder,files)
        print("Processing file: ", filepath)
        df = pd.read_excel(filepath, engine='xlrd', header=None)
        checking_dataIntegrity(df)
        combined_data = data_processing(df)
        combined_df = pd.DataFrame(combined_data)
        outfolder = config["output"]["folder"] # specify output folder from the config.json file    
        outputfile = os.path.join(outfolder, os.path.splitext(files)[0]+'_processed.xlsx')
        print("Finised processing, now storing in :", outputfile)
        combined_df.to_excel(outputfile,index=False)
