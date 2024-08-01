import paramiko
import logging
import stat
import argparse
import paramiko.ssh_exception

# paramiko.util.log_to_file("Paramiko.log", level=logging.DEBUG)
# logging.basicConfig(filename='Paramiko_v2.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
def test_sftp_connection(hostname, port, username, password, test_directory, operation, source, destination):
    try:
        if source == None or destination ==None:
            if operation != 'TEST':
                print("Parameter Error, Check command correctly")
                return False
            elif operation == 'UP' or operation == 'DOWN':
                print("Parameter Error, Check command correctly")
                return False
        else:
            print("Commands are successfull") 
        transport = paramiko.Transport((hostname, port))
        # logging.info(f"attemptiing to connect {hostname} and {port}")
        transport.get_security_options().ciphers = ['aes256-ctr','aes256-cbc','aes192-ctr',
                                                    'aes192-cbc','aes128-ctr','aes128-cbc','3des-cbc']
                                                    #,'blowfish-cbc']
        transport.get_security_options().compression = ['zlib']
        #transport.get_security_options().macs= ['hmac-sha2-256','hmac-sha2-512','hmac-sha1']
        #transport.get_security_options().compression = ['none']
        transport.connect(username=username, password=password)
        # transport.use_compression(False)
        sftp = paramiko.SFTPClient.from_transport(transport)
        if operation == 'UP':
            sftp.put(source,destination)
            print("Upload completed")
        elif operation == 'DOWN':
            sftp.get(source,destination)
            print("Download completed")
        elif operation == 'TEST':
            file_list = sftp.listdir(test_directory)
            file_lists = sftp.listdir_attr(test_directory)
            for item in file_lists:
                item_type = 'Directory' if stat.S_ISDIR(item.st_mode) else 'File'
                logging.info(f"{item.filename} - {item_type}")
            print(f"Files in directory '{test_directory}': {file_list}")
            #logging.info(f"Files in directory '{test_directory}': {file_list}")
        else:
            print("Provide Operation Details")
        
        sftp.close()
        transport.close()
        print("SFTP connection is working.")
        return True
    except paramiko.ssh_exception.SSHException as ssh_exc:
        print(f"SSH Error occured: {ssh_exc}")
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

if __name__=="__main__":
    parser = argparse.ArgumentParser(description="List SFTP Directory Content")
    parser.add_argument('--hostname', required=True, help='SFTP Server Hostname')
    parser.add_argument('--password', required=True, help='SFTP Server password')
    parser.add_argument('--port', type = int, required=True, help='SFTP Server Port number')
    parser.add_argument('--username', required=True, help='SFTP Server username')
    parser.add_argument('--testdirectory', default='/', help='SFTP Server Directory')
    parser.add_argument('--operation',default='TEST', help='SFTP Server upload or download')
    parser.add_argument('--source',default=None, help='source file')
    parser.add_argument('--destination',default=None, help='destination file')

    args = parser.parse_args()

    test_sftp_connection(args.hostname, args.port, args.username, args.password, args.testdirectory, args.operation
                         ,args.source, args.destination)
    
'''

For Compile:

python -m py_compile "SFTP_PROD.py"

For Running

Case 1:
Testing connection:
py "/__pycache__/SFTP_PROD.cpython-312.pyc" --hostname "host" --port port --username user --password "pwd" --testdirectory / --operation TEST
Files in directory '/': ['foldername']
SFTP connection is working.

Case 2:
Uploading:
py "/__pycache__/SFTP_PROD.cpython-312.pyc" --hostname "host" --port port --username user --password "pwd" --operation UP --source "C:/Folder/test.txt" --destination "/test.txt"

Case 2:
Downloading:
py "/__pycache__/SFTP_PROD.cpython-312.pyc" --hostname "host" --port port --username user --password "pwd" --operation DOWN --source "/test.txt" --destination "C:/Folder/test.txt"

'''