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
from structure.conceptmodel import classBeam



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
                 ifcFile: ifcopenshell.file = None, 
                 ifcBeam: ifcopenshell.entity_instance = None, 
                 context: str = None, 
                 subcontext: str = None
                 ) -> None:        
        super().__init__()
        self.L_EndA = [0.,0.,0.] # in meters (local coordinates)
        self.L_EndB = [0.,0.,0.] # in meters (local coordinates)
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

    def __LocalToGlobal(self, locCoords: list[float]) -> list[float]:
        """
        Converts from the local to global coordinates
        """
        lC = locCoords.copy()
        lC.append(1) # for the translation
        alC = np.array(lC)
        agC = np.matmul(self.locPlacMtx, alC)
        return agC.tolist()[:3]

    def getGlobalEndA(self): return self.__LocalToGlobal(self.L_EndA)
    def getGlobalEndB(self): return self.__LocalToGlobal(self.L_EndB)

    EndA = property(getGlobalEndA) 
    """(global coordinates)"""

    EndB = property(getGlobalEndB) 
    """(global coordinates)"""


    def __fGetLength(self) -> float:
        """
        Returns the beam length (meters)
        """
        V = np.array(self.L_EndA) - np.array(self.L_EndB)
        return np.linalg.norm(V)

    length = property(__fGetLength)


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
        self.locPlacMtx = ifcplace.get_local_placement(ifcBeam.ObjectPlacement)
        # convert the translational terms to S.I.
        for i in range(3): self.locPlacMtx[i,3] *= fconvL

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
        self.L_EndA = self.__MapTransfCoords(_EndA.copy())
        self.L_EndB = self.__MapTransfCoords(_EndB.copy())
        self.IniPos = self.L_EndA
        self.AddSegmentByEnd(self.L_EndB)
        
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
    

class ifcBeamList(list[bimBeam]):
    def __init__(self, ifcFilePath: str):
        """
        * ifcFilePath: (str) path to the IFC file
        """
        super().__init__()
        ifcFile = ifcopenshell.open(ifcFilePath)
        self._ImportBeamsFromIFC(ifcFile)
        
    def _ImportBeamsFromIFC(self, ifcFile: ifcopenshell.file) -> None:
        ifcBeams = GetMembersList(ifcFile)

        for ifcBeam in ifcBeams:
            newBeam = bimBeam(ifcFile, ifcBeam, "Model", "Axis")
            if newBeam: self.append(newBeam)
        
        print(f'{len(self)} beams imported fom IFC file.')

    def ByGUID(self, guid: str) -> bimBeam:
        result = None
        for beam in self:
            if beam.guid == guid:
                result = beam
                break
        return result




