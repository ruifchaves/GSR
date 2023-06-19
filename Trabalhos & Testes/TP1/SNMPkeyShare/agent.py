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
id_expiration = dict()

class RequestHandler(threading.Thread):
    def __init__(self, mib, keys):
        threading.Thread.__init__(self)

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((IP, PORT))
        self.port = PORT
        self.key_matrix = {}
        self.key = keys
        self.mib = mib







    # Funcao que divide (IID, valor) em (IID, valor) e (IID, error_code)
    def sort_errors_from_instance(self, ret):
        error = []
        errors_to_remove = []
        for tuple in ret:
            oid, value = tuple
            if value == -1 or value == -2 or value == -3:
                error.append((oid, str(abs(value))))
                errors_to_remove.append(tuple)

        for tuple in errors_to_remove:
            ret.remove(tuple)

        return ret, error

    # Funcao que da valores de oid lexicograficamente seguintes


    # Funcao que trata de um pedido do tipo get
    # get podes fazer de qualquer um
    def get_request(self, dec_pdu, addr):
        ret = []
        for tuple in dec_pdu.instances_values:
            Nl_oid, Nl_value = tuple
            Nl_value = int(Nl_value)

            print(Nl_oid, Nl_value)
            if Nl_oid.startswith("1.3.3."):
                # TODO:
                # lista de oids possiveis
                # iterar por cada um e adicionar get_value a ret
                #   caso oid = 2.X
                #       teste de visibilidade = 0 OU
                #       teste de visibilidade = 1 e addr != addr
                #           adicionar a ret (oid, -3) nao seja o mesmo addr
                #       caso contrario adicionar com get_value a ret
                #   else adicionar com get_value a ret
                key_id = Nl_oid.split(".")[-1]

                id_addr = self.mib.get_value(f"1.3.3.4.{key_id}")
                id_visibility = self.mib.get_value(f"1.3.3.6.{key_id}")
                print(type(id_visibility))
                print(id_addr, addr[0], id_visibility)

                if id_visibility == 0:
                    pass
                elif id_visibility == 1:
                    if id_addr != addr[0]:
                        ret += (Nl_oid, -3) #Error 3: Key only visible to 
                        pass
                    else:
                        ret += (self.mib.get_N_values(Nl_oid, Nl_value))
                else: ret += (self.mib.get_N_values(Nl_oid, Nl_value))
            else:
                # lista de oids possiveis
                # iterar por cada um e adicionar get_value a ret
                ret += (self.mib.get_N_values(Nl_oid, int(Nl_value)))
                print(ret)


            print(ret)
                #TODO Testar deverá ser lista com oids, values em que values podem ser vazios
            if ret:
                values_set, erros = [], []
                values_set, erros = self.sort_errors_from_instance(ret)

                print("Sending response message: ", len(ret))
                answer_pdu = SNMPkeySharePDU(0, 0, [], dec_pdu.request_id, 0, len(ret), ret, 0, [])
                print(answer_pdu)
                enc_answer_pdu = answer_pdu.encode()
                print(enc_answer_pdu)
                try:
                    self.socket.sendto(enc_answer_pdu, addr)
                except:
                    print("Error sending response Message")
                    sys.exit(1)




    def set_request(self, dec_pdu, addr):
        print(dec_pdu.instances_values)
        for tuple in dec_pdu.instances_values:
            Nw_oid, Nw_value = tuple
            if Nw_oid == "1.3.3.6.0":
                try:
                    key, key_expiration = self.key.generate_key()
                    self.key.update_matrix_Z()

                    key_exp_date_formatted = key_expiration.year * 104 + key_expiration.month * 102 + key_expiration.day
                    key_exp_time_formatted = key_expiration.hour * 104 + key_expiration.minute * 102 + key_expiration.second

                    ret = self.mib.add_key_entry(key, addr[0], key_exp_date_formatted, key_exp_time_formatted, int(Nw_value))
                    if ret:  
                        #keyvisibility_oid, value = ret
                        #answer_pdu = SNMPkeySharePDU(0, 0, [], dec_pdu.request_id, 0, 1, [(keyvisibility_oid, value)], 0, [])

                        values_set, erros = [], []
                        values_set, erros = self.sort_errors_from_instance(ret)

                        if len(values_set) == 0:
                            answer_pdu = SNMPkeySharePDU(0, 0, [], dec_pdu.request_id, 0, 1, [(0,0)], len(erros), erros)
                        elif len(erros) == 0:
                            answer_pdu = SNMPkeySharePDU(0, 0, [], dec_pdu.request_id, 0, len(values_set), values_set, 1, [(0,0)])
                        else:
                            answer_pdu = SNMPkeySharePDU(0, 0, [], dec_pdu.request_id, 0, len(values_set), values_set, len(erros), erros)
                        print(answer_pdu)
                        enc_answer_pdu = answer_pdu.encode()

                        try:
                            self.socket.sendto(enc_answer_pdu, addr)
                        except:
                            print("Error sending response Message")
                            sys.exit(1)

                    else:
                        print("Error adding key to MIB")
                except Exception as e:
                    print(e, "Error generating key")
                    response = "Invalid SNMP Set Request Syntax"
            # TODO:
            # elif  start with 1.3.3.6.X
            #   testar se 1.3.3.3.X == addr em que se recebeu o pedido
            #   caso seja alterar
            # fazer um set_value admin=False e adicionar a ret



            #Caso seja o mesmo ip a fazer 
            #elif Nw_oid == "1.3.3.{other}.0" for other in range(1, 6):
            #    print("Should be 1.3.3.6.0 instance")
            #    sys.exit(1) #TODO remover isto e enviar feedback pelos erros para o cliente?
        


    def run(self):
        try:
            while True:
                print("Waiting for request")
                data, addr = self.socket.recvfrom(4096)
                if addr[1] == self.port: #TODO é necessário fazer a verificação do IP?
                    dec_pdu = SNMPkeySharePDU.decode(data.decode())

                    if dec_pdu.primitive_type == 1:
                        print("Get request received")
                        print(dec_pdu)
                        self.get_request(dec_pdu, addr)
                    elif dec_pdu.primitive_type == 2:
                        print("Set request received")
                        print(dec_pdu)
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





#TODO: thread que faz update da matriz



#Thread que a cada 1 segundo verifica se existem chaves expiradas
#Se existirem, remove-as da tabela MIB
#Se não existirem, não faz nada
#TODO       
class KeyExpiration(threading.Thread):
    def __init__(self, mib, keys):
        threading.Thread.__init__(self)
        self.mib = mib

    def run(self):
        #Para um oid "1.3.3.[1-7].[1-X]" verificar se a data de expiração é menor que a data atual
        while True:
            pass



def main():
    global MIB, KEYS
    os.system('cls' if os.name == 'nt' else 'clear')                #clear terminal
    print("A Inicializar agente SNMP...")

    read_configuration_file("config.ini")
    MIB = SNMPKeyShareMIB(K, T, X, V, M)
    KEYS = Keys(M, K, T, V)

    rH = RequestHandler(MIB, KEYS)
    rH.start()


if __name__ == '__main__':
    main()
