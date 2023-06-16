import configparser, os, json, random, threading, socket, sys
from SNMPkeySharePDU import SNMPkeySharePDU
from MIB import SNMPKeyShareMIB
from keys import Keys
import numpy as np


# Global variables
IP = None
PORT = None
K = None
T = None
X = None
V = None
M = None
MIB = None
KEYS = None


class RequestHandler(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((IP, PORT))
        self.key_matrix = {}
        KEYS = Keys(M, K, T)

        #Generate Matrixes








    def get_request(self, dec_pdu, addr):
        print(KEYS.Z)
        pass




    def set_request(self, dec_pdu, addr):
        for Nw_oid, Nw_value in dec_pdu.instances_values:
            if Nw_oid == "1.3.3.6.0":
                try:
                    key, key_expiration = Keys.generate_key()
                    key_exp_date_formatted = key_expiration.year * 104 + key_expiration.month * 102 + key_expiration.day
                    key_exp_time_formatted = key_expiration.hour * 104 + key_expiration.minute * 102 + key_expiration.second
                    #result2 = MIB.add_key_entry(key_id=1, key_value=key, addr[0], key_exp_date_formatted, key_exp_time_formatted, Nw_value)
                except Exception as e:
                    print(e)
                    print("Error generating key")
                    response = "Invalid SNMP Set Request Syntax"

        response = ""



        try:

            pass
        except Exception as e:
            print(e)
            response = "Invalid SNMP Set Request Syntax"

    def run(self):
        try:
            while True:
                data, addr = self.socket.recvfrom(4096)
                if addr[1] == self.port: #TODO é necessário fazer a verificação do IP?
                    dec_pdu = SNMPkeySharePDU.decode(data.decode())

                    if dec_pdu.primitive_type == 1:
                        print("Get request received")
                        self.get_request(dec_pdu, addr)
                    elif dec_pdu.primitive_type == 2:
                        print("Set request received")
                        self.set_request(dec_pdu, addr)
                    else:
                        print("Invalid SNMP request received")
                else:
                    pass
                
        except Exception as e:
            print(e)
            sys.exit(1)





def read_configuration_file(config_file):
    global K, T, X, V, M, IP, PORT

    config = configparser.ConfigParser()
    config.read(config_file)
    IP = config['Agent']['ip']
    PORT = int(config['Agent']['snmpport'])
    K = int(config['Other']['K'])
    T = int(config['Other']['T'])
    X = int(config['Other']['X'])
    V = int(config['Other']['V'])

    # TODO Add à tabela MIB e ao config.ini
    first_char_ascii = 33        #configFirstCharOfKeysAlphabet
    num_alphabet_chars = 94      #configCardinalityOfKeysAlphabet

    #M = np.random.choice(list(map(chr, range(first_char_ascii, first_char_ascii+num_alphabet_chars))), size=2 * K)
    #M = np.random.randint(low=0, high=256, size=2 * K, dtype=np.uint8)
    #M = config['Other']['M']
    #M = config['Other']['M'].encode('ascii', errors='replace')
     
    M = "162561567256152675162756712522"
    M= "07994506586870582927"
    #numbers = np.random.randint(0, 9, size=2 * K)
    #M = ''.join(map(str, numbers))


    if(len(M) != 2*K):
        print("Error: M length must be 2K. Check config.ini file.")
        sys.exit(1)
    print(M)


def main():
    os.system('cls' if os.name == 'nt' else 'clear')                #clear terminal
    print("A Inicializar agente SNMP...")

    read_configuration_file("config.ini")
    MIB = SNMPKeyShareMIB(K, T, X, V, M)

    rH = RequestHandler()
    rH.start()


if __name__ == '__main__':
    main()
