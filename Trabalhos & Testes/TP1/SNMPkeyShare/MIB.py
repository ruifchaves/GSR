import json, time, threading, datetime




class SNMPKeyShareMIB:
    def __init__(self, K, T, X, V, M):
        self.mib = dict()
        self.mib_system = dict()
        self.mib_config = dict()
        self.mib_data = dict()
        self.used_ids = []

        # ii. Manter um objeto de gestão que indique (em segundos) há quanto tempo o agente
        #     iniciou/reiniciou a sua execução (timespamp S);
        self.start_time = time.time()

        self.importMIB('SNMPkeyShareMIB.json')
        self.set_initial_values(K, T, X, V, M)

        # Start the cleanup thread
        cleanup_thread = threading.Thread(target=self.clean_expired_thread, args=(60,))
        cleanup_thread.start()

    # function to import json file and init mib dictionaries
    def importMIB(self, file):
        self.mib = json.load(open(file))
        self.mib_system = self.mib["1"]["1"]
        self.mib_config = self.mib["1"]["2"]
        self.mib_data   = self.mib["1"]["3"]

    # function to update initial values  #TODO: isto é preciso????
    def set_initial_values(self, K, T, X, V, M):
        self.set_value("1.1.1.0", 1, True)
        self.set_value("1.1.2.0", 2, True)
        self.set_value("1.1.3.0", K, True)      #K
        self.set_value("1.1.4.0", T, True)      #T
        self.set_value("1.1.5.0", X, True)      #X
        self.set_value("1.1.6.0", V, True)      #V
        self.set_value("1.2.1.0", M, True)
        self.set_value("1.2.2.0", 33, True)
        self.set_value("1.2.3.0", 94, True)
        self.set_value("1.3.1.0", 0, True)

        self.K = K
        self.T = T
        self.X = X
        self.V = V
        self.M = M

    # function to translate oid to value
    def translateOID(self, oid):
        keys = oid.split(".")
        return keys



    # TODO: talvez seja substituido pelo set_value_forN
    def get_value(self, oid):
        keys = self.translateOID(oid)
        mib_dict = None
        
        if keys[1] == "1":
            mib_dict = self.mib_system
        elif keys[1] == "2":
            mib_dict = self.mib_config
        elif keys[1] == "3":
            mib_dict = self.mib_data
        else:
            print("OID not found")
            return None

        for key in keys[2:]:
            if isinstance(mib_dict, dict) and key in mib_dict:
                mib_dict = mib_dict[key]
            else:
                mib_dict = None
                print("OID not found")
                break

        return mib_dict



    # TODO teste de new get value a ver se retorna tambem o erro, substituir o get_value pelo new_get_value.
    # TODO adicionar admin flag para aceder a system e config groups
    def get_value_forN(self, oid):
        keys = self.translateOID(oid)
        mib_dict = None
        ret = None
        
        if keys[1] == "1":
            mib_dict = self.mib_system
        elif keys[1] == "2":
            mib_dict = self.mib_config
        elif keys[1] == "3":
            mib_dict = self.mib_data
        else:
            print("OID not found")
            return None

        for key in keys[2:]:
            if isinstance(mib_dict, dict) and key in mib_dict:
                mib_dict = mib_dict[key]
            else:
                print("OID not found")
                ret = (oid, -1) #Error 1: OID not found
                break
            ret = (oid, mib_dict)
        return ret


    # TODO passar esta funcaio para o agente
    def get_next_oids(self, oid, count):
        result = []
        current_string = oid

        # TODO correct for same group 1 and 2; for 3 needs implementation, same keyID instance
        for _ in range(count):
            result.append(current_string)
            parts = current_string.split('.')
            parts[-2] = str(int(parts[-2]) + 1)
            current_string = '.'.join(parts)

        return result

    # TODO passar esta funcao para o agente, passar a inline de get_request e usar apenas get_value no agente
    def get_N_values(self, oid, N):
        ret = []
        oids = self.get_next_oids(oid, N)
        print(oids)
        for i in oids:
            oid_value = self.get_value(i)
            ret.append((i, oid_value))

        return ret










    def check_type(self, set_value, supported_type):
        if((type(set_value) == int and supported_type == "INTEGER")
           or (type(set_value) == str and supported_type == "OCTET STRING")):
            return True
        else:
            return False

    # TODO: atualizar esta funcao para ser como a do set_new_value e retornar (oid, value or error). substituir a set_new_value por esta????
    def set_value(self, oid, set_value, admin=False):
        keys = self.translateOID(oid)
        mib_dict = None  # Variable to store the MIB dictionary

        if keys[1] == "1":
            mib_dict = self.mib_system
        elif keys[1] == "2":
            mib_dict = self.mib_config
        elif keys[1] == "3":
            mib_dict = self.mib_data
        else:
            print("OID not found")
            return None


        max_access = mib_dict[str(keys[-2])]["MAX-ACCESS"]  # type: ignore
        type_value = mib_dict[str(keys[-2])]["SYNTAX"]      # type: ignore

        if max_access == "read-only" and admin == False:
            print("OID is read-only")

        elif max_access == "read-write" or admin == True:
            if self.check_type(set_value, type_value) or admin == True:
                for key in keys[2:-1]:
                    if isinstance(mib_dict, dict) and key in mib_dict:
                        mib_dict = mib_dict[key]
                    else:
                        print("OID not found")
                        break
                mib_dict[keys[-1]] = set_value  # Update the value in the MIB dictionary
            else:
                print("OID Syntax not supported")

        print(f"OID {oid} ->  {self.get_value(oid)}")                             #!!!DEBUG









    def increase_dataNumberOfValidKeys(self):
        old = self.mib_data["1"]["0"]
        self.mib_data["1"]["0"] = int(old) + 1

    def decrease_dataNumberOfValidKeys(self):
        old = self.mib_data["1"]["0"]
        self.mib_data["1"]["0"] = int(old) - 1

    def get_unused_number(self):
        for i in range(1, 101):
            if i not in self.used_ids:
                return i
        return None

    def set_new_value(self, oid, set_value):
        keys = self.translateOID(oid)
        mib_dict = self.mib_data[str(keys[2])]
        ret = None
        
        type_value = mib_dict[str(keys[-2])]["SYNTAX"]      # type: ignore

        if self.check_type(set_value, type_value):
            for key in keys[3:-1]:
                if isinstance(mib_dict, dict) and key in mib_dict:
                    mib_dict = mib_dict[key]
                else:
                    print("OID not found")
                    ret = (oid, -1) #Error 1: OID not found
                    break
            mib_dict[keys[-1]] = set_value
            ret = (oid, set_value)
        else:
            print("OID Syntax not supported")
            ret = (oid, -2)  #Error 2: Value type not supported

        print(f"OID {oid} ->  {self.get_value(oid)}")       
        return ret


    def add_key_entry(self, keyValue, keyRequester, keyExpirationDate, keyExpirationTime, keyVisibility):
        result = []
        #result = None

        keyID = self.get_unused_number()
        values = [keyID, keyValue, keyRequester, keyExpirationDate, keyExpirationTime, keyVisibility]
        oids = [(f"1.3.3.{X}.{keyID}") for X in range(1, 7)]
        try:
            for oid, value in zip(oids, values):
                if self.get_value("1.3.1.0") < self.X:
                    set_or_nah = self.set_new_value(oid, value)
                    #result = f"1.3.3.6.{keyID}", self.get_value(f"1.3.3.6.{keyID}")
                    result.append(set_or_nah)
        except:
            print("Error adding key entry")

        if result: 
            self.increase_dataNumberOfValidKeys()
            self.used_ids.append(keyID)
        return result










    def compare_to_datetime(self, keyExpirationDate, keyExpirationTime):
        # Get current date and time
        cur_datetime = datetime.datetime.now()

        cur_date = cur_datetime.year * 104 + cur_datetime.month * 102 + cur_datetime.day
        cur_time = cur_datetime.hour * 104 + cur_datetime.minute * 102 + cur_datetime.second

        # Compare expiration_datetime to current_datetime
        if keyExpirationDate < cur_date:
            return True # Key has expired
        elif keyExpirationDate == cur_date and keyExpirationTime < cur_time:
            return True # Key has expired
        else:
            return False # Key is still valid


    # Functions related to key cleanup
    def clean_expired_thread(self, X):
        while True:
            self.remove_expired_entries()
            time.sleep(X)

    def remove_expired_entries(self):
        for X in self.used_ids:
            keyExpirationDate = int(self.mib_data["3"]["4"][str(X)])
            keyExpirationTime = int(self.mib_data["3"]["5"][str(X)])

            if self.compare_to_datetime(keyExpirationDate, keyExpirationTime):
                for entry in range(1, 7):
                    print(f"Gonna delete key {X}.{entry}")
                    del self.mib_data["3"][str(entry)][f"{X}"]
                self.decrease_dataNumberOfValidKeys()
                self.used_ids.remove(X)
            else:
                print(f"Key {X} is still valid")
                pass