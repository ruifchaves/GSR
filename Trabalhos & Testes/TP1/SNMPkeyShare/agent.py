import configparser, os, json, random, threading, socket, sys, time, datetime
from SNMPkeySharePDU import SNMPkeySharePDU
from MIB import SNMPKeyShareMIB
from keys import Keys
import numpy as np



class RequestHandler(threading.Thread):
    def __init__(self, IP, PORT, K, T, X, V, M, start_time):
        threading.Thread.__init__(self)

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((IP, PORT))
        self.socket.settimeout(None)
        self.port = PORT
        self.mib = SNMPKeyShareMIB()
        self.keys = Keys(M, K, V)
        self.K = K
        self.T = T
        self.X = X
        self.V = V
        self.M = M
        self.start_time = start_time
        self.set_mib_initial_values()
        self.used_ids = []
        self.addr_pAndTime = {}
        self.stop_signal_received = False

        # Start the matrix update thread
        self.matrix_update_thread = threading.Thread(target=self.update_matrix_thread, args=(20000,)) #TOOO remover this
        self.matrix_update_thread.start()

        # Start the cleanup thread
        self.cleanup_thread = threading.Thread(target=self.clean_expired_thread, args=(V,))
        self.cleanup_thread.start()

        # Start the update timestamp thread
        self.increase_timestamp_thread = threading.Thread(target=self.increment_timestamp_thread, args=(1,))
        self.increase_timestamp_thread.start()

        #NOTE: ensure the atomicity of the two function calls: generate_key followed by update_matrix_Z
        self.gen_and_updateZ_atomicity_lock = threading.Lock()


    # function to update initial values
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
        print("Initial values set!")



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
        print("Creating Response Message")
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
                print("Response message sent")
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

        #If you send an SNMP GETNEXT request with an OID that does not exist in the MIB, the SNMP agent will not gather the following OID values lexically.
        #The SNMP agent will respond with an SNMP error, specifically an "End of MIB View" error (SNMPv2c) or "noSuchObject" error (SNMPv1). This indicates that the requested OID does not exist or that there are no further OIDs available in the MIB that are lexicographically greater than the given OID.
        #In such a case, the SNMP agent will not gather or return any OID values beyond the non-existent OID. The SNMP manager will receive the error response and handle it accordingly.
        oid_value = self.mib.get_value(oid, admin=True)
        if oid_value[1] == -2:
            print(-2)
            return -2                                                            #Error 2: OID does not exist
        
        if count == 0:
            return [oid]
                
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
                    id_index = (id_index + 1) % len(self.used_ids)  # Increment index and wrap around if needed
                    if len(result) == count+1:
                        break
                parts = current_string.split('.')
                parts[-2] = str(int(parts[-2]) + 1)
                current_string = '.'.join(parts)

                if len(result) == count+1:
                    break
            result = [item for item in result if not item.endswith('.7.1') and int(item.split('.')[-2]) < 7]

        if result == []:
            print(-10)
            return -10                                                             #Error 10: No more OIDs past the given one (endOfMIBView)
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









   #! Auxiliary function: Spits out available Key ID
    def get_unused_number(self):
        for i in range(1, self.X+1):
            if i not in self.used_ids:
                return i
        return None


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
    # Client can only set values to it keyVisibility instance
    # Can try for other groups but will get error (including other instances of keys Table)
    # Admin can set values to all groups (except if non-accessible)
    def set_request(self, dec_pdu, addr):
        ret = []
        for tuple in dec_pdu.instances_values:

            W_oid, W_value = tuple
            if W_oid == "1.3.3.6.0":                                       #! Request to generate new key
                    firstChar = self.mib.get_value("1.2.2.0", admin=True)[1]
                    numChars  = self.mib.get_value("1.2.3.0", admin=True)[1]

                    #while self.mib.updating_matrix:
                    #    pass
                    with self.gen_and_updateZ_atomicity_lock:
                        key, key_expiration = self.keys.generate_key(firstChar, numChars) # type: ignore
                        self.update_matrix_afterT()

                    key_exp_date_formatted = key_expiration.year * 104 + key_expiration.month * 102 + key_expiration.day
                    key_exp_time_formatted = key_expiration.hour * 104 + key_expiration.minute * 102 + key_expiration.second

                    ret += self.add_key_entry(key, addr[0], key_exp_date_formatted, key_exp_time_formatted, int(W_value))
            
            elif W_oid.startswith("1.3.3.6."):                             #! Request to change current key visibility
                keyID = int(W_oid.split(".")[-1])
                instance_addr = self.mib.get_value(f"1.3.3.3.{keyID}")[1]
                if instance_addr == addr[0]:
                    ret.append(self.mib.set_value(W_oid, int(W_value)))

            else:                                                           #! Other requests 
                ret.append(self.mib.set_value(W_oid, W_value))
            
        if ret:
            self.send_response(dec_pdu, addr, ret)




    def verify_pdu(self, pdu, addr):
        P = pdu.request_id
        if pdu.num_instances != len(pdu.instances_values):
            return False, -1

        if addr in self.addr_pAndTime:
            addr_requests = self.addr_pAndTime[addr]
            for p, t in addr_requests:
                if P == p:
                    diff_time = time.time() - t
                    if diff_time < self.V:
                        return False, int(self.V - diff_time)
                    else:
                        addr_requests.remove((p, t))    #Can be removed because have expired and the function will certainly return True

        if addr not in self.addr_pAndTime:
            self.addr_pAndTime[addr] = []  # Create an empty list for the address
        self.addr_pAndTime[addr].append((P, time.time()))

        return True, 0

    #! Funcao que recebe um pedido, valida-o e delega o processamento para a funcao correspondente consoante o tipo de pedido
    def run(self):

        def monitor_stop_signal():
            while not self.stop_signal_received:
                time.sleep(1)  # Check the flag every second
            #self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()  # Close the socket when the flag is set to True
            print("Socket closed")

        monitor_thread = threading.Thread(target=monitor_stop_signal)
        monitor_thread.start()

        try:
            while not self.stop_signal_received:
                print("Waiting for request")

                data, addr = self.socket.recvfrom(4096)
                if data and addr[1] == self.port:
                    try:
                        dec_pdu = SNMPkeySharePDU.decode(data.decode())
                        valid_or_not = self.verify_pdu(dec_pdu, addr)
                        if valid_or_not[0]:
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

                        elif valid_or_not[1] == -1:
                            raise Exception(f"Invalid PDU: Number of elements of instances list ({dec_pdu.num_instances}) is not the same as the size of the list ({len(dec_pdu.instances_values)}).")  #type: ignore
                        else:
                            raise Exception(f"Invalid PDU: Wait {valid_or_not[1]} seconds before reusing the Request ID {dec_pdu.request_id}.")  #type: ignore

                    except Exception as e:
                        print("Exception occurred while processing request:", e)
                        # Handle the exception here (e.g., log the error, send an error response, etc.)

            self.debug()
            print("passsseii aqui stopped")
            #self.cleanup_thread.join()
            #monitor_thread.join()
            #self.clean_expired_thread.join()
            #self.update_matrix_thread.join()

        except Exception as e:

            print(e)
            self.debug()
            print("RequestHandler received Exception. Stopping...")
            self.socket.close()


    # Funcao de debug para guardar a MIB num ficheiro json
    def debug(self):
        json.dump(self.mib.mib, open("debug/MIB_debug.json", "w")) #type: ignore
        print("MIB saved to debug/MIB_debug.json")

















    #! Funcao que faz update da matrix Z a cada T segundos e guarda o timestamp na MIB
    def update_matrix_thread(self, T):
        T = int(T/1000)   # convert to seconds
        while not self.stop_signal_received:
            time.sleep(5)
            self.update_matrix_afterT()
        print("Matrix Update Thread stopped")


    def update_matrix_afterT(self):

        updated_time = self.keys.update_matrix_Z()

        systemRestartDate = updated_time.year * 104 + updated_time.month * 102 + updated_time.day
        systemRestartTime = updated_time.hour * 104 + updated_time.minute * 102 + updated_time.second

        self.mib.set_value("1.1.1.0", systemRestartDate, admin=True)
        self.mib.set_value("1.1.1.0", systemRestartTime, admin=True)
        print("Updated matrix Z")





    #! Functions related to key cleanup
    def decrease_dataNumberOfValidKeys(self):
        new_value = int(self.mib.get_value("1.3.1.0", True)[1]) - 1     #type: ignore
        self.mib.set_value("1.3.1.0", new_value, admin=True)

    def compare_to_datetime(self, keyExpirationDate, keyExpirationTime):
        # Get current date and time
        cur_datetime = datetime.datetime.now()

        cur_date = cur_datetime.year * 104 + cur_datetime.month * 102 + cur_datetime.day
        cur_time = cur_datetime.hour * 104 + cur_datetime.minute * 102 + cur_datetime.second

        # Compare expiration_datetime to current_datetime
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
            time.sleep(5)
            self.increment_timestamp()
        print("Increment Timestamp Thread stopped")

    # by not incrementing by X seconds, we can have a more precise timestamp
    def increment_timestamp(self):
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

    if(len(M) != 2*K):
        print("Error: M length must be 2K. Check config.ini file.")
        sys.exit(1)

    return IP, PORT, K, T, X, V, M




def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("A Inicializar agente SNMP...")

    IP, PORT, K, T, X, V, M = read_configuration_file("config.ini")
    start = time.time()
    rH = RequestHandler(IP, PORT, K, T, X, V, M, start)

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
        print("Stopping RequestHandler...")
        rH.debug()
        rH.stop_signal_received = True
        #rH.join()   # Wait for the RequestHandler thread to finish
        print("Stopping...")
        #sys.exit(0)


if __name__ == '__main__':
    main()





