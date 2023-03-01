"""
Retrives the beam geometry from IFC file
IFC4x version

Required packages:
    * ifcopenshell: pip install ifcopenshell
"""

# LIBS
from __future__ import annotations
from dataclasses import dataclass
from email.mime import base
from pyclbr import Function
import ifcopenshell
import ifcopenshell.util.representation as ifcrep
import ifcopenshell.util.unit as ifcunit
import ifcopenshell.util.placement as ifcplace
import ifcopenshell.api
import numpy as np
from structure.conceptmodel \
    import classBeam, classConceptModel, SectionType, classEquipList, classEquipment, \
        classSegment, classMatList, classISection, classPipeSection, \
        classBoxSection
from datetime import datetime
import math



# CONSTANTS
_supportedIfcClasses = ['IfcBeam','IfcColumn','IfcMember']
_matColorList = [ # R, G, B factors (0. to 1)
    [0. , 0. , 1. ], # blue
    [0. , 0.8, 1. ], # light blue
    [0. , 0.5, 0. ], # green
    [0. , 1. , 0. ], # light green
    [1. , 0.6, 0. ], # orange
    [0.9, 0.8, 0. ], # dark yellow
    [0.6, 0.0, 0.9], # purple
]


# CLASSES
class getRGBcolor:
    def __init__(self, order: int) -> None:
        i = order % len(_matColorList)
        color = _matColorList[i]
        self.R = color[0]
        self.G = color[1]
        self.B = color[2]

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
                      subcontext: str,
                      funcErrorMsg: Function
                      ) -> None:
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
                funcErrorMsg(f'Warning! Calculated length {calcLength}m different of the IFC pset data length {ifcLength}m.')
                #print(f'Warning! Calculated length {calcLength}m different of the IFC pset data length {ifcLength}m.')
        
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
        ifcObjPlace = _createPlacement(IfcInfo.ifcFile, self.IniPos, IfcInfo.WorldCoordSys, refPosition)

        # creates the object 'Axis' representation
        ini = [0., 0., 0.] # relative to obj place
        end = np.array(self.LastPos)- np.array(self.IniPos) # relative to obj place
        AxisRep = _createAxisRep(
            IfcInfo,
            ini, 
            end.tolist(), 
        )

        # creates the object 'Body' represenation
        BodyRep = _createBeamBodyRep(IfcInfo, self)

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

def _createPlacement(
        ifcFile: ifcopenshell.file,
        Position: list[float],
        WorldCoordSys: ifcopenshell.entity_instance, # global (building) origin
        refPosition: ifcopenshell.entity_instance, # (IfcAxis2Placement3D) reference coordinate system
    ) -> ifcopenshell.entity_instance:
    """ Creates the ObjectPlacement instance required by IfcElement """

    point = _createCartesianPnt(ifcFile, Position)
    Position = _createAxis2Place3D(ifcFile, point)
    
    return _createIfcObjPlace(
        ifcFile, 
        WorldCoordSys, 
        refPosition, 
        Position
    )




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

    def FindByName(self, name: str) -> bimBeam:
        return super().FindByName(name)

# ==== ifcModel CLASS DEFINITION ==== #
class ifcInfo:
    def __init__(self, funcErrorMsg: Function) -> None:
        self.ErrorMsg = funcErrorMsg # error/warning issue method
        self.ifcFile: ifcopenshell.file 
        self.ownerHistory: ifcopenshell.entity_instance # (IfcOwnerHistory)
        self.WorldCoords: list[float] # [x, y, z]
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
        self.DefaultStorey: ifcopenshell.entity_instance # (IfcBuildingStorey) Storey for beams not contained in any set
        self.Storeys: list[ifcopenshell.entity_instance]  # (IfcBuildingStorey)
        self.EquipStorey: ifcopenshell.entity_instance # IfcBuildingStorey store to contain the equipments
        self.Storeys = []
        self.ExportedBeams = list() # list of IfcBeams
        

class ifcModel(classConceptModel):
    def __init__(self, ifcFilePath: str = None) -> None:
        super().__init__()
        self._Beams = ifcBeamList(self, ifcFilePath)
        self.IfcInfo = ifcInfo(self._Message)        

    def ExportToIFC(self, ifcFilePath: str, beamIndexes: slice = None) -> None:
        self.IfcInfo.ifcFile = ifcopenshell.file(schema='IFC4')

        self.IfcInfo.unitsAssign = _writeIfcUnits(self.IfcInfo.ifcFile) # exports units

        self.IfcInfo.WorldCoords = [0.,0.,0.] # TODO: revise to obtain from original model
        self.IfcInfo.WorldOrigin = _createCartesianPnt(
            self.IfcInfo.ifcFile,
            self.IfcInfo.WorldCoords
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


        self._exportEquips()


        if beamIndexes == None: 
            for beam in self._Beams:
                self.IfcInfo.ExportedBeams.append(beam.exportBeamToIfc(self.IfcInfo)) # TODO: include reference position
        else: 
            for beam in self._Beams[beamIndexes]:
                self.IfcInfo.ExportedBeams.append(beam.exportBeamToIfc(self.IfcInfo))


        self._createContainment(self.IfcInfo)
        _exportMaterialsToIfc(self.IfcInfo, self._MaterialList)
        _createMatAssociations(self.IfcInfo, self._Beams, self._MaterialList)
        _createStyles(self.IfcInfo, self._MaterialList)


        self.IfcInfo.ifcFile.write(ifcFilePath)

        print(self.Status())


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

        IfcInfo.Building = _createBuildingOrStorey(
            IfcInfo,
            'IfcBuilding',
            'Platform name', # TODO: get from model or input
            'Offshore platform', # TODO: get from model or input
            IfcInfo.WorldLocPlace,
            # TODO: include "IfcPostalAddress" (geo location)
        )

        self._createStoreys()

        storeyList = [IfcInfo.DefaultStorey]
        storeyList.extend(IfcInfo.Storeys.copy())
        storeyList.append(IfcInfo.EquipStorey) 
        _createRelAggreg(IfcInfo, IfcInfo.Building, storeyList)
        _createRelAggreg(IfcInfo, IfcInfo.Site, [IfcInfo.Building])
        _createRelAggreg(IfcInfo, IfcInfo.Project, [IfcInfo.Site])

        return IfcInfo.Project

    def _createStoreys(self) -> None:
        # default storey
        baseName = 'DefaultStorey'
        name = baseName
        i = 0
        while name in self.SetList.ListOfNames():
            i += 1
            name = baseName + '_' + str(i)

        self.IfcInfo.DefaultStorey = _createBuildingOrStorey(
            self.IfcInfo,
            'IfcBuildingStorey',
            name,
            'Level',
            self.IfcInfo.WorldLocPlace,
            name,
            Elevation=self.IfcInfo.WorldCoords[2]
        )

        # storeys from concept model 'set' list
        for set in self.SetList:
            newstorey = _createBuildingOrStorey(
                self.IfcInfo,
                'IfcBuildingStorey',
                set.name, #'Unique level', # TODO: include different levels (storeys)
                'Level',
                self.IfcInfo.WorldLocPlace, # TODO: improve (with level definition)
                set.name, #'UNique Level',
                Elevation=self.IfcInfo.WorldCoords[2] # TODO: revise
            )
            set.IfcBuildingStorey = newstorey
            self.IfcInfo.Storeys.append(newstorey)

        # storey to contain the equipments TODO: revise (e.g., group equipments by IfcGroup)
        self.IfcInfo.EquipStorey = _createBuildingOrStorey( 
            self.IfcInfo,
            'IfcBuildingStorey',
            'Equipments',
            'Level',#'Equipments', # TODO: find the difference between 'Level' and other...
            self.IfcInfo.WorldLocPlace, # TODO: revise
            'Equipments',
            Elevation=self.IfcInfo.WorldCoords[2] # TODO: revise            
        )


    def _exportEquips(self):
        # create style
        style = _createStyleItem(self.IfcInfo.ifcFile, 0, 0.5, 0)

        # create equips IFC entities
        for Equip in self.EquipmentList:
            Equip.IfcEntity, rep = _exportEquipToIfc(self.IfcInfo, Equip)
            ifcopenshell.api.run("style.assign_representation_styles", self.IfcInfo.ifcFile,
                shape_representation=rep, styles=[style])

    def _createContainment(self, IfcInfo: ifcInfo):
        # storeys from concept model 'set' list
        notContainedBeams = self._Beams.nameList()
        for storey in self.SetList:
            beamList = []
            for name in storey:
                if name in notContainedBeams:
                    beam = self._Beams.FindByName(name)
                    beamList.append(beam.IfcBeam)
                    notContainedBeams.remove(name)
            """
            IfcInfo.ifcFile.create_entity(
                type='IfcRelContainedInSpatialStructure',
                GlobalId=ifcopenshell.guid.new(),
                OwnerHistory=IfcInfo.ownerHistory,
                RelatedElements=beamList,
                RelatingStructure=storey.IfcBuildingStorey
            )
            """
            _createRelContInSpatiaStr(IfcInfo, beamList, storey.IfcBuildingStorey)

        # beams which do not belong to any set
        notContBeamsIfcEntities =  []
        for name in notContainedBeams: 
            notContBeamsIfcEntities.append(self._Beams.FindByName(name).IfcBeam)

        _createRelContInSpatiaStr(
            IfcInfo, 
            notContBeamsIfcEntities, 
            IfcInfo.DefaultStorey
        )


        # storey to contain the equipments
        EquipIfcList = []
        for Equip in self.EquipmentList:
            EquipIfcList.append(Equip.IfcEntity)
        """    
        IfcInfo.ifcFile.create_entity(
            type='IfcRelContainedInSpatialStructure',
            GlobalId=ifcopenshell.guid.new(),
            OwnerHistory=IfcInfo.ownerHistory,
            RelatedElements=EquipIfcList,
            RelatingStructure=IfcInfo.EquipStorey
        )                

        """ 
        _createRelContInSpatiaStr(IfcInfo, EquipIfcList, IfcInfo.EquipStorey)


# ==== AUXILIARY METHODS ==== #
def _createRelContInSpatiaStr(
        IfcInfo: ifcInfo, 
        RelatedElements: list[ifcopenshell.entity_instance],
        RelatingStructure: ifcopenshell.entity_instance
    ) -> None:
    IfcInfo.ifcFile.create_entity(
        type='IfcRelContainedInSpatialStructure',
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=IfcInfo.ownerHistory,
        RelatedElements=RelatedElements,
        RelatingStructure=RelatingStructure
    )       

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


def _createStyles(IfcInfo: ifcInfo, matList: classMatList):   
    for i, mat in enumerate(matList):
        color = getRGBcolor(i)
        style = _createStyleItem(IfcInfo.ifcFile, color.R, color.G, color.B)
        ifcopenshell.api.run(
            "style.assign_material_style", 
            IfcInfo.ifcFile, 
            material=mat.IfcMat, 
            style=style, 
            context=IfcInfo.BodySubContext
        )

def _createStyleItem(
    IfcFile: ifcopenshell.file, 
    R: float, G: float, B: float, 
    transparency: float = 0.
    ) -> ifcopenshell.entity_instance:

    # Create a new surface style
    style = ifcopenshell.api.run("style.add_style", IfcFile)

    # Create a simple shading colour and transparency.
    ifcopenshell.api.run("style.add_surface_style", IfcFile,
        style=style, ifc_class="IfcSurfaceStyleShading", attributes={
            "SurfaceColour": { "Name": None, "Red": R, "Green": G, "Blue": B},
            "Transparency":transparency, # 0 is opaque, 1 is transparent
        })
    
    return style

def _createMatAssociations(IfcInfo: ifcInfo, 
                           beamList: ifcBeamList, 
                           matList: classMatList):
    matAssociations = {}
    for mat in matList: matAssociations[mat.name] = [mat.IfcMat, []]

    for beam in beamList:
        for i in range(1, len(beam.SegmentList)): 
            if beam.SegmentList[i].properties.material != \
                beam.SegmentList[i-1].properties.material:
                IfcInfo.ErrorMsg(f'Warning! Beam {beam.name} has segments with ' + \
                       'different materials. Only the material of the '+\
                       'first segment will be considered.')
                #print(f'Warning! Beam {beam.name} has segments with ' + \
                #       'different materials. Only the material of the '+\
                #       'first segment will be considered.')

        matName = beam.SegmentList[0].properties.material
        ifcBeam = beam.IfcBeam
        matAssociations[matName][1].append(ifcBeam)
        
    
    for matName, matIfcAndBeams in matAssociations.items():
        matIfc = matIfcAndBeams[0]
        beams = matIfcAndBeams[1]
        IfcInfo.ifcFile.create_entity(
            type = 'IfcRelAssociatesMaterial',
            GlobalId = ifcopenshell.guid.new(),
            RelatedObjects = beams,
            RelatingMaterial = matIfc,
        )

def _exportEquipToIfc(IfcInfo: ifcInfo, Equipment: classEquipment
    ) -> tuple[ifcopenshell.entity_instance, ifcopenshell.entity_instance]:
    """
    Exports an equipment to IFC file as an IfcElement class
    """
    """
    Location = _createCartesianPnt(IfcInfo.ifcFile, Equipment.origin)
    zAxis = Equipment.AxisVec('z')
    if zAxis == [0., 0., 1.]:
        Axis, RefDir = None, None
    else:
        Axis = _createDirection(zAxis)
        RefDir = _createDirection(Equipment.AxisVec('x'))
    RelPlace = _createAxis2Place3D(IfcInfo.ifcFile, Location, Axis, RefDir)
    IfcPlacement = _createIfcLocPlace(IfcInfo.ifcFile, IfcInfo.WorldLocPlace, RelPlace)
    """ 

    refPoint = _createCartesianPnt(IfcInfo.ifcFile, [0.,0.,0.]) # TODO: evaluate the possibility to consider a reference location (e.g., groups, sets, storeys)
    refPosition = _createAxis2Place3D(IfcInfo.ifcFile, refPoint) # TODO: handle the orientation (Axis and RefDirection)
    ObjPlacement = _createPlacement(IfcInfo.ifcFile, Equipment.origin, IfcInfo.WorldCoordSys, refPosition)


    AxisRep = _createAxisRep(IfcInfo, [0.,0.,0.], [0.,0.,Equipment.dimensions[2]])


    solid = _createBoxSolid(IfcInfo, Equipment.dimensions)
    BodyRep = _createShapeRep(IfcInfo, [solid], 'SweptSolid') #'BoundingBox') # TODO: understand better the effect of this attribute, e.g., difference between 'BoundingBox' and 'MappedRepresentation'

    # creates the product definition shape
    ifcProdDefShape = IfcInfo.ifcFile.create_entity(
        type='ifcProductDefinitionShape',
        Representations=[AxisRep, BodyRep], # TODO: include body representation
    )

    data = {}
    data['GlobalId'] = ifcopenshell.guid.new()
    data['OwnerHistory'] = IfcInfo.ownerHistory
    data['Name'] = Equipment.name
    data['Description'] = 'Equipment'
    # data['ObjectType'] = 'ElementGroupByFunction' # TODO: check the effect of this attribute
    data['ObjectPlacement'] = ObjPlacement
    data['Representation'] = ifcProdDefShape

    #IfcEquip = IfcInfo.ifcFile.create_entity(type = 'IfcElement',**data)
    IfcEquip = IfcInfo.ifcFile.create_entity(type = 'IfcBeam',**data) # TODO: testin IfcBeam or IfcElement
    return IfcEquip, BodyRep

def _createBoxSolid(
        IfcInfo: ifcInfo,
        dimensions: list[float] # [xDim, yDim, zDim]
    ) -> ifcopenshell.entity_instance:
    """ Creates an IfcGeometricRepresentation as a IfcBoundingBox """
    IfcFile = IfcInfo.ifcFile
    """
    CornerPnt = _createCartesianPnt(IfcFile, [-dimensions[0]/2, -dimensions[1]/2, 0.])
    CornerPos = _createAxis2Place3D(IfcFile, CornerPnt)
    return IfcFile.create_entity(
        type = 'IfcBoundingBox',
        Corner = CornerPnt,
        XDim = dimensions[0],
        YDim = dimensions[1],
        ZDim = dimensions[2],
    )
    """
    """
    return IfcFile.create_entity(
        type = 'IfcBlock',
        Position = CornerPos,
        XLength = dimensions[0],
        YLength = dimensions[1],
        ZLength = dimensions[2],
    )
    """
    ExtrudAreaPos = __createExtrudSweptAreaPosition(IfcInfo)

    BoxSectionProf = IfcFile.create_entity(
        type='IfcRectangleProfileDef',
        ProfileType='AREA',
        ProfileName='rectangle',
        Position=ExtrudAreaPos,
        XDim=dimensions[0]*0.05,
        YDim=dimensions[1]*0.05,
    )

    ExtrudAreaDir = _createDirection(IfcInfo, [0.,0.,1.])

    # Extruded Area (IfcExtrudedAreaSolid)
    ExtrudArea = IfcInfo.ifcFile.create_entity(
        type = 'IfcExtrudedAreaSolid',
        SweptArea = BoxSectionProf,
        Position = ExtrudAreaPos,
        ExtrudedDirection = ExtrudAreaDir,
        Depth = dimensions[2]
    )

    return ExtrudArea    


def _exportMaterialsToIfc(IfcInfo: ifcInfo, matList: classMatList):
    props = []
    for mat in matList:
        ifcMat = IfcInfo.ifcFile.create_entity(
            type='IfcMaterial', Name=mat.name
        )
        props.append(_setPropValue(IfcInfo, ifcMat, 'Pset_MaterialCommon', 'MassDensity', mat.density))
        props.append(_setPropValue(IfcInfo, ifcMat, 'Pset_MaterialSteel', 'YieldStress', mat.Sadm))
        props.append(_setPropValue(IfcInfo, ifcMat, 'Pset_MaterialMechanical', 'YoungModulus', mat.YoungModulus)) 
        props.append(_setPropValue(IfcInfo, ifcMat, 'Pset_MaterialMechanical', 'PoissonRatio', mat.PoissonCoef))
        props.append(_setPropValue(IfcInfo, ifcMat, 'Pset_MaterialMechanical', 'ThermalExpansionCoefficient', mat.alpha))
        mat.IfcMat = ifcMat


def _setPropValue(IfcInfo: ifcInfo, 
                  ifcMaterial: ifcopenshell.entity_instance,
                  pset: str, # e.g., Pset_MaterialCommon
                  prop: str, # identifier of the property
                  value: float
                  ) -> ifcopenshell.entity_instance:
   

    psetEntity = ifcopenshell.api.run("pset.add_pset", IfcInfo.ifcFile, product=ifcMaterial, name=pset)
    ifcopenshell.api.run("pset.edit_pset", IfcInfo.ifcFile, pset=psetEntity, properties={prop: value})
    '''
    return IfcInfo.ifcFile.create_entity(
        type = 'IfcPropertySingleValue',
        Name = prop,
        NominalValue = value
    ) 
    '''
    return pset

def _createRelAggreg(IfcInfo: ifcInfo, 
                     parentObj: ifcopenshell.entity_instance,
                     relatedObjs: list[ifcopenshell.entity_instance]
                     ) -> ifcopenshell.entity_instance:
    return IfcInfo.ifcFile.create_entity(
        type = 'IfcRelAggregates',
        GlobalId = ifcopenshell.guid.new(),
        OwnerHistory = IfcInfo.ownerHistory,
        RelatingObject = parentObj,
        RelatedObjects = relatedObjs
    )


def _createBuildingOrStorey(IfcInfo: ifcInfo, 
                            Type: str, # 'IfcBuilding' or 'IfcBuildingStorey'
                            Name: str,
                            ObjectType: str,
                            ObjectPlacement: ifcopenshell.entity_instance,
                            LongName: str = '',
                            CompositionType: str = 'ELEMENT',
                            Elevation: float = None,
                            ):
    data = {}
    data['GlobalId'] = ifcopenshell.guid.new()
    data['OwnerHistory'] = IfcInfo.ownerHistory
    data['Name'] = Name
    data['ObjectType'] = ObjectType
    data['ObjectPlacement'] = ObjectPlacement
    data['LongName'] = LongName
    data['CompositionType'] = CompositionType
    if Elevation: data['Elevation'] = Elevation
    return IfcInfo.ifcFile.create_entity(type=Type, **data)

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


def _createIfcObjPlace(
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


def _createIfcLine(ifcFile: ifcopenshell.file,
                   pointA: list[float],
                   pointB: list[float],
                   funcErrorMsg: Function
                  ) -> tuple[ifcopenshell.entity_instance,
                             ifcopenshell.entity_instance]:
    pnt = _createCartesianPnt(ifcFile, pointA)
    adir = np.array(pointB) - np.array(pointA)
    length = np.linalg.norm(adir)
    if length == 0: 
        funcErrorMsg(f'Warning! Beam with zero length')
        #print(f'Warning! Beam with zero length')
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
    
    
    ifcLine, trimm1 = _createIfcLine(ifcInfo.ifcFile, pointA, pointB, ifcInfo.ErrorMsg)
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
        RepresentationType= 'Curve3D',
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


def _createShapeRep(
    IfcInfo: ifcInfo,
    solids: list[ifcopenshell.entity_instance], # list of  IfcSSolidModel
    RepType: str, # type if representation (e.b., SweptSolid)
    ) -> ifcopenshell.entity_instance: 
    """ 
    Creates an ifcShapeRepresentation based on solids (list of IfcSSolidModel)
    """
    # shape representation (IfcShapeRepresentation)
    MapRep = IfcInfo.ifcFile.create_entity(
        type = 'IfcShapeRepresentation',
        ContextOfItems = IfcInfo.BodySubContext,
        RepresentationIdentifier = 'Body',
        RepresentationType = RepType,
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


def _createBeamBodyRep(
        IfcInfo: ifcInfo,
        beam: bimBeam
        ) -> ifcopenshell.entity_instance:
    # solids
    solids = []
    for segment in beam.SegmentList:
        solids.append(_createSegBodyRep(IfcInfo, beam, segment))
    
    while solids.count(None)>0: solids.remove(None)

    return _createShapeRep(IfcInfo, solids, 'SweptSolid')


def _createSegBodyRep(
                      IfcInfo: ifcInfo,
                      beam: bimBeam,
                      segment: classSegment
                     ) -> ifcopenshell.entity_instance:

    sectype = segment.properties.sectionPointer.sectype
    secptr = segment.properties.sectionPointer

    # cross section
    if sectype == SectionType.pipe_section:
        CrossSection = __createCircleHollowProfile(IfcInfo, secptr)
    elif sectype == SectionType.i_section:
        CrossSection = __createIProfile(IfcInfo, secptr)
    elif sectype == SectionType.box_section:
        CrossSection = __createBoxProfile(IfcInfo, secptr)
    elif sectype == SectionType.bar_section:
        CrossSection = __createBarProfile(IfcInfo, secptr)
    else:
        IfcInfo.ErrorMsg(f'Warning! Section type {sectype} not supported yet.')
        #print(f'Section type {sectype} not supported yet.')
        return None
    
    relIniPos = np.array(segment.IniPos) - np.array(beam.IniPos) # relative position to the object placement
    # position and direction
    ExtrudAreaPosLoc = _createCartesianPnt(
        IfcInfo.ifcFile,
        relIniPos.tolist()
        )
    
    vecA = segment.Direction
    if vecA[0] != 0. or vecA[1] != 0.:
        if vecA[1] == 0:
            y = abs(vecA[0])/vecA[0]
            vecRef = [0., y, 0.]
        else:
            x = math.sqrt(vecA[1]**2/(vecA[0]**2 + vecA[1]**2))
            sign = abs(vecA[1])/vecA[1]
            x = -x*sign
            y = -vecA[0]/vecA[1]*x
            vecRef = [x, y, 0.]
    else:
        vecRef = [1., 0., 0.]

    RefDirection = _createDirection(IfcInfo, vecRef)
    Axis = _createDirection(IfcInfo, vecA)

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


def __createExtrudSweptAreaPosition(
                      IfcInfo: ifcInfo,
                     ) -> ifcopenshell.entity_instance:
    ExtrudAreaLoc = _createCartesianPnt(IfcInfo.ifcFile, [0.,0.])
    #ExtrudAreaDir = _createDirection(IfcInfo, [1.,0.]) # default is already [1.,0.]
    ExtredAreaPos = IfcInfo.ifcFile.create_entity(
        type='IfcAxis2Placement2D',
        Location=ExtrudAreaLoc,
        #RefDirection=ExtrudAreaDir # default is [1.,0.]
    )    
    return ExtredAreaPos

def __createCircleHollowProfile(
                      IfcInfo: ifcInfo,
                      section: classPipeSection
                     ) -> ifcopenshell.entity_instance:

    ExtrudAreaPosition = __createExtrudSweptAreaPosition(IfcInfo)
    CircleHollowProf = IfcInfo.ifcFile.create_entity(
        type='IfcCircleHollowProfileDef',
        ProfileType='AREA',
        ProfileName=f'Pipe {section.OD*1e3:.1f}x{section.th*1e3:.1f}mm', # TODO: handle units
        Position=ExtrudAreaPosition,
        Radius=section.OD/2.,
        WallThickness=section.th
    )
    return CircleHollowProf
    
def __createIProfile(
                      IfcInfo: ifcInfo,
                      section: classISection,
                     ) -> ifcopenshell.entity_instance:

    ExtrudAreaPos = __createExtrudSweptAreaPosition(IfcInfo)
    ProfName = f'I section h={section.h*1e3:.1f}; b={section.b*1e3:.1f}; '+\
        f'tw={section.tw*1e3:.1f}; tf={section.tf*1e3:.1f}mm'
    ISectionProf = IfcInfo.ifcFile.create_entity(
        type='IfcIShapeProfileDef',
        ProfileType='AREA',
        ProfileName=ProfName,
        Position=ExtrudAreaPos,
        OverallWidth=section.b,
        OverallDepth=section.h,
        WebThickness=section.tw,
        FlangeThickness=section.tf,
        FilletRadius=section.fillet_radius
    )
    return ISectionProf


def __createBoxProfile(
                      IfcInfo: ifcInfo,
                      section: classBoxSection,
                     ) -> ifcopenshell.entity_instance:

    ExtrudAreaPos = __createExtrudSweptAreaPosition(IfcInfo)
    thickness = 0.5*(section.tftop+section.tfbot)
    ProfName = f'Box section h={section.h*1e3:.1f}; b={section.b*1e3:.1f}; '+\
        f'tw={thickness*1e3:.1f}mm'

    if section.tw != section.tfbot or section.tw != section.tftop:
        IfcInfo.ErrorMsg('Warning! Diference between flanges of box sections will be '+\
            'disregarded.') # TODO: Handle this case
        #print('Warning! Diference between flanges of box sections will be '+\
        #    'disregarded.') # TODO: Handle this case
        
    BoxSectionProf = IfcInfo.ifcFile.create_entity(
        type='IfcRectangleHollowProfileDef',
        ProfileType='AREA',
        ProfileName=ProfName,
        Position=ExtrudAreaPos,
        XDim=section.b,
        YDim=section.h,
        WallThickness=thickness
    )
    return BoxSectionProf

 
def __createBarProfile(
                      IfcInfo: ifcInfo,
                      section: classBoxSection,
                     ) -> ifcopenshell.entity_instance:

    ExtrudAreaPos = __createExtrudSweptAreaPosition(IfcInfo)
    ProfName = f'Bar section h={section.h*1e3:.1f}; b={section.b*1e3:.1f}mm'

    if section.tw != section.tfbot or section.tw != section.tftop:
        IfcInfo.ErrorMsg('Warning! Diference between flanges of box sections will be '+\
            'disregarded.') # TODO: Handle this case
        #print('Warning! Diference between flanges of box sections will be '+\
        #    'disregarded.') # TODO: Handle this case
        
    BarSectionProf = IfcInfo.ifcFile.create_entity(
        type='IfcRectangleProfileDef',
        ProfileType='AREA',
        ProfileName=ProfName,
        Position=ExtrudAreaPos,
        XDim=section.b,
        YDim=section.h,
    )
    return BarSectionProf




def _createDirection(ifcInfo: ifcInfo, dirRatios: list[float]
                        ) -> ifcopenshell.entity_instance:
    """ Creates an IfcDirection object """
    return ifcInfo.ifcFile.create_entity(
        type='IfcDirection',
        DirectionRatios = dirRatios
    )

