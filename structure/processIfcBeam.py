"""
Retrives the beam geometry

Required packages:
    * ifcopenshell: pip install ifcopenshell
"""

# INPUTS
file = r'C:\Temp\PCE_JACKET_IFC4.ifc'


# LIBS
import ifcopenshell
import ifcopenshell.util.representation as ifcrep
import ifcopenshell.util.unit as ifcunit
import numpy as np

# CONSTANTS
_supportedIfcClasses = ['IfcBeam','IfcColumn','IfcMember']


# CLASSES

class bimBeam:
    lengthTol = 0.001 
    # PredefinedType: pset dictionary key
    __psetskey = {'BEAM': ['Pset_BeamCommon','Span'], 
                  'COLUMN': None}

    def __init__(self,
                 ifcFile: ifcopenshell.file = None, 
                 ifcBeam: ifcopenshell.entity_instance = None, 
                 context: str = None, 
                 subcontext: str = None
                 ) -> None:        
        self.EndA = [0.,0.,0.] # in meters
        self.EndB = [0.,0.,0.] # in meters        
        np_matrix = np.identity(3) # creates identity matrix
        self.TransfMatrix = np_matrix.tolist()

        if ifcFile and ifcBeam and context:
            self.importFromIfc(ifcFile, ifcBeam, context, subcontext)
    
    def __setTranfByXandZ(self, X: list[float], Z: list[float]) -> None:
        """
        Calculates the tranformation matrix (local to global coordinates)
        """
        aX = np.array(X)
        aZ = np.array(Z)
        aY = np.cross(aZ,aX)
        self.TransfMatrix.clear()
        for x, y, z in zip(aX, aY, aZ):
            row = [x, y, z]
            self.TransfMatrix.append(row.copy())

    def __TransfCoords(self, localCoords: list[float]) -> list[float]:
        """
        Apply the transformation matrix to convert from local coordinates (lx, ly, lz)
        to global coordinates
        * input: local coordinates list (lx, ly, lz)
        * return: gloobal coordinate list
        """
        M = np.array(self.TransfMatrix)
        lV = np.array(localCoords)
        gV = np.matmul(M, lV)
        return [gV[0], gV[1], gV[2]]


    def Length(self) -> float:
        """
        Returns the beam length (meters)
        """
        V = np.array(self.EndA) - np.array(self.EndB)
        return np.linalg.norm(V)

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
        
        EndA, EndB = [0.,0.,0.], [0.,0.,0.]
        for i in range(3):
            # adds the origin coordinates to the mapping represantation
            EndA[i], EndB[i] = t1[0][i] + mapOriginLoc[i], t2[0][i] + mapOriginLoc[i]
            # converts units
            EndA[i] *= fconvL
            EndB[i] *= fconvL

        # applies the coord. transformation (Mapping Target) and stores the results
        self.EndA = self.__TransfCoords(EndA.copy())
        self.EndB = self.__TransfCoords(EndB.copy())

        # gets the pset key
        predefType = ifcBeam.PredefinedType        
        psetKeys = self.__psetskey[predefType]
        if psetKeys:
            # gets the property sets
            psets = ifcopenshell.util.element.get_psets(ifcBeam)
            # gets the beam length
            ifcLength = fconvL*psets[psetKeys[0]][psetKeys[1]]
            calcLength = self.Length()
            # verify the length
            if abs(calcLength-ifcLength)/ifcLength > self.lengthTol:
                print(f'Warning! Calculated length {calcLength}m different of the IFC pset data length {ifcLength}m.')
        

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

def ImportBeamsFromIFC(ifcFile: ifcopenshell.file) -> list[bimBeam]:
    ifcBeams = GetMembersList(ifcFile)

    impList = list()
    for ifcBeam in ifcBeams:
        newBeam = bimBeam(ifcFile, ifcBeam, "Model", "Axis")
        if newBeam: impList.append(newBeam)
    
    print(f'{len(impList)} beams imported fom IFC file.')

    return impList


# MAIN
print(f'Reading file {file} ...', flush=True)
ifcFile = ifcopenshell.open(file)
beamList = ImportBeamsFromIFC(ifcFile)


