import threading, sys, time, random, os, socket, json, subprocess, psutil


MIB = dict()
mibVals = []


class RequestHandler(threading.Thread):
    def __init__(self, cstring, targetproxy):
        threading.Thread.__init__(self)
        self.port = 161
        self.ip = '127.0.0.2'
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.ip, self.port))
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.targetProxy = targetproxy
        self.cstring = cstring
        self.cpuInfo = ""
        self.os = ""
        self.cpuUsage = ""
        self.availableRam = ""
        self.availableStorage = ""
        self.upTime = ""
        self.hostname = "snmpAgent"
    
    
    def processRequest(self,data, addr):
        
        if data.split(' ')[1] == "get-request" :
            print("get-request....")
            oid = data.split(' ')[2]
            print("OID: " + oid)
            ret = self.getRequest(oid)
                
        elif data.split(' ')[1] == "get-bulk":
            code = data.split(' ')[2]
            ret = self.getBulkRequest(code)
                
        elif data.split(' ')[1] == "set-request":
            code = data.split(' ')[2]
            typeR = data.split(' ')[3]
            value = data.split(' ')[4]
            ret = self.setRequest(code, typeR, value)
            
        else :
            ret = "Invalid SNMP Request"    
        return ret


    def getInfo(self, code):
        
        if code == "1":
            self.cpuInfo = subprocess.check_output(['grep', '-m', '1', 'model name', '/proc/cpuinfo']).decode().split(':')[1].strip()
        elif code == "2":
            self.os = subprocess.check_output(['grep', '-m', '1', 'PRETTY_NAME', '/etc/os-release']).decode().split('=')[1].strip()
        elif code == "3":
            self.cpuUsage = "CPU Usage: " + str(psutil.cpu_percent()) + "%"
        elif code == "4":
            self.availableRam = "RAM Usage: " + str(psutil.virtual_memory().percent) + "%"
        elif code == "5":
            self.availableStorage = "Storage Usage: " + str(psutil.disk_usage('/').percent) + "%"
        elif code == "6":
            self.upTime = subprocess.check_output(['uptime', '-p']).decode().strip()
        elif code == "7":
            return self.hostname
        elif code == "0":
            self.cpuInfo = subprocess.check_output(['grep', '-m', '1', 'model name', '/proc/cpuinfo']).decode().split(':')[1].strip()
            self.os = subprocess.check_output(['grep', '-m', '1', 'PRETTY_NAME', '/etc/os-release']).decode().split('=')[1].strip() 
            self.cpuUsage = "CPU Usage: " + str(psutil.cpu_percent()) + "%"
            self.availableRam = "RAM Usage: " + str(psutil.virtual_memory().percent) + "%"
            self.availableStorage = "Storage Usage: " + str(psutil.disk_usage('/').percent) + "%"
            self.upTime = subprocess.check_output(['uptime', '-p']).decode().strip()
        else:
            return "Invalid SNMP Request"
        
    
    
    
    def getBulkRequest(self, oid):
        
        response = ""
        try:
            if oid.split('.')[0] == "HWINFO":
                if oid.split('.')[1] == "0":
                    self.getInfo("0")
                    response = "CPU INFO: " + self.cpuInfo + "\n" + "OS: " + self.os + "\n" + "CPU Usage: " + self.cpuUsage + "\n" + "Available RAM: " + self.availableRam + "\n" + "Available Storage: " + self.availableStorage + "\n" + "Up Time: " + self.upTime + "\n" + "Hostname: " + self.hostname
        except Exception as e:
            response = "Invalid SNMP Request"
        return response
    
    def getRequest(self, oid):
        response = ""
        try:
            print("A processar get request com o OID: " + oid)
            if oid.split('.')[0] == "HWINFO":
                if oid.split('.')[1] == "1":
                    response = self.getInfo("1")
                    response = self.cpuInfo
                
                    
                elif oid.split('.')[1] == "2":
                    response = self.getInfo("2")
                    response = self.os
                    
                elif oid.split('.')[1] == "3":
                    response = self.getInfo("3")
                    response = self.cpuUsage
                    
                elif oid.split('.')[1] == "4":
                    response = self.getInfo("4")
                    response = self.availableRam
                    
                elif oid.split('.')[1] == "5":
                    response = self.getInfo("5")
                    response = self.availableStorage
                    
                elif oid.split('.')[1] == "6":
                    response = self.getInfo("6")
                    response = self.upTimes
                
                elif oid.split('.')[1] == "7":
                    return self.hostname
        except Exception as e:
            print(e)
            response = "Invalid SNMP Request"
        return response
    
    def setRequest(self, code, typeR, value):
        print("code: " + code + " typeR: " + typeR + " value: " + value)
        print("TRYING TO SET")
        response = ""
        if code.split('.')[0] == "HWINFO":
            if code.split('.')[1] == "7" and typeR == "s":
                self.hostname = value
                response = "Hostname changed to " + self.hostname
                print("Response: " + response)
            else:
                response = "access denied! or wrong type!"
        print(response)
        return response


    def run(self):
        try:
            while True:        
                data, addr = self.socket.recvfrom(4096)
                if addr[0] == self.targetProxy and addr[1] == self.port:
                    data = data.decode()
                    print(data)
                    if data.split(' ')[0] == self.cstring:
                        response = self.processRequest(data, addr[0])
                        self.socket.sendto(response.encode(), addr)
                else:
                    pass
                    
                
        except Exception as e:
            print(e)
            sys.exit(1)




class trapHAndler(threading.Thread):
    def __init__(self, targetProxy):
        threading.Thread.__init__(self)
        self.port = 162
        self.ip = '127.0.0.2'
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.ip, self.port))
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.targetProxy = targetProxy
        
    def run(self):
        
        while True:
            #generate a number between 0 and 3
            r = random.randint(0,2)
            traps = ["cpu usage spike!", "ram usage spike!", "storage usage spike!"]
            time.sleep(10)
            msg = "trap" + " " + str(traps[r])
            self.socket.sendto(msg.encode(), (self.targetProxy, self.port))
            print("trap enviada para " + self.targetProxy)
            data, addr = self.socket.recvfrom(4096)
            if data.decode() == 'trap-ack':
                print("Trap ack received")
            else:
                pass




def main():
    global MIB
    print("A Inicializar agente SNMP...")
    #clear terminal
    os.system('cls' if os.name == 'nt' else 'clear')
    MIB = json.load(open('MIBAgent.json'))
    cstring = "gsr"
    print("Community String: " + cstring)
    
    targetProxy = "127.0.0.3"
    rH = RequestHandler(cstring, targetProxy)
    rH.start()
    time.sleep(5)
    tH = trapHAndler(targetProxy)
    tH.start()
    
    
if __name__ == "__main__":
    main()

    
    
    
    
    