import sys, os, socket, threading, random, time, configparser, re
from SNMPkeySharePDU import SNMPkeySharePDU


class SNMPManager():
    def __init__(self, agentIP, snmpport, V):
        self.timeout = V #segundos
        self.p_time = {}

        self.ip = '127.0.0.3'
        self.agentIP = agentIP
        self.port = snmpport

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.ip, self.port))
        #self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.waitForCommand()
        
        
    def waitForCommand(self):
        os.system('cls' if os.name == 'nt' else 'clear')
            
        print("---------------------------------------------------------------")
        print("                   Bem Vindo ao SNMPkeyShare                   ")
        print("---------------------------------------------------------------")
        print("                     Primitivas disponíveis                    ")
        print("snmpkeyshare-get(P,Nl,L)  [e.g. snmpkeyshare-get(1,1,(x,y))]")
        print("snmpkeyshare-set(P,Nw,W)  [e.g. snmpkeyshare-set(55,2,(x,y)(z,j))]")
        print("exit")
        print("---------------------------------------------------------------")
        print("                     Sugestões de comandos                     ")
        print("1. Gerar uma chave visível apenas para mim [snmpkeyshare-set(P,1,(1.3.3.6.0,1))]")
        print("2. Gerar uma chave e mudar a visibilidade  [snmpkeyshare-set(P,2,(1.3.3.6.0,1) (1.3.3.6.0,2))]")
        print("---------------------------------------------------------------")
        command = input("Introduza o comando: ")
        self.request(command)
    
    # Build PDU from specified command and its parameters
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


            pairs = re.findall(r'\((\d.\d.\d.(?:\d.)?\d),\s?(\d+)\)', command)
            tuple_list = [(x, y) for x, y in pairs]

            pdu = SNMPkeySharePDU(0, 0, [], P, Y, snd, tuple_list, 1, [(0,0)])                    #type: ignore
            return pdu
        except:
            print("Invalid Command")
            input("Press Enter to continue...")
            self.waitForCommand()


    # Check if PDU Request ID is valid (not repeated within timeout period)
    def verify_pdu(self, pdu):
        P = pdu.request_id

        if P in self.p_time:
            diff_time = time.time() - self.p_time[P]
            if diff_time < self.timeout:
                return 1
        
        print("")
        if pdu.num_instances != len(pdu.instances_values):
            return 2

        self.p_time[P] = time.time()
        return True

    # Send PDU to agent
    def request(self, command):
        if command == "exit":
            sys.exit()
        elif command == "1":
            command = "snmpkeyshare-set(1,1,(1.3.3.6.0,1))"
        elif command == "2":
            command = "snmpkeyshare-set(2,2,(1.3.3.6.0,1) (1.3.3.6.0,2))"        
        elif command == "3":
            command = "snmpkeyshare-set(3,1,(1.3.3.6.0,2))"
        elif command == "4":
            command = "get(4,1,(1.3.3.3.1,3))"        
        elif command == "5":
            command = "get(5,1,(1.3.3.3.1,1))"

        try:
            pdu = self.build_pdu(command)
            valid_or_not = self.verify_pdu(pdu)
            if valid_or_not:
                print("Valid PDU")
            elif valid_or_not == 1:
                raise Exception(f"Invalid PDU: Wait a maximum of {self.timeout} seconds before reusing the Request ID {pdu.request_id}.")  #type: ignore
            elif valid_or_not == 2:
                raise Exception(f"Invalid PDU: Number of elements of instances list {pdu.num_instances} is not the same as the size of the list {len(pdu.num_instances)}.")  #type: ignore

            print(pdu)
            pdu_encoded = pdu.encode()
            self.socket.sendto(pdu_encoded, (self.agentIP, self.port))
        except Exception as e:
            print("Unable to send Message:\n", e)
            input("Press Enter to continue...")
            self.waitForCommand()
        
        print("Message sent")
        try:
            now = time.time()
            while time.time() < now + 2:
                data, addr = self.socket.recvfrom(1024)
                print(data)
                dec_pdu = SNMPkeySharePDU.decode(data.decode())

                if(data):
                    print("Message received")
                    print(dec_pdu)
                    break
                #TODO adicionar mais cenas aqui
        except Exception as e:
            print("Unable to receive Message:\n", e)
                


        input("Press Enter to continue...")
        self.waitForCommand()
     




def read_configuration_file(config_file):

    config = configparser.ConfigParser()
    config.read(config_file)
    agentIP = config['Agent']['ip']
    snmport = int(config['Agent']['snmpport'])
    V = int(config['Other']['V'])
    return [agentIP, snmport, V]


def main():
    config_values = read_configuration_file("config.ini")
    try:        
        manager = SNMPManager(config_values[0], config_values[1], config_values[2])
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
    
if __name__ == "__main__":
    main()
    
    