import datetime
import json

MIB

class SNMPKeyShareMIB:
    def __init__(self):
        current_datetime = datetime.now()

        MIB = json.load(open('MIBAgent.json'))


    # function to import json file

    # function to update initial values

    # function to translate oid to value
    # OID: "1.2.3.4.2.2.0"
    def translateOID(self, oid = "1.2.3.2.3"):
        keys = oid.split(".")

        for key in keys:
            if isinstance(value, dict) and key in value:  #value is a dict and key is in the dict
                value = value[key]
            else:
                value = None
                break
            #TODO erros explicitos
