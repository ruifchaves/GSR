/**
Tutorial Example
MIB Design and SNMP Agent Code Generation
Universidade do Minho, v1.0 February 2021
(c) João Pereira, d12267@di.uminho.pt
Disclaimer: This software/specification can be freely used and altered 
but the author should be acknowledged. Also, the author bears no 
responsibility on the use of this software/specification by a third person.
*/

package org.snmp4j.agent.grmib;
// --AgentGen BEGIN=_BEGIN
// --AgentGen END

import org.snmp4j.agent.mo.*;
import org.snmp4j.log.LogFactory;
import org.snmp4j.log.LogAdapter;
import org.snmp4j.agent.MOGroup;
import org.snmp4j.agent.MOServer;
import org.snmp4j.agent.DuplicateRegistrationException;
import org.snmp4j.smi.OctetString;

// --AgentGen BEGIN=_IMPORT
// --AgentGen END

public class Modules implements MOGroup {

    private static final LogAdapter LOGGER = LogFactory.getLogger(Modules.class);

    private GrStudentsMib grStudentsMib;

    private MOFactory factory;

    // --AgentGen BEGIN=_MEMBERS
    // --AgentGen END

    public Modules() {
        grStudentsMib = new GrStudentsMib();
        // --AgentGen BEGIN=_DEFAULTCONSTRUCTOR
        // --AgentGen END
    }

    public Modules(MOFactory factory) {
        grStudentsMib = new GrStudentsMib(factory);
        // --AgentGen BEGIN=_CONSTRUCTOR
        // --AgentGen END
    }

    public void registerMOs(MOServer server, OctetString context)
            throws DuplicateRegistrationException {
        grStudentsMib.registerMOs(server, context);
        // --AgentGen BEGIN=_registerMOs
        // --AgentGen END
    }

    public void unregisterMOs(MOServer server, OctetString context) {
        grStudentsMib.unregisterMOs(server, context);
        // --AgentGen BEGIN=_unregisterMOs
        // --AgentGen END
    }

    public GrStudentsMib getGrStudentsMib() {
        return grStudentsMib;
    }

    // --AgentGen BEGIN=_METHODS
    // --AgentGen END

    // --AgentGen BEGIN=_CLASSES
    // --AgentGen END

    // --AgentGen BEGIN=_END
    // --AgentGen END

}
