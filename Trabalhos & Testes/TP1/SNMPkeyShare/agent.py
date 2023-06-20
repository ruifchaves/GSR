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
        self.keys = keys
        self.mib = mib










    def send_response(self, P, L, R)
        try:
            print(pdu)
            pdu_encoded = pdu.encode()
            self.socket.sendto(pdu_encoded, (self.agentIP, self.port))
        except:
            print("Unable to send Response Message")
        pass

    #! Funcoes auxiliares que permitem tratar pedidos devidamente
    # Funcao que divide (IID, valor) em (IID, valor) e (IID, error_code)
    def sort_errors_from_instance(self, ret):
        error = []
        errors_to_remove = []
        for tuple in ret:
            oid, value = tuple
            if value in [-1, -2, -3, -4, -5, -6, -7]:
                error.append((oid, str(abs(value))))
                errors_to_remove.append(tuple)

        for tuple in errors_to_remove:
            ret.remove(tuple)

        return ret, error


    # Funcao auxiliar que retorna lista de oids lexicograficamente seguintes (apenas do mesmo grupo e keyID)
    def get_next_oids(self, oid, count):
        result = []
        current_string = oid

        # TODO same keyID instance or same intance but next keyID?
        # TODO pelos vistos comeca na instancia a seguir
        for _ in range(count):
            result.append(current_string)
            parts = current_string.split('.')
            parts[-2] = str(int(parts[-2]) + 1)
            current_string = '.'.join(parts)

        return result



    #! Funcao que trata de um pedido do tipo get
    # Client can get values from system and data groups (except keyValue if keyVisibility 0 or not same client and keyVisibility 1)
    # Admin can get values from all groups (except if non-accessible)
    def get_request(self, dec_pdu, addr):
        ret = []
        for tuple in dec_pdu.instances_values:
            L_oid, L_value = tuple
            L_value = int(L_value)

            oids = self.get_next_oids(L_oid, L_value)
            for i in oids:
                if L_oid.startswith("1.3.3.2."):
                    key_id = L_oid.split(".")[-1]

                    id_addr = self.mib.get_value(f"1.3.3.4.{key_id}")[1]
                    id_visibility = self.mib.get_value(f"1.3.3.6.{key_id}")[1]
                    print(id_addr, addr[0], id_visibility)

                    if id_visibility == 0:
                        ret.append((1, -3)) #Error 3: Key is not visible
                    elif id_visibility == 1 and id_addr != addr[0]:
                        ret.append((1, -4)) #Error 4: Key is not visible to this address
                    else:
                        ret.append(self.mib.get_value(i))
                else:
                    ret.append(self.mib.get_value(i))
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





    def add_key_entry(self, keyValue, keyRequester, keyExpirationDate, keyExpirationTime, keyVisibility):
        result = []

        keyID = self.mib.get_unused_number()
        values = [keyID, keyValue, keyRequester, keyExpirationDate, keyExpirationTime, keyVisibility]
        oids = [(f"1.3.3.{X}.{keyID}") for X in range(1, 7)]
        #try:
        for oid, value in zip(oids, values):
            if int(self.mib.get_value("1.3.1.0")[1]) < self.X:                       #type: ignore
                set_or_nah = self.mib.set_value(oid, value, admin=True)
                result.append(set_or_nah)
            else:
                print("Max number of keys reached")
        #except Exception as e:
        #    print(e, "Error adding key entry")
        #    return result

        if result: 
            new_value = int(self.mib.get_value("1.3.1.0", True)[1]) + 1
            self.mib.set_value("1.3.1.0", new_value, admin=True)
            self.mib.used_ids.append(keyID)
        return result






    #! Funcao que trata de um pedido do tipo set
    # Client can only set values to it keyVisibility instance
    # Can try for other groups but will get error (including other instances of keys Table) #TODO Testar isto!!
    # Admin can set values to all groups (except if non-accessible)
    def set_request(self, dec_pdu, addr):
        for tuple in dec_pdu.instances_values:
            W_oid, W_value = tuple
            if W_oid == "1.3.3.6.0":                                       #! Request to generate new key
                #try:
                    key, key_expiration = self.keys.generate_key()
                    self.keys.update_matrix_Z()

                    key_exp_date_formatted = key_expiration.year * 104 + key_expiration.month * 102 + key_expiration.day
                    key_exp_time_formatted = key_expiration.hour * 104 + key_expiration.minute * 102 + key_expiration.second

                    ret = self.add_key_entry(key, addr[0], key_exp_date_formatted, key_exp_time_formatted, int(W_value))
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
                #except Exception as e:
                #    print(e, "Error generating key")
                #    response = "Invalid SNMP Set Request Syntax"
            # TODO:
            elif W_oid.startswith("1.3.3.6."):                             #! Request to change current key visibility
                keyID = int(W_oid.split(".")[-1])
                pass
            #   testar se 1.3.3.3.X == addr em que se recebeu o pedido
            #   caso seja alterar
            # fazer um set_value admin=False e adicionar a ret



            #Caso seja o mesmo ip a fazer 
            #elif W_oid == "1.3.3.{other}.0" for other in range(1, 6):
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
