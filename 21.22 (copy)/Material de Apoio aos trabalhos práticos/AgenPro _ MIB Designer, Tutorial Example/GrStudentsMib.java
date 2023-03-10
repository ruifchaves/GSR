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

import org.snmp4j.smi.*;
import org.snmp4j.mp.SnmpConstants;
import org.snmp4j.agent.*;
import org.snmp4j.agent.mo.*;
import org.snmp4j.agent.mo.snmp.*;
import org.snmp4j.agent.mo.snmp.smi.*;
import org.snmp4j.agent.request.*;
import org.snmp4j.log.LogFactory;
import org.snmp4j.log.LogAdapter;
import org.snmp4j.agent.mo.snmp.tc.*;

// --AgentGen BEGIN=_IMPORT
// --AgentGen END

public class GrStudentsMib
        // --AgentGen BEGIN=_EXTENDS
        // --AgentGen END
        implements MOGroup
// --AgentGen BEGIN=_IMPLEMENTS
// --AgentGen END
{

    private static final LogAdapter LOGGER = LogFactory.getLogger(GrStudentsMib.class);

    // --AgentGen BEGIN=_STATIC
    // --AgentGen END

    // Factory
    private MOFactory moFactory = DefaultMOFactory.getInstance();

    // Constants

    /** OID of this MIB module for usage which can be used for its identification. */
    public static final OID oidGrStudentsMib = new OID(new int[] {1, 3, 6, 1, 4, 1, 8888});

    // Identities
    // Scalars
    public static final OID oidGrMIBTotalStudents =
            new OID(new int[] {1, 3, 6, 1, 4, 1, 8888, 1, 0});
    public static final OID oidGrMIBTotalStudentsMIETI =
            new OID(new int[] {1, 3, 6, 1, 4, 1, 8888, 2, 0});
    public static final OID oidGrMIBTotalStudentsMIEI =
            new OID(new int[] {1, 3, 6, 1, 4, 1, 8888, 3, 0});
    public static final OID oidGrMIBTotalStudentsMEI =
            new OID(new int[] {1, 3, 6, 1, 4, 1, 8888, 4, 0});
    public static final OID oidGrMIBTotalStudentsMERSTEL =
            new OID(new int[] {1, 3, 6, 1, 4, 1, 8888, 5, 0});
    // Tables

    // Notifications

    // Enumerations

    // TextualConventions

    // Scalars
    private MOScalar<Counter32> grMIBTotalStudents;
    private MOScalar<Counter32> grMIBTotalStudentsMIETI;
    private MOScalar<Counter32> grMIBTotalStudentsMIEI;
    private MOScalar<Counter32> grMIBTotalStudentsMEI;
    private MOScalar<Counter32> grMIBTotalStudentsMERSTEL;

    // Tables
    public static final OID oidGrMIBEntry = new OID(new int[] {1, 3, 6, 1, 4, 1, 8888, 6, 1});

    // Index OID definitions
    public static final OID oidIndex = new OID(new int[] {1, 3, 6, 1, 4, 1, 8888, 6, 1, 1});

    // Column TC definitions for grMIBEntry:

    // Column sub-identifier definitions for grMIBEntry:
    public static final int colIndex = 1;
    public static final int colNumber = 2;
    public static final int colCourse = 3;
    public static final int colName = 4;
    public static final int colEmail = 5;
    public static final int colTpStatus = 6;

    // Column index definitions for grMIBEntry:
    public static final int idxIndex = 0;
    public static final int idxNumber = 1;
    public static final int idxCourse = 2;
    public static final int idxName = 3;
    public static final int idxEmail = 4;
    public static final int idxTpStatus = 5;

    private MOTableSubIndex[] grMIBEntryIndexes;
    private MOTableIndex grMIBEntryIndex;

    @SuppressWarnings(value = {"rawtypes"})
    private MOTable<GrMIBEntryRow, MOColumn, MOTableModel<GrMIBEntryRow>> grMIBEntry;

    private MOTableModel<GrMIBEntryRow> grMIBEntryModel;

    // --AgentGen BEGIN=_MEMBERS
    // --AgentGen END

    /**
     * Constructs a GrStudentsMib instance without actually creating its <code>ManagedObject</code>
     * instances. This has to be done in a sub-class constructor or after construction by calling
     * {@link #createMO(MOFactory moFactory)}.
     */
    protected GrStudentsMib() {
        // --AgentGen BEGIN=_DEFAULTCONSTRUCTOR
        // --AgentGen END
    }

    /**
     * Constructs a GrStudentsMib instance and actually creates its <code>ManagedObject</code>
     * instances using the supplied <code>MOFactory</code> (by calling {@link #createMO(MOFactory
     * moFactory)}).
     *
     * @param moFactory the <code>MOFactory</code> to be used to create the managed objects for this
     *     module.
     */
    public GrStudentsMib(MOFactory moFactory) {
        this();
        // --AgentGen BEGIN=_FACTORYCONSTRUCTOR::factoryWrapper
        // --AgentGen END
        this.moFactory = moFactory;
        createMO(moFactory);
        // --AgentGen BEGIN=_FACTORYCONSTRUCTOR
        // --AgentGen END
    }

    // --AgentGen BEGIN=_CONSTRUCTORS
    // --AgentGen END

    /**
     * Create the ManagedObjects defined for this MIB module using the specified {@link MOFactory}.
     *
     * @param moFactory the <code>MOFactory</code> instance to use for object creation.
     */
    protected void createMO(MOFactory moFactory) {
        addTCsToFactory(moFactory);
        grMIBTotalStudents =
                moFactory.createScalar(
                        oidGrMIBTotalStudents,
                        moFactory.createAccess(MOAccessImpl.ACCESSIBLE_FOR_READ_ONLY),
                        new Counter32());
        grMIBTotalStudentsMIETI =
                moFactory.createScalar(
                        oidGrMIBTotalStudentsMIETI,
                        moFactory.createAccess(MOAccessImpl.ACCESSIBLE_FOR_READ_ONLY),
                        new Counter32());
        grMIBTotalStudentsMIEI =
                moFactory.createScalar(
                        oidGrMIBTotalStudentsMIEI,
                        moFactory.createAccess(MOAccessImpl.ACCESSIBLE_FOR_READ_ONLY),
                        new Counter32());
        grMIBTotalStudentsMEI =
                moFactory.createScalar(
                        oidGrMIBTotalStudentsMEI,
                        moFactory.createAccess(MOAccessImpl.ACCESSIBLE_FOR_READ_ONLY),
                        new Counter32());
        grMIBTotalStudentsMERSTEL =
                moFactory.createScalar(
                        oidGrMIBTotalStudentsMERSTEL,
                        moFactory.createAccess(MOAccessImpl.ACCESSIBLE_FOR_READ_ONLY),
                        new Counter32());
        createGrMIBEntry(moFactory);
    }

    public MOScalar<Counter32> getGrMIBTotalStudents() {
        return grMIBTotalStudents;
    }

    public MOScalar<Counter32> getGrMIBTotalStudentsMIETI() {
        return grMIBTotalStudentsMIETI;
    }

    public MOScalar<Counter32> getGrMIBTotalStudentsMIEI() {
        return grMIBTotalStudentsMIEI;
    }

    public MOScalar<Counter32> getGrMIBTotalStudentsMEI() {
        return grMIBTotalStudentsMEI;
    }

    public MOScalar<Counter32> getGrMIBTotalStudentsMERSTEL() {
        return grMIBTotalStudentsMERSTEL;
    }

    @SuppressWarnings(value = {"rawtypes"})
    public MOTable<GrMIBEntryRow, MOColumn, MOTableModel<GrMIBEntryRow>> getGrMIBEntry() {
        return grMIBEntry;
    }

    @SuppressWarnings(value = {"unchecked"})
    private void createGrMIBEntry(MOFactory moFactory) {
        // Index definition
        grMIBEntryIndexes =
                new MOTableSubIndex[] {
                    moFactory.createSubIndex(oidIndex, SMIConstants.SYNTAX_INTEGER, 1, 1)
                };

        grMIBEntryIndex =
                moFactory.createIndex(
                        grMIBEntryIndexes,
                        false,
                        new MOTableIndexValidator() {
                            public boolean isValidIndex(OID index) {
                                boolean isValidIndex = true;
                                // --AgentGen BEGIN=grMIBEntry::isValidIndex
                                // --AgentGen END
                                return isValidIndex;
                            }
                        });

        // Columns
        MOColumn<?>[] grMIBEntryColumns = new MOColumn<?>[6];
        grMIBEntryColumns[idxIndex] =
                moFactory.createColumn(
                        colIndex,
                        SMIConstants.SYNTAX_COUNTER32,
                        moFactory.createAccess(MOAccessImpl.ACCESSIBLE_FOR_READ_ONLY));
        grMIBEntryColumns[idxNumber] =
                moFactory.createColumn(
                        colNumber,
                        SMIConstants.SYNTAX_INTEGER,
                        moFactory.createAccess(MOAccessImpl.ACCESSIBLE_FOR_READ_ONLY));
        grMIBEntryColumns[idxCourse] =
                moFactory.createColumn(
                        colCourse,
                        SMIConstants.SYNTAX_OCTET_STRING,
                        moFactory.createAccess(MOAccessImpl.ACCESSIBLE_FOR_READ_ONLY));
        grMIBEntryColumns[idxName] =
                moFactory.createColumn(
                        colName,
                        SMIConstants.SYNTAX_OCTET_STRING,
                        moFactory.createAccess(MOAccessImpl.ACCESSIBLE_FOR_READ_ONLY));
        grMIBEntryColumns[idxEmail] =
                moFactory.createColumn(
                        colEmail,
                        SMIConstants.SYNTAX_OCTET_STRING,
                        moFactory.createAccess(MOAccessImpl.ACCESSIBLE_FOR_READ_ONLY));
        grMIBEntryColumns[idxTpStatus] =
                new MOMutableColumn<Integer32>(
                        colTpStatus,
                        SMIConstants.SYNTAX_INTEGER,
                        moFactory.createAccess(MOAccessImpl.ACCESSIBLE_FOR_READ_WRITE),
                        (Integer32) null
                        // --AgentGen BEGIN=tpStatus::auxInit
                        // --AgentGen END
                        );
        ((MOMutableColumn<?>) grMIBEntryColumns[idxTpStatus])
                .addMOValueValidationListener(new TpStatusValidator());
        // Table model
        grMIBEntryModel =
                moFactory.createTableModel(oidGrMIBEntry, grMIBEntryIndex, grMIBEntryColumns);
        ((MOMutableTableModel<GrMIBEntryRow>) grMIBEntryModel)
                .setRowFactory(new GrMIBEntryRowFactory());
        grMIBEntry =
                moFactory.createTable(
                        oidGrMIBEntry, grMIBEntryIndex, grMIBEntryColumns, grMIBEntryModel);
    }

    public void registerMOs(MOServer server, OctetString context)
            throws DuplicateRegistrationException {
        // Scalar Objects
        server.register(this.grMIBTotalStudents, context);
        server.register(this.grMIBTotalStudentsMIETI, context);
        server.register(this.grMIBTotalStudentsMIEI, context);
        server.register(this.grMIBTotalStudentsMEI, context);
        server.register(this.grMIBTotalStudentsMERSTEL, context);
        server.register(this.grMIBEntry, context);
        // --AgentGen BEGIN=_registerMOs
        // --AgentGen END
    }

    public void unregisterMOs(MOServer server, OctetString context) {
        // Scalar Objects
        server.unregister(this.grMIBTotalStudents, context);
        server.unregister(this.grMIBTotalStudentsMIETI, context);
        server.unregister(this.grMIBTotalStudentsMIEI, context);
        server.unregister(this.grMIBTotalStudentsMEI, context);
        server.unregister(this.grMIBTotalStudentsMERSTEL, context);
        server.unregister(this.grMIBEntry, context);
        // --AgentGen BEGIN=_unregisterMOs
        // --AgentGen END
    }

    // Notifications

    // Scalars

    // Value Validators

    /**
     * The <code>TpStatusValidator</code> implements the value validation for <code>TpStatus</code>.
     */
    static class TpStatusValidator implements MOValueValidationListener {

        public void validate(MOValueValidationEvent validationEvent) {
            Variable newValue = validationEvent.getNewValue();
            // --AgentGen BEGIN=tpStatus::validate
            // --AgentGen END
        }
    }

    // Rows and Factories

    public class GrMIBEntryRow extends DefaultMOMutableRow2PC {

        // --AgentGen BEGIN=grMIBEntry::RowMembers
        // --AgentGen END

        public GrMIBEntryRow(OID index, Variable[] values) {
            super(index, values);
            // --AgentGen BEGIN=grMIBEntry::RowConstructor
            // --AgentGen END
        }

        public Counter32 getIndex() {
            // --AgentGen BEGIN=grMIBEntry::getIndex
            // --AgentGen END
            return (Counter32) super.getValue(idxIndex);
        }

        public void setIndex(Counter32 newColValue) {
            // --AgentGen BEGIN=grMIBEntry::setIndex
            // --AgentGen END
            super.setValue(idxIndex, newColValue);
        }

        public Integer32 getNumber() {
            // --AgentGen BEGIN=grMIBEntry::getNumber
            // --AgentGen END
            return (Integer32) super.getValue(idxNumber);
        }

        public void setNumber(Integer32 newColValue) {
            // --AgentGen BEGIN=grMIBEntry::setNumber
            // --AgentGen END
            super.setValue(idxNumber, newColValue);
        }

        public OctetString getCourse() {
            // --AgentGen BEGIN=grMIBEntry::getCourse
            // --AgentGen END
            return (OctetString) super.getValue(idxCourse);
        }

        public void setCourse(OctetString newColValue) {
            // --AgentGen BEGIN=grMIBEntry::setCourse
            // --AgentGen END
            super.setValue(idxCourse, newColValue);
        }

        public OctetString getName() {
            // --AgentGen BEGIN=grMIBEntry::getName
            // --AgentGen END
            return (OctetString) super.getValue(idxName);
        }

        public void setName(OctetString newColValue) {
            // --AgentGen BEGIN=grMIBEntry::setName
            // --AgentGen END
            super.setValue(idxName, newColValue);
        }

        public OctetString getEmail() {
            // --AgentGen BEGIN=grMIBEntry::getEmail
            // --AgentGen END
            return (OctetString) super.getValue(idxEmail);
        }

        public void setEmail(OctetString newColValue) {
            // --AgentGen BEGIN=grMIBEntry::setEmail
            // --AgentGen END
            super.setValue(idxEmail, newColValue);
        }

        public Integer32 getTpStatus() {
            // --AgentGen BEGIN=grMIBEntry::getTpStatus
            // --AgentGen END
            return (Integer32) super.getValue(idxTpStatus);
        }

        public void setTpStatus(Integer32 newColValue) {
            // --AgentGen BEGIN=grMIBEntry::setTpStatus
            // --AgentGen END
            super.setValue(idxTpStatus, newColValue);
        }

        public Variable getValue(int column) {
            // --AgentGen BEGIN=grMIBEntry::RowGetValue
            // --AgentGen END
            switch (column) {
                case idxIndex:
                    return getIndex();
                case idxNumber:
                    return getNumber();
                case idxCourse:
                    return getCourse();
                case idxName:
                    return getName();
                case idxEmail:
                    return getEmail();
                case idxTpStatus:
                    return getTpStatus();
                default:
                    return super.getValue(column);
            }
        }

        public void setValue(int column, Variable value) {
            // --AgentGen BEGIN=grMIBEntry::RowSetValue
            // --AgentGen END
            switch (column) {
                case idxIndex:
                    setIndex((Counter32) value);
                    break;
                case idxNumber:
                    setNumber((Integer32) value);
                    break;
                case idxCourse:
                    setCourse((OctetString) value);
                    break;
                case idxName:
                    setName((OctetString) value);
                    break;
                case idxEmail:
                    setEmail((OctetString) value);
                    break;
                case idxTpStatus:
                    setTpStatus((Integer32) value);
                    break;
                default:
                    super.setValue(column, value);
            }
        }

        // --AgentGen BEGIN=grMIBEntry::Row
        // --AgentGen END
    }

    public class GrMIBEntryRowFactory implements MOTableRowFactory<GrMIBEntryRow> {
        public synchronized GrMIBEntryRow createRow(OID index, Variable[] values)
                throws UnsupportedOperationException {
            GrMIBEntryRow row = new GrMIBEntryRow(index, values);
            // --AgentGen BEGIN=grMIBEntry::createRow
            // --AgentGen END
            return row;
        }

        public synchronized void freeRow(GrMIBEntryRow row) {
            // --AgentGen BEGIN=grMIBEntry::freeRow
            // --AgentGen END
        }

        // --AgentGen BEGIN=grMIBEntry::RowFactory
        // --AgentGen END
    }

    // --AgentGen BEGIN=_METHODS
    // --AgentGen END

    // Textual Definitions of MIB module GrStudentsMib
    protected void addTCsToFactory(MOFactory moFactory) {}

    // --AgentGen BEGIN=_TC_CLASSES_IMPORTED_MODULES_BEGIN
    // --AgentGen END

    // Textual Definitions of other MIB modules
    public void addImportedTCsToFactory(MOFactory moFactory) {}

    // --AgentGen BEGIN=_TC_CLASSES_IMPORTED_MODULES_END
    // --AgentGen END

    // --AgentGen BEGIN=_CLASSES
    // --AgentGen END

    // --AgentGen BEGIN=_END
    // --AgentGen END
}
