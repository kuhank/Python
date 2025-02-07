from pyspark.sql import SparkSession
import os
import json

import time



def readConfigFile(configfile):
    with open(configfile,'r') as file:
        config = json.load(file)
    return config
def col_mapping(config):
    return config["mapping_column"]["map"] 

if __name__ == "__main__":
    start_time = time.time()
    config=readConfigFile("sparkconfigFile.json")
    source_hostname=config["source"]["host"]
    source_port=config["source"]["port"]
    source_database=config["source"]["database"]
    source_username=config["source"]["username"]
    source_password=config["source"]["password"] 
    source_tablename=config["source"]["tablename"] 

    source_url = f"jdbc:sqlserver://{source_hostname}:{source_port};database={source_database};encrypt=true;trustServerCertificate=false;hostNameInCertificate=*.database.windows.net;loginTimeout=60;"

    target_hostname=config["target"]["host"]
    target_port=config["target"]["port"]
    target_database=config["target"]["database"]
    target_username=config["target"]["username"]
    target_password=config["target"]["password"] 
    target_tablename=config["target"]["tablename"] 


    target_url = f"jdbc:sqlserver://{target_hostname}:{target_port};database={target_database};encrypt=true;trustServerCertificate=false;hostNameInCertificate=*.database.windows.net;loginTimeout=60;"

    jarfilepath=config["driverconfig"]["jarFilePath"]
    jdbc_driver_jar=config["driverconfig"]["jarFileName"]

    os.environ["HADOOP_HOME"] = "C:/hadoop"
    '''
    Spark internally uses Hadoop APIs for file handling and distributed computation
    PySpark maps columns by name, not by order when writing to a database using JDBC.
    PySpark's .option() method expects string values for all parameters
    writing data to a database, PySpark does not require a specific column to determine partitioning
    '''

    driver="com.microsoft.sqlserver.jdbc.SQLServerDriver"


    spark = SparkSession.builder.appName("AzureSQLDataTransfer").config("spark.jars", jdbc_driver_jar).getOrCreate()

    try:
            
        df = (spark.read
        .format("jdbc")
        .option("driver", driver)
        .option("url", source_url)
        .option("dbtable", source_tablename)
        .option("user", source_username)
        .option("password", source_password)
        .option("fetchsize", "10000")
        .option("numPartitions", "8")
        .option("partitionColumn", "id")
        .option("lowerBound", "1")
        .option("upperBound", "10000")
        .load()
        )
        
        column_mapping = col_mapping(config=config)
        for sourceCol, TargetCol in column_mapping.items():
            df = df.withColumnRenamed(sourceCol, TargetCol)

        # df.show()
        print("total number of rows to be transferred: ", df.count())

        

        (df.write
        .format("jdbc")
        .option("driver", driver)  # Example: "com.microsoft.sqlserver.jdbc.SQLServerDriver"
        .option("url", target_url)  # Connection URL for the target database
        .option("dbtable", target_tablename)  # Target table name
        .option("user", target_username)  # Target database username
        .option("password", target_password)  # Target database password
        .option("batchsize","5000")
        .option("numPartitions","8")
        .mode("overwrite")  # Change to "append" if you don't want to overwrite
        .save()
        )
    except Exception as e:
        print(f"Exception Error: {str(e)}")
    finally:
        spark.stop()
        end_time = time.time()
    elapsed_time = end_time-start_time
    print(f"Execution time : {elapsed_time:.2f} seconds")

