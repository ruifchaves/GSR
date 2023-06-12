import sys,os,socket,pyotp, base64, rsa, threading


class SNMPManager():
    def __init__(self):
        self.port = 161
        self.ip = '127.0.0.4'
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.ip, self.port))
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.proxyIP = ""
        self.login()
        self.username = ""
        self.privateKey = ""
        self.publicKey = ""
        
    #method to encrypt a message before sending it to the proxy
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
        
        
    def login(self):
        self.getKeys()
        #clear terminal
        os.system('cls' if os.name == 'nt' else 'clear')
        print("Bem Vindo ao Manager SNMP")
        #proxyIP = input("Introduza o IP do Proxy:")
        proxyIP = "127.0.0.3"
        self.proxyIP = proxyIP
        input("Pressione Enter para proceder à autenticação...")
        user = input("Introduza o Username:\n")
        self.username = user
        os.system('cls' if os.name == 'nt' else 'clear')
        msg =  self.encrypt('login')
        self.socket.sendto(msg, (proxyIP, self.port))
        while True:
            data,addr = self.socket.recvfrom(4096)
            if addr[0] == proxyIP:
                data = self.decrypt(data) 
                if data == "Username?":
                    msg = "username " + user
                    os.system('cls' if os.name == 'nt' else 'clear')
                    msg = self.encrypt(msg)
                    self.socket.sendto(msg, (proxyIP, self.port))
                elif data == "Password?":
                    password = input("Introduza a Password:\n")
                    os.system('cls' if os.name == 'nt' else 'clear')
                    msg = "password " + password
                    msg = self.encrypt(msg)
                    self.socket.sendto(msg, (proxyIP, self.port))
                elif data == "2FA?": 
                     
                    secret = str(user + password)
                    print(secret) 
                    totp = pyotp.TOTP(base64.b32encode(secret.encode()))
                    #print("Current 2FA code: " + str(totp.now()))
                    auth = totp.now()
                    msg = self.encrypt(auth)
                    self.socket.sendto(msg, (proxyIP, self.port))
                elif data == "login-ack":
                    print("Autenticação concluída\n")
                    break
        tH = Traps(self.privateKey, self.publicKey, self.proxyIP)
        tH.start()
        self.waitForCommand()
        
    def waitForCommand(self):
        #clear terminal
        os.system('cls' if os.name == 'nt' else 'clear')
        print("----------------------------------------------------")
        print("Comandos disponíveis:")
        print("get-request <OID> \n get-bulk <OID> \n set-request <OID> <type> <value>\n exit")
        print("----------------------------------------------------")
        command = input("Introduza o comando:")
        self.request(command)
    
    def request(self, command):
        
        if command == "exit":
            sys.exit()
        msg = self.encrypt(command)
        self.socket.sendto(msg, (self.proxyIP, self.port))
        while True:
            data,addr = self.socket.recvfrom(4096)
            if addr[0] == self.proxyIP:
                data = self.decrypt(data)
                if data == "ack":
                    break
                else:
                    print(data)
                    break
        while True:
            data, addr = self.socket.recvfrom(4096)
            response = self.decrypt(data)
            msg = "ack"
            msg = self.encrypt(msg)
            self.socket.sendto(msg, addr)
            break
        print(response)
        input("Press Enter to continue...")
        self.waitForCommand()
     
     
class Traps(threading.Thread):
    def __init__(self, privateKey, publicKey, proxyIp):
        threading.Thread.__init__(self)
        self.port = 162
        self.ip = '127.0.0.4'
        self.proxyIp = proxyIp
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.ip, self.port))
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.privateKey = privateKey
        self.publicKey = publicKey
        
    
    def encrypt(self, message):
        msg = message.encode()
        encrypted = rsa.encrypt(msg, self.publicKey)
        return encrypted
    
    def decrypt(self, message):
        decoded_msg = rsa.decrypt(message, self.privateKey)
        return decoded_msg.decode()
    
    def run(self):
        print("Á escuta de traps...")
        while True:
            data, addr = self.socket.recvfrom(4096)
            if addr[0] == self.proxyIp:
                try:
                    data = self.decrypt(data)
                    print('\n----------------------------------------------------')
                    print(data + "!!!")
                    print('----------------------------------------------------')
                    self.socket.sendto(self.encrypt("trap-ack"), (self.proxyIp, self.port))
                except Exception as e:
                    print(e)
                    pass
            else:
                print(data)
                        
     
        
def main():
    sm = SNMPManager()
    
    
    
    
    
if __name__ == "__main__":
    main()
    #sm = SNMPManager()
    #sm.login()
    #sm.waitForCommand()
    #sm.request("get
    
    
    