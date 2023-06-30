"""
Autor: Rui Chaves (ruichaves99@gmail.com)
Descrição: Ficheiro que representa uma MIB simplificada. Fulcral para a correta implementação das funcionalidades, tratando de guardar nos diversos objetos/instâncias as informações relativas às chaves geradas, de sistemas e de configuração.
"""

import json


class SNMPKeyShareMIB:
    def __init__(self):
        self.mib = dict()
        self.mib_system = dict()
        self.mib_config = dict()
        self.mib_data = dict()

        self.importMIB('SNMPkeyShareMIB.json')

    #! Função que importa a MIB de um ficheiro JSON e a guarda num dicionário
    def importMIB(self, file):
        self.mib = json.load(open(file))
        self.mib_system = self.mib["1"]["1"]
        self.mib_config = self.mib["1"]["2"]
        self.mib_data   = self.mib["1"]["3"]

    #! Função que traduz o OID para uma lista de chaves
    def translateOID(self, oid):
        keys = oid.split(".")
        return keys

    #! Get value
    # Client can get values from system and data groups (except keyValue if keyVisibility 0 or not same client and keyVisibility 1)
    # Admin can get values from all groups
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
            #print("OID not found")                                  
            return (oid, -2)                                                #Error 2: OID not found (noSuchName)        

        max_access = mib_dict[str(keys[-2])]["MAX-ACCESS"] #type: ignore

        if max_access == "not-accessible" and not admin:
            #print("OID not accessible")                                     
            return (oid, -6)                                                #Error 6: OID not accessible (noAccess)
        else:
            for key in keys[(2 if len(keys)==4 else 3):]:
                if isinstance(mib_dict, dict) and key in mib_dict:
                    mib_dict = mib_dict[key]
                else:
                    #print("OID not found")
                    return (oid, -2)                                        #Error 2: OID not found (noSuchName)
            return (oid, mib_dict)




    #! Função que verifica se o tipo de dados é coerente com o suportado
    def check_type(self, set_value, supported_type):
        if (type(set_value) == int and supported_type == "INTEGER") or (type(set_value) == str and supported_type == "OCTET STRING"):
            return True
        else:
            return False

    #! Set value
    # Client can only set values to its keyVisibility instance(s)
    # Can try for other groups but will get error (including other instances of keys Table)
    # Admin can set values to all groups
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
            #print("OID not found")
            return (oid, -2)                                                #Error 2: OID not found (noSuchName)

        max_access = mib_dict[str(keys[-2])]["MAX-ACCESS"] #type: ignore
        type_value = mib_dict[str(keys[-2])]["SYNTAX"]     #type: ignore

        if max_access == "read-only" and not admin:
            #print("OID is read-only")
            return (oid, -4)                                                #Error 4: OID is read-only (readOnly)
        elif max_access == "not-accessible" and not admin:
            #print("OID not accessible")                                     
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
                    #print(f"  {self.get_value(oid, admin=True)}")
                    return (oid, self.get_value(oid, True)[1]) #type: ignore
            else:
                #print("OID Syntax not supported")
                return (oid, -3)                                            #Error 3: Value type not supported (badValue)
        









 






