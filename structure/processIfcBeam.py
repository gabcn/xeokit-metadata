"""
Retrives the beam geometry

Required packages:
    * ifcopenshell: pip install ifcopenshell
"""

# INPUTS
file = r'C:\Temp\PCE_JACKET_IFC4.ifc'


# LIBS
import ifcopenshell
import ifcopenshell.api
import ifcopenshell.util.element as ifcelem
import ifcopenshell.util.placement
import ifcopenshell.util.representation as ifcrep
import ifcopenshell.geom as ifcgeom
import ifcopenshell.util.attribute as ifcattr
import ifcopenshell.util.unit as ifcunit
import numpy as np


# CLASSES

class bimBeam:
    lengthTol = 0.001 
    def __init__(self) -> None:
        self.EndA = [0.,0.,0.] # in meters
        self.EndB = [0.,0.,0.] # in meters
    
    def __setTranfByXandZ(self, X: list[float], Z: list[float]) -> None:
        """
        Calculates the tranformation matrix (local to global coordinates)
        """
        aX = np.array(X)
        aZ = np.array(Z)
        aY = np.cross(aZ,aX)
        self.TransfMatrix = []
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
        """

        fconvL = ifcunit.calculate_unit_scale(ifcFile)


        if not ifcBeam.is_a('IfcBeam'): 
            raise Exception(f'Error! The instance {ifcBeam} is not a IfcBeam class.')   
        
        representation = ifcrep.get_representation(ifcBeam, context, subcontext) 
        if not representation.is_a('IfcShapeRepresentation'):
            raise Exception(f'Representation type {representation.is_a()} not supported.')

        repItems = representation.Items #IfcMapItem
        repItem = repItems[0]
        if not repItem.is_a('IfcMappedItem'):
            raise Exception(f'Representation item type {repItem.is_a()} not supported.')

        mapSource = repItem.MappingSource
        mapOrigin = mapSource.MappingOrigin
        mapTarget = repItem.MappingTarget
        if not mapTarget.is_a('IfcCartesianTransformationOperator3D'):
            raise Exception(f'Mapping target type {mapTarget.is_a()} not supported.')
        if mapTarget.Axis1 or mapTarget.Axis2 or mapTarget.Scale != 1. or mapTarget.Axis3:
            raise Exception(f'Axis 1, 2, 3 or scale attribuites of ' + \
                'IfcCartesianTransformationOperator3D not implemented.')
        TransfOrigin = mapTarget.LocalOrigin[0]
        if TransfOrigin[0] != 0 or TransfOrigin[1] != 0 or TransfOrigin[2] != 0:
            raise Exception(f'Error! Transformation origin not equal to (0,0,0).')

        if not mapOrigin.is_a('IfcAxis2Placement3D'):
            raise Exception(f'Error! Mapping origin type {mapOrigin.is_a()} not supported.')

        mapOriginLoc = mapOrigin.Location[0]
        '''
        if mapOriginLoc[0] != 0 or mapOriginLoc[1] != 0 or mapOriginLoc[2] != 0:
            raise Exception(f'Error! Mapping origin location '+\
                f'({mapOriginLoc[0]},{mapOriginLoc[1]},{mapOriginLoc[2]}) ' + \
                'not equal to (0,0,0).')
        '''
        if mapOrigin.Axis or mapOrigin.RefDirection:
            if mapOrigin.Axis: Z = list(mapOrigin.Axis.DirectionRatios)
            else: Z = [0.,0.,1.]
            if mapOrigin.RefDirection: X = list(mapOrigin.RefDirection.DirectionRatios)
            else: X = [1.,0.,0.]
            self.__setTranfByXandZ(X, Z)
            """
            raise Exception(f'Error! Mapping origin axis or RefDirection not supported.' + \
                f'\n {mapOrigin}'
                )
            """

        mapRep = mapSource.MappedRepresentation
        if not mapRep.is_a('IfcShapeRepresentation'):
            raise Exception(f'Error! Mapping source representation {mapRep.is_a()} not supported.')
        
        c = mapRep.ContextOfItems.ContextIdentifier
        if subcontext != c:
            raise Exception(f'Error! Subcontext not equal to the representation items context ({c}).')

        mapRepItems = mapRep.Items
        if len(mapRepItems) > 1:
            raise Exception('Error! Number of Mapping representation items greater then 1 ' + \
                            f'({len(mapRepItems)}) not supported.')

        mapRepItem = mapRepItems[0]
        if not mapRepItem.is_a('IfcTrimmedCurve'):
            raise Exception(f'Error! Representation item type ({mapRepItem.is_a()}) not supported.')

        basisCurve = mapRepItem.BasisCurve
        if not basisCurve.is_a('IfcLine'):
            raise Exception(f'Error! Basis curve type ({basisCurve.is_a()}) not supported.')

        masterRep = mapRepItem.MasterRepresentation
        if masterRep != 'CARTESIAN':
            raise Exception(f'Error! Master representation {masterRep} not supported.')

        trim1, trim2 = mapRepItem.Trim1, mapRepItem.Trim2
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
            EndA[i], EndB[i] = t1[0][i] + mapOriginLoc[i], t2[0][i] + mapOriginLoc[i]
            EndA[i] *= fconvL
            EndB[i] *= fconvL

        self.EndA = EndA.copy()
        self.EndB = EndB.copy()

        psets = ifcopenshell.util.element.get_psets(ifcBeam)
        #ifcLength = fconvL*psets['Qto_BeamBaseQuantities']['Length']
        ifcLength = fconvL*psets['Pset_BeamCommon']['Span']
        calcLength = self.Length()
        if abs(calcLength-ifcLength)/ifcLength > self.lengthTol:
            print(f'Warning! Calculated length {calcLength}m different of the IFC pset data length {ifcLength}m.')
        

# MAIN
print(f'Reading file {file} ...', flush=True)
ifcFile = ifcopenshell.open(file)
ifcBeams = ifcFile.by_type('IfcBeam')
beam = bimBeam()
for ifcBeam in ifcBeams:
    #print('\nBeam: ', ifcBeam)
    beam.importFromIfc(ifcFile, ifcBeam, "Model", "Axis")
    #print(' Length = ', beam.Length())


