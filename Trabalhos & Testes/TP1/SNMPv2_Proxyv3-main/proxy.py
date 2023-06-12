import socket, json, base64, pyotp, rsa, threading, os


import pyotp



class RequestHandler():
    def __init__(self, cstring):
        self.port = 161
        self.ip = '127.0.0.3'
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.ip, self.port))
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.agentIp = "127.0.0.2"
        self.MIB = dict()
        self.clients = dict()
        self.clientsIP = []
        self.clientsUsers = []
        self.idCounter = 1
        self.cstring = cstring
        self.privateKey = ""
        self.publicKey = ""
        self.run()
        
    def populateMIBsAndCfg(self):
        self.MIB = json.load(open("MIBProxy.json"))
        self.clients = json.load(open("authorizedUsers.json"))
        
    def encrypt(self, message):
        msg = message.encode()  
        encrypted = rsa.encrypt(msg, self.publicKey)
        return encrypted
    
    def decrypt(self, message):
        decoded_msg = rsa.decrypt(message, self.privateKey)
        return decoded_msg.decode()
        
            
    def getKeys(self):
        with open("private_key.pem", "rb") as f:
                self.privateKey = rsa.PrivateKey.load_pkcs1(f.read())
        with open("public_key.pem", "rb") as f:
                self.publicKey = rsa.PublicKey.load_pkcs1(f.read())    
    

    def getUsername(self, addr):
        """
        search the self.clients dictionary which has the following format
        {
            "adminTeste":{
            "username":"adminTeste",
            "password":"password",
            "status": "0",
            "IP": ""
            },
            ...
        }
        and return the username associated with the IP addr
        """
        for key in self.clients:
            if self.clients[key]["IP"] == addr:
                return key
        return None
        
        
    def processRequest(self, data, addr):
        try:
            idOperTmp = self.idCounter
            typeOperTmp = data.split(' ')[0]
            typeOp = typeOperTmp
            setValueTypeTmp = ""
            setValueTmp = ""
            if typeOperTmp == "get-next":
                typeOperTmp = 0
            elif typeOperTmp == "get-bulk":
                typeOperTmp = 1
            elif typeOperTmp == "set-request":
                setValueTypeTmp = data.split(' ')[2]
                setValueTmp = data.split(' ')[3]
                typeOperTmp = 2
                
            idSourceTmp = str(self.getUsername(addr[0]))
            idDestinationTmp = str(self.agentIp)
            oidArgTmp = data.split(' ')[1]
            valueArgTmp = " "
            typeArgTmp = "STRING"
            sizeArgTmp = ""          
            responseTmp = self.requestToAgent(oidArgTmp, typeOp, setValueTypeTmp, setValueTmp)
            if responseTmp == "Invalid SNMP Request":
                #Trigger the exception
                raise Exception
            valueArgTmp = str(responseTmp)
            sizeArgTmp = len(valueArgTmp)
            
            idOper = str(idOperTmp)
            typeOper = (typeOperTmp)
            idSource = str(idSourceTmp)
            idDestination = str(idDestinationTmp)
            oidArg = str(oidArgTmp)
            valueArg = str(valueArgTmp)
            typeArg = str(typeArgTmp)
            sizeArg = str(sizeArgTmp)
            response = responseTmp
            valueArg = str(valueArgTmp)
            sizeArgTmp = str(sizeArg)
            setValueType = str(setValueTypeTmp)
            setValue = str(setValueTmp)
            
            print("idOper: " + str(idOper))
            print("typeOper: " + str(typeOper))
            print("idSource: " + str(idSource))
            print("idDestination: " + str(idDestination))
            print("oidArg: " + str(oidArg))
            print("valueArg: " + str(valueArg))
            print("typeArg: " + str(typeArg))
            print("sizeArg: " + str(sizeArg))
            print("setValueType: " + str(setValueType))
            print("setValue: " + str(setValue))
            print("----------------------------------------------------")
            
            
            self.MIB["Lines"]["1"][self.idCounter] = idOper
            self.MIB["Lines"]["2"][self.idCounter] = typeOper
            self.MIB["Lines"]["3"][self.idCounter] = idSource
            self.MIB["Lines"]["4"][self.idCounter] = idDestination
            self.MIB["Lines"]["5"][self.idCounter] = oidArg
            self.MIB["Lines"]["6"][self.idCounter] = valueArg
            self.MIB["Lines"]["7"][self.idCounter] = typeArg
            self.MIB["Lines"]["8"][self.idCounter] = sizeArg
            self.MIB["Lines"]["9"][self.idCounter] = setValueType
            self.MIB["Lines"]["10"][self.idCounter] = setValue
            json.dump(self.MIB, open("debug/MIBProxy.json", "w"))
            response = response
            self.responseToManager(response, addr[0])
            self.idCounter += 1 
        except Exception as e:
            print(e)
            response = "Invalid Syntax!"
            self.responseToManager(response, addr[0])
    
    
    def requestToAgent(self, oid, typeOper, setValueType, setValue):
        if typeOper == "set-request":
            request = self.cstring + " " + str(typeOper) + " " + str(oid) + " " + str(setValueType) + " " + str(setValue)
        else:
            request = self.cstring + " " + str(typeOper) + " " + str(oid) 
        print(request)
        self.socket.sendto(request.encode(), (self.agentIp, self.port))
        while True:
            data,addr = self.socket.recvfrom(4096)
            if addr[0] == self.agentIp:
                agentResponse = data.decode()
                break
        return agentResponse
        
    def responseToManager(self, response, addr):
        print("Response to Manager: " + response)
        response = self.encrypt(response)
        self.socket.sendto(response, (addr, self.port))
        while True:
            data, addr = self.socket.recvfrom(4096)
            data = self.decrypt(data)
            if data == "ack":
                break
        
    def run(self):
        self.populateMIBsAndCfg()
        self.getKeys()
        while True:
            data, addr = self.socket.recvfrom(4096)
            data =  self.decrypt(data)
            if addr[0] not in self.clientsIP:
                    if data.split(' ')[0] == "login":
                        self.socket.sendto(self.encrypt("Username?"), addr)
                    elif data.split(' ')[0] == "username":
                        username = data.split(' ')[1]
                        self.socket.sendto(self.encrypt("Password?"), addr)
                    elif data.split(' ')[0] == "password":
                        password = data.split(' ')[1]
                        if self.clients[username]["password"] == password:
                            print("Login Success from " + addr[0] + " with username " + username)
                            self.clientsIP.append(addr[0])
                            self.socket.sendto(self.encrypt("2FA?"), addr)
                            data,addr = self.socket.recvfrom(4096)
                            data = self.decrypt(data)
                            totp = pyotp.TOTP(base64.b32encode((username+password).encode()))
                            if data == totp.now():
                                self.socket.sendto(self.encrypt('login-ack'),addr)
                            tHandler = Traps(addr[0], self.privateKey, self.publicKey, self.agentIp)
                            tHandler.start()
            else:
                self.socket.sendto(self.encrypt("ack"), addr)
                print("Pedido recebido: " + data)
                self.processRequest(data, addr) 

class Traps(threading.Thread):
    def __init__(self, managerIp, privateKey, publicKey, agentIp):
        threading.Thread.__init__(self)
        self.port = 162
        self.managerIP = managerIp
        self.ip = '127.0.0.3'
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.ip, self.port))
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.privateKey = privateKey
        self.publicKey = publicKey
        self.agentIp = agentIp


         
    def encrypt(self, message):
        msg = message.encode()
        encrypted = rsa.encrypt(msg, self.publicKey)
        return encrypted
    
    def decrypt(self, message):
        decoded_msg = rsa.decrypt(message, self.privateKey)
        return decoded_msg.decode()



    def transmitTrap(self, msg):
        msg = self.encrypt(msg)
        self.socket.sendto(msg, (self.managerIP, self.port))
        while True:
            data, addr = self.socket.recvfrom(4096)
            data = self.decrypt(data)
            if data == "trap-ack":
                break

    def run(self):
        
        while True:
            data, addr = self.socket.recvfrom(4096)
            if addr[0] == self.agentIp:
                if data.decode().split(' ')[0] == "trap":
                    self.socket.sendto("trap-ack".encode(), addr)
                    self.transmitTrap(data.decode())
                    
                else: 
                    pass


def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("Bem-Vindo ao SNMP Proxy")
    requestHandler = RequestHandler("gsr")
    
    
if __name__ == "__main__":
    main()
