import sys, os, socket, threading, random, time, configparser, re
from SNMPkeySharePDU import SNMPkeySharePDU


class SNMPManager():
    def __init__(self, agentIP, snmpport, V):
        self.timeout = V #segundos
        self.p_time = {}

        self.ip = '127.0.0.3'
        self.agentIP = agentIP
        self.port = snmpport
        self.p_id_key = {}

        #self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.setIP()
        self.waitForCommand()


    def setIP(self):
        ip = input("Enter your the IP: ")
        if ip == "1":   self.ip = "127.0.0.3"
        elif ip == "2": self.ip = "127.0.0.4"
        print("IP set to: " + self.ip)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.ip, self.port))
        input("Press Enter to continue...")


    def waitForCommand(self):
        os.system('cls' if os.name == 'nt' else 'clear')
            
        print("---------------------------------------------------------------")
        print("                   Bem Vindo ao SNMPkeyShare                   ")
        print("---------------------------------------------------------------")
        print("                     Primitivas disponíveis                    ")
        print("snmpkeyshare-get(Nl,L)  [e.g. snmpkeyshare-get(1,(x,y))]")
        print("snmpkeyshare-set(Nw,W)  [e.g. snmpkeyshare-set(2,(x,y)(z,j))]")
        print("exit")
        print("---------------------------------------------------------------")
        print("                     Sugestões de comandos                     ")
        print("1. Gerar uma chave visível apenas para mim [snmpkeyshare-set(1,(1.3.3.6.0,1))]")
        print("2. Gerar uma chave e mudar a visibilidade  [snmpkeyshare-set(2,(1.3.3.6.0,1) (1.3.3.6.0,2))]")
        print("---------------------------------------------------------------")
        command = input("Introduza o comando: ")
        self.send_request(command)
    
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
            
            
            #! DEBUG
            #P = int(values[0])
            P = random.randint(0, 1000)
            Nl_Nw = int(values[0])


            pairs = re.findall(r'\((\d.\d.\d.(?:\d.)?\d),\s?(\d+)\)', command)
            tuple_list = [(x, y) for x, y in pairs]

            pdu = SNMPkeySharePDU(0, 0, [], P, Y, Nl_Nw, tuple_list, 1, [(0,0)])                    #type: ignore
            return pdu
        except:
            print("Invalid Command")
            input("Press Enter to continue...")
            self.waitForCommand()

    
    # Verify if PDU is valid (more specifically its ID P, all other fields are assumed to be valid and later verified by the agent, ignoring the invalid messages)
    def verify_pdu(self, pdu):
        P = pdu.request_id

        if P in self.p_time:
            diff_time = time.time() - self.p_time[P]
            # "aconselhável que o gestor não utilize valores para P repetidos num intervalo temporal muito maior que V segundos": self.timeout*3
            if diff_time < (self.timeout *3) :
                return False
                
            

        self.p_time[P] = time.time()
        return True


    # Send PDU to agent
    def send_request(self, command):
        if command == "exit":
            sys.exit()
        elif command == "1":
            command = "snmpkeyshare-set(1,(1.3.3.6.0,1))"
        elif command == "2":
            command = "snmpkeyshare-set(2,(1.3.3.6.0, 1) (1.3.3.6.0, 2))"
        elif command == "3":
            command = "get(3, (1.1.1.0, 3) (1.1.1.0,0) (1.3.3.2.1, 3))"
        elif command == "4":
            command = "get(3, (1.3.1.0, 3) (1.3.3.5.1, 8) (1.3.3.2.2, 3))"  
        elif command == "5":
            command = "get(1,(1.3.3.3.1,1))"

        try:
            pdu = self.build_pdu(command)
            valid_or_not = self.verify_pdu(pdu)
            if valid_or_not:
                print("Valid PDU")
            elif valid_or_not == 1:
                print(f"Invalid PDU: Wait a maximum of {self.timeout} seconds before reusing the Request ID {pdu.request_id}.\nTrying again...")  #type: ignore
                while not self.verify_pdu(pdu):
                    pdu = pdu._replace(request_id = random.randint(0, 1000))  #type: ignore
            print(pdu)
            pdu_encoded = pdu.encode()
            self.socket.sendto(pdu_encoded, (self.agentIP, self.port))

        except Exception as e:
            print("Unable to send Message:\n", e)
            input("Press Enter to continue...")
            self.waitForCommand()
        
        print("Message sent")        
        self.get_response()


    def get_response(self):
        try:
            # NOTE: "não é obrigatório que o agente responda, nem que responda num intervalo de tempo qualquer, nem que responda aos pedidos
            #       numa ordem qualquer pré-definida;" 
            #               -> por isso, se o agente não responder, o cliente não faz nada 
            #            OU -> o cliente não fica à espera de uma resposta do agente?
            message_received = False
            now = time.time()
            while time.time() < now + self.timeout:
                data, addr = self.socket.recvfrom(4096)
                if addr[0] == self.agentIP:

                    if(data):
                        dec_pdu = SNMPkeySharePDU.decode(data.decode())
                        print("Message received")
                        print(dec_pdu)
                        message_received = True
                        break
                    
                #TODO adicionar mais cenas aqui
                # se quisermos saber a key de outro manager
                #   temos que guardar todos os pedidos que fizemos e saber o tipo de cada um (get/set e oids pedido)
                #   depois ver se o id resposta é igual ao que fizemos

            if not message_received:
                raise Exception(f"Timeout. Agent did not respond within {self.timeout} seconds or at all or the message did not arrive.")
        except Exception as e:
            print("Unable to receive Message:\n", e)
                
        #if message_received and P in self.W
        #    self.p_id_key = dec_pdu.request_id

        input("Press Enter to continue...")
        self.waitForCommand()



#! Funções que dão inicio ao Manager
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
    
    