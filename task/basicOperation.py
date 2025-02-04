import os
import json

def load_configfile(filename):
    with open(filename,"r") as config_file:
        config = json.load(config_file)
        return config

def deleteFileInFolder(config):
    folderlist = config["deleteOperation"]["folderpath"]
    for folderpath in folderlist:
        for file in os.listdir(folderpath):
            filepath = os.path.join(folderpath,file)
            if os.path.isfile(filepath):
                os.remove(filepath)
                print(f"deleted {filepath}")

if __name__ == "__main__":
    config = load_configfile("basicOperation_config.json")
    deleteFileInFolder(config=config)