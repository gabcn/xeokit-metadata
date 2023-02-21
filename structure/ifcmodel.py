"""
Retrives the beam geometry from IFC file
IFC4x version

Required packages:
    * ifcopenshell: pip install ifcopenshell
"""

# LIBS
import ifcopenshell
import ifcopenshell.util.representation as ifcrep
import ifcopenshell.util.unit as ifcunit
import ifcopenshell.util.placement as ifcplace
import numpy as np
from structure.conceptmodel import classBeam, classConceptModel



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
            ifcFile: ifcopenshell.file,
            WorldOrigin: ifcopenshell.entity_instance, # (ifcCartesianPoint)
            WorldCoordSys: ifcopenshell.entity_instance, # (IfcAxis2Placement3D)
            WorldCartesianOp: ifcopenshell.entity_instance, # (ifcCartesianTransformationOperator3D)
            Context: ifcopenshell.entity_instance, # (IfcGeometricRepresentationContext)
            AxisSubContext: ifcopenshell.entity_instance, # (IfcGeometricRepresentationSubContext)
            BodySubContext: ifcopenshell.entity_instance, # (IfcGeometricRepresentationSubContext)
            refPosition: ifcopenshell.entity_instance = None # (IfcAxis2Placement3D) rerefence (e.g., storey) position
            ) -> ifcopenshell.entity_instance:
        """
        Export beam to Ifc
        * return: entity_instance of the objecte created
        """

        if not refPosition:
            refPoint = _createCartesianPnt(ifcFile, self.RefCoords) # TODO: evaluate the possibility to consider a reference location (e.g., groups, sets, storeys)
            refPosition = _createAxis2Place3D(ifcFile, refPoint) # TODO: handle the orientation (Axis and RefDirection)

        # creates the ObjectPlacement
        ifcObjPlace = self.__createPlacement(ifcFile, WorldCoordSys, refPosition)

        # creates the object 'Axis' representation
        AxisRep = _createAxisRep(
            ifcFile, 
            WorldOrigin, 
            WorldCartesianOp, 
            self.IniPos, 
            self.LastPos, 
            Context
        )

        ifcProdDefShape = ifcFile.create_entity(
            type='ifcProductDefinitionShape',
            Representations=[AxisRep], # TODO: include body representation
        )
        


        ifcBeam = ifcFile.create_entity(
            type='IfcBeam',
            GlobalId = ifcopenshell.guid.new(),
            # TODO: OwnerHistory
            Name = self.name, #beam.name,
            Description = self.Description, # beam.Description,
            # TODO: ObjectType
            ObjectPlacement = ifcObjPlace,
            Representation = ifcProdDefShape,
            # TODO: Tag    
            # TODO: PredefinedType
            )
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
class ifcModel(classConceptModel):
    def __init__(self, ifcFilePath: str = None) -> None:
        super().__init__()
        self._Beams = ifcBeamList(self, ifcFilePath)

    def ExportToIFC(self, ifcFilePath: str, beamIndexes: slice = None) -> None:
        ifcFile = ifcopenshell.file(schema='IFC4')

        WorldOrigin = _createCartesianPnt(ifcFile, [0.,0.,0.])
        WorldCoordSys = _createAxis2Place3D(ifcFile, WorldOrigin) # TODO: handle the orientation (Axis and RefDirection)
        WorldCartesianOp = ifcFile.create_entity(type='ifcCartesianTransformationOperator3D',
            LocalOrigin=WorldOrigin, Scale=1.)

        ModelContext = _createModelContext(ifcFile, WorldCoordSys) # TODO: handle the precision
        AxisSubContext = _createSubContext(ifcFile, 'Axis', ModelContext, 'GRAPH_VIEW')
        BodySubContext = _createSubContext(ifcFile, 'Body', ModelContext, 'MODEL_VIEW')
        
       

        if beamIndexes == None: 
            for beam in self._Beams:
                beam.exportBeamToIfc(ifcFile, 
                                     WorldOrigin,
                                     WorldCoordSys,
                                     WorldCartesianOp,
                                     ModelContext, 
                                     AxisSubContext, 
                                     BodySubContext)
        else: 
            for beam in self._Beams[beamIndexes]:
                beam.exportBeamToIfc(ifcFile, 
                                     WorldOrigin,
                                     WorldCoordSys, 
                                     WorldCartesianOp,
                                     ModelContext, 
                                     AxisSubContext, 
                                     BodySubContext)


        ifcFile.write(ifcFilePath)



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

def _createModelContext(ifcFile: ifcopenshell.file,
                        WorldCoordSys: ifcopenshell.entity_instance, #(IfcAxis2Placement)
                        CoordSysDim: int = 3,
                        ContextType: str = 'Model', # (e.g., 'Model')
                        Precision: float = None,
                        TrueNorth: ifcopenshell.entity_instance = None,
                        ) -> ifcopenshell.entity_instance:

    data = {}
    data['WorldCoordinateSystem'] = WorldCoordSys
    data['CoordinateSpaceDimension'] = CoordSysDim
    data['ContextType'] = ContextType
    if Precision: data['Precision'] = Precision
    if TrueNorth: data['TrueNorth'] = TrueNorth

    return ifcFile.create_entity(type='IfcGeometricRepresentationContext', **data) 

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

    #ifcLocPlace = ifcFile.create_entity(type = 'IfcLocalPlacement')
    #ifcLocPlace = __createIfcLocPlace(ifcFile)
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
                   ifcFile: ifcopenshell.file,
                   WorldOrigin: ifcopenshell.entity_instance, # (ifcCartesianPoint)
                   WorldCartesianOp: ifcopenshell.entity_instance, # (ifcCartesianTransformationOperator3D)
                   pointA: list[float],
                   pointB: list[float],
                   context: ifcopenshell.entity_instance, # (IfcGeometricRepresentationSubContext)
                   ) -> ifcopenshell.entity_instance:
    
    
    ifcLine, trimm1 = _createIfcLine(ifcFile, pointA, pointB)
    trimm2 = _createCartesianPnt(ifcFile, pointB)
    trimmedCurve = ifcFile.create_entity(
        type='IfcTrimmedCurve',
        BasisCurve = ifcLine,
        Trim1 = [trimm1],
        Trim2 = [trimm2],
        SenseAgreement = True, #'T',
        MasterRepresentation = 'CARTESIAN'
    )

    ifcShapeRep = ifcFile.create_entity(
        type='ifcShapeRepresentation',
        ContextOfItems= context,
        RepresentationIdentifier='Axis',
        RepresentationType= 'MappedRepresentation',
        Items=[trimmedCurve]
    )

    MapOrigin = _createAxis2Place3D(ifcFile, WorldOrigin)
    MapSource = ifcFile.create_entity(
        type='ifcRepresentationMap',
        MappingOrigin=MapOrigin,
        MappedRepresentation=ifcShapeRep
    )

    MapItem = ifcFile.create_entity(
        type='ifcMappedItem',
        MappingSource=MapSource,
        MappingTarget=WorldCartesianOp
    )

    ifcShapeRep = ifcFile.create_entity(
        type='ifcShapeRepresentation',
        ContextOfItems=context,
        RepresentationIdentifier='Axis',
        RepresentationType='MappedRepresentation',
        Items=[MapItem]
    )

    return ifcShapeRep





