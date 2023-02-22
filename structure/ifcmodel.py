"""
Retrives the beam geometry from IFC file
IFC4x version

Required packages:
    * ifcopenshell: pip install ifcopenshell
"""

# LIBS
from __future__ import annotations
import ifcopenshell
import ifcopenshell.util.representation as ifcrep
import ifcopenshell.util.unit as ifcunit
import ifcopenshell.util.placement as ifcplace
import numpy as np
from structure.conceptmodel import classBeam, classConceptModel, SectionType, classSegment
from datetime import datetime



# CONSTANTS
_supportedIfcClasses = ['IfcBeam','IfcColumn','IfcMember']


# CLASSES
class bimBeam(classBeam):
    lengthTol = 0.001 
    # PredefinedType: pset dictionary key
    __psetskeyLength = {'BEAM': ['Pset_BeamCommon','Span'], 
                        'COLUMN': None
                        }
    __psetskeyId = {'BEAM': ['Pset_BeamCommon','id'], 
                    'COLUMN': ['Pset_ColumnCommon','id'],
                    'MEMBER': ['Pset_MemberCommon','id'],
                    }

    def __init__(self, 
                 name: str = '', 
                 IniPos: list[float] = None,
                 ifcFile: ifcopenshell.file = None, 
                 ifcBeam: ifcopenshell.entity_instance = None, 
                 context: str = None, 
                 subcontext: str = None
                 ) -> None:        
        super().__init__(name, IniPos)
        np_matrix = np.identity(3) # creates identity matrix
        self.MapTransfMatrix = np_matrix.tolist()
        self.guid = ''
        self.PropSet = {}
        self.IfcBeam: ifcopenshell.entity_instance
        

        if ifcFile and ifcBeam and context:
            self.importFromIfc(ifcFile, ifcBeam, context, subcontext)
    
    def __setTranfByXandZ(self, X: list[float], Z: list[float]) -> None:
        """
        Calculates the tranformation matrix (Mapping target for representation)
        """
        aX = np.array(X)
        aZ = np.array(Z)
        aY = np.cross(aZ,aX)
        self.MapTransfMatrix.clear()
        for x, y, z in zip(aX, aY, aZ):
            row = [x, y, z]
            self.MapTransfMatrix.append(row.copy())

    def __MapTransfCoords(self, sourceCoords: list[float]) -> list[float]:
        """
        Apply the transformation matrix to obtain the representation (source -> target)
        * input: mapping source coordinate list (sx, sy, sz)
        * return: target coordinate list
        """
        M = np.array(self.MapTransfMatrix)
        sV = np.array(sourceCoords)
        tV = np.matmul(M, sV)
        return [tV[0], tV[1], tV[2]]





    def importFromIfc(self, 
                      ifcFile: ifcopenshell.file, 
                      ifcBeam: ifcopenshell.entity_instance, 
                      context: str, 
                      subcontext: str) -> None:
        """
        Imports the beam information from an IFC file
        * ifcFile: IFC file loaded by ifcopenshell.open()
        * ifcBeam: IFC beam instance to be imported
        * context: Context of the representation to be imported
        * subcontext: Subcontext of the representation to be imported
        """

        fconvL = ifcunit.calculate_unit_scale(ifcFile) # conversion from the length unit of IFC file to S.I. (meters)

        # only for IfcBeam class
        if not ifcBeam.is_a() in _supportedIfcClasses: 
            raise Exception(f'Error! The instance {ifcBeam} is not a IfcBeam class.')   

        # gets the object placement matrix
        self.locToGlobTransfMtx = ifcplace.get_local_placement(ifcBeam.ObjectPlacement)
        # convert the translational terms to S.I.
        for i in range(3): self.locToGlobTransfMtx[i,3] *= fconvL

        # gets the  representation (IfcShapeRepresentation)
        representation = ifcrep.get_representation(ifcBeam, context, subcontext) 
        if not representation.is_a('IfcShapeRepresentation'):
            raise Exception(f'Representation type {representation.is_a()} not supported.')

        repItems = representation.Items # IfcRepresentationItem list
        repItem = repItems[0] # 1st item (IfcMappedItem)
        if not repItem.is_a('IfcMappedItem'):
            raise Exception(f'Representation item type {repItem.is_a()} not supported.')

        mapSource = repItem.MappingSource # MappingSource attribute (IfcRepresentationMap)
        mapOrigin = mapSource.MappingOrigin # MappingOrigin attribute (IfcAxis2Placement3D)
        mapTarget = repItem.MappingTarget # MappingTarget attribute (IfcCartesianTransformationOperator3D)
        if not mapTarget.is_a('IfcCartesianTransformationOperator3D'):
            raise Exception(f'Mapping target type {mapTarget.is_a()} not supported.')
        if mapTarget.Axis1 or mapTarget.Axis2 or mapTarget.Scale != 1. or mapTarget.Axis3:
            raise Exception(f'Axis 1, 2, 3 or scale attribuites of ' + \
                'IfcCartesianTransformationOperator3D not implemented.')
        TransfOrigin = mapTarget.LocalOrigin[0] # LocalOrigin list 1st item (IfcCartesionPoint)
        if TransfOrigin[0] != 0 or TransfOrigin[1] != 0 or TransfOrigin[2] != 0:
            raise Exception(f'Error! Transformation origin not equal to (0,0,0).') # TODO: include transformation for translation

        if not mapOrigin.is_a('IfcAxis2Placement3D'):
            raise Exception(f'Error! Mapping origin type {mapOrigin.is_a()} not supported.')

        mapOriginLoc = mapOrigin.Location[0] # Location attribute (IfcCartesionPoint)

        if mapOrigin.Axis or mapOrigin.RefDirection: # Axis and RefDirection attributes (IfcDirection)        
            if mapOrigin.Axis: Z = list(mapOrigin.Axis.DirectionRatios)
            else: Z = [0.,0.,1.]
            if mapOrigin.RefDirection: X = list(mapOrigin.RefDirection.DirectionRatios)
            else: X = [1.,0.,0.]
            self.__setTranfByXandZ(X, Z)

        mapRep = mapSource.MappedRepresentation # MappedRepresentation attribute (IfcShapeRepresentation)
        if not mapRep.is_a('IfcShapeRepresentation'):
            raise Exception(f'Error! Mapping source representation {mapRep.is_a()} not supported.')
        
        citems = mapRep.ContextOfItems # ContextOfItems attribute (IfcRepresentationContext)
        cid = citems.ContextIdentifier # ContextIdentifier (IfcLabel)
        if subcontext != cid:
            raise Exception(f'Error! Subcontext not equal to the representation items context ({cid}).')

        mapRepItems = mapRep.Items # Items attributes (list of IfcRepresentationItem)
        if len(mapRepItems) > 1:
            raise Exception('Error! Number of Mapping representation items greater then 1 ' + \
                            f'({len(mapRepItems)}) not supported.')

        mapRepItem = mapRepItems[0] # 1st item (IfcTrimmedCurve)
        if not mapRepItem.is_a('IfcTrimmedCurve'):
            raise Exception(f'Error! Representation item type ({mapRepItem.is_a()}) not supported.')

        basisCurve = mapRepItem.BasisCurve # BasisCurve attribute (IfcCurve -> IfcLine)
        if not basisCurve.is_a('IfcLine'):
            raise Exception(f'Error! Basis curve type ({basisCurve.is_a()}) not supported.')

        masterRep = mapRepItem.MasterRepresentation # MasterRepresentation attribute (IfcTrimmingPreference)
        if masterRep != 'CARTESIAN':
            raise Exception(f'Error! Master representation {masterRep} not supported.')

        trim1, trim2 = mapRepItem.Trim1, mapRepItem.Trim2 # Trimming points (IfcTrimmingSelect -> IfcCartesianPoint)
        if len(trim1) > 1 or len(trim2) > 1:
            raise Exception(f'Error! Number of trimming points for Trim1 ({len(trim1)}) ' + \
                f'or Trim2({len(trim1)}) greater than 1.'
                )

        t1, t2 = trim1[0], trim2[0]
        if not t1.is_a('IfcCartesianPoint') or not t2.is_a('IfcCartesianPoint'):
            raise Exception(f'Error! Trimming point 1 type ({t1.is_a()}) or 2 ({t2.is_a()}) '+ \
                'not supported.'
                )
        
        _EndA, _EndB = [0.,0.,0.], [0.,0.,0.] # in local coordinates
        for i in range(3):
            # adds the origin coordinates to the mapping represantation
            _EndA[i], _EndB[i] = t1[0][i] + mapOriginLoc[i], t2[0][i] + mapOriginLoc[i]
            # converts units
            _EndA[i] *= fconvL
            _EndB[i] *= fconvL

        # applies the coord. transformation (Mapping Target) and stores the results (local coordinates)
        L_EndA = self.__MapTransfCoords(_EndA.copy())
        L_EndB = self.__MapTransfCoords(_EndB.copy())
        self.IniPos = L_EndA
        self.AddSegmentByEnd(L_EndB)
        
        self.PropSet = ifcopenshell.util.element.get_psets(ifcBeam) # gets the property sets
        predefType = ifcBeam.PredefinedType # gets the pset key for length        
        psetKeysL = self.__psetskeyLength[predefType] # gets the pset key for id        
        psetKeysID = self.__psetskeyId[predefType]

        if psetKeysL:
            # gets the beam length
            ifcLength = fconvL*self.PropSet[psetKeysL[0]][psetKeysL[1]]
            calcLength = self.length
            # verify the length
            if abs(calcLength-ifcLength)/ifcLength > self.lengthTol:
                print(f'Warning! Calculated length {calcLength}m different of the IFC pset data length {ifcLength}m.')
        
        id1 = self.PropSet[psetKeysID[0]][psetKeysID[1]]
        id2 = ifcBeam.GlobalId
        self.name = ifcBeam.Name # f'{id1} | {id2}'
        self.guid = ifcBeam.GlobalId
    
    # ==== export to IFC file ==== #
    def exportBeamToIfc(
            self, 
            IfcInfo: ifcInfo,
            refPosition: ifcopenshell.entity_instance = None # (IfcAxis2Placement3D) rerefence (e.g., storey) position
            ) -> ifcopenshell.entity_instance:
        """
        Export beam to Ifc
        * return: entity_instance of the objecte created
        """

        if not refPosition:
            refPoint = _createCartesianPnt(IfcInfo.ifcFile, self.RefCoords) # TODO: evaluate the possibility to consider a reference location (e.g., groups, sets, storeys)
            refPosition = _createAxis2Place3D(IfcInfo.ifcFile, refPoint) # TODO: handle the orientation (Axis and RefDirection)

        # creates the ObjectPlacement
        ifcObjPlace = self.__createPlacement(IfcInfo.ifcFile, IfcInfo.WorldCoordSys, refPosition)

        # creates the object 'Axis' representation
        AxisRep = _createAxisRep(
            IfcInfo,
            self.IniPos, 
            self.LastPos, 
        )

        # creates the object 'Body' represenation
        BodyRep = _createBodyRep(IfcInfo, self)

        # creates the product definition shape
        ifcProdDefShape = IfcInfo.ifcFile.create_entity(
            type='ifcProductDefinitionShape',
            Representations=[AxisRep, BodyRep], # TODO: include body representation
        )

        ifcBeam = IfcInfo.ifcFile.create_entity(
            type='IfcBeam',
            GlobalId = ifcopenshell.guid.new(),
            OwnerHistory = IfcInfo.ownerHistory,
            Name = self.name, #beam.name,
            Description = self.Description, # beam.Description,
            # TODO: ObjectType
            ObjectPlacement = ifcObjPlace,
            Representation = ifcProdDefShape,
            # TODO: Tag    
            # TODO: PredefinedType
            )
        
        self.IfcBeam = ifcBeam
        return ifcBeam

    def __createPlacement(self, 
                          ifcFile: ifcopenshell.file,
                          WorldCoordSys: ifcopenshell.entity_instance, # global (building) origin
                          refPosition: ifcopenshell.entity_instance, # (IfcAxis2Placement3D) reference coordinate system
                         ) -> ifcopenshell.entity_instance:

        point = _createCartesianPnt(ifcFile, self.IniPos)
        Position = _createAxis2Place3D(ifcFile, point)
        
        return _createIfcObjPlace(self, 
                                  ifcFile, 
                                  WorldCoordSys, 
                                  refPosition, 
                                  Position)




# ==== ifcBeamList CLASS DEFINITION ==== #
class ifcBeamList(list[bimBeam]):
    def __init__(self, conceptModel: classConceptModel, ifcFilePath: str = None):
        """
        * ifcFilePath: (str) path to the IFC file
        """
        super().__init__()
        self.conceptModel = conceptModel
        if ifcFilePath:
            ifcFile = ifcopenshell.open(ifcFilePath)
            self.ImportFromIFC(ifcFile)
        
    def ImportFromIFC(self, ifcFile: ifcopenshell.file) -> None:
        ifcBeams = GetMembersList(ifcFile)

        for ifcBeam in ifcBeams:
            newBeam = bimBeam(ifcFile=ifcFile, 
                              ifcBeam=ifcBeam, 
                              context="Model", 
                              subcontext="Axis")
            if newBeam: self.append(newBeam)
        
        print(f'{len(self)} beams imported fom IFC file.')

    def ByGUID(self, guid: str) -> bimBeam:
        result = None
        for beam in self:
            if beam.guid == guid:
                result = beam
                break
        return result


# ==== ifcModel CLASS DEFINITION ==== #
class ifcInfo:
    def __init__(self) -> None:
        self.ifcFile: ifcopenshell.file 
        self.ownerHistory: ifcopenshell.entity_instance # (IfcOwnerHistory)
        self.WorldOrigin: ifcopenshell.entity_instance # (IfcCartesianPoint)
        self.WorldCoordSys: ifcopenshell.entity_instance # (IfcAxis2Placement3D)
        self.WorldCartesianOp: ifcopenshell.entity_instance # (ifcCartesianTransformationOperator3D)
        self.WorldLocPlace: ifcopenshell.entity_instance # (ifcLocalPlacement)
        self.ModelContext: ifcopenshell.entity_instance # (IfcGeometricRepresentationContext)
        self.AxisSubContext: ifcopenshell.entity_instance # (IfcGeometricRepresentationSubContext)
        self.BodySubContext: ifcopenshell.entity_instance # (IfcGeometricRepresentationSubContext)
        self.unitsAssign: ifcopenshell.entity_instance # (IfcUnitAssignment)
        self.Project: ifcopenshell.entity_instance  # (IfcProject)
        self.Site: ifcopenshell.entity_instance # (IfcSite)
        self.Building: ifcopenshell.entity_instance  # (IfcBuilding)
        self.ExportedBeams = list() # list of IfcBeams
        

class ifcModel(classConceptModel):
    def __init__(self, ifcFilePath: str = None) -> None:
        super().__init__()
        self._Beams = ifcBeamList(self, ifcFilePath)
        self.IfcInfo = ifcInfo()        

    def ExportToIFC(self, ifcFilePath: str, beamIndexes: slice = None) -> None:
        self.IfcInfo.ifcFile = ifcopenshell.file(schema='IFC4')

        self.IfcInfo.unitsAssign = _writeIfcUnits(self.IfcInfo.ifcFile) # exports units

        self.IfcInfo.WorldOrigin = _createCartesianPnt(
            self.IfcInfo.ifcFile,
            [0.,0.,0.]
        )

        self.IfcInfo.WorldCoordSys = _createAxis2Place3D(
            self.IfcInfo.ifcFile, 
            self.IfcInfo.WorldOrigin
        ) # TODO: handle the orientation (Axis and RefDirection)

        self.IfcInfo.WorldCartesianOp = self.IfcInfo.ifcFile.create_entity(
            type='ifcCartesianTransformationOperator3D',
            LocalOrigin=self.IfcInfo.WorldOrigin, 
            Scale=1.
        )

        self.IfcInfo.WorldLocPlace = _createIfcLocPlace(
            self.IfcInfo.ifcFile, 
            RelPlace=self.IfcInfo.WorldCoordSys
        )

        self.IfcInfo.ModelContext = _createModelContext(self.IfcInfo) # TODO: handle the precision

        self._writeProjectData(self.IfcInfo) # exports original model info
        self.IfcInfo.Building = _createBuilding(self.IfcInfo)

        self.IfcInfo.AxisSubContext = _createSubContext(
            self.IfcInfo.ifcFile, 'Axis', 
            self.IfcInfo.ModelContext, 
            'GRAPH_VIEW'
        )
        self.IfcInfo.BodySubContext = _createSubContext(
            self.IfcInfo.ifcFile, 
            'Body', 
            self.IfcInfo.ModelContext, 
            'MODEL_VIEW'
        )

        if beamIndexes == None: 
            for beam in self._Beams:
                self.IfcInfo.ExportedBeams.append(beam.exportBeamToIfc(self.IfcInfo))
        else: 
            for beam in self._Beams[beamIndexes]:
                self.IfcInfo.ExportedBeams.append(beam.exportBeamToIfc(self.IfcInfo))

        _createContainment(self.IfcInfo)

        self.IfcInfo.ifcFile.write(ifcFilePath)

    def _writeProjectData(self, IfcInfo: ifcInfo) -> ifcopenshell.entity_instance:

        prog = str(self.OriginInfo['Program'])
        ver = str(self.OriginInfo['Version'])
        description = f'Model exported from {prog}' + \
            f', version {ver} ' +\
            f'to IFC by NSG in {datetime.now()}'

        org = self.IfcInfo.ifcFile.create_entity(
            type='IfcOrganization', 
            Name='NSG',
            Description=description,
            #Addresses=['http://www.nsg.eng.br']
        )

        app = self.IfcInfo.ifcFile.create_entity(
            type='IfcApplication',
            ApplicationDeveloper=org,
            Version='1.0',
            ApplicationFullName='BIM conversion tools',
            ApplicationIdentifier='bim-tools'
        )

        person = self.IfcInfo.ifcFile.create_entity(
            type='IfcPerson',
            GivenName=self.OriginInfo['User']
        )

        personAndOrg = self.IfcInfo.ifcFile.create_entity(
            type='IfcPersonAndOrganization',
            ThePerson=person,
            TheOrganization=org
        )

        date = self.OriginInfo['Date']
        d = datetime.strptime(date, r'%d-%b-%Y')
        epoch_time = datetime(1970, 1, 1)
        delta = d - epoch_time       
        dateInSeconds = int(delta.total_seconds()) # from 01/01/1970

        IfcInfo.ownerHistory = self.IfcInfo.ifcFile.create_entity(
            type='IfcOwnerHistory',
            OwningUser=personAndOrg,
            OwningApplication=app,
            ChangeAction='NOCHANGE',
            CreationDate=dateInSeconds
        )
        
        IfcInfo.Project = IfcInfo.ifcFile.create_entity(
            type='IfcProject',
            GlobalId=ifcopenshell.guid.new(),
            OwnerHistory=IfcInfo.ownerHistory,
            Name='0001',
            LongName='Project name',
            Phase='Project status',
            RepresentationContexts=[IfcInfo.ModelContext],
            UnitsInContext=IfcInfo.unitsAssign            
        )
        
        IfcInfo.Site = IfcInfo.ifcFile.create_entity(
            type = 'IfcSite',
            GlobalId = ifcopenshell.guid.new(),
            OwnerHistory = IfcInfo.ownerHistory,
            Name = 'Site',
            ObjectPlacement = IfcInfo.WorldLocPlace,
            CompositionType = 'ELEMENT',
            # TODO: RefLatitude,
            # TODO: RefLongitude,
            # TODO: RefElevation,
        )

        return IfcInfo.Project






# ==== AUXILIARY METHODS ==== #

def GetMembersList(ifcFile: ifcopenshell.file) -> list[ifcopenshell.entity_instance]:
    """
    Returns the list of instances type 'ifcBeam', 'ifcColumn', and 'ifcMember'
    """
    instList = list()
    for ifcClass in _supportedIfcClasses:
        add = ifcFile.by_type(ifcClass)
        if add:
            instList.extend(add)
    print(f'{len(instList)} beams found in IFC file.')
    return instList.copy()


def _createContainment(IfcInfo: ifcInfo):
    return IfcInfo.ifcFile.create_entity(
        type='IfcRelContainedInSpatialStructure',
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=IfcInfo.ownerHistory,
        RelatedElements=IfcInfo.ExportedBeams,
        RelatingStructure=IfcInfo.Building
    )
    

def _createBuilding(IfcInfo: ifcInfo):
    return IfcInfo.ifcFile.create_entity(
        type='IfcBuilding',
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=IfcInfo.ownerHistory,
        Name='Platform Name', # TODO: get from model or input
        ObjectType='Offshore platform', # TODO: get from model or input
        ObjectPlacement=IfcInfo.WorldLocPlace,
        LongName='',
        CompositionType='ELEMENT',
        # TODO: include "IfcPostalAddress" (geo location)
    )

def _createUnit(ifcFile: ifcopenshell.file,
                UnitType: str, 
                Name: str, 
                Prefix: str = None
                ) -> ifcopenshell.entity_instance:
    data = {}
    data['UnitType'] = UnitType
    data['Name'] = Name
    if Prefix: data['Prefix'] = Prefix

    return ifcFile.create_entity(type='IfcSIUnit', **data)

def _createDerivedUnit(ifcFile: ifcopenshell.file,
                       UnitType: str,
                       BaseUnits: list[ifcopenshell.entity_instance],
                       Exponents: list[float],
                       ) -> ifcopenshell.entity_instance:
    Elements = []
    if len(BaseUnits) != len(Exponents):
        raise Exception('Error! Number of items in BaseUnits '+\
            'different of Expoents')
    for unit, exp in zip(BaseUnits, Exponents):
        Elements.append(
            ifcFile.create_entity(
                type='IfcDerivedUnitElement',
                Unit=unit,
                Exponent=exp
            )
        )
    
    return ifcFile.create_entity(
        Elements=Elements,
        type='IfcDerivedUnit',        
        UnitType=UnitType
    )



def _writeIfcUnits(ifcFile: ifcopenshell.file) -> ifcopenshell.entity_instance:
    """
    Write the units in the IFC file
    * return: IfcUnitAssignment
    """
    units = {}
    units['LENGTHUNIT'] = _createUnit(ifcFile,'LENGTHUNIT','METRE')
    units['AREAUNIT'] = _createUnit(ifcFile,'AREAUNIT','SQUARE_METRE')
    units['VOLUMEUNIT'] = _createUnit(ifcFile,'VOLUMEUNIT','CUBIC_METRE')
    units['PLANEANGLEUNIT'] = _createUnit(ifcFile, 'PLANEANGLEUNIT','RADIAN')
    units['MASSUNIT'] = _createUnit(ifcFile, 'MASSUNIT','GRAM','KILO')
    units['MASSDENSITYUNIT'] = _createDerivedUnit(
        ifcFile, 'MASSDENSITYUNIT' ,
        [units['MASSUNIT'], units['LENGTHUNIT']], 
        [1,-3]
        )
    
    units['MOMENTOFINERTIAUNIT'] = _createDerivedUnit(
        ifcFile, 'MOMENTOFINERTIAUNIT',
        [units['LENGTHUNIT']],
        [4]
        )

    units['TIMEUNIT'] = _createUnit(ifcFile,'TIMEUNIT','SECOND')
    units['FREQUENCYUNIT'] = _createUnit(ifcFile,'FREQUENCYUNIT','HERTZ')
    units['THERMODYNAMICTEMPERATUREUNIT'] = _createUnit(
        ifcFile, 'THERMODYNAMICTEMPERATUREUNIT', 'DEGREE_CELSIUS')

    unitList = []
    for unit in units.values(): unitList.append(unit)

    return ifcFile.create_entity(type='IfcUnitAssignment', Units=unitList)
    

def _createModelContext(IfcInfo: ifcInfo,
                        #ifcFile: ifcopenshell.file,
                        #WorldCoordSys: ifcopenshell.entity_instance, #(IfcAxis2Placement)
                        CoordSysDim: int = 3,
                        ContextType: str = 'Model', # (e.g., 'Model')
                        Precision: float = None,
                        TrueNorth: ifcopenshell.entity_instance = None,
                        ) -> ifcopenshell.entity_instance:

    data = {}
    data['WorldCoordinateSystem'] = IfcInfo.WorldCoordSys
    data['CoordinateSpaceDimension'] = CoordSysDim
    data['ContextType'] = ContextType
    if Precision: data['Precision'] = Precision
    if TrueNorth: data['TrueNorth'] = TrueNorth

    return IfcInfo.ifcFile.create_entity(
        type='IfcGeometricRepresentationContext', 
        **data
    ) 

def _createSubContext(ifcFile: ifcopenshell.file,
                      Identifier: str,
                      ParentContext: ifcopenshell.entity_instance, # (IfcGeometricRepresentationContext)
                      TargetView: str, # (IfcGeometricProjectionEnum) e.g., MODEL_VIEW, GRAPH_VIEW
                      Type: str = 'Model',
                      ) -> ifcopenshell.entity_instance:    

    return ifcFile.create_entity(type='IfcGeometricRepresentationSubContext',
                                 ContextIdentifier=Identifier,
                                 ContextType=Type,
                                 ParentContext=ParentContext,
                                 TargetView=TargetView,
                                 )

def _createIfcLocPlace(ifcFile: ifcopenshell.file,
                        RelTo: ifcopenshell.entity_instance = None,
                        RelPlace: ifcopenshell.entity_instance = None
                       ) -> ifcopenshell.entity_instance:

    data = {}
    if RelTo: data['PlacementRelTo'] = RelTo
    if RelPlace: data['RelativePlacement'] = RelPlace

    result = ifcFile.create_entity(
        type = 'IfcLocalPlacement',
        **data
        )

    return result   

def _createCartesianPnt(ifcFile: ifcopenshell.file,
                         Coordinates: list[float] = None
                        ) -> ifcopenshell.entity_instance:
    data = {}
    if Coordinates: data['Coordinates'] = Coordinates
    return ifcFile.create_entity(type='IfcCartesianPoint', **data)    


def _createAxis2Place3D(ifcFile: ifcopenshell.file,
                         Location: ifcopenshell.entity_instance = None, # (IfcCartesianPoint)
                         Axis: ifcopenshell.entity_instance = None,
                         RefDirection: ifcopenshell.entity_instance = None,
                        ) -> ifcopenshell.entity_instance:
    
    data = {}
    if Location: data['Location'] = Location
    if Axis: data['Axis'] = Axis
    if RefDirection: data['RefDirection'] = RefDirection    
    result = ifcFile.create_entity(type='IfcAxis2Placement3D', **data)
    return result


def _createIfcObjPlace(beam: classBeam,
                       ifcFile: ifcopenshell.file,
                       WorldOrigin: ifcopenshell.entity_instance, # (IfcAxis2Place3D) 
                       refPosition:  ifcopenshell.entity_instance, # (IfcAxis2Place3D) position of the group reference (e.g., storey)
                       Position: ifcopenshell.entity_instance, # (IfcAxis2Place3D) position of the entity (relative to refPosition and globalOrigin)
                      ) -> ifcopenshell.entity_instance:
    """
    Creates the IfcObjectPlacement based on the beam information
    * return: entity_instance of the objecte created
    """
    prevPlace = None
    for i in range(4): # same scheme of Revit IFC exported
        if i == 0: # global origin
            RelPlace = WorldOrigin
        elif i == 1: # global origin
            RelPlace = WorldOrigin
        elif i == 2: # Reference position (e.g., Storey, group, set)
            RelPlace = refPosition
        elif i == 3: # position relative to ref pos. relative to global origin
            RelPlace = Position
        else:
            #Location = None
            RelPlace = _createAxis2Place3D(ifcFile)

        prevPlace = _createIfcLocPlace(ifcFile, prevPlace, RelPlace)

    return prevPlace

'''    
def _createProdDefShape(ifcFile: ifcopenshell.file,
                        name: str = None,
                        description: str = None
                       ) -> ifcopenshell.entity_instance:
    """Creates the product definition shape"""
    return

'''
def _createIfcLine(ifcFile: ifcopenshell.file,
                   pointA: list[float],
                   pointB: list[float]
                  ) -> tuple[ifcopenshell.entity_instance,
                             ifcopenshell.entity_instance]:
    pnt = _createCartesianPnt(ifcFile, pointA)
    adir = np.array(pointB) - np.array(pointA)
    length = np.linalg.norm(adir)
    if length == 0: 
        print(f'Warning! Beam with zero length')
        length = 1
    adirnorm = adir*(1./length)
    dir = adirnorm.tolist()
    ifcDir = ifcFile.create_entity(type='IfcDirection', DirectionRatios=dir)
    ifcVec = ifcFile.create_entity(type='IfcVector',
                                   Orientation=ifcDir,
                                   Magnitude=length)
    ifcLine = ifcFile.create_entity(type='IfcLine', Pnt=pnt, Dir=ifcVec)
    return ifcLine, pnt

def _createAxisRep(
                   ifcInfo: ifcInfo,
                   pointA: list[float],
                   pointB: list[float],
                   ) -> ifcopenshell.entity_instance:
    
    
    ifcLine, trimm1 = _createIfcLine(ifcInfo.ifcFile, pointA, pointB)
    trimm2 = _createCartesianPnt(ifcInfo.ifcFile, pointB)
    trimmedCurve = ifcInfo.ifcFile.create_entity(
        type='IfcTrimmedCurve',
        BasisCurve = ifcLine,
        Trim1 = [trimm1],
        Trim2 = [trimm2],
        SenseAgreement = True, #'T',
        MasterRepresentation = 'CARTESIAN'
    )

    ifcShapeRep = ifcInfo.ifcFile.create_entity(
        type='ifcShapeRepresentation',
        ContextOfItems= ifcInfo.AxisSubContext,
        RepresentationIdentifier='Axis',
        RepresentationType= 'MappedRepresentation',
        Items=[trimmedCurve]
    )

    MapOrigin = _createAxis2Place3D(ifcInfo.ifcFile, ifcInfo.WorldOrigin)
    MapSource = ifcInfo.ifcFile.create_entity(
        type='ifcRepresentationMap',
        MappingOrigin=MapOrigin,
        MappedRepresentation=ifcShapeRep
    )

    MapItem = ifcInfo.ifcFile.create_entity(
        type='ifcMappedItem',
        MappingSource=MapSource,
        MappingTarget=ifcInfo.WorldCartesianOp
    )

    ifcShapeRep = ifcInfo.ifcFile.create_entity(
        type='ifcShapeRepresentation',
        ContextOfItems=ifcInfo.AxisSubContext,
        RepresentationIdentifier='Axis',
        RepresentationType='MappedRepresentation',
        Items=[MapItem]
    )

    return ifcShapeRep


def _createBodyRep(
                   IfcInfo: ifcInfo,
                   beam: bimBeam
                   ) -> ifcopenshell.entity_instance:
    # solids
    solids = []
    for segment in beam.SegmentList:
        solids.append(_createSegBodyRep(IfcInfo, segment))
    
    while solids.count(None)>0: solids.remove(None)

    # shape representation (IfcShapeRepresentation)
    MapRep = IfcInfo.ifcFile.create_entity(
        type = 'IfcShapeRepresentation',
        ContextOfItems = IfcInfo.BodySubContext,
        RepresentationIdentifier = 'Body',
        RepresentationType = 'SweptSolid',
        Items = solids
    )

    MapOrigin = IfcInfo.WorldCoordSys

    # MappingSource (ifcRepresentationMap)
    MapSource = IfcInfo.ifcFile.create_entity(
        type = 'ifcRepresentationMap',
        MappingOrigin = MapOrigin,
        MappedRepresentation = MapRep
    )

    # MappingTarget (ifcCartesianTransformationOperator3D)
    MapTarget = IfcInfo.WorldCartesianOp

    # MappedItem (ifcMappedItem)
    MapItem = IfcInfo.ifcFile.create_entity(
        type = 'ifcMappedItem',
        MappingSource = MapSource,
        MappingTarget = MapTarget
    )

    # (ifcShapeRepresentation)
    Representation = IfcInfo.ifcFile.create_entity(
        type = 'ifcShapeRepresentation',
        ContextOfItems = IfcInfo.BodySubContext,
        RepresentationIdentifier = 'Body',
        RepresentationType = 'MappedRepresentation',
        Items = [MapItem]
    )

    return Representation



def _createSegBodyRep(
                      IfcInfo: ifcInfo,
                      segment: classSegment
                     ) -> ifcopenshell.entity_instance:

    sectype = segment.properties.sectionPointer.sectype

    # cross section
    if sectype == SectionType.pipe_section:
        CrossSection = __createCircleHollowProfile(IfcInfo, segment)
    else:
        print(f'Section type {sectype} not supported yet.')
        return None
    
    # position and direction
    ExtrudAreaPosLoc = _createCartesianPnt(
        IfcInfo.ifcFile,
        segment.IniPos
        )
    
    vecA = np.array(segment.Direction)
    if segment.Direction[0] != 0 or segment.Direction[2] != 0:
        vecB = np.array([0.,1.,0])
    else:
        vecB = np.array([0.,0.,-1.])

    RefDir = np.cross(vecB,vecA).tolist()
    RefDirection = _createDirection(IfcInfo, RefDir)

    Axis = _createDirection(IfcInfo, segment.Direction)

    ExtrudAreaPos = _createAxis2Place3D(
        IfcInfo.ifcFile,
        ExtrudAreaPosLoc,
        Axis,
        RefDirection
    )

    ExtrudAreaDir = _createDirection(IfcInfo, [0.,0.,1.])

    # Extruded Area (IfcExtrudedAreaSolid)
    ExtrudArea = IfcInfo.ifcFile.create_entity(
        type = 'IfcExtrudedAreaSolid',
        SweptArea = CrossSection,
        Position = ExtrudAreaPos,
        ExtrudedDirection = ExtrudAreaDir,
        Depth = segment.length
    )

    return ExtrudArea

def __createCircleHollowProfile(
                      IfcInfo: ifcInfo,
                      segment: classSegment
                     ) -> ifcopenshell.entity_instance:

    section = segment.properties.sectionPointer
    ExtrudAreaCircleLoc = _createCartesianPnt(IfcInfo.ifcFile, [0.,0.,0.])
    ExtrudAreaCircleDir = _createDirection(IfcInfo, [1.,0.])
    ExtredAreaCirclePos = IfcInfo.ifcFile.create_entity(
        type='IfcAxis2Placement2D',
        Location=ExtrudAreaCircleLoc,
        RefDirection=ExtrudAreaCircleDir
    )

    CircleHollowProf = IfcInfo.ifcFile.create_entity(
        type='IfcCircleHollowProfileDef',
        ProfileType='AREA',
        ProfileName=f'Pipe {section.OD*1e3}mm x {section.th}mm',
        Position=ExtredAreaCirclePos,
        Radius=section.OD/2.,
        WallThickness=section.th
    )

    return CircleHollowProf
    


def _createDirection(ifcInfo: ifcInfo, dirRatios: list[float]
                        ) -> ifcopenshell.entity_instance:

    return ifcInfo.ifcFile.create_entity(
        type='IfcDirection',
        DirectionRatios = dirRatios
    )

