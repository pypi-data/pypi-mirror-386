from datetime import datetime
from typing import List
from sqlalchemy import (
    Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Text, and_,
    SmallInteger, and_, or_, select, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import aliased, declarative_base, relationship
from sqlalchemy import func
import pandas as pd

Base = declarative_base()

class AuxCellmapping(Base):
    __tablename__ = "Aux_CellMapping"

    newcellid = Column("NewCellID", Integer, primary_key=True)
    newtablevid = Column("NewTableVID", Integer, primary_key=True)
    oldcellid = Column("OldCellID", Integer)
    oldtablevid = Column("OldTableVID", Integer)

    __table_args__ = (
        UniqueConstraint('NewCellID', 'NewTableVID'),
    )

class AuxCellstatus(Base):
    __tablename__ = "Aux_CellStatus"

    tablevid = Column("TableVID", Integer, primary_key=True)
    cellid = Column("CellID", Integer, primary_key=True)
    status = Column("Status", String(100))
    isnewcell = Column("IsNewCell", Boolean)

    __table_args__ = (
        UniqueConstraint('TableVID', 'CellID'),
    )

class Category(Base):
    __tablename__ = "Category"

    categoryid = Column("CategoryID", Integer, primary_key=True)
    code = Column("Code", String(20))
    name = Column("Name", String(50))
    description = Column("Description", String(1000))
    isenumerated = Column("IsEnumerated", Boolean)
    issupercategory = Column("IsSuperCategory", Boolean)
    isactive = Column("IsActive", Boolean)
    isexternalrefdata = Column("IsExternalRefData", Boolean)
    refdatasource = Column("RefDataSource", String(255))
    rowguid = Column("RowGUID", String(36), ForeignKey("Concept.ConceptGUID"))

    # Use string references instead of direct class references
    concept = relationship("Concept", foreign_keys=[rowguid])
    subcategories = relationship("SubCategory", back_populates="category")  # Note: SubCategory not Subcategory
    property_categories = relationship("PropertyCategory", back_populates="category")
    supercategory_compositions = relationship("SupercategoryComposition",
                                            foreign_keys="SupercategoryComposition.supercategoryid",
                                            back_populates="supercategory")
    category_compositions = relationship("SupercategoryComposition",
                                       foreign_keys="SupercategoryComposition.categoryid",
                                       back_populates="category")

class SubCategory(Base):
    __tablename__ = "SubCategory"

    subcategoryid = Column("SubCategoryID", Integer, primary_key=True)
    categoryid = Column("CategoryID", Integer, ForeignKey("Category.CategoryID"))
    code = Column("Code", String(30))
    name = Column("Name", String(500))
    description = Column("Description", String(500))
    rowguid = Column("RowGUID", String(36), ForeignKey("Concept.ConceptGUID"))

    # Relationships
    category = relationship("Category", back_populates="subcategories")
    concept = relationship("Concept", foreign_keys=[rowguid])
    subcategory_versions = relationship("SubCategoryVersion", back_populates="subcategory")
    operand_references = relationship("OperandReference", back_populates="subcategory")
class Cell(Base):
    __tablename__ = "Cell"

    cellid = Column("CellID", Integer, primary_key=True)
    tableid = Column("TableID", Integer, ForeignKey("Table.TableID"))
    columnid = Column("ColumnID", Integer, ForeignKey("Header.HeaderID"))
    rowid = Column("RowID", Integer, ForeignKey("Header.HeaderID"))
    sheetid = Column("SheetID", Integer, ForeignKey("Header.HeaderID"))
    rowguid = Column("RowGUID", String(36), ForeignKey("Concept.ConceptGUID"))

    # Relationships
    table = relationship("Table", foreign_keys=[tableid])
    column_header = relationship("Header", foreign_keys=[columnid])
    row_header = relationship("Header", foreign_keys=[rowid])
    sheet_header = relationship("Header", foreign_keys=[sheetid])
    concept = relationship("Concept", foreign_keys=[rowguid])
    table_version_cells = relationship("TableVersionCell", back_populates="cell")
    operand_reference_locations = relationship("OperandReferenceLocation", back_populates="cell")

    __table_args__ = (
        UniqueConstraint('ColumnID', 'RowID', 'SheetID'),
    )

class Changelog(Base):
    __tablename__ = "ChangeLog"

    rowguid = Column("RowGUID", String(36), primary_key=True)
    classid = Column("ClassID", Integer, ForeignKey("DPMClass.ClassID"), primary_key=True)
    attributeid = Column("AttributeID", Integer, ForeignKey("DPMAttribute.AttributeID"), primary_key=True)
    timestamp = Column("Timestamp", Integer, primary_key=True)
    oldvalue = Column("OldValue", String(255))
    newvalue = Column("NewValue", String(255))
    changetype = Column("ChangeType", String(20))
    status = Column("Status", String(1))
    userid = Column("UserID", Integer, ForeignKey("User.UserID"))
    releaseid = Column("ReleaseID", Integer, ForeignKey("Release.ReleaseID"))

    # Relationships
    dpm_class = relationship("DpmClass", foreign_keys=[classid])
    dpm_attribute = relationship("DpmAttribute", foreign_keys=[attributeid])
    user = relationship("User", foreign_keys=[userid])
    release = relationship("Release", foreign_keys=[releaseid])

class CompoundItemContext(Base):
    __tablename__ = "CompoundItemContext"

    itemid = Column("ItemID", Integer, ForeignKey("Item.ItemID"), primary_key=True)
    startreleaseid = Column("StartReleaseID", Integer, ForeignKey("Release.ReleaseID"), primary_key=True)
    contextid = Column("ContextID", Integer, ForeignKey("Context.ContextID"))
    endreleaseid = Column("EndReleaseID", Integer, ForeignKey("Release.ReleaseID"))
    rowguid = Column("RowGUID", String(36))

    # Relationships
    item = relationship("Item", foreign_keys=[itemid])
    start_release = relationship("Release", foreign_keys=[startreleaseid])
    end_release = relationship("Release", foreign_keys=[endreleaseid])
    context = relationship("Context", foreign_keys=[contextid])

class CompoundKey(Base):
    __tablename__ = "CompoundKey"

    keyid = Column("KeyID", Integer, primary_key=True)
    signature = Column("Signature", String(255), unique=True)
    rowguid = Column("RowGUID", String(36), ForeignKey("Concept.ConceptGUID"))

    # Relationships
    concept = relationship("Concept", foreign_keys=[rowguid])
    key_compositions = relationship("KeyComposition", back_populates="compound_key")
    module_versions = relationship("ModuleVersion", back_populates="global_key")
    table_versions = relationship("TableVersion", back_populates="key")

class Concept(Base):
    __tablename__ = "Concept"

    conceptguid = Column("ConceptGUID", String(36), primary_key=True)
    classid = Column("ClassID", Integer, ForeignKey("DPMClass.ClassID"))
    ownerid = Column("OwnerID", Integer, ForeignKey("Organisation.OrgID"))

    # Relationships
    dpm_class = relationship("DpmClass", foreign_keys=[classid])
    owner = relationship("Organisation", foreign_keys=[ownerid])
    related_concepts = relationship("RelatedConcept", back_populates="concept")
    context_compositions = relationship("ContextComposition", back_populates="concept")

class ConceptRelation(Base):
    __tablename__ = "ConceptRelation"

    conceptrelationid = Column("ConceptRelationID", Integer, primary_key=True)
    type = Column("Type", String(50))
    rowguid = Column("RowGUID", String(36))

    # Relationships
    related_concepts = relationship("RelatedConcept", back_populates="concept_relation")

class Context(Base):
    __tablename__ = "Context"

    contextid = Column("ContextID", Integer, primary_key=True)
    signature = Column("Signature", String(2000), unique=True)
    rowguid = Column("RowGUID", String(36), ForeignKey("Concept.ConceptGUID"))

    # Relationships
    concept = relationship("Concept", foreign_keys=[rowguid])
    context_compositions = relationship("ContextComposition", back_populates="context")
    variable_versions = relationship("VariableVersion", back_populates="context")
    header_versions = relationship("HeaderVersion", back_populates="context")
    table_versions = relationship("TableVersion", back_populates="context")
    compound_item_contexts = relationship("CompoundItemContext", back_populates="context")

class ContextComposition(Base):
    __tablename__ = "ContextComposition"

    contextid = Column("ContextID", Integer, ForeignKey("Context.ContextID"), primary_key=True)
    propertyid = Column("PropertyID", Integer, ForeignKey("Property.PropertyID"), primary_key=True)
    itemid = Column("ItemID", Integer, ForeignKey("Item.ItemID"))
    rowguid = Column("RowGUID", String(36), ForeignKey("Concept.ConceptGUID"))

    # Relationships
    context = relationship("Context", back_populates="context_compositions")
    property = relationship("Property", back_populates="context_compositions")
    item = relationship("Item", foreign_keys=[itemid])
    concept = relationship("Concept", foreign_keys=[rowguid], back_populates="context_compositions")


class DpmAttribute(Base):
    __tablename__ = "DPMAttribute"

    attributeid = Column("AttributeID", Integer, primary_key=True)
    classid = Column("ClassID", Integer, ForeignKey("DPMClass.ClassID"))
    name = Column("Name", String(20))
    hastranslations = Column("HasTranslations", Boolean)

    # Relationships
    dpm_class = relationship("DpmClass", back_populates="dpm_attributes")
    changelogs = relationship("Changelog", back_populates="dpm_attribute")
    translations = relationship("Translation", back_populates="dpm_attribute")

class DpmClass(Base):
    __tablename__ = "DPMClass"

    classid = Column("ClassID", Integer, primary_key=True)
    name = Column("Name", String(50))
    type = Column("Type", String(20))
    ownerclassid = Column("OwnerClassID", Integer, ForeignKey("DPMClass.ClassID"))
    hasreferences = Column("HasReferences", Boolean)

    # Relationships
    owner_class = relationship("DpmClass", remote_side=[classid], back_populates="owned_classes")
    owned_classes = relationship("DpmClass", back_populates="owner_class")
    concepts = relationship("Concept", back_populates="dpm_class")
    dpm_attributes = relationship("DpmAttribute", back_populates="dpm_class")
    changelogs = relationship("Changelog", back_populates="dpm_class")

class DataType(Base):
    __tablename__ = "DataType"

    datatypeid = Column("DataTypeID", Integer, primary_key=True)
    code = Column("Code", String(20), unique=True)
    name = Column("Name", String(50), unique=True)
    parentdatatypeid = Column("ParentDataTypeID", Integer, ForeignKey("DataType.DataTypeID"))
    isactive = Column("IsActive", Boolean)

    # Relationships
    parent_datatype = relationship("DataType", remote_side=[datatypeid], back_populates="child_datatypes")
    child_datatypes = relationship("DataType", back_populates="parent_datatype")
    properties = relationship("Property", back_populates="datatype")

class Document(Base):
    __tablename__ = "Document"

    documentid = Column("DocumentID", Integer, primary_key=True)
    name = Column("Name", String(50))
    code = Column("Code", String(20))
    type = Column("Type", String(255))
    orgid = Column("OrgID", Integer, ForeignKey("Organisation.OrgID"))
    rowguid = Column("RowGUID", String(36), ForeignKey("Concept.ConceptGUID"))

    # Relationships
    organisation = relationship("Organisation", foreign_keys=[orgid])
    concept = relationship("Concept", foreign_keys=[rowguid])
    document_versions = relationship("DocumentVersion", back_populates="document")

class DocumentVersion(Base):
    __tablename__ = "DocumentVersion"

    documentvid = Column("DocumentVID", Integer, primary_key=True)
    documentid = Column("DocumentID", Integer, ForeignKey("Document.DocumentID"))
    code = Column("Code", String(20))
    version = Column("Version", String(20))
    publicationdate = Column("PublicationDate", Date)
    rowguid = Column("RowGUID", String(36), ForeignKey("Concept.ConceptGUID"))

    # Relationships
    document = relationship("Document", back_populates="document_versions")
    concept = relationship("Concept", foreign_keys=[rowguid])
    subdivisions = relationship("Subdivision", back_populates="document_version")

    __table_args__ = (
        UniqueConstraint('DocumentID', 'PublicationDate'),
    )

class Framework(Base):
    __tablename__ = "Framework"

    frameworkid = Column("FrameworkID", Integer, primary_key=True)
    code = Column("Code", String(255))
    name = Column("Name", String(255))
    description = Column("Description", String(255))
    rowguid = Column("RowGUID", String(36), ForeignKey("Concept.ConceptGUID"))

    # Relationships
    concept = relationship("Concept", foreign_keys=[rowguid])
    modules = relationship("Module", back_populates="framework")
    operation_code_prefixes = relationship("OperationCodePrefix", back_populates="framework")

class Header(Base):
    __tablename__ = "Header"

    headerid = Column("HeaderID", Integer, primary_key=True)
    tableid = Column("TableID", Integer, ForeignKey("Table.TableID"))
    direction = Column("Direction", String(1))
    iskey = Column("IsKey", Boolean)
    rowguid = Column("RowGUID", String(36), ForeignKey("Concept.ConceptGUID"))

    # Relationships
    table = relationship("Table", back_populates="headers")
    concept = relationship("Concept", foreign_keys=[rowguid])
    header_versions = relationship("HeaderVersion", back_populates="header")
    column_cells = relationship("Cell", foreign_keys="Cell.columnid", back_populates="column_header")
    row_cells = relationship("Cell", foreign_keys="Cell.rowid", back_populates="row_header")
    sheet_cells = relationship("Cell", foreign_keys="Cell.sheetid", back_populates="sheet_header")

class HeaderVersion(Base):
    __tablename__ = "HeaderVersion"

    headervid = Column("HeaderVID", Integer, primary_key=True)
    headerid = Column("HeaderID", Integer, ForeignKey("Header.HeaderID"))
    code = Column("Code", String(10))
    label = Column("Label", String(500))
    propertyid = Column("PropertyID", Integer, ForeignKey("Property.PropertyID"))
    contextid = Column("ContextID", Integer, ForeignKey("Context.ContextID"))
    subcategoryvid = Column("SubCategoryVID", Integer, ForeignKey("SubCategoryVersion.SubCategoryVID"))
    keyvariablevid = Column("KeyVariableVID", Integer, ForeignKey("VariableVersion.VariableVID"))
    startreleaseid = Column("StartReleaseID", Integer, ForeignKey("Release.ReleaseID"))
    endreleaseid = Column("EndReleaseID", Integer, ForeignKey("Release.ReleaseID"))
    rowguid = Column("RowGUID", String(36), ForeignKey("Concept.ConceptGUID"))

    # Relationships
    header = relationship("Header", back_populates="header_versions")
    property = relationship("Property", foreign_keys=[propertyid])
    context = relationship("Context", foreign_keys=[contextid])
    subcategory_version = relationship("SubCategoryVersion", foreign_keys=[subcategoryvid])
    key_variable_version = relationship("VariableVersion", foreign_keys=[keyvariablevid])
    start_release = relationship("Release", foreign_keys=[startreleaseid])
    end_release = relationship("Release", foreign_keys=[endreleaseid])
    concept = relationship("Concept", foreign_keys=[rowguid])

    __table_args__ = (
        UniqueConstraint('HeaderID', 'StartReleaseID'),
    )

class Item(Base):
    __tablename__ = "Item"

    itemid = Column("ItemID", Integer, primary_key=True)
    name = Column("Name", String(500))
    description = Column("Description", String(2000))
    iscompound = Column("IsCompound", Boolean)
    isproperty = Column("IsProperty", Boolean)
    isactive = Column("IsActive", Boolean)
    rowguid = Column("RowGUID", String(36), ForeignKey("Concept.ConceptGUID"))

    # Relationships - specify foreign_keys to resolve ambiguity
    concept = relationship("Concept", foreign_keys=[rowguid])
    item_categories = relationship("ItemCategory", back_populates="item")
    property = relationship("Property", back_populates="item", uselist=False)
    operand_references = relationship("OperandReference", back_populates="item")
    context_compositions = relationship("ContextComposition", back_populates="item")
    subcategory_items = relationship("SubCategoryItem", foreign_keys="SubCategoryItem.itemid", back_populates="item")
    compound_item_contexts = relationship("CompoundItemContext", back_populates="item")


class ItemCategory(Base):
    __tablename__ = "ItemCategory"

    itemid = Column("ItemID", Integer, ForeignKey("Item.ItemID"), primary_key=True)
    startreleaseid = Column("StartReleaseID", Integer, ForeignKey("Release.ReleaseID"), primary_key=True)
    categoryid = Column("CategoryID", Integer, ForeignKey("Category.CategoryID"))
    code = Column("Code", String(20))
    isdefaultitem = Column("IsDefaultItem", Boolean)
    signature = Column("Signature", String(255))
    endreleaseid = Column("EndReleaseID", Integer, ForeignKey("Release.ReleaseID"))
    rowguid = Column("RowGUID", String(36))

    # Relationships
    item = relationship("Item", back_populates="item_categories")
    start_release = relationship("Release", foreign_keys=[startreleaseid])
    end_release = relationship("Release", foreign_keys=[endreleaseid])
    category = relationship("Category", foreign_keys=[categoryid])
    
    @classmethod
    def get_items(cls, session, items, release_id=None):
        """
        Get ItemCategory records for a list of item signatures.
        
        Args:
            session: SQLAlchemy session
            items: List of item signatures to look up
            release_id: Release ID to filter by (optional)
            
        Returns:
            DataFrame with ItemCategory data for the requested items
        """
        import pandas as pd
        from sqlalchemy import or_
        
        query = session.query(cls.signature.label('Signature'), 
                            cls.code.label('Code'),
                            cls.categoryid.label('CategoryID'))
        
        # Filter by signatures
        if items:
            query = query.filter(cls.signature.in_(items))
        
        # Filter by release
        if release_id is not None:
            query = query.filter(
                and_(
                    cls.startreleaseid <= release_id,
                    or_(cls.endreleaseid > release_id, cls.endreleaseid.is_(None))
                )
            )
        else:
            # Get current/active items (no end release)
            query = query.filter(cls.endreleaseid.is_(None))
        
        # Execute query and convert to DataFrame
        result = query.all()
        if result:
            return pd.DataFrame([{
                'Signature': row.Signature,
                'Code': row.Code, 
                'CategoryID': row.CategoryID
            } for row in result])
        else:
            return pd.DataFrame(columns=['Signature', 'Code', 'CategoryID'])

class KeyComposition(Base):
    __tablename__ = "KeyComposition"

    keyid = Column("KeyID", Integer, ForeignKey("CompoundKey.KeyID"), primary_key=True)
    variablevid = Column("VariableVID", Integer, ForeignKey("VariableVersion.VariableVID"), primary_key=True)
    rowguid = Column("RowGUID", String(36))

    # Relationships
    compound_key = relationship("CompoundKey", back_populates="key_compositions")
    variable_version = relationship("VariableVersion", back_populates="key_compositions")

class KeyHeaderMapping(Base):
    __tablename__ = "KeyHeaderMapping"

    associationid = Column("AssociationID", Integer, ForeignKey("TableAssociation.AssociationID"), primary_key=True)
    foreignkeyheaderid = Column("ForeignKeyHeaderID", Integer, ForeignKey("Header.HeaderID"), primary_key=True)
    primarykeyheaderid = Column("PrimaryKeyHeaderID", Integer, ForeignKey("Header.HeaderID"))
    rowguid = Column("RowGUID", String(36))

    # Relationships
    table_association = relationship("TableAssociation", foreign_keys=[associationid])
    foreign_key_header = relationship("Header", foreign_keys=[foreignkeyheaderid])
    primary_key_header = relationship("Header", foreign_keys=[primarykeyheaderid])

class Language(Base):
    __tablename__ = "Language"

    languagecode = Column("LanguageCode", Integer, primary_key=True)
    name = Column("Name", String(20))

    # Relationships
    translations = relationship("Translation", back_populates="language")

class ModelViolations(Base):
    __tablename__ = "ModelViolations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    violationcode = Column("ViolationCode", String(10))
    violation = Column("Violation", String(255))
    isblocking = Column("isBlocking", Boolean)
    tablevid = Column("TableVID", Integer)
    oldtablevid = Column("OldTableVID", Integer)
    tablecode = Column("TableCode", String(40))
    headerid = Column("HeaderID", Integer)
    headercode = Column("HeaderCode", String(20))
    headervid = Column("HeaderVID", Integer)
    oldheadervid = Column("OldHeaderVID", Integer)
    keyheader = Column("KeyHeader", Boolean)
    headerdirection = Column("HeaderDirection", String(1))
    headerpropertyid = Column("HeaderPropertyID", Integer)
    headerpropertycode = Column("HeaderPropertyCode", String(20))
    headersubcategoryid = Column("HeaderSubcategoryID", Integer)
    headersubcategoryname = Column("HeaderSubcategoryName", String(60))
    headercontextid = Column("HeaderContextID", Integer)
    categoryid = Column("CategoryID", Integer)
    categorycode = Column("CategoryCode", String(30))
    itemid = Column("ItemID", Integer)
    itemcode = Column("ItemCode", String(30))
    cellid = Column("CellID", Integer)
    cellcode = Column("CellCode", String(50))
    cell2id = Column("Cell2ID", Integer)
    cell2code = Column("Cell2Code", String(50))
    vvendreleaseid = Column("VVEndReleaseID", Integer)
    newaspect = Column("NewAspect", String(80))

class Module(Base):
    __tablename__ = "Module"

    moduleid = Column("ModuleID", Integer, primary_key=True)
    frameworkid = Column("FrameworkID", Integer, ForeignKey("Framework.FrameworkID"))
    rowguid = Column("RowGUID", String(36), ForeignKey("Concept.ConceptGUID"))

    # Relationships
    framework = relationship("Framework", back_populates="modules")
    concept = relationship("Concept", foreign_keys=[rowguid])
    module_versions = relationship("ModuleVersion", back_populates="module")
    variable_calculations = relationship("VariableCalculation", back_populates="module")

class ModuleParameters(Base):
    __tablename__ = "ModuleParameters"

    modulevid = Column("ModuleVID", Integer, ForeignKey("ModuleVersion.ModuleVID"), primary_key=True)
    variablevid = Column("VariableVID", Integer, ForeignKey("VariableVersion.VariableVID"), primary_key=True)
    rowguid = Column("RowGUID", String(36))

    # Relationships
    module_version = relationship("ModuleVersion", back_populates="module_parameters")
    variable_version = relationship("VariableVersion", back_populates="module_parameters")

class ModuleVersion(Base):
    __tablename__ = "ModuleVersion"

    modulevid = Column("ModuleVID", Integer, primary_key=True)
    moduleid = Column("ModuleID", Integer, ForeignKey("Module.ModuleID"))
    globalkeyid = Column("GlobalKeyID", Integer, ForeignKey("CompoundKey.KeyID"))
    startreleaseid = Column("StartReleaseID", Integer, ForeignKey("Release.ReleaseID"))
    endreleaseid = Column("EndReleaseID", Integer, ForeignKey("Release.ReleaseID"))
    code = Column("Code", String(30))
    name = Column("Name", String(100))
    description = Column("Description", String(255))
    versionnumber = Column("VersionNumber", String(20))
    fromreferencedate = Column("FromReferenceDate", Date)
    toreferencedate = Column("ToReferenceDate", Date)
    rowguid = Column("RowGUID", String(36), ForeignKey("Concept.ConceptGUID"))

    # Relationships
    module = relationship("Module", back_populates="module_versions")
    global_key = relationship("CompoundKey", foreign_keys=[globalkeyid])
    start_release = relationship("Release", foreign_keys=[startreleaseid])
    end_release = relationship("Release", foreign_keys=[endreleaseid])
    concept = relationship("Concept", foreign_keys=[rowguid])
    module_version_compositions = relationship("ModuleVersionComposition", back_populates="module_version")
    operation_scope_compositions = relationship("OperationScopeComposition", back_populates="module_version")
    module_parameters = relationship("ModuleParameters", back_populates="module_version")

    __table_args__ = (
        UniqueConstraint('ModuleID', 'StartReleaseID'),
    )

class ModuleVersionComposition(Base):
    __tablename__ = "ModuleVersionComposition"

    modulevid = Column("ModuleVID", Integer, ForeignKey("ModuleVersion.ModuleVID"), primary_key=True)
    tableid = Column("TableID", Integer, ForeignKey("Table.TableID"), primary_key=True)
    tablevid = Column("TableVID", Integer, ForeignKey("TableVersion.TableVID"))
    order = Column("Order", Integer)
    rowguid = Column("RowGUID", String(36))

    # Relationships
    module_version = relationship("ModuleVersion", back_populates="module_version_compositions")
    table = relationship("Table", back_populates="module_version_compositions")
    table_version = relationship("TableVersion", back_populates="module_version_compositions")

class OperandReference(Base):
    __tablename__ = "OperandReference"

    operandreferenceid = Column("OperandReferenceID", Integer, primary_key=True)
    nodeid = Column("NodeID", Integer, ForeignKey("OperationNode.NodeID"))
    x = Column("x", Integer)
    y = Column("y", Integer)
    z = Column("z", Integer)
    operandreference = Column("OperandReference", String(255))
    itemid = Column("ItemID", Integer, ForeignKey("Item.ItemID"))
    propertyid = Column("PropertyID", Integer, ForeignKey("Property.PropertyID"))
    variableid = Column("VariableID", Integer, ForeignKey("Variable.VariableID"))
    subcategoryid = Column("SubCategoryID", Integer, ForeignKey("SubCategory.SubCategoryID"))

    # Relationships
    operation_node = relationship("OperationNode", back_populates="operand_references")
    item = relationship("Item", back_populates="operand_references")
    property = relationship("Property", foreign_keys=[propertyid])
    variable = relationship("Variable", back_populates="operand_references")
    subcategory = relationship("SubCategory", foreign_keys=[subcategoryid])
    operand_reference_locations = relationship("OperandReferenceLocation", back_populates="operand_reference")

class OperandReferenceLocation(Base):
    __tablename__ = "OperandReferenceLocation"

    operandreferenceid = Column("OperandReferenceID", Integer, ForeignKey("OperandReference.OperandReferenceID"), primary_key=True)
    cellid = Column("CellID", Integer, ForeignKey("Cell.CellID"))
    table = Column("Table", String(255))
    row = Column("Row", String(255))
    column = Column("Column", String(255))
    sheet = Column("Sheet", String(255))

    # Relationships
    operand_reference = relationship("OperandReference", back_populates="operand_reference_locations")
    cell = relationship("Cell", back_populates="operand_reference_locations")

class Operation(Base):
    __tablename__ = "Operation"

    operationid = Column("OperationID", Integer, primary_key=True)
    code = Column("Code", String(20))
    type = Column("Type", String(20))
    source = Column("Source", String(20))
    groupoperid = Column("GroupOperID", Integer, ForeignKey("Operation.OperationID"))
    rowguid = Column("RowGUID", String(36), ForeignKey("Concept.ConceptGUID"))

    # Relationships
    group_operation = relationship("Operation", remote_side=[operationid], back_populates="grouped_operations")
    grouped_operations = relationship("Operation", back_populates="group_operation")
    concept = relationship("Concept", foreign_keys=[rowguid])
    operation_versions = relationship("OperationVersion", back_populates="operation")

class OperationCodePrefix(Base):
    __tablename__ = "OperationCodePrefix"

    operationcodeprefixid = Column("OperationCodePrefixID", Integer, primary_key=True)
    code = Column("Code", String(20), unique=True)
    listname = Column("ListName", String(20))
    frameworkid = Column("FrameworkID", Integer, ForeignKey("Framework.FrameworkID"))

    # Relationships
    framework = relationship("Framework", back_populates="operation_code_prefixes")

class OperationNode(Base):
    __tablename__ = "OperationNode"

    nodeid = Column("NodeID", Integer, primary_key=True)
    operationvid = Column("OperationVID", Integer, ForeignKey("OperationVersion.OperationVID"))
    parentnodeid = Column("ParentNodeID", Integer, ForeignKey("OperationNode.NodeID"))
    operatorid = Column("OperatorID", Integer, ForeignKey("Operator.OperatorID"))
    argumentid = Column("ArgumentID", Integer, ForeignKey("OperatorArgument.ArgumentID"))
    absolutetolerance = Column("AbsoluteTolerance", String)
    relativetolerance = Column("RelativeTolerance", String)
    fallbackvalue = Column("FallbackValue", String(50))
    useintervalarithmetics = Column("UseIntervalArithmetics", Boolean)
    operandtype = Column("OperandType", String(20))
    isleaf = Column("IsLeaf", Boolean)
    scalar = Column("Scalar", Text)

    # Relationships
    operation_version = relationship("OperationVersion", back_populates="operation_nodes")
    parent = relationship("OperationNode", remote_side=[nodeid], back_populates="children")
    children = relationship("OperationNode", back_populates="parent")
    operator = relationship("Operator", foreign_keys=[operatorid])
    operator_argument = relationship("OperatorArgument", foreign_keys=[argumentid])
    operand_references = relationship("OperandReference", back_populates="operation_node")

class OperationScope(Base):
    __tablename__ = "OperationScope"

    operationscopeid = Column("OperationScopeID", Integer, primary_key=True)
    operationvid = Column("OperationVID", Integer, ForeignKey("OperationVersion.OperationVID"))
    isactive = Column("IsActive", Boolean)
    severity = Column("Severity", String(20))
    fromsubmissiondate = Column("FromSubmissionDate", Date)
    rowguid = Column("RowGUID", String(36))

    # Relationships
    operation_version = relationship("OperationVersion", back_populates="operation_scopes")
    operation_scope_compositions = relationship("OperationScopeComposition", back_populates="operation_scope")

class OperationScopeComposition(Base):
    __tablename__ = "OperationScopeComposition"

    operationscopeid = Column("OperationScopeID", Integer, ForeignKey("OperationScope.OperationScopeID"), primary_key=True)
    modulevid = Column("ModuleVID", Integer, ForeignKey("ModuleVersion.ModuleVID"), primary_key=True)
    rowguid = Column("RowGUID", String(36))

    # Relationships
    operation_scope = relationship("OperationScope", back_populates="operation_scope_compositions")
    module_version = relationship("ModuleVersion", back_populates="operation_scope_compositions")

class OperationVersion(Base):
    __tablename__ = "OperationVersion"

    operationvid = Column("OperationVID", Integer, primary_key=True)
    operationid = Column("OperationID", Integer, ForeignKey("Operation.OperationID"))
    preconditionoperationvid = Column("PreconditionOperationVID", Integer, ForeignKey("OperationVersion.OperationVID"))
    severityoperationvid = Column("SeverityOperationVID", Integer, ForeignKey("OperationVersion.OperationVID"))
    startreleaseid = Column("StartReleaseID", Integer, ForeignKey("Release.ReleaseID"))
    endreleaseid = Column("EndReleaseID", Integer, ForeignKey("Release.ReleaseID"))
    expression = Column("Expression", Text)
    description = Column("Description", String(1000))
    rowguid = Column("RowGUID", String(36), ForeignKey("Concept.ConceptGUID"))
    endorsement = Column("Endorsement", String(25))
    isvariantapproved = Column("IsVariantApproved", Boolean)

    # Relationships
    operation = relationship("Operation", back_populates="operation_versions")
    precondition_operation = relationship("OperationVersion",
                                        remote_side=[operationvid],
                                        foreign_keys=[preconditionoperationvid],
                                        back_populates="precondition_dependent_operations")
    severity_operation = relationship("OperationVersion",
                                    remote_side=[operationvid],
                                    foreign_keys=[severityoperationvid],
                                    back_populates="severity_dependent_operations")
    precondition_dependent_operations = relationship("OperationVersion",
                                                   foreign_keys=[preconditionoperationvid],
                                                   back_populates="precondition_operation")
    severity_dependent_operations = relationship("OperationVersion",
                                                foreign_keys=[severityoperationvid],
                                                back_populates="severity_operation")
    start_release = relationship("Release", foreign_keys=[startreleaseid])
    end_release = relationship("Release", foreign_keys=[endreleaseid])
    concept = relationship("Concept", foreign_keys=[rowguid])
    operation_nodes = relationship("OperationNode", back_populates="operation_version")
    operation_scopes = relationship("OperationScope", back_populates="operation_version")
    operation_version_data = relationship("OperationVersionData", back_populates="operation_version", uselist=False)
    variable_calculations = relationship("VariableCalculation", back_populates="operation_version")

    __table_args__ = (
        UniqueConstraint('OperationID', 'StartReleaseID'),
    )

class OperationVersionData(Base):
    __tablename__ = "OperationVersionData"

    operationvid = Column("OperationVID", Integer, ForeignKey("OperationVersion.OperationVID"), primary_key=True)
    error = Column("Error", String(2000))
    errorcode = Column("ErrorCode", String(50))
    isapplying = Column("IsApplying", Boolean)
    proposingstatus = Column("ProposingStatus", String(50))

    # Relationships
    operation_version = relationship("OperationVersion", back_populates="operation_version_data")

class Operator(Base):
    __tablename__ = "Operator"

    operatorid = Column("OperatorID", Integer, primary_key=True)
    name = Column("Name", String(50))
    symbol = Column("Symbol", String(20))
    type = Column("Type", String(20))

    # Relationships
    operator_arguments = relationship("OperatorArgument", back_populates="operator")
    operation_nodes = relationship("OperationNode", back_populates="operator")
    comparison_subcategory_items = relationship("SubCategoryItem",
                                              foreign_keys="SubCategoryItem.comparisonoperatorid",
                                              back_populates="comparison_operator")
    arithmetic_subcategory_items = relationship("SubCategoryItem",
                                               foreign_keys="SubCategoryItem.arithmeticoperatorid",
                                               back_populates="arithmetic_operator")

class OperatorArgument(Base):
    __tablename__ = "OperatorArgument"

    argumentid = Column("ArgumentID", Integer, primary_key=True)
    operatorid = Column("OperatorID", Integer, ForeignKey("Operator.OperatorID"))
    order = Column("Order", SmallInteger)
    ismandatory = Column("IsMandatory", Boolean)
    name = Column("Name", String(50))

    # Relationships
    operator = relationship("Operator", back_populates="operator_arguments")
    operation_nodes = relationship("OperationNode", back_populates="operator_argument")

class Organisation(Base):
    __tablename__ = "Organisation"

    orgid = Column("OrgID", Integer, primary_key=True)
    name = Column("Name", String(200), unique=True)
    acronym = Column("Acronym", String(20))
    idprefix = Column("IDPrefix", Integer, unique=True)
    rowguid = Column("RowGUID", String(36), ForeignKey("Concept.ConceptGUID"))

    # Relationships
    concept = relationship("Concept", foreign_keys=[rowguid])
    concepts_owned = relationship("Concept", foreign_keys="Concept.ownerid", back_populates="owner")
    documents = relationship("Document", back_populates="organisation")
    users = relationship("User", back_populates="organisation")
    translations = relationship("Translation", back_populates="translator")

class Property(Base):
    __tablename__ = "Property"

    propertyid = Column("PropertyID", Integer, ForeignKey("Item.ItemID"), primary_key=True)
    iscomposite = Column("IsComposite", Boolean)
    ismetric = Column("IsMetric", Boolean)
    datatypeid = Column("DataTypeID", Integer, ForeignKey("DataType.DataTypeID"))
    valuelength = Column("ValueLength", Integer)
    periodtype = Column("PeriodType", String(20))
    rowguid = Column("RowGUID", String(36), ForeignKey("Concept.ConceptGUID"))

    # Relationships
    item = relationship("Item", back_populates="property")
    datatype = relationship("DataType", back_populates="properties")
    concept = relationship("Concept", foreign_keys=[rowguid])
    property_categories = relationship("PropertyCategory", back_populates="property")
    context_compositions = relationship("ContextComposition", back_populates="property")
    variable_versions = relationship("VariableVersion", back_populates="property")
    header_versions = relationship("HeaderVersion", back_populates="property")
    table_versions = relationship("TableVersion", back_populates="property")

class PropertyCategory(Base):
    __tablename__ = "PropertyCategory"

    propertyid = Column("PropertyID", Integer, ForeignKey("Property.PropertyID"), primary_key=True)
    startreleaseid = Column("StartReleaseID", Integer, ForeignKey("Release.ReleaseID"), primary_key=True)
    categoryid = Column("CategoryID", Integer, ForeignKey("Category.CategoryID"))
    endreleaseid = Column("EndReleaseID", Integer, ForeignKey("Release.ReleaseID"))
    rowguid = Column("RowGUID", String(36))

    # Relationships
    property = relationship("Property", back_populates="property_categories")
    start_release = relationship("Release", foreign_keys=[startreleaseid])
    end_release = relationship("Release", foreign_keys=[endreleaseid])
    category = relationship("Category", back_populates="property_categories")

class Reference(Base):
    __tablename__ = "Reference"

    subdivisionid = Column("SubdivisionID", Integer, ForeignKey("Subdivision.SubdivisionID"), primary_key=True)
    conceptguid = Column("ConceptGUID", String(36), ForeignKey("Concept.ConceptGUID"), primary_key=True)
    rowguid = Column("RowGUID", String(36))

    # Relationships
    subdivision = relationship("Subdivision", back_populates="references")
    concept = relationship("Concept", foreign_keys=[conceptguid])

class RelatedConcept(Base):
    __tablename__ = "RelatedConcept"

    conceptguid = Column("ConceptGUID", String(36), ForeignKey("Concept.ConceptGUID"), primary_key=True)
    conceptrelationid = Column("ConceptRelationID", Integer, ForeignKey("ConceptRelation.ConceptRelationID"), primary_key=True)
    isrelatedconcept = Column("IsRelatedConcept", Boolean)
    rowguid = Column("RowGUID", String(36))

    # Relationships
    concept = relationship("Concept", back_populates="related_concepts")
    concept_relation = relationship("ConceptRelation", back_populates="related_concepts")

class Release(Base):
    __tablename__ = "Release"

    releaseid = Column("ReleaseID", Integer, primary_key=True)
    code = Column("Code", String(20))
    date = Column("Date", Date)
    description = Column("Description", String(255))
    status = Column("Status", String(50))
    iscurrent = Column("IsCurrent", Boolean)
    rowguid = Column("RowGUID", String(36), ForeignKey("Concept.ConceptGUID"))
    latestvariablegentime = Column("LatestVariableGenTime", DateTime)
    name = Column("Name", String(50))

    # Relationships
    concept = relationship("Concept", foreign_keys=[rowguid])
    changelogs = relationship("Changelog", back_populates="release")
    variable_generations = relationship("VariableGeneration", back_populates="release")

class Role(Base):
    __tablename__ = "Role"

    roleid = Column("RoleID", Integer, primary_key=True)
    name = Column("Name", String(50))

    # Relationships
    user_roles = relationship("UserRole", back_populates="role")

class SubCategoryItem(Base):
    __tablename__ = "SubCategoryItem"

    itemid = Column("ItemID", Integer, ForeignKey("Item.ItemID"), primary_key=True)
    subcategoryvid = Column("SubCategoryVID", Integer, ForeignKey("SubCategoryVersion.SubCategoryVID"), primary_key=True)
    order = Column("Order", Integer)
    label = Column("Label", String(200))
    parentitemid = Column("ParentItemID", Integer, ForeignKey("Item.ItemID"))
    comparisonoperatorid = Column("ComparisonOperatorID", Integer, ForeignKey("Operator.OperatorID"))
    arithmeticoperatorid = Column("ArithmeticOperatorID", Integer, ForeignKey("Operator.OperatorID"))
    rowguid = Column("RowGUID", String(36), ForeignKey("Concept.ConceptGUID"))

    # Relationships - specify foreign_keys to resolve ambiguity
    item = relationship("Item", foreign_keys=[itemid], back_populates="subcategory_items")
    subcategory_version = relationship("SubCategoryVersion", back_populates="subcategory_items")
    parent_item = relationship("Item", foreign_keys=[parentitemid])
    comparison_operator = relationship("Operator", foreign_keys=[comparisonoperatorid], back_populates="comparison_subcategory_items")
    arithmetic_operator = relationship("Operator", foreign_keys=[arithmeticoperatorid], back_populates="arithmetic_subcategory_items")
    concept = relationship("Concept", foreign_keys=[rowguid])


class SubCategoryVersion(Base):
    __tablename__ = "SubCategoryVersion"

    subcategoryvid = Column("SubCategoryVID", Integer, primary_key=True)
    subcategoryid = Column("SubCategoryID", Integer, ForeignKey("SubCategory.SubCategoryID"))
    startreleaseid = Column("StartReleaseID", Integer, ForeignKey("Release.ReleaseID"))
    endreleaseid = Column("EndReleaseID", Integer, ForeignKey("Release.ReleaseID"))
    rowguid = Column("RowGUID", String(36), ForeignKey("Concept.ConceptGUID"))

    # Relationships
    subcategory = relationship("SubCategory", back_populates="subcategory_versions")
    start_release = relationship("Release", foreign_keys=[startreleaseid])
    end_release = relationship("Release", foreign_keys=[endreleaseid])
    concept = relationship("Concept", foreign_keys=[rowguid])
    subcategory_items = relationship("SubCategoryItem", back_populates="subcategory_version")
    header_versions = relationship("HeaderVersion", back_populates="subcategory_version")
    variable_versions = relationship("VariableVersion", back_populates="subcategory_version")

    __table_args__ = (
        UniqueConstraint('SubCategoryID', 'StartReleaseID'),
    )

class Subdivision(Base):
    __tablename__ = "Subdivision"

    subdivisionid = Column("SubdivisionID", Integer, primary_key=True)
    documentvid = Column("DocumentVID", Integer, ForeignKey("DocumentVersion.DocumentVID"))
    subdivisiontypeid = Column("SubdivisionTypeID", Integer, ForeignKey("SubdivisionType.SubdivisionTypeID"))
    number = Column("Number", String(20))
    parentsubdivisionid = Column("ParentSubdivisionID", Integer, ForeignKey("Subdivision.SubdivisionID"))
    structurepath = Column("StructurePath", String(255))
    textexcerpt = Column("TextExcerpt", Text)
    rowguid = Column("RowGUID", String(36), ForeignKey("Concept.ConceptGUID"))

    # Relationships
    document_version = relationship("DocumentVersion", back_populates="subdivisions")
    subdivision_type = relationship("SubdivisionType", back_populates="subdivisions")
    parent_subdivision = relationship("Subdivision", remote_side=[subdivisionid], back_populates="child_subdivisions")
    child_subdivisions = relationship("Subdivision", back_populates="parent_subdivision")
    concept = relationship("Concept", foreign_keys=[rowguid])
    references = relationship("Reference", back_populates="subdivision")

class SubdivisionType(Base):
    __tablename__ = "SubdivisionType"

    subdivisiontypeid = Column("SubdivisionTypeID", Integer, primary_key=True)
    name = Column("Name", String(50))
    description = Column("Description", String(255))

    # Relationships
    subdivisions = relationship("Subdivision", back_populates="subdivision_type")

class SupercategoryComposition(Base):
    __tablename__ = "SuperCategoryComposition"

    supercategoryid = Column("SuperCategoryID", Integer, ForeignKey("Category.CategoryID"), primary_key=True)
    categoryid = Column("CategoryID", Integer, ForeignKey("Category.CategoryID"), primary_key=True)
    startreleaseid = Column("StartReleaseID", Integer, ForeignKey("Release.ReleaseID"))
    endreleaseid = Column("EndReleaseID", Integer, ForeignKey("Release.ReleaseID"))
    rowguid = Column("RowGUID", String(36))

    # Relationships
    supercategory = relationship("Category", foreign_keys=[supercategoryid], back_populates="supercategory_compositions")
    category = relationship("Category", foreign_keys=[categoryid], back_populates="category_compositions")
    start_release = relationship("Release", foreign_keys=[startreleaseid])
    end_release = relationship("Release", foreign_keys=[endreleaseid])

class Table(Base):
    __tablename__ = "Table"

    tableid = Column("TableID", Integer, primary_key=True)
    isabstract = Column("IsAbstract", Boolean)
    hasopencolumns = Column("HasOpenColumns", Boolean)
    hasopenrows = Column("HasOpenRows", Boolean)
    hasopensheets = Column("HasOpenSheets", Boolean)
    isnormalised = Column("IsNormalised", Boolean)
    isflat = Column("IsFlat", Boolean)
    rowguid = Column("RowGUID", String(36), ForeignKey("Concept.ConceptGUID"))

    # Relationships - specify foreign_keys to resolve ambiguity
    concept = relationship("Concept", foreign_keys=[rowguid])
    headers = relationship("Header", back_populates="table")
    cells = relationship("Cell", back_populates="table")
    table_versions = relationship("TableVersion", foreign_keys="TableVersion.tableid", back_populates="table")
    abstract_table_versions = relationship("TableVersion", foreign_keys="TableVersion.abstracttableid", back_populates="abstract_table")
    table_group_compositions = relationship("TableGroupComposition", back_populates="table")
    module_version_compositions = relationship("ModuleVersionComposition", back_populates="table")

class TableAssociation(Base):
    __tablename__ = "TableAssociation"

    associationid = Column("AssociationID", Integer, primary_key=True)
    childtablevid = Column("ChildTableVID", Integer, ForeignKey("TableVersion.TableVID"))
    parenttablevid = Column("ParentTableVID", Integer, ForeignKey("TableVersion.TableVID"))
    name = Column("Name", String(50))
    description = Column("Description", String(255))
    isidentifying = Column("IsIdentifying", Boolean)
    issubtype = Column("IsSubtype", Boolean)
    subtypediscriminator = Column("SubtypeDiscriminator", Integer, ForeignKey("Header.HeaderID"))
    parentcardinalityandoptionality = Column("ParentCardinalityAndOptionality", String(3))
    childcardinalityandoptionality = Column("ChildCardinalityAndOptionality", String(3))
    rowguid = Column("RowGUID", String(36), ForeignKey("Concept.ConceptGUID"))

    # Relationships
    child_table_version = relationship("TableVersion", foreign_keys=[childtablevid], back_populates="table_associations_as_child")
    parent_table_version = relationship("TableVersion", foreign_keys=[parenttablevid], back_populates="table_associations_as_parent")
    subtype_discriminator = relationship("Header", foreign_keys=[subtypediscriminator])
    concept = relationship("Concept", foreign_keys=[rowguid])
    key_header_mappings = relationship("KeyHeaderMapping", back_populates="table_association")

class TableGroup(Base):
    __tablename__ = "TableGroup"

    tablegroupid = Column("TableGroupID", Integer, primary_key=True)
    code = Column("Code", String(255))
    name = Column("Name", String(255))
    description = Column("Description", String(2000))
    type = Column("Type", String(20))
    rowguid = Column("RowGUID", String(36), ForeignKey("Concept.ConceptGUID"))
    startreleaseid = Column("StartReleaseID", Integer, ForeignKey("Release.ReleaseID"))
    endreleaseid = Column("EndReleaseID", Integer, ForeignKey("Release.ReleaseID"))
    parenttablegroupid = Column("ParentTableGroupID", Integer, ForeignKey("TableGroup.TableGroupID"))

    # Relationships
    concept = relationship("Concept", foreign_keys=[rowguid])
    start_release = relationship("Release", foreign_keys=[startreleaseid])
    end_release = relationship("Release", foreign_keys=[endreleaseid])
    parent_table_group = relationship("TableGroup", remote_side=[tablegroupid], back_populates="child_table_groups")
    child_table_groups = relationship("TableGroup", back_populates="parent_table_group")
    table_group_compositions = relationship("TableGroupComposition", back_populates="table_group")

class TableGroupComposition(Base):
    __tablename__ = "TableGroupComposition"

    tablegroupid = Column("TableGroupID", Integer, ForeignKey("TableGroup.TableGroupID"), primary_key=True)
    tableid = Column("TableID", Integer, ForeignKey("Table.TableID"), primary_key=True)
    order = Column("Order", Integer)
    startreleaseid = Column("StartReleaseID", Integer, ForeignKey("Release.ReleaseID"))
    endreleaseid = Column("EndReleaseID", Integer, ForeignKey("Release.ReleaseID"))
    rowguid = Column("RowGUID", String(36))

    # Relationships
    table_group = relationship("TableGroup", back_populates="table_group_compositions")
    table = relationship("Table", back_populates="table_group_compositions")
    start_release = relationship("Release", foreign_keys=[startreleaseid])
    end_release = relationship("Release", foreign_keys=[endreleaseid])
class TableVersion(Base):
    __tablename__ = "TableVersion"

    tablevid = Column("TableVID", Integer, primary_key=True)
    code = Column("Code", String(30))
    name = Column("Name", String(255))
    description = Column("Description", String(500))
    tableid = Column("TableID", Integer, ForeignKey("Table.TableID"))
    abstracttableid = Column("AbstractTableID", Integer, ForeignKey("Table.TableID"))
    keyid = Column("KeyID", Integer, ForeignKey("CompoundKey.KeyID"))
    propertyid = Column("PropertyID", Integer, ForeignKey("Property.PropertyID"))
    contextid = Column("ContextID", Integer, ForeignKey("Context.ContextID"))
    startreleaseid = Column("StartReleaseID", Integer, ForeignKey("Release.ReleaseID"))
    endreleaseid = Column("EndReleaseID", Integer, ForeignKey("Release.ReleaseID"))
    rowguid = Column("RowGUID", String(36), ForeignKey("Concept.ConceptGUID"))

    # Relationships - specify foreign_keys to resolve ambiguity
    table = relationship("Table", foreign_keys=[tableid], back_populates="table_versions")
    abstract_table = relationship("Table", foreign_keys=[abstracttableid], back_populates="abstract_table_versions")
    key = relationship("CompoundKey", foreign_keys=[keyid])
    property = relationship("Property", foreign_keys=[propertyid])
    context = relationship("Context", foreign_keys=[contextid])
    start_release = relationship("Release", foreign_keys=[startreleaseid])
    end_release = relationship("Release", foreign_keys=[endreleaseid])
    concept = relationship("Concept", foreign_keys=[rowguid])
    table_version_cells = relationship("TableVersionCell", back_populates="table_version")
    table_version_headers = relationship("TableVersionHeader", back_populates="table_version")
    table_associations_as_child = relationship("TableAssociation", foreign_keys="TableAssociation.childtablevid", back_populates="child_table_version")
    table_associations_as_parent = relationship("TableAssociation", foreign_keys="TableAssociation.parenttablevid", back_populates="parent_table_version")
    module_version_compositions = relationship("ModuleVersionComposition", back_populates="table_version")

    __table_args__ = (
        UniqueConstraint('TableID', 'StartReleaseID'),
    )

class TableVersionCell(Base):
    __tablename__ = "TableVersionCell"

    tablevid = Column("TableVID", Integer, ForeignKey("TableVersion.TableVID"), primary_key=True)
    cellid = Column("CellID", Integer, ForeignKey("Cell.CellID"), primary_key=True)
    cellcode = Column("CellCode", String(100))
    isnullable = Column("IsNullable", Boolean)
    isexcluded = Column("IsExcluded", Boolean)
    isvoid = Column("IsVoid", Boolean)
    sign = Column("Sign", String(8))
    variablevid = Column("VariableVID", Integer, ForeignKey("VariableVersion.VariableVID"))
    rowguid = Column("RowGUID", String(36))

    # Relationships
    table_version = relationship("TableVersion", back_populates="table_version_cells")
    cell = relationship("Cell", back_populates="table_version_cells")
    variable_version = relationship("VariableVersion", back_populates="table_version_cells")

class TableVersionHeader(Base):
    __tablename__ = "TableVersionHeader"

    tablevid = Column("TableVID", Integer, ForeignKey("TableVersion.TableVID"), primary_key=True)
    headerid = Column("HeaderID", Integer, ForeignKey("Header.HeaderID"), primary_key=True)
    headervid = Column("HeaderVID", Integer, ForeignKey("HeaderVersion.HeaderVID"))
    parentheaderid = Column("ParentHeaderID", Integer, ForeignKey("Header.HeaderID"))
    parentfirst = Column("ParentFirst", Boolean)
    order = Column("Order", Integer)
    isabstract = Column("IsAbstract", Boolean)
    isunique = Column("IsUnique", Boolean)
    rowguid = Column("RowGUID", String(36))

    # Relationships
    table_version = relationship("TableVersion", back_populates="table_version_headers")
    header = relationship("Header", foreign_keys=[headerid])
    header_version = relationship("HeaderVersion", foreign_keys=[headervid])
    parent_header = relationship("Header", foreign_keys=[parentheaderid])

class Translation(Base):
    __tablename__ = "Translation"

    conceptguid = Column("ConceptGUID", String(36), ForeignKey("Concept.ConceptGUID"), primary_key=True)
    attributeid = Column("AttributeID", Integer, ForeignKey("DPMAttribute.AttributeID"), primary_key=True)
    translatorid = Column("TranslatorID", Integer, ForeignKey("Organisation.OrgID"), primary_key=True)
    languagecode = Column("LanguageCode", Integer, ForeignKey("Language.LanguageCode"), primary_key=True)
    translation = Column("Translation", Text)
    rowguid = Column("RowGUID", String(36))

    # Relationships
    concept = relationship("Concept", foreign_keys=[conceptguid])
    dpm_attribute = relationship("DpmAttribute", back_populates="translations")
    translator = relationship("Organisation", foreign_keys=[translatorid], back_populates="translations")
    language = relationship("Language", back_populates="translations")

class User(Base):
    __tablename__ = "User"

    userid = Column("UserID", Integer, primary_key=True)
    orgid = Column("OrgID", Integer, ForeignKey("Organisation.OrgID"))
    name = Column("Name", String(50))

    # Relationships
    organisation = relationship("Organisation", back_populates="users")
    user_roles = relationship("UserRole", back_populates="user")
    changelogs = relationship("Changelog", back_populates="user")

class UserRole(Base):
    __tablename__ = "UserRole"

    userid = Column("UserID", Integer, ForeignKey("User.UserID"), primary_key=True)
    roleid = Column("RoleID", Integer, ForeignKey("Role.RoleID"), primary_key=True)

    # Relationships
    user = relationship("User", back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")

class Variable(Base):
    __tablename__ = "Variable"

    variableid = Column("VariableID", Integer, primary_key=True)
    type = Column("Type", String(20))
    rowguid = Column("RowGUID", String(36), ForeignKey("Concept.ConceptGUID"))

    # Relationships
    concept = relationship("Concept", foreign_keys=[rowguid])
    variable_versions = relationship("VariableVersion", back_populates="variable")
    variable_calculations = relationship("VariableCalculation", back_populates="variable")
    operand_references = relationship("OperandReference", back_populates="variable")

class VariableCalculation(Base):
    __tablename__ = "VariableCalculation"

    moduleid = Column("ModuleID", Integer, ForeignKey("Module.ModuleID"), primary_key=True)
    variableid = Column("VariableID", Integer, ForeignKey("Variable.VariableID"), primary_key=True)
    operationvid = Column("OperationVID", Integer, ForeignKey("OperationVersion.OperationVID"), primary_key=True)
    fromreferencedate = Column("FromReferenceDate", Date)
    toreferencedate = Column("ToReferenceDate", Date)
    rowguid = Column("RowGUID", String(36))

    # Relationships
    module = relationship("Module", back_populates="variable_calculations")
    variable = relationship("Variable", back_populates="variable_calculations")
    operation_version = relationship("OperationVersion", back_populates="variable_calculations")

class VariableGeneration(Base):
    __tablename__ = "VariableGeneration"

    variablegenerationid = Column("VariableGenerationID", Integer, primary_key=True)
    startdate = Column("StartDate", DateTime)
    enddate = Column("EndDate", DateTime)
    status = Column("Status", String(50))
    releaseid = Column("ReleaseID", Integer, ForeignKey("Release.ReleaseID"))
    error = Column("Error", String(4000))

    # Relationships
    release = relationship("Release", back_populates="variable_generations")

class VariableVersion(Base):
    __tablename__ = "VariableVersion"

    variablevid = Column("VariableVID", Integer, primary_key=True)
    variableid = Column("VariableID", Integer, ForeignKey("Variable.VariableID"))
    propertyid = Column("PropertyID", Integer, ForeignKey("Property.PropertyID"))
    subcategoryvid = Column("SubCategoryVID", Integer, ForeignKey("SubCategoryVersion.SubCategoryVID"))
    contextid = Column("ContextID", Integer, ForeignKey("Context.ContextID"))
    keyid = Column("KeyID", Integer, ForeignKey("CompoundKey.KeyID"))
    ismultivalued = Column("IsMultiValued", Boolean)
    code = Column("Code", String(20))
    name = Column("Name", String(50))
    startreleaseid = Column("StartReleaseID", Integer, ForeignKey("Release.ReleaseID"))
    endreleaseid = Column("EndReleaseID", Integer, ForeignKey("Release.ReleaseID"))
    rowguid = Column("RowGUID", String(36), ForeignKey("Concept.ConceptGUID"))

    # Relationships
    variable = relationship("Variable", back_populates="variable_versions")
    property = relationship("Property", back_populates="variable_versions")
    subcategory_version = relationship("SubCategoryVersion", back_populates="variable_versions")
    context = relationship("Context", back_populates="variable_versions")
    key = relationship("CompoundKey", foreign_keys=[keyid])
    start_release = relationship("Release", foreign_keys=[startreleaseid])
    end_release = relationship("Release", foreign_keys=[endreleaseid])
    concept = relationship("Concept", foreign_keys=[rowguid])
    key_compositions = relationship("KeyComposition", back_populates="variable_version")
    module_parameters = relationship("ModuleParameters", back_populates="variable_version")
    table_version_cells = relationship("TableVersionCell", back_populates="variable_version")
    header_versions = relationship("HeaderVersion", back_populates="key_variable_version")

    __table_args__ = (
        UniqueConstraint('VariableID', 'StartReleaseID'),
    )
    
    @classmethod
    def check_variable_exists(cls, session, variable_code, release_id=None):
        """
        Check if a variable exists in the database.
        
        Args:
            session: SQLAlchemy session
            variable_code: Variable code to check
            release_id: Release ID to filter by (optional)
            
        Returns:
            Boolean indicating if the variable exists
        """
        from sqlalchemy import or_
        
        query = session.query(cls).filter(cls.code == variable_code)
        
        # Filter by release
        if release_id is not None:
            query = query.filter(
                and_(
                    cls.startreleaseid <= release_id,
                    or_(cls.endreleaseid > release_id, cls.endreleaseid.is_(None))
                )
            )
        else:
            # Check current/active variables (no end release)
            query = query.filter(cls.endreleaseid.is_(None))
        
        return query.first() is not None

# Utility functions (keep these from your original models)
def filter_by_release(query, start_release, end_release, release_id):
    """
    Live Release: EndReleaseID is NULL
    Specific Release: StartReleaseID <= ?  and (EndReleaseID > ? or EndReleaseID is NULL)
    """
    if release_id is None:
        return query.filter(and_(end_release.is_(None), True))
    return query.filter(and_(start_release <= release_id,
                             or_(end_release > release_id,
                                 end_release.is_(None))))

def filter_by_date(query, start_date, end_date, date):
    date = datetime.strptime(date, '%Y-%m-%d')
    if date is None:
        return query.filter(and_(end_date.is_(None), True))
    return query.filter(and_(start_date <= date), or_(end_date > date, end_date.is_(None)))

def filter_elements(query, column, values):
    if len(values) == 1:
        if values[0] == '*':
            return query.filter(column.is_not(None))
        elif '-' in values[0]:
            limits = values[0].split('-')
            return query.filter(column.between(limits[0], limits[1]))
        else:
            return query.filter(column == values[0])
    range_control = any(['-' in x for x in values])
    if not range_control:
        return query.filter(column.in_(values))
    dynamic_filter = []
    for x in values:
        if '-' in x:
            limits = x.split('-')
            dynamic_filter.append(column.between(limits[0], limits[1]))
        else:
            dynamic_filter.append(column == x)
    return query.filter(or_((x for x in dynamic_filter)))

def _check_ranges_values_are_present(data: pd.DataFrame, data_column, values):
    if values is not None and len(values) > 0 and '-' in values[0]:
        test = values[0].split('-')
        if test[0] not in list(data[data_column].values):
            data = pd.DataFrame(columns=data.columns)
        if test[1] not in list(data[data_column].values):
            data = pd.DataFrame(columns=data.columns)
    return data

class ViewDatapoints(Base):
    __tablename__ = "datapoints"

    cell_code = Column(String, primary_key=True)
    table_code = Column(String)
    row_code = Column(String)
    column_code = Column(String)
    sheet_code = Column(String)
    variable_id = Column(String)
    data_type = Column(String)
    table_vid = Column(Integer)
    property_id = Column(Integer)
    start_release = Column(Integer)
    end_release = Column(Integer)
    cell_id = Column(Integer)
    context_id = Column(Integer)
    variable_vid = Column(String)

    @classmethod
    def _create_base_query_with_aliases(cls, session):
        """
        Create the base query with all aliases and joins.
        Returns query and the aliases for reuse in other methods.
        """
        # Create aliases for the header version subqueries
        hvr_subq = aliased(HeaderVersion)
        hvc_subq = aliased(HeaderVersion)
        hvs_subq = aliased(HeaderVersion)

        tvh_row = aliased(TableVersionHeader)
        tvh_col = aliased(TableVersionHeader)
        tvh_sheet = aliased(TableVersionHeader)

        # Build the base query with all joins
        query = session.query().select_from(TableVersionCell)

        # Join with TableVersion
        query = query.join(
            TableVersion,
            and_(
                TableVersionCell.tablevid == TableVersion.tablevid,
                TableVersionCell.isvoid == False
            )
        )

        # Join with ModuleVersionComposition and ModuleVersion
        query = query.join(
            ModuleVersionComposition,
            TableVersion.tablevid == ModuleVersionComposition.tablevid
        )

        query = query.join(
            ModuleVersion,
            ModuleVersionComposition.modulevid == ModuleVersion.modulevid
        )

        # Left join with VariableVersion
        query = query.outerjoin(
            VariableVersion,
            TableVersionCell.variablevid == VariableVersion.variablevid
        )

        # Left join with Property
        query = query.outerjoin(
            Property,
            VariableVersion.propertyid == Property.propertyid
        )

        # Left join with DataType
        query = query.outerjoin(
            DataType,
            Property.datatypeid == DataType.datatypeid
        )

        # Join with Cell
        query = query.join(
            Cell,
            TableVersionCell.cellid == Cell.cellid
        )

        # Left join for Row headers (hvr)
        query = query.outerjoin(
            tvh_row,
            tvh_row.tablevid == TableVersion.tablevid
        )

        query = query.outerjoin(
            hvr_subq,
            and_(
                tvh_row.headervid == hvr_subq.headervid,
                hvr_subq.headerid == Cell.rowid,
                hvr_subq.endreleaseid.is_(None)
            )
        )

        # Left join for Column headers (hvc)
        query = query.outerjoin(
            tvh_col,
            tvh_col.tablevid == TableVersion.tablevid
        )

        query = query.outerjoin(
            hvc_subq,
            and_(
                tvh_col.headervid == hvc_subq.headervid,
                hvc_subq.headerid == Cell.columnid,
                hvc_subq.endreleaseid.is_(None)
            )
        )

        # Left join for Sheet headers (hvs)
        query = query.outerjoin(
            tvh_sheet,
            tvh_sheet.tablevid == TableVersion.tablevid
        )

        query = query.outerjoin(
            hvs_subq,
            and_(
                tvh_sheet.headervid == hvs_subq.headervid,
                hvs_subq.headerid == Cell.sheetid,
                hvs_subq.endreleaseid.is_(None)
            )
        )

        # Return query and aliases for reuse
        aliases = {
            'hvr': hvr_subq,
            'hvc': hvc_subq,
            'hvs': hvs_subq,
            'tvh_row': tvh_row,
            'tvh_col': tvh_col,
            'tvh_sheet': tvh_sheet
        }

        return query, aliases

    @classmethod
    def create_view_query(cls, session):
        """Create the full datapoints view query with all columns."""
        query, aliases = cls._create_base_query_with_aliases(session)

        # Add the column selections
        query = query.add_columns(
            TableVersionCell.cellcode.label('cell_code'),
            TableVersion.code.label('table_code'),
            aliases['hvr'].code.label('row_code'),
            aliases['hvc'].code.label('column_code'),
            aliases['hvs'].code.label('sheet_code'),
            VariableVersion.variableid.label('variable_id'),
            DataType.code.label('data_type'),
            TableVersion.tablevid.label('table_vid'),
            Property.propertyid.label('property_id'),
            ModuleVersion.startreleaseid.label('start_release'),
            ModuleVersion.endreleaseid.label('end_release'),
            TableVersionCell.cellid.label('cell_id'),
            VariableVersion.contextid.label('context_id'),
            VariableVersion.variablevid.label('variable_vid')
        )

        # Make it distinct
        query = query.distinct()

        return query

    @classmethod
    def count_all(cls, session):
        return cls.create_view_query(session).count()

    @classmethod
    def get_filtered_datapoints(cls, session, table: str, table_info: dict, release_id: int = None):
        query, aliases = cls._create_base_query_with_aliases(session)

        # Add the column selections
        query = query.add_columns(
            TableVersionCell.cellcode.label('cell_code'),
            TableVersion.code.label('table_code'),
            aliases['hvr'].code.label('row_code'),
            aliases['hvc'].code.label('column_code'),
            aliases['hvs'].code.label('sheet_code'),
            VariableVersion.variableid.label('variable_id'),
            DataType.code.label('data_type'),
            TableVersion.tablevid.label('table_vid'),
            Property.propertyid.label('property_id'),
            ModuleVersion.startreleaseid.label('start_release'),
            ModuleVersion.endreleaseid.label('end_release'),
            TableVersionCell.cellid.label('cell_id'),
            VariableVersion.contextid.label('context_id'),
            VariableVersion.variablevid.label('variable_vid')
        ).distinct()

        # Apply table filter
        query = query.filter(TableVersion.code == table)

        # Apply dimension filters
        mapping_dictionary = {
            'rows': aliases['hvr'].code,
            'cols': aliases['hvc'].code,
            'sheets': aliases['hvs'].code
        }

        for key, values in table_info.items():
            if values is not None and key in mapping_dictionary:
                column = mapping_dictionary[key]
                if '-' in values[0]:
                    low_limit, high_limit = values[0].split('-')
                    query = query.filter(column.between(low_limit, high_limit))
                elif values[0] == '*':
                    continue
                else:
                    query = query.filter(column.in_(values))

        if release_id:
            query = filter_by_release(query, ModuleVersion.startreleaseid, ModuleVersion.endreleaseid, release_id)

        return pd.read_sql_query(query.statement, session.connection())


    @classmethod
    def get_datapoints_count(cls, session):
        """Get count of datapoints using the view query"""
        query = cls.create_view_query(session)
        return query.count()

    @classmethod
    def get_datapoints_sample(cls, session, limit=1000):
        """Get a sample of datapoints"""
        query = cls.create_view_query(session)
        return pd.read_sql_query(
            query.limit(limit).statement,
            session.connection()
        )

    @classmethod
    def export_datapoints_query(cls, session):
        """Get the compiled SQL query for the datapoints view"""
        query = cls.create_view_query(session)
        return str(query.statement.compile(
            dialect=session.bind.dialect,
            compile_kwargs={"literal_binds": True}
        ))
    @classmethod
    def get_all_datapoints(cls, session):
        query = cls.create_view_query(session)
        return pd.read_sql_query(query.statement, session.connection())

    @classmethod
    def get_table_data(cls, session, table, rows=None, columns=None, sheets=None, release_id=None):
        # Query the datapoints view directly instead of reconstructing it
        from sqlalchemy import text
        
        sql = "SELECT cell_code, table_code, row_code, column_code, sheet_code, variable_id, data_type, table_vid, cell_id FROM datapoints WHERE table_code = :table"
        params = {'table': table}
        
        # Apply row filter
        if rows is not None and rows != ['*']:
            if len(rows) == 1 and '-' in rows[0]:
                low, high = rows[0].split('-')
                sql += " AND row_code BETWEEN :row_low AND :row_high"
                params['row_low'] = low
                params['row_high'] = high
            else:
                placeholders = ','.join([f":row{i}" for i in range(len(rows))])
                sql += f" AND row_code IN ({placeholders})"
                for i, r in enumerate(rows):
                    params[f'row{i}'] = r
        
        # Apply column filter
        if columns is not None and columns != ['*']:
            if len(columns) == 1 and '-' in columns[0]:
                low, high = columns[0].split('-')
                sql += " AND column_code BETWEEN :col_low AND :col_high"
                params['col_low'] = low
                params['col_high'] = high
            else:
                placeholders = ','.join([f":col{i}" for i in range(len(columns))])
                sql += f" AND column_code IN ({placeholders})"
                for i, c in enumerate(columns):
                    params[f'col{i}'] = c
        
        # Apply sheet filter
        if sheets is not None and sheets != ['*']:
            if len(sheets) == 1 and '-' in sheets[0]:
                low, high = sheets[0].split('-')
                sql += " AND sheet_code BETWEEN :sheet_low AND :sheet_high"
                params['sheet_low'] = low
                params['sheet_high'] = high
            else:
                placeholders = ','.join([f":sheet{i}" for i in range(len(sheets))])
                sql += f" AND sheet_code IN ({placeholders})"
                for i, s in enumerate(sheets):
                    params[f'sheet{i}'] = s
        
        # Apply release filter  
        # Note: In the DPM database, if release_id is None, we should get all active rows
        # The original logic with ORM was more complex, but for views we simplify:
        # - If release_id is provided: start_release <= release_id AND (end_release IS NULL OR end_release > release_id)
        # - If release_id is None: get all rows (no filter on releases)
        if release_id is not None:
            sql += " AND start_release <= :release AND (end_release IS NULL OR end_release > :release)"
            params['release'] = release_id
        
        data = pd.read_sql_query(text(sql), session.connection(), params=params)
        
        data = _check_ranges_values_are_present(data, 'row_code', rows)
        data = _check_ranges_values_are_present(data, 'column_code', columns)
        data = _check_ranges_values_are_present(data, 'sheet_code', sheets)

        return data

    @classmethod
    def get_from_property(cls, session, property_id, release_id=None):
        query, aliases = cls._create_base_query_with_aliases(session)

        query = query.add_columns(
            TableVersionCell.cellcode.label('cell_code'),
            TableVersion.code.label('table_code'),
            aliases['hvr'].code.label('row_code'),
            aliases['hvc'].code.label('column_code'),
            aliases['hvs'].code.label('sheet_code'),
            VariableVersion.variableid.label('variable_id'),
            DataType.code.label('data_type'),
            TableVersion.tablevid.label('table_vid')
        ).distinct()

        query = query.filter(Property.propertyid == property_id)
        query = filter_by_release(query, ModuleVersion.startreleaseid, ModuleVersion.endreleaseid, release_id)

        return pd.read_sql_query(query.statement, session.connection())

    @classmethod
    def get_from_table_vid(cls, session, table_version_id):
        query = cls.create_view_query(session)
        query = query.filter(TableVersion.tablevid == table_version_id)
        query = filter_by_release(query, ModuleVersion.startreleaseid, ModuleVersion.endreleaseid, release_id=None)
        return pd.read_sql_query(query.statement, session.connection())

    @classmethod
    def get_from_table_code(cls, session, table_code, release_id=None):
        query = cls.create_view_query(session)
        query = query.filter(TableVersion.code == table_code)
        query = filter_by_release(query, ModuleVersion.startreleaseid, ModuleVersion.endreleaseid, release_id)
        return pd.read_sql_query(query.statement, session.connection())

    @classmethod
    def get_from_table_vid_with_is_nullable(cls, session, table_version_id):
        query, aliases = cls._create_base_query_with_aliases(session)

        query = query.add_columns(
            TableVersionCell.cellcode.label('cell_code'),
            TableVersion.code.label('table_code'),
            aliases['hvr'].code.label('row_code'),
            aliases['hvc'].code.label('column_code'),
            aliases['hvs'].code.label('sheet_code'),
            VariableVersion.variableid.label('variable_id'),
            DataType.code.label('data_type'),
            TableVersion.tablevid.label('table_vid'),
            Property.propertyid.label('property_id'),
            ModuleVersion.startreleaseid.label('start_release'),
            ModuleVersion.endreleaseid.label('end_release'),
            TableVersionCell.cellid.label('cell_id'),
            VariableVersion.contextid.label('context_id'),
            VariableVersion.variablevid.label('variable_vid'),
            TableVersionCell.isnullable  # Add the nullable column
        ).distinct()

        query = query.filter(TableVersion.tablevid == table_version_id)
        return pd.read_sql_query(query.statement, session.connection())

    @classmethod
    def get_from_subcategory_properties(cls, session, properties, release_id):
        query, aliases = cls._create_base_query_with_aliases(session)

        # Add ContextComposition join
        query = query.join(
            ContextComposition,
            and_(
                ContextComposition.contextid == VariableVersion.contextid,
                ContextComposition.propertyid.in_(properties)
            )
        )

        query = query.add_columns(
            TableVersion.code.label('table_code'),
            aliases['hvr'].code.label('row_code'),
            aliases['hvc'].code.label('column_code'),
            aliases['hvs'].code.label('sheet_code'),
            Property.propertyid.label('property_id'),
            VariableVersion.contextid.label('context_id'),
            VariableVersion.variablevid.label('variable_vid'),
            ContextComposition.propertyid.label('subcategory_property'),
            TableVersionCell.cellid.label('cell_id'),
            DataType.code.label('data_type')
        ).distinct()

        query = filter_by_release(query, ModuleVersion.startreleaseid, ModuleVersion.endreleaseid, release_id)
        return pd.read_sql_query(query.statement, session.connection())

    @classmethod
    def filter_by_context_and_property(cls, session, context, property_key, release_id):
        query, aliases = cls._create_base_query_with_aliases(session)

        query = query.add_columns(
            TableVersion.code.label('table_code'),
            aliases['hvr'].code.label('row_code'),
            aliases['hvc'].code.label('column_code'),
            aliases['hvs'].code.label('sheet_code'),
            Property.propertyid.label('property_id'),
            VariableVersion.contextid.label('context_id'),
            VariableVersion.variablevid.label('variable_vid'),
            TableVersionCell.cellid.label('cell_id')
        ).distinct()

        query = query.filter(VariableVersion.contextid == context)

        if property_key:
            query = query.filter(Property.propertyid == property_key)

        query = filter_by_release(query, ModuleVersion.startreleaseid, ModuleVersion.endreleaseid, release_id)
        return pd.read_sql_query(query.statement, session.connection())
class ViewKeyComponents(Base):
    __tablename__ = "key_components"

    table_code = Column(String, primary_key=True)
    property_code = Column(String, primary_key=True)
    data_type = Column(String, primary_key=True)
    table_version_id = Column(Integer)
    start_release_ic = Column(Integer)
    end_release_ic = Column(Integer)
    start_release_mv = Column(Integer)
    end_release_mv = Column(Integer)

    @classmethod
    def get_by_table(cls, session, table, release_id):
        query = session.query(cls.table_code, cls.property_code, cls.data_type)
        query = query.filter_by(table_code=table)
        query = filter_by_release(query, cls.start_release_ic, cls.end_release_ic, release_id)
        query = filter_by_release(query, cls.start_release_mv, cls.end_release_mv, release_id)
        data = pd.read_sql_query(query.statement, session.connection())
        return data

    @classmethod
    def get_from_several_tables(cls, session, tables, release_id):
        query = session.query(cls.table_code, cls.property_code, cls.data_type)
        query = query.filter(cls.table_code.in_(tables))
        query = filter_by_release(query, cls.start_release_ic, cls.end_release_ic, release_id)
        query = filter_by_release(query, cls.start_release_mv, cls.end_release_mv, release_id)
        data = pd.read_sql_query(query.statement, session.connection())
        return data

    @classmethod
    def get_by_table_version_id(cls, session, table_version_id):
        query = session.query(cls.table_code, cls.property_code, cls.data_type)
        query = query.filter_by(table_version_id=table_version_id)
        return pd.read_sql_query(query.statement, session.connection())

class ViewOpenKeys(Base):
    __tablename__ = "open_keys"

    property_code = Column(String, primary_key=True)
    data_type = Column(String, primary_key=True)
    start_release = Column(Integer)
    end_release = Column(Integer)

    @classmethod
    def get_keys(cls, session, dimension_codes, release_id):
        query = session.query(cls.property_code, cls.data_type)
        query = query.filter(cls.property_code.in_(dimension_codes))
        query = filter_by_release(query, cls.start_release, cls.end_release, release_id)
        data = pd.read_sql_query(query.statement, session.connection())
        return data

    @classmethod
    def get_all_keys(cls, session, release_id):
        query = session.query(cls.property_code, cls.data_type)
        query = filter_by_release(query, cls.start_release, cls.end_release, release_id)
        data = pd.read_sql_query(query.statement, session.connection())
        return data

class ViewDataTypes(Base):
    __tablename__ = "data_types"

    datapoint = Column(String, primary_key=True)
    data_type = Column(String, primary_key=True)
    start_release = Column(Integer)
    end_release = Column(Integer)

    @classmethod
    def get_data_types(cls, session, datapoints, release_id):
        results = []
        batch_size = 2000
        batch_start = 0

        while batch_start < len(datapoints):
            batch_end = batch_start + batch_size
            datapoints_batch = datapoints[batch_start:batch_end]
            query = session.query(cls.datapoint, cls.data_type)
            query = filter_by_release(query, cls.start_release, cls.end_release, release_id)
            query = query.filter(cls.datapoint.in_(datapoints_batch))
            results.append(pd.read_sql_query(query.statement, session.connection()))
            batch_start += batch_size

        data = pd.concat(results, axis=0)
        return data

class ViewSubcategoryItemInfo(Base):
    __tablename__ = "subcategory_info"

    subcategory_id = Column(Integer, primary_key=True)
    item_code = Column(String, primary_key=True)
    is_default_item = Column(Boolean)
    parent_item_code = Column(String)
    ordering = Column(Integer)
    arithmetic_operator = Column(String, nullable=True)
    comparison_symbol = Column(String, nullable=True)
    start_release_id = Column(Integer)
    end_release_id = Column(Integer)

    @classmethod
    def get_info(cls, session, subcategory_id, release_id=None):
        query = session.query(cls.item_code, cls.is_default_item, cls.parent_item_code,
                              cls.ordering,
                              cls.arithmetic_operator,
                              cls.comparison_symbol).filter(cls.subcategory_id == subcategory_id)
        query = filter_by_release(query, cls.start_release_id, cls.end_release_id, release_id)
        query = query.order_by(cls.ordering)
        data = pd.read_sql_query(query.statement, session.connection())
        return data

class ViewHierarchyVariables(Base):
    __tablename__ = "hierarchy_variables"

    subcategory_id = Column(Integer, primary_key=True)
    variable_vid = Column(Integer, primary_key=True)
    main_property_code = Column(String, primary_key=True)
    context_property_code = Column(String)
    cell_code = Column(String)
    item_code = Column(String)
    start_release_id = Column(Integer)
    end_release_id = Column(Integer)

    @classmethod
    def get_subcategory_data(cls, session, subcategory_id, release_id):
        query = session.query(cls.cell_code, cls.variable_vid, cls.main_property_code,
                              cls.context_property_code,
                              cls.item_code).filter(
            cls.subcategory_id == subcategory_id)
        query = filter_by_release(query, cls.start_release_id, cls.end_release_id, release_id)
        data = pd.read_sql_query(query.statement, session.connection())
        return data

class ViewHierarchyVariablesContext(Base):
    __tablename__ = "hierarchy_variables_context"

    variable_vid = Column(Integer, primary_key=True)
    context_property_code = Column(String, primary_key=True)
    item_code = Column(String)
    start_release_id = Column(Integer)
    end_release_id = Column(Integer)

    @classmethod
    def get_context_from_variables(cls, session, variables: List[int], release_id=None):
        # Make batches of 1000 variables
        results = []
        batch_size = 1000
        for i in range(0, len(variables), batch_size):
            batch_end = i + batch_size
            variables_batch = variables[i:batch_end]
            query = session.query(cls.variable_vid, cls.context_property_code, cls.item_code).filter(
                cls.variable_vid.in_(variables_batch))
            query = filter_by_release(query, cls.start_release_id, cls.end_release_id, release_id)
            results.append(pd.read_sql_query(query.statement, session.connection()))
        data = pd.concat(results, axis=0)
        # Removing duplicates to avoid issues later with default values
        data = data.drop_duplicates(keep='first').reset_index(drop=True)
        return data

class ViewHierarchyPreconditions(Base):
    __tablename__ = "hierarchy_preconditions"

    expression = Column(String, primary_key=True)
    operation_code = Column(String, primary_key=True)
    variable_code = Column(String, primary_key=True)

    @classmethod
    def get_preconditions(cls, session):
        query = session.query(cls)
        return pd.read_sql_query(query.statement, session.connection())

class ViewOperations(Base):
    __tablename__ = "operation_list"

    operation_version_id = Column(Integer, primary_key=True)
    operation_code = Column(String)
    expression = Column(String)
    start_release = Column(Integer)
    end_release = Column(Integer)
    precondition_operation_version_id = Column(Integer)

    @classmethod
    def get_operations(cls, session):
        query = session.query(cls).distinct()
        operations = pd.read_sql_query(query.statement, session.connection())
        return operations.to_dict(orient="records")

    @classmethod
    def get_expression_from_operation_code(cls, session, operation_code):
        query = session.query(cls.expression).filter(cls.operation_code == operation_code)
        query = filter_by_release(query, cls.start_release, cls.end_release, None)
        return query.one_or_none()

    @classmethod
    def get_preconditions_used(cls, session):
        query = session.query(cls)
        preconditions = query.filter(cls.operation_version_id.is_not(None)).distinct().all()
        preconditions_ids = list(set([p.precondition_operation_version_id for p in
                                      query.filter(cls.precondition_operation_version_id.is_not(None)).distinct().all()]))
        query = session.query(cls)

        query = query.filter(cls.operation_version_id.in_(preconditions_ids)).distinct()
        preconditions = pd.read_sql_query(query.statement, session.connection())

        return preconditions.to_dict(orient="records")

class ViewModules(Base):
    __tablename__ = "module_from_table"

    module_code = Column(String, primary_key=True)
    table_code = Column(String, primary_key=True)
    from_date = Column(Date)
    to_date = Column(Date)

    @classmethod
    def get_all_modules(cls, session):
        query = session.query(cls.module_code, cls.table_code).distinct()
        return pd.read_sql_query(query.statement, session.connection())

    @classmethod
    def get_modules(cls, session, tables, release_id=None):
        query = session.query(cls.module_code, cls.table_code)
        query = query.filter(cls.table_code.in_(tables))
        result = query.all()
        if len(result) == 0:
            return []
        module_list = [r[0] for r in result]
        return list(set(module_list))

class ViewOperationFromModule(Base):
    __tablename__ = "operations_versions_from_module_version"

    module_version_id = Column(Integer, primary_key=True)
    operation_version_id = Column(Integer, primary_key=True)
    module_code = Column(String)
    from_date = Column(Date)
    to_date = Column(Date)
    expression = Column(String)
    operation_code = Column(String)
    precondition_operation_version_id = Column(Integer)
    is_active = Column(Boolean, nullable=False)
    severity = Column(String(20), nullable=False)
    operation_scope_id = Column(Integer)

    @classmethod
    def get_operations(cls, session, module_code, ref_date):
        query = session.query(
            cls.module_code, cls.from_date, cls.to_date, cls.expression, cls.operation_code, cls.operation_version_id)
        query = query.filter(cls.module_code == module_code)
        query = filter_by_date(query, cls.from_date, cls.to_date, ref_date)
        return pd.read_sql_query(query.statement, session.connection()).to_dict(orient="records")

    @classmethod
    def get_module_version_id_from_operation_vid(cls, session, operation_version_id):
        query = session.query(cls.module_version_id, cls.module_code, cls.from_date, cls.to_date)
        query = query.filter(cls.operation_version_id == operation_version_id).distinct()
        return pd.read_sql_query(query.statement, session.connection()).to_dict(orient="records")

    @classmethod
    def get_operations_from_moduleversion_id(cls, session, module_version_id, with_preconditions=True, with_errors=False):
        query = session.query(
            cls.module_code, cls.from_date, cls.to_date, cls.expression, cls.operation_code, cls.operation_version_id,
            cls.precondition_operation_version_id, cls.is_active, cls.severity)
        query = query.filter(cls.module_version_id == module_version_id).distinct()
        reference = pd.read_sql_query(query.statement, session.connection())
        not_errors = []
        preconditions_to_remove = []
        if not with_errors:
            not_errors = session.query(OperationNode.nodeid.label('operation_version_id')).distinct()
            not_errors = pd.read_sql_query(not_errors.statement, session.connection())
            not_errors = list(not_errors['operation_version_id'])
            reference = reference[reference['operation_version_id'].isin(not_errors)]
        if not with_preconditions:
            preconditions = session.query(ViewPreconditionInfo.operation_version_id).distinct()
            preconditions = pd.read_sql_query(preconditions.statement, session.connection())
            preconditions_to_remove = list(preconditions['operation_version_id'])
            reference = reference[~reference['operation_version_id'].isin(preconditions_to_remove)]

        return reference.to_dict(orient="records")

class ViewOperationInfo(Base):
    __tablename__ = "operation_info"

    operation_node_id = Column(Integer, primary_key=True)
    operation_version_id = Column(Integer)
    parent_node_id = Column(Integer)
    operator_id = Column(Integer)
    symbol = Column(String(20))
    argument = Column(String(50))
    operator_argument_order = Column(Integer)
    is_leaf = Column(Boolean, nullable=False)
    scalar = Column(String)
    operand_reference_id = Column(Integer, nullable=False)
    operand_reference = Column(String)
    x = Column(Integer)
    y = Column(Integer)
    z = Column(Integer)
    item_id = Column(Integer)
    property_id = Column(Integer)
    variable_id = Column(Integer)
    use_interval_arithmetics = Column(Boolean, nullable=False)
    fallback_value = Column(String(50))

    @classmethod
    def get_operation_info(cls, session, operation_version_id):
        query = session.query(cls).filter(cls.operation_version_id == operation_version_id)
        return pd.read_sql_query(query.statement, session.connection()).to_dict(orient="records")

    @classmethod
    def get_operation_info_df(cls, session, operation_version_ids):
        rename_dict = {
            "operation_node_id": "NodeID",
            "operation_version_id": "OperationVID",
            "operator_id": "OperatorID",
            "operator_argument_order": "Order",
            "parent_node_id": "ParentNodeID",
            "symbol": "symbol",
            "argument": "argument",
            "operand_reference": "OperandReference",
            "use_interval_arithmetics": "UseIntervalArithmetics",
            "fallback_value": "FallbackValue",
            "operand_reference_id": "OperandReferenceId",
            "scalar": "Scalar",
            "is_leaf": "IsLeaf",
            "item_id": "ItemID",
            "property_id": "PropertyID",
            "variable_id": "VariableID"
        }
        query = session.query(cls).filter(cls.operation_version_id.in_(operation_version_ids))
        df = pd.read_sql_query(query.statement, session.connection())
        df = df.rename(columns=rename_dict)
        return df

class ViewTableInfo(Base):
    __tablename__ = "table_info"

    table_code = Column(String, primary_key=True)
    table_version_id = Column(Integer, primary_key=True)
    table_id = Column(Integer)
    module_code = Column(String)
    module_version_id = Column(Integer)
    variable_id = Column(Integer)
    variable_version_id = Column(Integer)

    @classmethod
    def get_tables_from_module_code(cls, session, module_code):
        query = session.query(cls.table_code, cls.table_version_id).filter(cls.module_code == module_code).distinct()
        return pd.read_sql_query(query.statement, session.connection()).to_dict(orient="records")

    @classmethod
    def get_tables_from_module_version(cls, session, module_version_id):
        query = session.query(cls.table_code, cls.table_version_id).filter(cls.module_version_id == module_version_id).distinct()
        return pd.read_sql_query(query.statement, session.connection()).to_dict(orient="records")

    @classmethod
    def get_variables_from_table_code(cls, session, table_code, to_dict=True):
        query = session.query(cls.variable_id, cls.variable_version_id).filter(cls.table_code == table_code)
        data = pd.read_sql_query(query.statement, session.connection())
        if to_dict:
            return data.to_dict(orient="records")
        return data

    @classmethod
    def get_variables_from_table_version(cls, session, table_version_id):
        query = session.query(cls.variable_id, cls.variable_version_id).filter(cls.table_version_id == table_version_id)
        return pd.read_sql_query(query.statement, session.connection()).to_dict(orient="records")

    @classmethod
    def get_intra_module_variables(cls, session):
        query = session.query(cls.variable_version_id, cls.module_code).distinct()
        module_data = pd.read_sql_query(query.statement, session.connection())
        intra_module_data = module_data.drop_duplicates(subset=["variable_version_id"], keep=False,
                                                        ignore_index=True)
        del module_data
        intra_module_variables = intra_module_data['variable_version_id'].unique().tolist()
        del intra_module_data
        return intra_module_variables

    @classmethod
    def is_intra_module(cls, session, table_codes):
        query = session.query(cls.table_code, cls.module_code).distinct().filter(cls.table_code.in_(table_codes))
        module_data = pd.read_sql_query(query.statement, session.connection())

        all_combinations = module_data.groupby("table_code")["module_code"].apply(list).reset_index(
            drop=False).to_dict(orient="records")

        intersect_set = None
        for combination in all_combinations:
            if intersect_set is None:
                intersect_set = set(combination['module_code'])
            else:
                intersect_set = intersect_set.intersection(set(combination['module_code']))

        if intersect_set is None:
            return False
        return len(intersect_set) > 0

class ViewPreconditionInfo(Base):
    __tablename__ = "precondition_info"

    operation_node_id = Column(Integer, primary_key=True)
    operation_version_id = Column(Integer)
    operation_code = Column(String)
    variable_type = Column(String)
    variable_id = Column(Integer)
    variable_version_id = Column(Integer)
    variable_code = Column(String)

    @classmethod
    def get_preconditions(cls, session):
        query = session.query(cls.operation_version_id, cls.operation_code, cls.variable_code).distinct()
        return pd.read_sql_query(query.statement, session.connection()).to_dict(orient="records")

    @classmethod
    def get_precondition_code(cls, session, variable_version_id):
        query = session.query(cls.variable_code).filter(cls.variable_version_id == variable_version_id).distinct()
        return query.one()

class ViewHierarchyOperandReferenceInfo(Base):
    __tablename__ = "hierarchy_operand_reference"

    operation_code = Column(String, primary_key=True)
    operation_node_id = Column(Integer, primary_key=True)
    cell_id = Column(Integer, primary_key=True)
    variable_id = Column(Integer)

    @classmethod
    def get_operations(cls, session, cell_id):
        query = session.query(cls.operation_code, cls.operation_node_id).filter(cls.cell_id == cell_id).distinct()
        operations = pd.read_sql_query(query.statement, session.connection()).to_dict(orient="records")
        return operations

    @classmethod
    def get_hierarchy_operations(cls, session, var_id_list):
        query = session.query(cls).filter(cls.variable_id.in_(var_id_list))
        possible_op_codes = []

        df = pd.read_sql_query(query.statement, session.connection())
        grouped_code = df.groupby("operation_code")
        for elto_k, elto_v in grouped_code.groups.items():
            if len(grouped_code.groups[elto_k]) == len(var_id_list):
                possible_op_codes.append(elto_k)
        return possible_op_codes

class ViewReportTypeOperandReferenceInfo(Base):
    __tablename__ = "report_type_operand_reference_info"

    operation_code = Column(String, primary_key=True)
    operation_node_id = Column(Integer, primary_key=True)
    cell_id = Column(Integer, primary_key=True)
    variable_id = Column(Integer)
    report_type = Column(String)
    table_version_id = Column(Integer)
    table_version_vid = Column(Integer)
    sub_category_id = Column(Integer)

    @classmethod
    def get_operations(cls, session, cell_id):
        query = session.query(cls.operation_code, cls.operation_node_id).filter(cls.cell_id == cell_id).distinct()
        operations = pd.read_sql_query(query.statement, session.connection()).to_dict(orient="records")
        return operations
