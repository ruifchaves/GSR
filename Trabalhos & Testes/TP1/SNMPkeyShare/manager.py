import sys, os, socket, threading, random, time, configparser, re
from SNMPkeySharePDU import SNMPkeySharePDU
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, hmac


class SNMPManager():
    def __init__(self, agentIP, snmpport, V, KEY):
        self.timeout = V #segundos
        self.p_time = {}

        self.ip = '127.0.0.3'
        self.agentIP = agentIP
        self.port = snmpport
        self.p_id_key = {}
        self.key = KEY.encode()
        self.cypher = Fernet(self.key)

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
            
        print("---------------------------------------------------------------------------------------------------------------")
        print("                                            Bem Vindo ao SNMPkeyShare                                          ")
        print("---------------------------------------------------------------------------------------------------------------")
        print("                                              Primitivas disponíveis                                           ")
        print("    snmpkeyshare-get(Nl,L)  [e.g. snmpkeyshare-get(1,(x,y))]                                                   ")
        print("    snmpkeyshare-set(Nw,W)  [e.g. snmpkeyshare-set(2,(x,y)(z,j))]                                              ")
        print("    exit                                                                                                       ")                                                        
        print("---------------------------------------------------------------------------------------------------------------")
        print("                                              Sugestões de comandos                                            ")
        print("1.  Gerar 1 chave visível apenas para mim:                set(1, (1.3.3.6.0, 1))                               ")
        print("2.  Gerar 1 chave visível visivel para todos:             set(1, (1.3.3.6.0, 2))                               ")
        print("3.  Gerar 1 chave e alterar visibilidade: (key 1)         set(2, (1.3.3.6.0, 1) (1.3.3.6.1, 2))                ")
        print("4.  Gerar 2 chaves:                                       set(2, (1.3.3.6.0, 1) (1.3.3.6.0, 2))                ")
        print("5.  Gerar 1 chave invisível:                              set(1, (1.3.3.6.0, 0))                               ")
        print("6.  Alterar 1 valor de system e 1 de config:              set(2, (1.1.1.0, 3278) (1.2.1.0, 2187))              ")
        print("7.  Obter 1 valor de system:                              get(1, (1.1.2.0, 0))                                 ")
        print("8.  Obter 3 valores de system:                            get(1, (1.1.1.0, 3))                                 ")
        print("9.  Obter 10 valores de system:                           get(1, (1.1.1.0, 10))                                ")
        print("10. Obter 1 valor de config:                              get(1, (1.2.1.0, 0))                                 ")
        print("11. Obter 10 valores de config:                           get(1, (1.2.1.0, 10))                                ")
        print("12. Obter 10 valores de config e 10 de system:            get(2, (1.2.1.0, 10) (1.1.1.0, 10))                  ")
        print("13. Obter todos os valores do grupo data:                 get(1, (1.3.1.0, 500))                               ")
        print("14. Obter 1 valor de chave (key 1):                       get(1, (1.3.3.3.1, 0))                               ")
        print("15. Obter 1 valor de chave (ñ existente):                 get(1, (1.3.3.3.0, 0))                               ")
        print("16. Obter 10 valores de chave (após ñ existente):         get(1, (1.3.3.6.0, 10))                              ")
        print("17. Obter 10 valores de chave (após existente):           get(1, (1.3.3.4.1, 10))                              ")
        print("18. Obter todos os valores da MIB:                        get(3, (1.1.1.0, 10) (1.2.1.0, 10) (1.3.1.0, 500))")
        print("---------------------------------------------------------------------------------------------------------------")
        command = input("Introduza o comando: ")
        self.send_request(command)
    

    #! Funcao que calcula o MAC (Message Authentication Code) de uma mensagem
    def calculate_authentication_code(self, P):
        id = str(P).encode()  # Converte o identificador do PDU para bytes

        hmac_alg = hmac.HMAC(self.key, hashes.SHA256())
        hmac_alg.update(id)
        authentication_code = hmac_alg.finalize()

        return str(authentication_code)[2:-1]


    #! Funcao que constroi um PDU a partir de um comando
    def build_pdu(self, command):
        try:
            if "get" in command:
                Y = 1
            elif "set" in command:
                Y = 2

            # Parse do comando
            substring = command[command.find("(") + 1: command.find(")")]
            values = substring.split(",")
            
            P = random.randint(0, 1000)
            Nl_Nw = int(values[0])


            pairs = re.findall(r'\((\d.\d.\d.(?:\d.)?\d),\s?(\d+)\)', command)
            tuple_list = [(x, y) for x, y in pairs]

            auth_code = [self.calculate_authentication_code(P)]

            pdu = SNMPkeySharePDU(1, len(auth_code), auth_code, P, Y, Nl_Nw, tuple_list, 1, [(0,0)])                    #type: ignore
            return pdu
        except:
            print("Invalid Command")
            input("Press Enter to continue...")
            self.waitForCommand()

    
    #! Funcao que verifica se o ID P do PDU é válido
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


    #! Funcao que envia um PDU para o gestor
    def send_request(self, command):
        if command == "exit":
            sys.exit()
        elif command == "1":  command = "snmpkeyshare-set(1, (1.3.3.6.0, 1))"
        elif command == "2":  command = "snmpkeyshare-set(1, (1.3.3.6.0, 2))"
        elif command == "3":  command = "snmpkeyshare-set(2, (1.3.3.6.0, 1) (1.3.3.6.1, 2))"
        elif command == "4":  command = "snmpkeyshare-set(2, (1.3.3.6.0, 1) (1.3.3.6.0, 2))"
        elif command == "5":  command = "snmpkeyshare-set(1, (1.3.3.6.0, 0))"
        elif command == "6":  command = "snmpkeyshare-set(2, (1.1.1.0, 3278) (1.2.1.0, 2187))"
        elif command == "7":  command = "snmpkeyshare-get(1, (1.1.2.0, 0))"
        elif command == "8":  command = "snmpkeyshare-get(1, (1.1.1.0, 3))"
        elif command == "9":  command = "snmpkeyshare-get(1, (1.1.1.0, 10))"
        elif command == "10":  command = "snmpkeyshare-get(1, (1.2.1.0, 0))"
        elif command == "11":  command = "snmpkeyshare-get(1, (1.2.1.0, 10))"
        elif command == "12":  command = "snmpkeyshare-get(2, (1.2.1.0, 10) (1.1.1.0, 10))"
        elif command == "13":  command = "snmpkeyshare-get(1, (1.3.1.0, 500))"
        elif command == "14":  command = "snmpkeyshare-get(1, (1.3.3.3.1, 0))"
        elif command == "15":  command = "snmpkeyshare-get(1, (1.3.3.3.0, 0))"
        elif command == "16":  command = "snmpkeyshare-get(1, (1.3.3.6.0, 10))"
        elif command == "17":  command = "snmpkeyshare-get(1, (1.3.3.4.1, 10))"
        elif command == "18":  command = "snmpkeyshare-get(3, (1.1.1.0, 10) (1.2.1.0, 10) (1.3.1.0, 500))"

        try:
            pdu = self.build_pdu(command)
            valid_or_not = self.verify_pdu(pdu)
            if valid_or_not:
                print("Valid PDU")
            elif valid_or_not == 1:
                print(f"Invalid PDU: Wait a maximum of {self.timeout} seconds before reusing the Request ID {pdu.request_id}.\nTrying again...")  #type: ignore
                while not self.verify_pdu(pdu):
                    pdu = pdu._replace(request_id = random.randint(0, 1000))  #type: ignore
                print
            print(pdu)
            pdu_encoded = pdu.encode()
            encrypted_pdu = self.cypher.encrypt(pdu_encoded)
            self.socket.sendto(encrypted_pdu, (self.agentIP, self.port))

        except Exception as e:
            print("Unable to send Message:\n", e)
            input("Press Enter to continue...")
            self.waitForCommand()
        
        print("Message sent")        
        self.get_response()


    #! Funcao que verifica se a mensagem recebida é autêntica
    def verify_authentication(self, pdu):
        if pdu.security_model == 1:
            auth_code_received = pdu.security_params_list[0]
            auth_code_calculated = self.calculate_authentication_code(pdu.request_id)

            auth_code_calculated = auth_code_calculated
            if auth_code_received == auth_code_calculated:
                # A mensagem é autêntica, continue com o processamento
                return True
            else:
                # A mensagem não é autêntica, trate o caso adequadamente (por exemplo, rejeite a mensagem)
                return False

    #! Funcao que recebe um PDU do gestor
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
                        print("Message received")
                        decrypted_data = self.cypher.decrypt(data)
                        dec_pdu = SNMPkeySharePDU.decode(decrypted_data.decode())
                        if self.verify_authentication(dec_pdu):
                            print(dec_pdu)
                            message_received = True
                            break

            if not message_received:
                raise Exception(f"Timeout. Agent did not respond within {self.timeout} seconds or at all or the message did not arrive.")
        except Exception as e:
            print("Unable to receive Message:\n", e)
                

        input("Press Enter to continue...")
        self.waitForCommand()



#! Funções que dão inicio ao Manager
def read_configuration_file(config_file):
    config = configparser.ConfigParser()
    config.read(config_file)
    agentIP = config['Agent']['ip']
    snmport = int(config['Agent']['snmpport'])
    V = int(config['Other']['V'])
    KEY = str(config['Other']['KEY'])
    return agentIP, snmport, V, KEY


def main():
    agentIP, snmport, V, KEY = read_configuration_file("config.ini")
    try:        
        manager = SNMPManager(agentIP, snmport, V, KEY)
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
    

if __name__ == "__main__":
    main()
    
    