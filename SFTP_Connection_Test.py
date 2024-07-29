import paramiko
import logging
import stat
import argparse

import paramiko.ssh_exception

#paramiko.util.log_to_file("Paramiko.log", level=logging.DEBUG)
logging.basicConfig(filename='Paramiko_v2.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def test_sftp_connection(hostname, port, username, password, test_directory):
    try:
        transport = paramiko.Transport((hostname, port))
        logging.info(f"attemptiing to connect {hostname} and {port}")
        transport.get_security_options().ciphers = ['aes256-ctr','aes256-cbc','aes192-ctr',
                                                    'aes192-cbc','aes128-ctr','aes128-cbc','3des-cbc']
                                                    #,'blowfish-cbc']
        transport.get_security_options().compression = ['zlib']
        #transport.get_security_options().macs= ['hmac-sha2-256','hmac-sha2-512','hmac-sha1']
        #transport.get_security_options().compression = ['none']
        transport.connect(username=username, password=password)
        # transport.use_compression(False)
        sftp = paramiko.SFTPClient.from_transport(transport)

        file_list = sftp.listdir(test_directory)
        file_lists = sftp.listdir_attr(test_directory)
        for item in file_lists:
            item_type = 'Directory' if stat.S_ISDIR(item.st_mode) else 'File'
            logging.info(f"{item.filename} - {item_type}")
        print(f"Files in directory '{test_directory}': {file_list}")
        logging.info(f"Files in directory '{test_directory}': {file_list}")

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
    parser.add_argument('--directory', default='/', help='SFTP Server Directory')

    args = parser.parse_args()

    test_sftp_connection(args.hostname, args.port, args.username, args.password, args.directory)
