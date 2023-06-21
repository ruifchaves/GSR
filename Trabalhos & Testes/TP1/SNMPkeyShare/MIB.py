import json, time, threading, datetime




class SNMPKeyShareMIB:
    def __init__(self, K, T, X, V, M, start_time):
        self.mib = dict()
        self.mib_system = dict()
        self.mib_config = dict()
        self.mib_data = dict()
        self.used_ids = []

        # ii. Manter um objeto de gestão que indique (em segundos) há quanto tempo o agente
        #     iniciou/reiniciou a sua execução (timespamp S);
        self.start_time = start_time

        self.importMIB('SNMPkeyShareMIB.json')
        self.set_initial_values(K, T, X, V, M)

        # Start the cleanup thread
        cleanup_thread = threading.Thread(target=self.clean_expired_thread, args=(V,))
        cleanup_thread.start()

        # Start the update timestamp thread
        cleanup_thread = threading.Thread(target=self.increment_timestamp_thread, args=(5,))
        cleanup_thread.start()


    #! Initizalization of MIB as dictionary and its values
    # function to import json file and init mib dictionaries
    def importMIB(self, file):
        self.mib = json.load(open(file))
        self.mib_system = self.mib["1"]["1"]
        self.mib_config = self.mib["1"]["2"]
        self.mib_data   = self.mib["1"]["3"]

    # function to update initial values  #TODO: isto é preciso????
    def set_initial_values(self, K, T, X, V, M):
        print("Setting initial values...")
        self.set_value("1.1.1.0", 1,  True)
        self.set_value("1.1.2.0", 2,  True)
        self.set_value("1.1.3.0", K,  True)
        self.set_value("1.1.4.0", T,  True)
        self.set_value("1.1.5.0", X,  True)
        self.set_value("1.1.6.0", V,  True)
        self.set_value("1.1.7.0", 0,  True)
        self.set_value("1.2.1.0", M,  True)
        self.set_value("1.2.2.0", 33, True)
        self.set_value("1.2.3.0", 94, True)
        self.set_value("1.3.1.0", 0,  True)
        print("Initial values set!")

        self.X = X

        #Following lines are for testing purposes
        #self.set_value("1.1.1.0", 1)
        #self.set_value("1.2.1.0", M)
        #self.set_value("1.3.1.0", 0)

        #print(self.get_value("1.1.1.0", True))
        #print(self.get_value("1.2.1.0", True))
        #print(self.get_value("1.3.1.0", True))

        #print(self.get_value("1.1.1.0"))
        #print(self.get_value("1.2.1.0"))
        #print(self.get_value("1.3.1.0"))


    # function to translate oid to value
    def translateOID(self, oid):
        keys = oid.split(".")
        return keys


    #! Get value
    # Client can get values from system and data groups (except keyValue if keyVisibility 0 or not same client and keyVisibility 1)
    # Admin can get values from all groups (except if non-accessible)
    def get_value(self, oid, admin=False):
        keys = self.translateOID(oid)
        mib_dict = None
        ret = None
        
        if keys[1] == "1":
            mib_dict = self.mib_system
        elif keys[1] == "2":
            mib_dict = self.mib_config
        elif keys[1] == "3" and len(keys) == 4:
            mib_dict = self.mib_data        
        elif keys[1] == "3" and len(keys) == 5:
            mib_dict = self.mib_data[str(keys[1])]
        else:
            print("OID not found")                                  
            return (oid, -2)                                                #Error 2: OID not found (noSuchName)        

        max_access = mib_dict[str(keys[-2])]["MAX-ACCESS"] #type: ignore

        if max_access == "not-accessible" and not admin:
            print("OID not accessible")                                     
            return (oid, -6)                                                #Error 6: OID not accessible (noAccess)
        else:
            for key in keys[(2 if len(keys)==4 else 3):]:
                if isinstance(mib_dict, dict) and key in mib_dict:
                    mib_dict = mib_dict[key]
                else:
                    print("OID not found")
                    return (oid, -2)                                        #Error 2: OID not found (noSuchName)
            return (oid, mib_dict)


    #! Set value and auxiliar function
    #Function that checks if given value is of supported type
    def check_type(self, set_value, supported_type):
        if (type(set_value) == int and supported_type == "INTEGER") or (type(set_value) == str and supported_type == "OCTET STRING"):
            return True
        else:
            return False

    # Client can only set values to it keyVisibility instance
    # Can try for other groups but will get error (including other instances of keys Table) #TODO Testar isto!!
    # Admin can set values to all groups (except if non-accessible)
    def set_value(self, oid, set_value, admin=False):
        keys = self.translateOID(oid)
        mib_dict = None
        ret = None

        if keys[1] == "1":
            mib_dict = self.mib_system
        elif keys[1] == "2":
            mib_dict = self.mib_config
        elif keys[1] == "3" and len(keys) == 4:
            mib_dict = self.mib_data        
        elif keys[1] == "3" and len(keys) == 5:
            mib_dict = self.mib_data[str(keys[1])]
        else:
            print("OID not found")
            return (oid, -2)                                                #Error 2: OID not found (noSuchName)

        max_access = mib_dict[str(keys[-2])]["MAX-ACCESS"] #type: ignore
        type_value = mib_dict[str(keys[-2])]["SYNTAX"]     #type: ignore

        if max_access == "read-only" and not admin:
            print("OID is read-only")
            return (oid, -7)                                                #Error 4: OID is read-only (wrongType)
        elif max_access == "not-accessible" and not admin:
            print("OID not accessible")                                     
            return (oid, -6)                                                #Error 6: OID not accessible (noAccess)
        elif max_access == "read-write" or admin:
            if self.check_type(set_value, type_value):
                for key in keys[(2 if len(keys)==4 else 3):-1]:
                    if isinstance(mib_dict, dict) and key in mib_dict:
                        mib_dict = mib_dict[key]
                    else:
                        print("OID not found")
                        return (oid, -2)                                    #Error 2: OID not found (noSuchName)
                    
                    mib_dict[keys[-1]] = set_value
                    print(f"    {self.get_value(oid, admin=True)}")
                    return (oid, self.get_value(oid, True)[1]) #type: ignore
            else:
                print("OID Syntax not supported")
                return (oid, -3)                                            #Error 3: Value type not supported (badValue)
        









    #! Auxiliary function: Spits out available Key ID
    def get_unused_number(self):
        for i in range(1, self.X+1):
            if i not in self.used_ids:
                return i
        return None



    #! Functions related to key cleanup
    def decrease_dataNumberOfValidKeys(self):
        new_value = int(self.get_value("1.3.1.0", True)[1]) - 1     #type: ignore
        self.set_value("1.3.1.0", new_value, admin=True)

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
        while True:
            time.sleep(V)
            self.remove_expired_entries()

    def remove_expired_entries(self):
        for id in self.used_ids:
            print(f"Checking key {id}")
            keyExpirationDate = int(self.mib_data["3"]["4"][str(id)])
            keyExpirationTime = int(self.mib_data["3"]["5"][str(id)])

            if self.compare_to_datetime(keyExpirationDate, keyExpirationTime):
                for entry in range(1, 7):
                    print(f"Gonna delete key {id}.{entry}")
                    del self.mib_data["3"][str(entry)][f"{id}"]
                self.decrease_dataNumberOfValidKeys()
                self.used_ids.remove(id)
            else:
                print(f"Key {id} is still valid")
                pass




    #! Functions related to timestamp S instance update
    def increment_timestamp_thread(self, seconds):
        while True:
            time.sleep(seconds)
            self.increment_timestamp()

    def increment_timestamp(self):
        now = time.time()
        new = int(now - self.start_time)
        self.set_value("1.1.7.0", new, admin=True)


