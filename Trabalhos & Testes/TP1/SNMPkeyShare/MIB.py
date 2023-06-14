import json, time


class SNMPKeyShareMIB:
    def __init__(self):
        #current_datetime = datetime.now()
        self.mib = dict()
        self.mib_system = dict()
        self.mib_config = dict()
        self.mib_data = dict()

        # ii. Manter um objeto de gestão que indique (em segundos) há quanto tempo o agente
        #     iniciou/reiniciou a sua execução (timespamp S);
        self.start_time = time.time()

        self.importMIB('SNMPkeyShareMIB.json')
        self.set_initial_values()

    # function to import json file
    def importMIB(self, file):
        self.mib = json.load(open(file))
        self.mib_system = self.mib["1"]["1"]
        self.mib_config = self.mib["1"]["2"]
        self.mib_data   = self.mib["1"]["3"]

    # function to update initial values  #TODO: isto é preciso????
    def set_initial_values(self):
        self.set_value("1.1.1.0", 1)
        self.set_value("1.1.2.0", 2)
        self.set_value("1.1.3.0", 3)
        self.set_value("1.1.4.0", 4)
        self.set_value("1.1.5.0", 5)
        self.set_value("1.1.6.0", 6)

        self.set_value("1.2.1.0", "SNMPkeyShare_example")
        self.set_value("1.2.2.0", 2)
        self.set_value("1.2.3.0", 3)

        self.set_value("1.2.3.0", 3)
        self.set_value("1.2.3.0", 3)

        self.get_value("1.2.1.0")
        self.get_value("1.2.2.0")

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
        if((type(set_value) == int and supported_type == "INTEGER")
           or (type(set_value) == str and supported_type == "OCTET STRING")):
            return True
        else:
            return False


    def set_value(self, oid, set_value):
        print("OID: ", oid)                             #!!!DEBUG
        print("Value: ", self.get_value(oid))

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

        if max_access == "read-only":
            print("OID is read-only")

        elif max_access == "read-write":
            if self.check_type(set_value, type_value):
                for key in keys[2:-1]:
                    if isinstance(mib_dict, dict) and key in mib_dict:
                        mib_dict = mib_dict[key]
                    else:
                        print("OID not found")
                        break
                print("VALUE SET")
                mib_dict[keys[-1]] = set_value  # Update the value in the MIB dictionary
            else:
                print("OID Syntax not supported")

        print("OID: ", oid)                             #!!!DEBUG
        print("Value: ", self.get_value(oid))


        

    
    def set_sudo(self, oid, value):
        pass



    def add_new_key(self, oid, value, keyID, keyValue, keyRequester, keyExpirationDate, keyExpiration):
        pass
