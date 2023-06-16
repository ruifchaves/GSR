import json, time




class SNMPKeyShareMIB:
    def __init__(self, K, T, X, V, M):
        self.mib = dict()
        self.mib_system = dict()
        self.mib_config = dict()
        self.mib_data = dict()

        # ii. Manter um objeto de gestão que indique (em segundos) há quanto tempo o agente
        #     iniciou/reiniciou a sua execução (timespamp S);
        self.start_time = time.time()

        self.importMIB('SNMPkeyShareMIB.json')
        self.set_initial_values(K, T, X, V, M)

        self.add_key_entry()

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



    def check_type(self, set_value, supported_type):
        print(type(set_value), supported_type)
        if((type(set_value) == int and supported_type == "INTEGER")
           or (type(set_value) == str and supported_type == "OCTET STRING")):
            return True
        else:
            return False



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
            mib_dict[keys[-1]] = dict()
            mib_dict[keys[-1]] = set_value
            print(mib_dict)
        else:
            print("OID Syntax not supported")

        print(f"OID {oid} ->  {self.get_value(oid)}")         




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


        
    def increase_dataNumberOfValidKeys_by1(self):
        curr_value = self.get_value("1.3.1.0")
        new_value = int(curr_value + 1);    #type: ignore
        self.set_value("1.3.1.0", new_value, True)


    def add_key_entry(self, keyID = 4, keyValue = "4", keyRequester="32432", keyExpirationDate=786247, keyExpirationTime=6565, keyVisibility=1):

        result = [self.translateOID(f"1.3.3.{X}.{keyID}") for X in range(1, 7)]

        self.set_new_value(f"1.3.3.1.{keyID}", keyID)
        self.set_new_value(f"1.3.3.3.{keyID}", keyRequester)
        self.set_new_value(f"1.3.3.2.{keyID}", keyValue)
        self.set_new_value(f"1.3.3.4.{keyID}", keyExpirationDate)
        self.set_new_value(f"1.3.3.5.{keyID}", keyExpirationTime)
        self.set_new_value(f"1.3.3.6.{keyID}", keyVisibility)
        self.increase_dataNumberOfValidKeys_by1()
        try:
            print(self.mib_data)
        except:
            print("Error adding key entry")
