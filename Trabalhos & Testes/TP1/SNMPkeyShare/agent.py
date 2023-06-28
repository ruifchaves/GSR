"""
Autor: Rui Chaves (ruichaves99@gmail.com)
Descrição: Ficheiro que representa o agente no sistema e que, como tal, recebe pedidos das diversas aplicações/gestores e os trata devidamente, fornecendo ou não a resposta devida.
"""

import configparser, os, json, threading, socket, sys, time, datetime
from SNMPkeySharePDU import SNMPkeySharePDU
from MIB import SNMPKeyShareMIB
from keys import Keys
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hmac
from cryptography.hazmat.primitives import hashes


class RequestHandler(threading.Thread):
    def __init__(self, IP, PORT, K, T, X, V, M, KEY, start_time):
        threading.Thread.__init__(self)

        # Iniciar o socket UDP (removendo o timeout)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((IP, PORT))
        self.socket.settimeout(None)

        # Iniciar a MIB, Keys e outras variaveis
        self.port = PORT
        self.mib = SNMPKeyShareMIB()
        self.keys = Keys(M, K, V)
        self.K = K
        self.T = T
        self.X = X
        self.V = V  
        self.M = M
        self.KEY = KEY.encode()
        self.CYPHER = Fernet(self.KEY) #type: Fernet
        self.start_time = start_time
        self.set_mib_initial_values()

        # Objetos auxiliares
        self.used_ids = []
        self.addr_pAndTime = {}
        self.stop_signal_received = False

        # Iniciar a Thread que a atualiza a Matriz a cada T/1000 segundos
        self.matrix_update_thread = threading.Thread(target=self.update_matrix_thread, args=(T,))
        self.matrix_update_thread.start()

        # Iniciar a Thread que remove chaves expiradas da MIB a cada V segundos
        self.cleanup_thread = threading.Thread(target=self.clean_expired_thread, args=(5,))
        self.cleanup_thread.start()

        # Iniciar a Thread que atualiza o timestamp S da MIB a cada 1 segundo
        self.increase_timestamp_thread = threading.Thread(target=self.increment_timestamp_thread, args=(1,))
        self.increase_timestamp_thread.start()

        #NOTE: ensure the atomicity of the two function calls: generate_key followed by update_matrix_Z
        self.gen_and_updateZ_atomicity_lock = threading.Lock()


    #! Funcao que atualiza os valores iniciais da MIB com os valores do ficheiro de configuracao
    def set_mib_initial_values(self):
        print("Setting initial values...")
        self.mib.set_value("1.1.1.0", 1,      True)
        self.mib.set_value("1.1.2.0", 2,      True)
        self.mib.set_value("1.1.3.0", self.K, True)
        self.mib.set_value("1.1.4.0", self.T, True)
        self.mib.set_value("1.1.5.0", self.X, True)
        self.mib.set_value("1.1.6.0", self.V, True)
        self.mib.set_value("1.1.7.0", 0,      True)
        self.mib.set_value("1.2.1.0", self.M, True)
        self.mib.set_value("1.2.2.0", 33,     True)
        self.mib.set_value("1.2.3.0", 94,     True)
        self.mib.set_value("1.3.1.0", 0,      True)
        self.update_matrix_afterT()
        print("Initial values set!")





    #! SEND RESPONSE AND AUXILIARY FUNCTIONS
    #! Funcao que divide (IID, valor) em (IID, valor) e (IID, error_code)
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

    #! Funcao que envia uma resposta a um pedido
    def send_response(self, dec_pdu, addr, ret):
        print("Creating Response Message")
        try:
            auth_code = [self.calculate_authentication_code(dec_pdu.request_id)]
            values_set, erros = self.sort_errors_from_instance(ret)
            if len(values_set) == 0:
                answer_pdu = SNMPkeySharePDU(1, 1, auth_code, dec_pdu.request_id, 0, 1, [(0,0)], len(erros), erros)
            elif len(erros) == 0:
                answer_pdu = SNMPkeySharePDU(1, 1, auth_code, dec_pdu.request_id, 0, len(values_set), values_set, 1, [(0,0)])
            else:
                answer_pdu = SNMPkeySharePDU(1, 1, auth_code, dec_pdu.request_id, 0, len(values_set), values_set, len(erros), erros)
                
            enc_answer_pdu = answer_pdu.encode()
            if len(enc_answer_pdu) > 1500:
                answer_pdu = SNMPkeySharePDU(1, 1, auth_code, dec_pdu.request_id, 0, 1, [(0,0)], 1, [(0,1)])
                enc_answer_pdu = answer_pdu.encode()
                
            print(answer_pdu)
            encrypted_response = self.CYPHER.encrypt(enc_answer_pdu)
            try:
                self.socket.sendto(encrypted_response, addr)
                print("Response message sent")
            except Exception as e:
                print("Unable to send Response Message: ", e)
                sys.exit(1)
        except:
            print("Unable to create Response Message")
            sys.exit(1)





    #! GET REQUEST AND AUXILIARY FUNCTIONS
    #! Funcao auxiliar que retorna lista de oids lexicograficamente seguintes (apenas do mesmo grupo - system, config or data, tendo em conta os ids usados na tabela de chaves)
    def get_next_oids(self, oid, count):
        possible_oids = ["1.1.1.0", "1.1.2.0", "1.1.3.0", "1.1.4.0", "1.1.5.0", "1.1.6.0", "1.1.7.0", "1.2.1.0", "1.2.2.0", "1.2.3.0"]  #NOTE hardcoded but best pratice to maintain SNMP resemblence in this implementation (by not getting errors for non existing OIDs, as ideally the MIB would be iterated oid by oid)
        result = []
        current_string = oid
        keys = oid.split(".")                   
        
        if count == 0:
            return [oid]
                
        if len(keys) == 4 and oid != "1.3.1.0":
            result.append(current_string)
            for _ in range(count):
                parts = current_string.split('.')
                parts[-2] = str(int(parts[-2]) + 1)
                current_string = '.'.join(parts)
                result.append(current_string)
                if len(result) == count +1:
                    break
            result = [item for item in result if item in possible_oids]
        elif oid == "1.3.1.0" or len(keys) == 5:
            if oid == "1.3.1.0":
                result.append(current_string)
                current_string = "1.3.3.1.0"
                
            if int(current_string.split('.')[-1]) in self.used_ids:
                id_index = self.used_ids.index(int(current_string.split('.')[-1]))
            else:
                id_index = 0
            for _ in range(count+1):
                for usedid in self.used_ids:
                    if len(result) == count+1:
                        break
                    parts = current_string.split('.')
                    parts[-1] = str(self.used_ids[id_index])
                    result.append('.'.join(parts))
                    id_index = (id_index + 1) % len(self.used_ids)  # Incrementar o indice e voltar ao inicio se necessário
                    if len(result) == count+1:
                        break
                parts = current_string.split('.')
                parts[-2] = str(int(parts[-2]) + 1)
                current_string = '.'.join(parts)

                if len(result) == count+1:
                    break
            result = [item for item in result if not item.endswith('.7.1') and int(item.split('.')[-2]) < 7]

        if result == []:
            return -10                                                                            #Error 10: No more OIDs past the given one (endOfMIBView)                                                           
        return result


    #! Funcao que trata de um pedido do tipo get
    # Client can get values from system and data groups (except keyValue if keyVisibility 0 or not same client and keyVisibility 1)
    # Admin can get values from all groups
    def get_request(self, dec_pdu, addr):
        ret = []
        for tuple in dec_pdu.instances_values:
            L_oid, L_value = tuple
            L_value = int(L_value)

            oids = self.get_next_oids(L_oid, L_value)
            if oids != -2 and oids != -10:
                for oid in oids:
                    if oid.startswith("1.3.3.2."):   # type: ignore
                        key_id = oid.split(".")[-1]

                        id_addr = self.mib.get_value(f"1.3.3.3.{key_id}")[1]
                        id_visibility = self.mib.get_value(f"1.3.3.6.{key_id}")[1]

                        if id_visibility == 0:
                            ret.append((oid, -8))                                                 #Error 8: Key is not visible
                        elif id_visibility == 1 and id_addr != addr[0]:
                            
                            ret.append((oid, -9))                                                 #Error 9: Key is not visible to this address
                        else:
                            ret.append(self.mib.get_value(oid))
                    else:
                        ret.append(self.mib.get_value(oid))
            elif oids == -2:
                ret.append((L_oid, -2))
            elif oids == -10:
                ret.append((L_oid, -10))

        if ret:
            self.send_response(dec_pdu, addr, ret)






   #! Função Auxiliar: Retorna o primeiro id disponivel
    def get_unused_number(self):
        for i in range(1, self.X+1):
            if i not in self.used_ids:
                return i
        return None


   #! Função que adiciona as instancias correspondentes a uma nova chave à MIB
    def add_key_entry(self, keyValue, keyRequester, keyExpirationDate, keyExpirationTime, keyVisibility):
        result = []
        keyID = self.get_unused_number()
        values = [keyID, keyValue, keyRequester, keyExpirationDate, keyExpirationTime, keyVisibility]
        oids = [(f"1.3.3.{inst}.{keyID}") for inst in range(1, 7)]

        curr_num_keys = int(self.mib.get_value("1.3.1.0", admin=True)[1])   # type: ignore
        if curr_num_keys < self.X:
            for oid, value in zip(oids, values): 
                set_or_nah = self.mib.set_value(oid, value, admin=True)
                result.append(set_or_nah)
        else:
            print("Max number of keys reached")
            self.debug()

        if result:
            new_value = int(curr_num_keys) + 1
            self.mib.set_value("1.3.1.0", new_value, admin=True)
            self.used_ids.append(keyID)
        return result


    #! Funcao que trata de um pedido do tipo set
    # Client can only set values to its keyVisibility instance(s)
    # Can try for other groups but will get error (including other instances of keys Table)
    def set_request(self, dec_pdu, addr):
        ret = []
        for tuple in dec_pdu.instances_values:
            W_oid, W_value = tuple

            #! Pedido para gerar uma nova chave
            if W_oid == "1.3.3.6.0":                                       
                    firstChar = self.mib.get_value("1.2.2.0", admin=True)[1]
                    numChars  = self.mib.get_value("1.2.3.0", admin=True)[1]

                    with self.gen_and_updateZ_atomicity_lock:
                        key, key_expiration = self.keys.generate_key(firstChar, numChars) # type: ignore
                        self.update_matrix_afterT()

                    key_exp_date_formatted = key_expiration.year * 104 + key_expiration.month * 102 + key_expiration.day
                    key_exp_time_formatted = key_expiration.hour * 104 + key_expiration.minute * 102 + key_expiration.second

                    ret += self.add_key_entry(key, addr[0], key_exp_date_formatted, key_exp_time_formatted, int(W_value))
            
            #! Pedido para alterar a visibilidade de uma chave
            elif W_oid.startswith("1.3.3.6."):                             
                keyID = int(W_oid.split(".")[-1])
                instance_addr = self.mib.get_value(f"1.3.3.3.{keyID}")[1]
                if instance_addr == addr[0]:
                    ret.append(self.mib.set_value(W_oid, int(W_value)))

            #! Outro pedido qualquer
            else:
                ret.append(self.mib.set_value(W_oid, W_value))
            
        if ret:
            self.send_response(dec_pdu, addr, ret)





    #! Funcao que calcula o MAC (Message Authentication Code) de uma mensagem
    def calculate_authentication_code(self, P):
        id = str(P).encode()  # Converte o identificador do PDU para bytes
        
        hmac_alg = hmac.HMAC(self.KEY, hashes.SHA256())
        hmac_alg.update(id)
        authentication_code = hmac_alg.finalize()
        return str(authentication_code)[2:-1]

    #! Funcao que verifica se a mensagem recebida é autêntica
    def verify_authentication(self, pdu):
        if pdu.security_model == 1:
            auth_code_received = pdu.security_params_list[0]
            auth_code_calculated = self.calculate_authentication_code(pdu.request_id)

            auth_code_calculated = auth_code_calculated
            if auth_code_received == auth_code_calculated:
                return True     # A mensagem é autêntica
            else:
                return False    # A mensagem não é autêntica

    #! Funcao que verifica se o PDU recebido é válido, e se não for, retorna um valor de erro que irá ser tratado na função que a chamou
    def verify_pdu(self, pdu, addr):
        P = pdu.request_id
        # Verificar se os valores dos tamanho da lista de instancias é coerente com o número de instâncias
        if pdu.num_instances != len(pdu.instances_values):
            return False, -1        
        
        # Verificar se os valores dos tamanho da lista de segurance é coerente com o número de valores de segurança
        if pdu.security_params_num != len(pdu.security_params_list):
            return False, -2

        # Verificar se o código de autenticação da mensagem é válido
        if not self.verify_authentication(pdu):
            return False, -3
        
        # Verificar se o ID do pedido é válido (não foi repetido nos últimos V segundos; removendo os que já expiraram)
        if addr in self.addr_pAndTime:
            addr_requests = self.addr_pAndTime[addr]
            for p, t in addr_requests:
                if P == p:
                    diff_time = time.time() - t
                    if diff_time < self.V:
                        return False, int(self.V - diff_time)
                    else:
                        addr_requests.remove((p, t))    # Pode ser removido porque já expirou e a funcao vai retornar True

        # Se o PDU for válido, adicionar o ID do PDU à lista de IDs juntamente com o tempo de receção
        if addr not in self.addr_pAndTime:
            self.addr_pAndTime[addr] = []
        self.addr_pAndTime[addr].append((P, time.time()))
        return True, 0
    

    #! Funcao que recebe um pedido, valida-o e delega o processamento para a funcao correspondente consoante o tipo de pedido
    def run(self):

        def monitor_stop_signal():
            while not self.stop_signal_received:
                time.sleep(1)    # Verificar a flag a cada segundo
            self.socket.close()  # Fechar o socket para poder terminar o processo
            print("Socket closed")

        monitor_thread = threading.Thread(target=monitor_stop_signal)
        monitor_thread.start()

        try:
            while not self.stop_signal_received:
                print("Waiting for request")

                data, addr = self.socket.recvfrom(4096)
                if data and addr[1] == self.port:
                    try:
                        decrypted_data = self.CYPHER.decrypt(data)
                        dec_pdu = SNMPkeySharePDU.decode(decrypted_data.decode())
                        valid_or_not = self.verify_pdu(dec_pdu, addr)
                        if valid_or_not[0]:
                            if dec_pdu.primitive_type == 1:
                                print("Get request received")
                                self.get_request(dec_pdu, addr)
                            elif dec_pdu.primitive_type == 2:
                                print("Set request received")
                                self.set_request(dec_pdu, addr)
                            else:
                                print("Invalid SNMP request received")

                        elif valid_or_not[1] == -1:
                            raise Exception(f"Invalid PDU: Number of elements of instances list ({dec_pdu.num_instances}) is not the same as the size of the list ({len(dec_pdu.instances_values)}).")  #type: ignore
                        else:
                            raise Exception(f"Invalid PDU: Wait {valid_or_not[1]} seconds before reusing the Request ID {dec_pdu.request_id}.")  #type: ignore

                    except Exception as e:
                        print("Exception occurred while processing request:", e)

            self.debug()

        except Exception as e:

            print(e)
            self.debug()
            print("RequestHandler received Exception. Stopping...")
            self.socket.close()


    #! Funcao de debug para guardar a MIB num ficheiro json
    def debug(self):
        json.dump(self.mib.mib, open("debug/MIB_debug.json", "w")) #type: ignore
        print("MIB saved to debug/MIB_debug.json")

















    #! Funcao que faz update da matrix Z a cada T segundos e guarda o timestamp na MIB
    def update_matrix_thread(self, T):
        T = int(T/1000)   # converter para segundos
        while not self.stop_signal_received:
            time.sleep(T)
            self.update_matrix_afterT()
        print("Matrix Update Thread stopped")


    def update_matrix_afterT(self):
        updated_time = self.keys.update_matrix_Z()

        zUpdateDate = updated_time.year * 104 + updated_time.month * 102 + updated_time.day
        zUpdateTime = updated_time.hour * 104 + updated_time.minute * 102 + updated_time.second

        self.mib.set_value("1.1.1.0", zUpdateDate, admin=True)
        self.mib.set_value("1.1.1.0", zUpdateTime, admin=True)
        print("Updated matrix Z")



    #! Functions related to key cleanup
    def decrease_dataNumberOfValidKeys(self):
        new_value = int(self.mib.get_value("1.3.1.0", True)[1]) - 1   #type: ignore
        self.mib.set_value("1.3.1.0", new_value, admin=True)

    def compare_to_datetime(self, keyExpirationDate, keyExpirationTime):
        cur_datetime = datetime.datetime.now()

        cur_date = cur_datetime.year * 104 + cur_datetime.month * 102 + cur_datetime.day
        cur_time = cur_datetime.hour * 104 + cur_datetime.minute * 102 + cur_datetime.second

        if keyExpirationDate < cur_date:                                        # Key has expired
            return True         
        elif keyExpirationDate == cur_date and keyExpirationTime < cur_time:    # Key has expired
            return True         
        else:                                                                   # Key is still valid
            return False        

    def clean_expired_thread(self, V):
        while not self.stop_signal_received:
            time.sleep(5)
            self.remove_expired_entries()
        print("Remove Expired Keys Thread stopped")

    def remove_expired_entries(self):
        for id in self.used_ids:
            keyExpirationDate = int(self.mib.mib_data["3"]["4"][str(id)])       #NOTE: directly accessed mib_data because it's faster, might change to get_value for consistency
            keyExpirationTime = int(self.mib.mib_data["3"]["5"][str(id)])

            if self.compare_to_datetime(keyExpirationDate, keyExpirationTime):
                for entry in range(1, 7):
                    del self.mib.mib_data["3"][str(entry)][f"{id}"]
                self.decrease_dataNumberOfValidKeys()
                self.used_ids.remove(id)
                print(f"Key {id} has expired and was removed")



    #! Functions related to timestamp S instance update
    def increment_timestamp_thread(self, seconds):
        while not self.stop_signal_received:
            time.sleep(seconds)
            self.increment_timestamp()
        print("Increment Timestamp Thread stopped")

    
    def increment_timestamp(self):                                              #NOTE: by not incrementing by X seconds, we can have a more precise timestamp
        now = time.time()
        new = int(now - self.start_time)
        self.mib.set_value("1.1.7.0", new, admin=True)
















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
    M = str(config['Other']['M'])
    KEY = str(config['Other']['KEY'])

    if(len(M) != 2*K):
        print("Error: M length must be 2K. Check config.ini file.")
        sys.exit(1)

    return IP, PORT, K, T, X, V, M, KEY


def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("A Inicializar agente SNMP...")

    IP, PORT, K, T, X, V, M, KEY = read_configuration_file("config.ini")
    start = time.time()
    rH = RequestHandler(IP, PORT, K, T, X, V, M, KEY, start)

    try:
        rH.daemon = True
        rH.start()
        while not rH.stop_signal_received:    #input 1 recebido: guardar MIB
            debug = input("")
            if rH.stop_signal_received:
                break
            elif debug == "1":
                rH.debug()
    

    except KeyboardInterrupt:
        # Gracefully close the agent
        print("\nStopping RequestHandler...")
        rH.debug()
        rH.stop_signal_received = True
        #rH.join()   # Wait for the RequestHandler thread to finish
        print("Stopping...")


if __name__ == '__main__':
    main()





