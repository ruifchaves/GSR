import sys, os, socket, threading, random, time
from SNMPkeySharePDU import SNMPkeySharePDU


class SNMPManager():
    def __init__(self):
        self.timeout = 30 #segundos
        self.p_time = {}

        self.port = 162
        self.ip = '127.0.0.3'
        self.agentIP = "127.0.0.2"
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.ip, self.port))
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.waitForCommand(0)
        
        
    def waitForCommand(self, err):
        os.system('cls' if os.name == 'nt' else 'clear')
        if(err == 1): print("Error: Comando inválido\n")
            
        print("---------------------------------------------------------------")
        print("                   Bem Vindo ao SNMPkeyShare                   ")
        print("---------------------------------------------------------------")
        print("                     Primitivas disponíveis                    ")
        print("snmpkeyshare-get(P,Nl,L)  [e.g. snmpkeyshare-get(1,1,(x,y))]")
        print("snmpkeyshare-set(P,Nw,W)  [e.g. snmpkeyshare-set(55,2,(x,y)(z,j))]")
        print("exit")
        print("---------------------------------------------------------------")
        command = input("Introduza o comando:")
        self.request(command)
    

    def build_pdu(self, command):
        try:
            if("get" in command):
                Y = 1
            elif("set" in command):
                Y = 2

            # Parse do comando
            substring = command[command.find("(") + 1: command.find(")")]
            values = substring.split(",")
            P = int(values[0])
            snd = int(values[1])
            thr = values[2] #TODO dar parse aos pares

            print(thr) #!!DEBUG

            pdu = SNMPkeySharePDU(0, 0, [], P, Y, snd, thr, 0, [])
            return pdu
        except:
            self.waitForCommand(1)


    def verify_pdu(self, pdu):
        P = SNMPkeySharePDU(pdu).request_id

        if(P in self.p_time):
            diff_time = time.time() - self.p_time[P]
            if(diff_time > self.timeout):
                return False

        self.p_time[P] = time.time()

    def request(self, command):
        if command == "exit":
            sys.exit()

        pdu = self.build_pdu(command)
        if(self.verify_pdu(pdu)):
            print("PDU válido")
        else: 
            print("PDU inválido...")
            time.sleep(2)
            self.waitForCommand(1)
        self.socket.sendto(pdu, (self.agentIP, self.port))
        print("Mensagem enviada")

        input("Press Enter to continue...")
        self.waitForCommand(0)
     
        
def main():
    manager = SNMPManager()

    
if __name__ == "__main__":
    main()
    
    