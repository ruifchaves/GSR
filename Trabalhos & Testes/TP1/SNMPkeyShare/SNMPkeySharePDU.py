# 1. S - Identificação do modelo de segurança – Número inteiro que identificará quais os mecanismos
#       de segurança a utilizar; se for igual a zero então não se aplicam mecanismos de segurança (neste
#       trabalho o único valor de S válido é zero);
# 2. Ns - Número de parâmetros necessários à implementação dos mecanismos de segurança – Se S
#       for igual a zero então NS também é obrigatoriamente igual a zero;
# 3. Q - Lista dos parâmetros necessários à implementação dos mecanismos de segurança – O tipo
#       de parâmetros depende do modelo de segurança; se S e NS forem iguais a zero, então Q é uma
#       lista vazia;
# 4. P - Identificação do pedido – Número inteiro (ver explicação das primitivas);
# 5. Y - Identificação do tipo de primitiva – Um número inteiro que identifica um dos três tipos de
#       primitivas possíveis (0 = response, 1 = get, 2 = set);
# 6. Nl ou Nw - Número de elementos da lista de instâncias e valores associados – Número inteiro
#       que indica a quantidade de pares duma lista L (primitiva get) ou duma lista W (primitiva set ou
#       primitiva response);
# 7. L ou W - Lista de instâncias e valores associados – Lista L (primitiva get) ou lista W (primitiva
#       set ou response); esta lista é formada por pares de valores (I-ID,H ou N) (ver explicação das
#       primitivas);
# 8. Nr - Número de elementos da lista de erros – Número inteiro que indica a quantidade de erros
#       reportados na primitiva (ver explicação das primitivas) através da lista R;
# 9. R - Lista de erros e valores associados – A lista R inclui todos os erros encontrados durante o
#       processo de processamento do pedido P no agente (ver explicação das primitivas); no caso das
#       primitivas get temos Nr = 1, I-ID = 0 e E = 0.


class SNMPkeySharePDU:
    def __init__(self, security_model, security_params_num, security_params_list, request_id, primitive_type, num_instances, instances_values, num_errors, errors):
        self.security_model = security_model
        self.security_params_num = security_params_num
        self.security_params_list = security_params_list
        self.request_id = request_id
        self.primitive_type = primitive_type
        self.num_instances = num_instances
        self.instances_values = instances_values
        self.num_errors = num_errors
        self.errors = errors
    
    def encode(self):
        pdu_string = f"{self.security_model}\x00{self.security_params_num}\x00{self.security_params_list}\x00{self.request_id}\x00{self.primitive_type}\x00{self.num_instances}\x00{self.instances_values}\x00{self.num_errors}\x00{self.errors}\x00"
        return pdu_string.encode('ascii')
    
    @staticmethod
    def decode(pdu_string):
        pdu_fields = pdu_string.split("\x00")
        security_model = int(pdu_fields[0])
        security_params_num = int(pdu_fields[1])
        security_params_list = pdu_fields[2]
        request_id = int(pdu_fields[3])
        primitive_type = int(pdu_fields[4])
        num_instances = int(pdu_fields[5])
        instances_values = pdu_fields[6]
        num_errors = int(pdu_fields[7])
        errors = pdu_fields[8]
        
        return SNMPkeySharePDU(security_model, security_params_num, security_params_list, request_id, primitive_type, num_instances, instances_values, num_errors, errors)



## Create an SNMPkeySharePDU instance
#pdu = SNMPkeySharePDU(0, '', 12345, 1, 2, '1\x000\x002\x00', 1, '0\x000\x000\x00')

# Encode the PDU
#encoded_pdu = pdu.encode()
#print(encoded_pdu)  # Output: "0\x0012345\x001\x002\x001\x00\x001\x000\x002\x00\x001\x000\x000\x00\x00"

# Decode the PDU
#decoded_pdu = SNMPkeySharePDU.decode(encoded_pdu)
#print(decoded_pdu.security_model)  # Output: 0
#print(decoded_pdu.request_id)  # Output: 12345
# ... access other fields of the decoded PDU object
