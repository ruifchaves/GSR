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

    def get_config_values(self):
        return [
            self.get_value("1.1.3.0"),
            self.get_value("1.1.4.0"),
            self.get_value("1.1.5.0"),
            self.get_value("1.1.6.0"),
            self.get_value("1.2.1.0")
        ]

    # function to translate oid to value
    def translateOID(self, oid):
        keys = oid.split(".")
        return keys

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




    #def get_next_oids(self, given_oid, n):
    #    given_parts = given_oid.split('.')
    #    next_oids = []
#
    #    while len(next_oids) < n:
    #        last_oid = next_oids[-1] if next_oids else given_oid
    #        parts = last_oid.split('.')
    #        next_part = str(int(parts[-1]) + 1)
    #        next_oid = '.'.join(parts[:-1] + [next_part])
#
    #        if next_oid.startswith('.'.join(given_parts)):
    #            next_oids.append(next_oid)
    #        else:
    #            break
    #    return next_oids

    def get_next_oids(self, oid, count):
        result = []
        current_string = oid
        possibilities = ["1.1.1.0", "1.1.2.0", "1.1.3.0", "1.1.4.0", "1.1.5.0", "1.1.6.0", "1.2.1.0", "1.2.2.0", "1.2.3.0", "1.3.1.0"]

        for _ in range(count):
            result.append(current_string)
            parts = current_string.split('.')
            parts[-2] = str(int(parts[-2]) + 1)
            current_string = '.'.join(parts)

        return result



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
        print(self.mib_data["1"]["0"])
        #curr_value = self.get_value("1.3.1.0")
        #new_value = int(curr_value + 1);    #type: ignore
        #self.set_value("1.3.1.0", new_value, True)

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
        
        type_value = mib_dict[str(keys[-2])]["SYNTAX"]      # type: ignore

        if self.check_type(set_value, type_value):
            for key in keys[3:-1]:
                if isinstance(mib_dict, dict) and key in mib_dict:
                    mib_dict = mib_dict[key]
                else:
                    print("OID not found")
                    break
            mib_dict[keys[-1]] = set_value
        else:
            print("OID Syntax not supported")

        print(f"OID {oid} ->  {self.get_value(oid)}")       


    def add_key_entry(self, keyValue, keyRequester, keyExpirationDate, keyExpirationTime, keyVisibility):

        keyID = self.get_unused_number()

        #result = [self.translateOID(f"1.3.3.{X}.{keyID}") for X in range(1, 7)]
        result = None
        try:
            if self.get_value("1.3.1.0") < self.X:
                self.set_new_value(f"1.3.3.1.{keyID}", keyID)
                self.set_new_value(f"1.3.3.2.{keyID}", keyValue)
                self.set_new_value(f"1.3.3.3.{keyID}", keyRequester)
                self.set_new_value(f"1.3.3.4.{keyID}", keyExpirationDate)
                self.set_new_value(f"1.3.3.5.{keyID}", keyExpirationTime)
                self.set_new_value(f"1.3.3.6.{keyID}", keyVisibility)
                self.increase_dataNumberOfValidKeys()
                
                result = f"1.3.3.6.{keyID}", self.get_value(f"1.3.3.6.{keyID}")
        except:
            print("Error adding key entry")

        if result is not None: self.used_ids.append(keyID)
        return result










    def compare_to_datetime(self, keyExpirationDate, keyExpirationTime):
        # Convert keyExpirationDate to datetime object
        year = keyExpirationDate // 10000
        month = (keyExpirationDate % 10000) // 100
        day = keyExpirationDate % 100
        expiration_date = datetime.datetime(year, month, day)

        # Convert keyExpirationTime to datetime object
        hours = keyExpirationTime // 10000
        minutes = (keyExpirationTime % 10000) // 100
        seconds = keyExpirationTime % 100
        expiration_time = datetime.time(hours, minutes, seconds)

        # Get current date and time
        current_datetime = datetime.datetime.now()

        # Combine expiration_date and expiration_time into a datetime object
        expiration_datetime = datetime.datetime.combine(expiration_date, expiration_time)

        # Compare expiration_datetime to current_datetime
        if current_datetime < expiration_datetime:
            return False # Key is still valid
        else:
            return True # Key has expired

    # Functions related to key cleanup
    def clean_expired_thread(self, X):
        while True:
            self.remove_expired_entries()
            time.sleep(X)

    def remove_expired_entries(self):
        for X in self.used_ids:
            print(self.mib_data["3"])
            print(f"Checking key {X}: {self.used_ids}")
            keyExpirationDate = self.mib_data["3"]["4"][str(X)]
            keyExpirationTime = self.mib_data["3"]["5"][str(X)]
            if self.compare_to_datetime(keyExpirationDate, keyExpirationTime):
                for entry in range(1, 7):
                    print(f"Gonna delete")
                    print(f"Deleted key {X}: {self.used_ids}")
                    del self.mib_data["3"][str(entry)][f"{X}"]
                self.decrease_dataNumberOfValidKeys()
                self.used_ids.remove(X)
                print(self.mib_data["3"])
            else:
                pass