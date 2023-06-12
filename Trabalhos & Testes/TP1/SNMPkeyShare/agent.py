import configparser, os, json, random, threading, socket, sys
from SNMPkeySharePDU import SNMPkeySharePDU

MIB = dict()
mibVals = []

class RequestHandler(threading.Thread):
    def __init__(self, config_file, cstring):
        threading.Thread.__init__(self)
        # Sets ip, port, K, M, T, V, X, and Z
        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        self.read_configuration_file()

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.ip, self.port))
        self.cstring = cstring
        self.key_matrix = []


    def read_configuration_file(self):
        # Read and retrieve the necessary parameters from the configuration file
        self.port = int(self.config['Agent']['snmpport'])
        self.ip = self.config['Agent']['ip']
        self.K = int(self.config['Agent']['K'])
        self.M = int(self.config['Agent']['M'])
        self.T = int(self.config['Agent']['T'])
        self.V = int(self.config['Agent']['V'])
        self.X = int(self.config['Agent']['X'])
        # other configurations

    def generate_key_matrix(self):
        # Implement the algorithm to generate the key matrix
        # using the values of K and M
        # update the matrix Z
        self.key_matrix = [[random.randint(0, self.V) for _ in range(self.M)] for _ in range(self.K)]


    def update_key_matrix(self):
        # Implement the algorithm to update the key matrix
        # at regular intervals of T milliseconds
        # update the matrix Z
        self.generate_key_matrix()


    def handle_key_request(self, application_id):
        # Generate a new key and return its value and identifier
        # Add the key to the key table along with the application ID
        key_id = random.randint(1, self.X)
        key = random.choice(self.key_matrix)
        self.add_key_to_table(key_id, key, application_id)
        return key_id, key

    def verify_key(self, key_id):
        # Verify the key using the key table and return the result
        key_table = self.get_key_table()
        return key_id in key_table

    def add_key_to_table(self, key_id, key, application_id):
        # Implement the logic to add the key to the key table
        pass

    def get_key_table(self):
        # Implement the logic to retrieve the key table
        pass

    # Other methods for managing the key table, handling requests, etc.




    def process_request(self, data, addr):
        dec_pdu = SNMPkeySharePDU.decode(data)

        if(dec_pdu.primitive_type == 1):
            print(" type received")
            ret = self.get_request()
        else :
            ret = "Invalid SNMP Request"    
        return ret
    
    def response(self, data, addr):
        answer_pdu = SNMPkeySharePDU()
        answer_pdu = answer_pdu.encode('ascii')
        response = self.process_request(answer_pdu, addr)
        self.socket.sendto(response.encode(), addr)


    def get_request(self, dec_pdu, addr):
        pass

    def set_request(self, dec_pdu, addr):
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
                    dec_pdu = SNMPkeySharePDU.decode(data)
                    print(data)
                    print(dec_pdu)
                    if dec_pdu.primitive_type == 1:
                        print("Get request received")
                        self.get_request(data, addr)
                    elif dec_pdu.primitive_type == 2:
                        print("Set request received")
                        self.set_request(data, addr)
                    else:
                        print("Invalid SNMP request received")
                else:
                    pass
                    
                
        except Exception as e:
            print(e)
            sys.exit(1)

def main():
    global MIB
    print("A Inicializar agente SNMP...")
    os.system('cls' if os.name == 'nt' else 'clear')                #clear terminal
    MIB = json.load(open('SNMPkeyShareMIB.json'))
    cstring = "public"
    rH = RequestHandler("config.ini", cstring)
    rH.start()


if __name__ == '__main__':
    main()