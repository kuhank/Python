from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType
import pandas as pd

def createSparkSession(app_name, tempdir):
    spark=SparkSession.builder \
        .appName(app_name) \
            .config("spark.driver.extraClassPath","./sqljdbc42.jar") \
            .config("spark.local.dir", tempdir) \
            .getOrCreate()
    return spark

def readServerParameter(dataFile, sheetname):
    param_df = pd.read_excel(dataFile, sheet_name=sheetname)
    servername = param_df[param_df['parameter']=='server'].iloc[0]['value']
    username=param_df[param_df['parameter']=='user'].iloc[0]['value']
    password=param_df[param_df['parameter']=='password'].iloc[0]['value']
    databasename=param_df[param_df['parameter']=='databasename'].iloc[0]['value']
    tablename=param_df[param_df['parameter']=='tablename'].iloc[0]['value']
    port=param_df[param_df['parameter']=='port'].iloc[0]['value']
    return servername, username, password, databasename, tablename, port

def CreateSchema(SchemaFile, Sheetname):
    data_Df = pd.read_excel(SchemaFile, sheet_name=Sheetname)
    schema_Data = []
    for _,row in data_Df.iterrows():
        column_name = row['columnname']
        data_type = row['datatype']
        nullable = row['nullable']
        if data_type == 'StringType':
            field_type=StringType()
        elif data_type == 'IntegerType':
            field_type=IntegerType()
        else:
            raise ValueError(f"unknow datatype: {data_type}")
        schema_Data.append(StructField(column_name,field_type,nullable))
    schema = StructType(schema_Data)   
    return schema

def readCSVData(spark, schema, delimiter, filename, isHeader):
    df = spark.read.option("delimiter", delimiter).schema(schema).csv(filename, header=isHeader)
    return df


def renamecolumn(data_Df, renamefile, renamesheet):
    selectedcolumns=['columnname','tablecolumn']
    rename_Df = pd.read_excel(renamefile, sheet_name=renamesheet, usecols=selectedcolumns)
    excl_Df=rename_Df
    # use notapplicable to remove from inserting to table
    rename_Df = rename_Df[rename_Df['tablecolumn'].fillna('keep') != 'notapplicable']
    rename_Df = rename_Df.set_index('columnname')['tablecolumn'].to_dict()
    excludedcolumn = excl_Df[excl_Df['tablecolumn']=='notapplicable']['columnname'].tolist()
    data_Df = data_Df.drop(*excludedcolumn)
    for old_name, new_name in rename_Df.items():
        data_Df=data_Df.withColumnRenamed(old_name,new_name)
    return data_Df

def writetoSQLServer(df, servername, port,databasename, username, password, tablename, Operation, repetition):
    sql_server_prop = {
    "driver": "com.microsoft.sqlserver.jdbc.SQLServerDriver",
        "url": f"jdbc:sqlserver://{servername}:{port};databaseName={databasename};",
        "user": username,
        "password": password
    }
    df=df.repartition(repetition)
    df.write.jdbc(url=sql_server_prop["url"],
                table=tablename,
                mode=Operation, 
                properties=sql_server_prop
                )


if __name__ =="__main__":
    spark = createSparkSession("csv to sql server", "./temp")
    servername, username, password, databasename, tablename, port = readServerParameter("info.xlsx", "server")
    schema = CreateSchema("info.xlsx", "file1")
    df = readCSVData(spark, schema,",","test.txt", True)
    df = renamecolumn(df, "info.xlsx", "file1")
    Operation = "append"
    repetition=10
    writetoSQLServer(df,servername, port, databasename,username, password, tablename,Operation, repetition)
    spark.stop()
