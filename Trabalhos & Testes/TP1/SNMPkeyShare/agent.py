import configparser, os, json, random, threading, socket, sys, time
from SNMPkeySharePDU import SNMPkeySharePDU
from MIB import SNMPKeyShareMIB
from keys import Keys
import numpy as np



class RequestHandler(threading.Thread):
    def __init__(self, IP, PORT, K, T, X, V, M, start_time):
        threading.Thread.__init__(self)

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((IP, PORT))
        self.port = PORT
        self.mib = SNMPKeyShareMIB(K, T, X, V, M, start_time)
        self.keys = Keys(M, K, T, V)
        self.K = K
        self.T = T
        self.X = X
        self.V = V
        self.M = M

        # Start the cleanup thread
        cleanup_thread = threading.Thread(target=self.update_matrix_thread, args=(T,))
        cleanup_thread.start()



    #! Funcao que faz update da matrix Z a cada T segundos e guarda o timestamp na MIB
    def update_matrix_thread(self, T):
        while True:
            updated_time = self.keys.update_matrix_Z()

            systemRestartDate = updated_time.year * 104 + updated_time.month * 102 + updated_time.day
            systemRestartTime = updated_time.hour * 104 + updated_time.minute * 102 + updated_time.second

            self.mib.set_value("1.1.1.0", systemRestartDate, admin=True)
            self.mib.set_value("1.1.1.0", systemRestartTime, admin=True)
            print("Updated matrix Z")
            time.sleep(T)


    #! SEND RESPONSE AND AUXILIARY FUNCTIONS
    # Funcao que divide (IID, valor) em (IID, valor) e (IID, error_code)
    def sort_errors_from_instance(self, ret):
        error = []
        errors_to_remove = []
        for tuple in ret:
            oid, value = tuple
            if isinstance(value, int) and value < 0:
                error.append((oid, str(abs(value))))
                errors_to_remove.append(tuple)

        for tuple in errors_to_remove:
            ret.remove(tuple)

        return ret, error

    # Funcao que envia resposta ao pedido
    def send_response(self, dec_pdu, addr, ret):
        try:
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
                print("Sending response message")
                self.socket.sendto(enc_answer_pdu, addr)
            except Exception as e:
                print("Unable to send Response Message: ", e)
                sys.exit(1)
        except:
            print("Unable to create Response Message")
            sys.exit(1)





    #! GET REQUEST AND AUXILIARY FUNCTIONS
    # Funcao auxiliar que retorna lista de oids lexicograficamente seguintes (apenas do mesmo grupo - system, config or data, tendo em conta os ids usados na tabela de chaves)
    def get_next_oids(self, oid, count):
        possible_oids = ["1.1.1.0", "1.1.2.0", "1.1.3.0", "1.1.4.0", "1.1.5.0", "1.1.6.0", "1.1.7.0", "1.2.1.0", "1.2.2.0", "1.2.3.0"]         #hardcoded but best pratice to maintain SNMP resemblence in this implementation (by not getting errors for non existing OIDs, as ideally the MIB would be iterated oid by oid)
        result = []
        current_string = oid
        keys = oid.split(".")
        used_ids_store = self.mib.used_ids
        used_ids_store = [3,4]

        #If you send an SNMP GETNEXT request with an OID that does not exist in the MIB, the SNMP agent will not gather the following OID values lexically.
        #The SNMP agent will respond with an SNMP error, specifically an "End of MIB View" error (SNMPv2c) or "noSuchObject" error (SNMPv1). This indicates that the requested OID does not exist or that there are no further OIDs available in the MIB that are lexicographically greater than the given OID.
        #In such a case, the SNMP agent will not gather or return any OID values beyond the non-existent OID. The SNMP manager will receive the error response and handle it accordingly.
        oid_value = self.mib.get_value(oid, admin=True)
        if oid_value[1] == -2:
            print(-2)
            return -2                                                            #Error 2: OID does not exist
                
        if len(keys) == 4 and oid != "1.3.1.0":
            result.append(current_string)
            for _ in range(count):
                parts = current_string.split('.')
                parts[-2] = str(int(parts[-2]) + 1)
                current_string = '.'.join(parts)
                result.append(current_string)
                if len(result) == count +1:                         # Check if desired count is reached
                    break
            result = [item for item in result if item in possible_oids]
        elif oid == "1.3.1.0" or len(keys) == 5:
            if oid == "1.3.1.0":
                result.append(current_string)                       # Include the given OID in the result list
                current_string = "1.3.3.1.0"
            cur_len_size = count - len(result)
            if int(current_string.split('.')[-1]) in used_ids_store:
                id_index = used_ids_store.index(int(current_string.split('.')[-1]))
            else:
                id_index = 0
            for _ in range(cur_len_size):
                for usedid in used_ids_store:
                    if len(result) == cur_len_size:
                        break
                    parts = current_string.split('.')
                    parts[-1] = str(used_ids_store[id_index])
                    result.append('.'.join(parts))
                    id_index = (id_index + 1) % len(used_ids_store)  # Increment index and wrap around if needed
                    if len(result) == cur_len_size:
                        break
                parts = current_string.split('.')
                parts[-2] = str(int(parts[-2]) + 1)
                current_string = '.'.join(parts)
                
                if len(result) == cur_len_size:
                    break
            result = [item for item in result if not item.endswith('.7.1') and int(item.split('.')[-2]) < 7]

        if result == []:
            print(-10)
            return -10                                                             #Error 10: No more OIDs past the given one (endOfMIBView)
        print("list oids: ",result)
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
            print(oids)
            if oids != -2 and oids != -10:
                for oid in oids:
                    if oid.startswith("1.3.3.2."):   # type: ignore
                        key_id = oid.split(".")[-1]

                        id_addr = self.mib.get_value(f"1.3.3.4.{key_id}")[1]
                        id_visibility = self.mib.get_value(f"1.3.3.6.{key_id}")[1]
                        print(id_addr, addr[0], id_visibility)

                        if id_visibility == 0:
                            ret.append((1, -8))                                                 #Error 8: Key is not visible
                        elif id_visibility == 1 and id_addr != addr[0]:
                            ret.append((1, -9))                                                 #Error 9: Key is not visible to this address
                        else:
                            ret.append(self.mib.get_value(oid))
                    else:
                        ret.append(self.mib.get_value(oid))
            elif oids == -2:
                ret.append((L_oid, -2))
            elif oids == -10:
                ret.append((L_oid, -10))



        #TODO Testar deverá ser lista com oids, values em que values podem ser vazios
        print(ret)
        if ret:
            self.send_response(dec_pdu, addr, ret)








    def add_key_entry(self, keyValue, keyRequester, keyExpirationDate, keyExpirationTime, keyVisibility):
        result = []
        keyID = self.mib.get_unused_number()
        values = [keyID, keyValue, keyRequester, keyExpirationDate, keyExpirationTime, keyVisibility]
        oids = [(f"1.3.3.{inst}.{keyID}") for inst in range(1, 7)]

        curr_num_keys = int(self.mib.get_value("1.3.1.0", admin=True)[1])   # type: ignore
        if curr_num_keys < self.X:
            for oid, value in zip(oids, values): 
                set_or_nah = self.mib.set_value(oid, value, admin=True)
                result.append(set_or_nah)
        else:
            print("Max number of keys reached")

        if result: #TODO verificar se tem erros no result?
            new_value = int(curr_num_keys) + 1
            self.mib.set_value("1.3.1.0", new_value, admin=True)
            self.mib.used_ids.append(keyID)
        return result






    #! Funcao que trata de um pedido do tipo set
    # Client can only set values to it keyVisibility instance
    # Can try for other groups but will get error (including other instances of keys Table)
    # Admin can set values to all groups (except if non-accessible)
    def set_request(self, dec_pdu, addr):
        ret = []
        for tuple in dec_pdu.instances_values:
            W_oid, W_value = tuple
            if W_oid == "1.3.3.6.0":                                       #! Request to generate new key
                    key, key_expiration = self.keys.generate_key()
                    self.keys.update_matrix_Z()

                    key_exp_date_formatted = key_expiration.year * 104 + key_expiration.month * 102 + key_expiration.day
                    key_exp_time_formatted = key_expiration.hour * 104 + key_expiration.minute * 102 + key_expiration.second

                    ret = self.add_key_entry(key, addr[0], key_exp_date_formatted, key_exp_time_formatted, int(W_value))
            
            elif W_oid.startswith("1.3.3.6."):                             #! Request to change current key visibility
                keyID = int(W_oid.split(".")[-1])
                instance_addr = self.mib.get_value(f"1.3.3.3.{keyID}")[1]
                if instance_addr == addr[0]:
                    ret.append(self.mib.set_value(W_oid, int(W_value), admin=False))

            else:                                                           #! Other requests 
                ret.append(self.mib.set_value(W_oid, W_value, admin=False)) #TODO testar os tipos do W_value
            
        if ret:
            self.send_response(dec_pdu, addr, ret)
        


    def run(self):
        try:
            print("Waiting for request")
            data, addr = self.socket.recvfrom(4096)
            if addr[1] == self.port:  # TODO: Is it necessary to check the IP as well?

                try:
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

                except Exception as e:
                    print("Exception occurred while processing request:", e)
                    # Handle the exception here (e.g., log the error, send an error response, etc.)

            else:
                pass

        except Exception as e:
            print("RequestHandler received KeyboardInterrupt by user. Stopping...")
            print(e)
            self.debug()
            sys.exit(1)


    # Funcao de debug para guardar a MIB num ficheiro json
    def debug(self):
        json.dump(mib.mib, open("debug/MIB_debug.json", "w")) #type: ignore
        print("MIB saved to debug/MIB_debug.json")






#! Funções que dão inicio ao Agent
def read_configuration_file(config_file):
    config = configparser.ConfigParser()
    config.read(config_file)
    IP = config['Agent']['ip']
    PORT = int(config['Agent']['snmpport'])
    K = int(config['Other']['K'])
    T = int(config['Other']['T'])
    X = int(config['Other']['X'])
    V = int(config['Other']['V'])

    # TODO Add à tabela MIB e ao config.ini
    #first_char_ascii = 33        #configFirstCharOfKeysAlphabet
    #num_alphabet_chars = 94      #configCardinalityOfKeysAlphabet
    #M = np.random.choice(list(map(chr, range(first_char_ascii, first_char_ascii+num_alphabet_chars))), size=2 * K)
    #M = np.random.randint(low=0, high=256, size=2 * K, dtype=np.uint8)
    #M = config['Other']['M']
    #M = config['Other']['M'].encode('ascii', errors='replace')
    #M = "162561567256152675162756712522"
    M = "07994506586870582927"
    #numbers = np.random.randint(0, 9, size=2 * K)
    #M = ''.join(map(str, numbers))

    if(len(M) != 2*K):
        print("Error: M length must be 2K. Check config.ini file.")
        sys.exit(1)

    return IP, PORT, K, T, X, V, M


def main():
    global MIB, KEYS
    os.system('cls' if os.name == 'nt' else 'clear')
    print("A Inicializar agente SNMP...")

    IP, PORT, K, T, X, V, M = read_configuration_file("config.ini")
    start = time.time()
    rH = RequestHandler(IP, PORT, K, T, X, V, M, start)
    rH.start()


if __name__ == '__main__':
    main()
