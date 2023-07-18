# SNMPkeyShare

### Concept
"O SNMPkeyShare será implementado sobre um modelo análogo à arquitetura SNMP, ou seja, o coração do sistema é um agente parecido a um agente SNMP que implementará a instrumentação duma MIB especial simplificada. A comunicação com o agente SNMPkeyShare será feita através duma versão simplificada do SNMP. Os gestores serão as aplicações que necessitam gerar e partilhar chaves entre si utilizando indiretamente o agente SNMPkeyShare."

### Requirements

Python 3

### Running project

> **_NOTE:_**  Run each instance of Agent and Manager in a separate Terminal with privileges

Navigate to the directory and run:
```bash
python3 agent.py
```
```bash
python3 manager.py
```
