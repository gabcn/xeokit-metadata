"""
* File containing the class with functions (tools) to create 
* a beam structures 
*
* Created by Gabriel Nascimento (NSG) in 14/02/2023
* Last revision in ...
*
* Usage ....
"""

# ========== LIBS ========== #
from __future__ import annotations
import ctypes
from dataclasses import dataclass, replace #, field
#from typing import Union #, overload
import math
import numpy as np
from enum import Enum
from scipy import interpolate
from structure.auxfuncs import *


_char = ctypes.c_wchar
_letters = 'abcdefghijklimnoprstuvwxyz'
#relpostol = 0.0001 # relative position tolerance 
#MinLength = 0.05 # TODO: revise this constant in other functions
#ProximityTol = 0.01 # tolerance of distance to assume coincident


# ==== Options ==== #
class classOptions:
    def __init__(self) -> None:
        self.MinLength = 0
        self.ProximityTol = 0.1
        self.ExcludeSections = list()      
        self.ExcludeSets = list()  
        self.Xlimits = [None, None]
        self.Ylimits = [None, None]
        self.Zlimits = [None, None]
        self.UseConstraints = False
        self.LineStatic = True
        self.AngleTol = 1 # angle tolerance (in deg) to assume parallel lines

    def __WithinLimits(self, value: float, limits: list[float]) -> bool:
        ok = True        
        if limits[0] != None:
            if value < limits[0]: ok = False
        if limits[1] != None:
            if value > limits[1]: ok = False
        return ok

    def IsWithinLimits(self, coords: list[float]) -> bool:
        x, y, z = coords[0], coords[1], coords[2]
        if not self.__WithinLimits(x, self.Xlimits): return False
        if not self.__WithinLimits(y, self.Ylimits): return False
        if not self.__WithinLimits(z, self.Zlimits): return False
        return True


# ==== ENVIRONMENT ==== #
@dataclass
class classEnvironment:
    WaterDepth: float = 100
    WaterSurfaceZ: float = 0
    MaxWaveHeight: float = 15

# ==== MATERIALS ==== #
@dataclass
class MaterialProps:
    '''density in kg/m³, YongModulus and Sadm in Pa, damping  is ratio of critical damping'''
    name: str
    density: float 
    YoungModulus: float # in Pa
    PoissonCoef: float #
    Sadm: float = 0 # in Pa
    alpha: float = 0 #
    damping: float = 0 #

class classMatList(list[MaterialProps]):
    def __init__(self):
        result = super().__init__()
        return result

    def Find(self, material: str) -> MaterialProps:
        found = -1
        for i, mat in enumerate(self):
            if mat.name == material: 
                found = i
                break
        return self[found]


@dataclass
class GenLineTypeProps:
    """masslin in kg/m; EIx, EIy, and GJ in N.m2, EA in N"""
    masslin: float
    EIx: float
    EIy: float
    EA: float
    Poisson: float
    GJ: float

@dataclass
class classSegProps:
    section: str 
    material: str
    #morison_coef: str = None # TODO: import hydrodynamic coefficients
    #air_drag_coef: str = None # TODO: import air drag coefficient
    hydro_coefs: str = None
    sectionPointer: __classSection = None

    def copy(self):
        return replace(self)
    def EncodeLineTypeName(self) -> str:
        #return f'Sec={self.section}_Mat={self.material}_Hydro={self.morison_coef}_Air={self.air_drag_coef}'    
        return f'Sec={self.section}_Mat={self.material}_HydroCoefs={self.hydro_coefs}'    

class classLineTypeList(list[classSegProps]):
    def __FindLineTypeIndex(self, segmentprops: classSegProps) -> int:
        if len(self) == 0: return -1
        found = -1
        for i, lt in enumerate(self):
            if lt == segmentprops:
                found = i
                break
        return found   

    def Add(self, 
            segmentprops: classSegProps, 
            ) -> classSegProps:
        """
        Verifies if the linetype exists, and:
        * if not, add the linetype to the list and returns the new object
        * if exists, return the existing linetype
        """
        i = self.__FindLineTypeIndex(segmentprops)
        if  i < 0:
            self.append(segmentprops)
            return segmentprops
        else:
            return self[i]

    def GenerateAll(self):
        for beam in self.orcbeam._Beams:
            for seg in beam.SegmentList:
                self.Add(seg.properties)


    def __CheckHydroCoefsForHomogeneousPipe(self, HydroCoeffs: classMorisonCoeffs) -> bool:
        ok = True
        if HydroCoeffs.cd.x != HydroCoeffs.cd.y: ok = False
        if HydroCoeffs.ca != None:
            if HydroCoeffs.ca.x != HydroCoeffs.ca.y: ok = False
            if HydroCoeffs.cm != None:
                if HydroCoeffs.cm.x != HydroCoeffs.ca.x+1 or \
                   HydroCoeffs.cm.y != HydroCoeffs.ca.y+1 or \
                   HydroCoeffs.cm.z != HydroCoeffs.ca.z+1:
                    ok = False
        return ok





# ==== Hydro props ==== #
@dataclass
class classDirections:
    x: float = math.nan
    y: float = math.nan
    z: float = math.nan

@dataclass 
class classMorCoeffPoint:
    diameter: float
    cd: float
    cm: float
    cd_nf: float
    cm_nf: float

class cListMorCoeffPnt(list[classMorCoeffPoint]):
    def Add(self, diameter: float, 
            cd: float, cm: float, 
            cd_nf: float, cm_nf: float) -> None:
        newpnt = classMorCoeffPoint(diameter, cd, cm, cd_nf, cm_nf)
        self.append(newpnt)

#@dataclass
class classMorisonCoeffs:
    def __init__(self, 
                 name: str, 
                 # constant
                 cd: classDirections = None,
                 ca: classDirections = None,
                 cm: classDirections = None,
                 # by diameter
                 points: cListMorCoeffPnt = None):
        self.name = name
        self.cd = cd
        self.ca = ca
        self.cm = cm
        if points == None:
            self.points = cListMorCoeffPnt()
        else:
            self.points = points

class classHPropsList(list[classMorisonCoeffs]):
    def __init__(self):
        result = super().__init__()
        return result

    def _FindIndex(self, name: str) -> int:
        for i, item in enumerate(self):
            if item.name == name:
                return i
        return -1
    
    def Find(self, name: str) -> classMorisonCoeffs:
        i = self._FindIndex(name)
        if i < 0:
            raise Exception(f'Error! Hydraulic properties named "{name}" not found.')
        else:
            return self[i]
    """
    def append(self, __object: classMorisonCoeffs) -> None:
        __object.points = cListMorCoeffPnt()
        return super().append(__object)
    """

# ==== EQUIPMENTS ==== #
class classEquipment:
    def __init__(self, name: str) -> None:
        """
        Equipment
            * name
        """
        self.name = name
        self.mass: float # (in kg)
        self.origin: list[float] # (in meters) [x, y, z]
        self.CoG: list[float] # (in meters) [x, y, z] relative to origin
        self.dimensions: list[float] # (in meters) [x, y, z] 
        self.footprint: list[float] # (in meters) [x1, y1, x2, y2] relative to origin
        self.OrientationMatrix = [[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]]
        self.LoadCase: str

class classEquipList(list[classEquipment]):
    def __init__(self, conceptModel: classConceptModel) -> None:
        super().__init__()
        self.conceptModel = conceptModel


# ==== sections ==== #
class SectionType(Enum):
    pipe_section = 1
    i_section = 2
    doblei_section = 3
    bar_section = 4
    box_section = 5
    doublebox_section = 6

@dataclass
class CrossSectionProps:
    """ A in m2; Ixx, Iyy, Izz in m4"""
    # TODO: check unit from source model
    A: float
    Ixx: float
    Iyy: float
    Izz: float    

class __classSection:
    def __init__(self, name:str, sectype: SectionType) -> None:
        self.name = name
        self.sectype = sectype
        self.generalsec = None
    
    def _Get_OD(self): ...
    def _Get_ID(self): ...
    OD = property(_Get_OD)
    ID = property(_Get_ID)
    
    def SetGeneralSection(self, A: float, Ixx: float, Iyy: float, Izz: float):        
        """
        Set general section type (area and inertia manually defined)
        * A: section area
        * Ixx, Iyy: transversal moment of inertia
        * Izz: axial (torsional) moment of inertia
        """
        # TODO: improve the input definitions and handling
        self.generalsec = CrossSectionProps(A, Ixx, Iyy, Izz)


    def CalcLineTypeProps(self, material: MaterialProps, csprops: CrossSectionProps) -> GenLineTypeProps:
        rho, E, Poisson = material.density, material.YoungModulus, material.PoissonCoef 
        G = E/(2*(1+Poisson))
        A, Ixx, Iyy, Izz = csprops.A, csprops.Ixx, csprops.Iyy, csprops.Izz
        return GenLineTypeProps(A*rho, E*Ixx, E*Iyy, E*A, Poisson, G*Izz)        



class classPipeSection(__classSection):
    def __init__(self, name: str, OD: float, th: float) -> None:
        self._OD = OD
        self.th = th
        super().__init__(name, SectionType.pipe_section)
    
    def _Get_OD(self): return self._OD    
    def _Get_ID(self): return self._OD - 2*self.th
    OD = property(_Get_OD)
    ID = property(_Get_ID)



class classISection(__classSection):
    def __init__(self, name: str, h, b, tw, tf, fillet_radius, ws=None) -> None:
        self.h = h
        self.b = b
        self.tw = tw
        self.tf = tf
        self.fillet_radius = fillet_radius
        self.ws = ws # web spacing (double I section)
        super().__init__(name, SectionType.i_section)
        
    def _Get_OD(self):
        OD = (self.h+self.b)/2
        return OD
    def _Get_ID(self):
        ID = self.OD-2*self.tf                
        return ID
    OD = property(_Get_OD)
    ID = property(_Get_ID)
    



class classBoxSection(__classSection):
    def __init__(self, name: str, h, b, tw=None, tftop=None, tfbot=None, otw=None) -> None:
        self.h = h          # height
        self.b = b          # base width
        self.tw = tw        # web thickness
        self.tftop = tftop  # top flange thickness
        self.tfbot = tfbot  # bottom flange thickness
        self.otw = otw      # outer web thickness (<>None -> double box section)
        if tw == None: sectype = SectionType.bar_section
        elif otw == None: sectype = SectionType.box_section
        else: sectype = SectionType.doublebox_section
        super().__init__(name, sectype)
        
    def _Get_OD(self):
        OD = (self.h+self.b)/2
        return OD
    def _Get_ID(self):
        return 0.0
    OD = property(_Get_OD)
    ID = property(_Get_ID)
    


class classSectionList(list[__classSection]):
    def __init__(self):
        result = super().__init__()
        return result

    def names(self) -> list[str]:
        return [sec.name for sec in self]

    def Index(self, name: str) -> int:
        return self.names().index(name)
        
    def Find(self, name: str) -> __classSection: #classISection:
        i = self.Index(name)
        return self[i]
    
    def IsDefined(self, name: str):
        return name in self.names()
    
    def SectionNames(self) -> list:
        return [sec.name for sec in self]
    
    def Add(self, section: __classSection):
        self.append(section)


# === connection === #
@dataclass
class classConnectMember:
    beam: classBeam
    #position: float # 0 for EndA; 1 for EndB
    position: str # end A or B

    def Coord(self) -> np.array:
        if self.position == 'A': pos = 0
        else: pos = 1 # 'B'
        return CalcBetweenCoordinates(self.beam.EndA, self.beam.EndB, pos)
    """
    def PosInsideTol(self, pos: float) -> bool:
        if pos - MinLength/self.beam.length <= self.position and \
           self.position <= pos + MinLength/self.beam.length:
            return True
        else:
            return False
    """
class classConnectMemberList(list[classConnectMember]): 
    def __init__(self, 
                 beamA: classBeam, posA: str,
                 beamB: classBeam=None, posB: str=None) -> None:
        self.append(classConnectMember(beamA, posA))
        if beamB != None and posB != None:
            self.append(classConnectMember(beamB, posB))

    def Add(self, beam: classBeam, pos: str) -> None:
        self.append(classConnectMember(beam, pos))    

    def AddByMember(self, member: classConnectMember) -> None:
        self.append(member)

    def Search(self, beam: classBeam, pos: str) -> int:
        found = -1
        for i, cmember in enumerate(self):
            if cmember.beam == beam and cmember.position == pos: # cmember.PosInsideTol(pos):
                found = i
                break
        return found  
    
    def print(self, outputfunction: function = None):
        #print('Connection members: ', end=' ')
        for member in self:
            if outputfunction != None:
                outputfunction(f'{member.beam.name}@{member.position}', end=', ')
            else:
                print(f'{member.beam.name}@{member.position}', end=', ')
        #print('.')

class classConnectList(list[classConnectMemberList]):  
    def SearchByMember(self, member: classConnectMember) -> int:
        return self.Search(member.beam, member.position)

    def Search(self, beam: classBeam, pos: str) -> int:
        for i, connect in enumerate(self):
            found = connect.Search(beam, pos)
            if found >= 0: return i
        return -1

    def AddMembers(self, members: classConnectMemberList) -> None:
        while members.count(None) > 0: members.remove(None)
        if len(members) > 0:
            found = False
            for member in members:
                i = self.SearchByMember(member)
                if i >= 0:
                    found = True
                    for m in members:
                        if self[i].Search(m.beam, m.position) < 0:
                            self[i].append(m)
                    break
            if not found:
                memberlist = classConnectMemberList(members[0].beam, 
                                                    members[0].position)
                for m in members[1:]:
                    memberlist.append(m)
                self.append(memberlist)

    def AddPair(self, 
                beamA: classConnectMember, 
                posA: str,
                beamB: classConnectMember,
                posB: str):
        iA = self.Search(beamA, posA)
        iB = self.Search(beamB, posB)
        if iA >= 0 and iB >= 0: pass # pair already in a connection
        elif iA >= 0: self[iA].Add(beamB, posB) # only beamA already in a connection
        elif iB >= 0: self[iB].Add(beamA, posA) # only beamB already in a connection
        else: self.append(classConnectMemberList(beamA, posA, beamB, posB)) # neither in a connection

    def print(self):
        for i, connection in enumerate(self):            
            self.orcbeam._Message(f'Connection {i+1}:', end=' ')
            #for member in connection:
            #    print(f'{member.beam.name}@{member.position}', end=' ')
            connection.print(self.orcbeam._Message)
            self.orcbeam._Message('.')
            



# === SUPPORTS === #
class FixType(Enum):
    x  = 0
    y  = 1
    z  = 2
    Rx = 3
    Ry = 4
    Rz = 5

#@dataclass
class classSupport:
    def __init__(self, name: str, conceptModel: classConceptModel) -> None:
        self.name = name
        self.position = None
        self.fixings = list[FixType]
        self.__connection = None # classConnectMember
        self.conceptModel = conceptModel

    def __Set_Connection(self, connection: classConnectMember) -> None:
        self.__connection = connection
    def __Get_Connection(self) -> classConnectMember:
        return self.__connection
    connection = property(__Get_Connection, __Set_Connection)


    
class classSupportList(list[classSupport]):
    def __init__(self, conceptModel: classConceptModel):
        self.conceptModel = conceptModel
        super().__init__()

    def Add(self, name: str) -> classSupport:
        newsupport = classSupport(name, self.conceptModel)
        self.append(newsupport)
        return newsupport
    
    def LinkToConnections(self):
        tol = self.conceptModel.Selections.ProximityTol        
        connections = self.conceptModel._Connections
        for support in self:
            connected = False
            A = support.position
            for connection in connections:
                B = connection[0].Coord()
                dist = CalcSimpDist(A, B)
                if dist < tol:
                    support.connection = connection[0]
                    connected = True
                    break

            if not connected:
                for beam in self.orcbeam._Beams:
                    for End, coord in zip(['A', 'B'], [beam.EndA, beam.EndB]):
                        B = np.array(coord)
                        dist = CalcSimpDist(A, B)
                        if dist < tol:
                            support.connection = classConnectMember(beam, End)
                            connected = True
                        if connected: break
                    if connected: break
            # TODO: include what to do if no near connection is found


    def ToOrcaFlex(self):
        self.LinkToConnections()
        for support in self:
            support.ToOrcaFlex(self.orcbeam.OrcFxModel)


# === BEAMS === #
@dataclass
class classSegment:
    length: float
    properties: classSegProps = None
    IniPos: list[float] = None # in local coordinate system
    Direction: list[float] = None # in local coordinate system
    flooding: str = '' # TODO: import flooding condition
    def copy(self):
        return replace(self)
    
class classSegmentList(list[classSegment]):
    def Add(self, length: float, segprops: classSegProps):
        seg = classSegment(length, segprops)
        self.append(seg)

class classBeam:
    def __init__(self, 
                 name: str = '', 
                 IniPos: list[float] = None # local coordinate system
                 ):
        super().__init__()
        self.name = name  
        #self.__IniPos = IniPos # in local coord. system
        if not IniPos: self.__IniPos = [0,0,0]
        else: self.__IniPos = IniPos.copy()

        #self.InitialPos = IniPos.copy()
        self.LastPos = self.__IniPos.copy() # in local coord. system
        self.ConnectionA, self.ConnectionB = ('Free',)*2        
        self.SegmentList = classSegmentList()
        self.Description = ''
        # transformation matrix from local beam coordinates to global coordinates
        self.locToGlobTransfMtx = \
            [[1.,0.,0.,0.],[0.,1.,0.,0.],[0.,0.,1.,0.],[0.,0.,0.,1.]]
        #self.L_EndA = [0.,0.,0.] # in meters (local coordinates)
        #self.L_EndB = [0.,0.,0.] # in meters (local coordinates)
    
    # encapsulate to ensure that if IniPos is changed before adding segment, LastPos also is
    def __getIniPos(self): return self.__IniPos
    def __setIniPos(self, pos: list[float]): 
        if self.Nsegs>0: 
            raise Exception('Error! The initial beam position (1st segment) '+\
                            'can not be changed after adding segments.')
        else:
            setVecValuesAtoB(pos, self.__IniPos)
            setVecValuesAtoB(pos, self.LastPos)

    IniPos = property(__getIniPos, __setIniPos)

    def __LocalToGlobal(self, locCoords: list[float]) -> list[float]:
        """
        Converts from the local to global coordinates
        """
        lC = locCoords.copy()
        lC.append(1) # for the translation
        alC = np.array(lC)
        agC = np.matmul(self.locToGlobTransfMtx, alC)
        return agC.tolist()[:3]

    def getGlobalEndA(self) -> list[float]: 
        return self.__LocalToGlobal(self.IniPos) # self.L_EndA)
    def getGlobalEndB(self) -> list[float]: 
        return self.__LocalToGlobal(self.LastPos) # self.L_EndB)

    EndA = property(getGlobalEndA) 
    """(global coordinates)"""
    EndB = property(getGlobalEndB) 
    """(global coordinates)"""

    def getRefCoords(self) -> list[float]:
        """Returns the reference coordinates (x, y, z)"""
        M = self.locToGlobTransfMtx
        coords = []
        for i in range(3): coords.append(M[i][3])
        return coords.copy()

    RefCoords = property(getRefCoords)
    """Reference coordinates"""

    def _GetNsegs(self):
        return len(self.SegmentList)
    Nsegs = property(_GetNsegs)

    '''
    def __fGetLength(self) -> float:
        """
        Returns the beam length (meters)
        """
        V = np.array(self.L_EndA) - np.array(self.L_EndB)
        return np.linalg.norm(V)

    length = property(__fGetLength)    
    '''
    def _GetTotalLength(self):
        L = 0
        for seg in self.SegmentList: L += seg.length
        return L
    length = property(_GetTotalLength)
    """"Total beam length"""

    def LengthToSeg(self, iseg: int) -> float:
        """Returns the cumulative length until the i-th segment"""
        L = 0
        if self.Nsegs > 0 and iseg >= 0:
            for i in range(iseg+1): L += self.SegmentList[i].length
        return L

    def AddSegmentByEnd(self, 
                        EndPos: list[float], 
                        segprops: classSegProps = None
                        ) -> None:
        """
        Adds a straight segment by the end coordinate (local system)
        from the LastPos defined
        * EndPos: [x,y,z] (local coordinate)
        * segprops: properties defined by the classSegProps
        """

        #length = _CalcDist(self.LastPos, EndPos)
        direction, length = CalcDirection(self.LastPos, EndPos)
        self.__AddSegmentByLength(
            length, 
            segprops, 
            self.LastPos.copy(),
            direction
            )
        self.LastPos = EndPos.copy()

    def __AddSegmentByLength(self, 
                             length: float, 
                             segprops: classSegProps,
                             IniPos: list[float] = None,
                             Direction: list[float] = None
                             ):
        self.SegmentList.append(
            classSegment(
                length, 
                segprops,
                IniPos,
                Direction
            )
        )

    def copy(self) -> classBeam:        
        newbeam = classBeam(self.name, self.IniPos)
        newbeam.ConnectionA = self.ConnectionA
        newbeam.ConnectionB = self.ConnectionB
        for seg in self.SegmentList:
            newbeam.SegmentList.append(seg.copy())
        newbeam.LastPos = self.LastPos.copy()
        return newbeam
        
    def MeanCoords(self) -> list[float]:
        """Returns the mean coordinates (center)"""
        A = np.array(self.EndA)
        B = np.array(self.EndB)
        mean = 0.5*(A+B)
        return mean.tolist().copy()

    """    
    def AngleToBeam(toBeam: classBeam) -> float:
        Calculates the angle between the current beam and other
        * toBeam: beam to 

    """
    def CoincidentLevel(self, otherBeam: classBeam) -> float:
        """
        Calculates the coincident level between the current beam and other
        * otherBeam: the other beam (classBeam)
        * returns: coincident level (0 - 1)
        """
        V = list()
        for b in [self, otherBeam]:
            V.append(np.array(b.EndB) - np.array(b.EndA))
        angle = CalcAngleBetweenVectors(V[0], V[1])

        _eta1, dist1 = _CalcDistBetweenBeamAndPoint(self, otherBeam.EndA)
        _eta2, dist2 = _CalcDistBetweenBeamAndPoint(self, otherBeam.EndB)

        #fEta1, fEta2 = 1-min(abs(_eta1), abs(1-_eta1)), 1-min(abs(_eta2), abs(1-_eta2))

        fEta1xfEta2a = abs(_eta1) + abs(1-_eta2)
        fEta1xfEta2b = abs(1-_eta1) + abs (_eta2)
        fEta1xfEta2 = max(0, 1-min(fEta1xfEta2a, fEta1xfEta2b))

        refDist = self.length/10
        fDist1, fDist2 = max(0, 1-dist1/refDist), max(0, 1-dist2/refDist)

        #fEtaXfDist = min(fEta1*fDist1, fEta2*fDist2)

        fAngle = max(0, 1-angle/(math.pi/2))

        #f = fAngle*fEtaXfDist
        f = fAngle*fEta1xfEta2*fDist1*fDist2
        return f


class classBeamList(list[classBeam]):   
    def __init__(self, conceptModel: classConceptModel):
        self.conceptModel = conceptModel
        super().__init__()

    def AddBeam(self, name:str, IniPos: list[float]) -> classBeam: 
        beam = classBeam(name, IniPos)
        super().append(beam)
        return beam
    
    def RemoveBeam(self, beam: classBeam):
        super().remove(beam)

    def FindByName(self, name: str) -> classBeam:
        """Returns the first occurence of beam with the specified name"""
        found = None
        for beam in self:
            if beam.name == name:
                found = beam
                break
        return found

    def DetectIntersections(self): 
        tolerance = self.conceptModel.Selections.ProximityTol
        i = 0
        while i < len(self)-1:
            j = i+1
            while j < len(self):
                beam1 = self[i]
                beam2 = self[j]
                d, ksi1, ksi2 = self._CalcDistBetweenBeams(beam1, beam2) #, tolerance)
                if d != None:
                    if d <= tolerance:
                        connect1A, connect1B = self._DivideBeam(beam1, ksi1) #, minlength)
                        connect2A, connect2B = self._DivideBeam(beam2, ksi2) #, minlength)
                        connections = [connect1A, connect1B, connect2A, connect2B]
                        self.ConnectList.AddMembers(connections)
                j += 1
            i += 1


    def _CalcDistBetweenBeams(self, beam1: classBeam, beam2: classBeam) -> tuple[float,float,float]:
        A1, B1 = beam1.EndA, beam1.EndB
        A2, B2 = beam2.EndA, beam2.EndB
        return CalcDistBetweenLines([A1, B1], [A2, B2], 
                                      self.orcbeam.Selections.AngleTol,
                                      self.orcbeam.Selections.ProximityTol)
    
    def _DivideBeam(self, 
                    beam: classBeam, 
                    ksi: float#, 
                    #minlength: float
                    ) -> tuple[classConnectMember,classConnectMember]:
        """
        Divide the beam, creating one more beam
        * ksi: natural coordinate of the dividing point
        * minlength: minimum 
        * return: the connection
        """
        #minlength = self.orcbeam.Selections.MinLength
        n = self._SliceBeam(beam, ksi) #, minlength)
        if n > 0 and n < beam.Nsegs:
            newbeam = beam.copy()
            beam.name += '_PartA'  # TODO: revise name conflict and correlation with other objects
            newbeam.name += '_PartB'
            divpoint = CalcBetweenCoordinates(beam.EndA, beam.EndB, ksi)
            beam.LastPos = divpoint.tolist().copy()
            newbeam.IniPos = beam.LastPos.copy()
            del newbeam.SegmentList[:n]
            self.append(newbeam)
            del beam.SegmentList[n:]

            connectA = classConnectMember(beam, 'B') # 1.0)
            connectB = classConnectMember(newbeam, 'A') #0.0)

            # update the end B connection
            jconnectionold = self.ConnectList.Search(beam, 'B') #1.0)
            if jconnectionold >= 0:
                k = self.ConnectList[jconnectionold].Search(beam, 'B') #1.0)
                member = self.ConnectList[jconnectionold][k]
                member.beam = newbeam                

        elif n == 0:
            connectA = None
            connectB = classConnectMember(beam, 'A') #0)

        else: # n == beam.Nsegs
            connectA = classConnectMember(beam, 'B') #1)
            connectB = None

        return connectA, connectB
        

    def _SliceBeam(self, 
                  beam: classBeam, 
                  ksi: float#, 
                  #minlength: float
                  ) -> int:
        """
        Slice the beam, creating one more segment
        * ksi: natural coordinate of the slicing point
        * minlength: minimum 
        * return the number of segments before the slicing point
        """
        minlength = self.orcbeam.Selections.MinLength
        L = beam.length        
        n = beam.Nsegs
        i = 0
        while i<n-1 and ksi > beam.LengthToSeg(i)/L: #Lj/L: # search the i-th segment to be sliced
            i += 1

        Li = ksi*L-beam.LengthToSeg(i-1)
        Lj = beam.LengthToSeg(i)-ksi*L
        if  Li >= minlength and Lj >= minlength: # slice
            #Lnew = ksi*L-Li
            beam.SegmentList[i].length -= Li
            newseg = beam.SegmentList[i].copy()
            newseg.length = Li
            beam.SegmentList.insert(i, newseg)
            return i+1
        else:
            if Lj >= minlength: return i
            elif Li >= minlength: return i+1
            else:
                if Li < Lj: return i
                else: return i+1


    # PUBLIC METHODS (classOrcBeamTools)

    def __ExportBeams(self, LineTypeList: classLineTypeList):
        for beam in self._Beams:
            name = beam.name
            nsegs = beam.Nsegs
            if nsegs == 0:
                self._Message(f'Warning! The structure {name} has no segments and will be skipped.')
                return False        

            LineType, Weighting = [], []

            for seg in beam.SegmentList:
                ltname = seg.properties.EncodeLineTypeName()
                LineType.append(ltname)
                l = seg.length
                Weighting.append(l/beam.length)
                # TODO: import mesh refinement from source model 
            line = self.AddBeam(name, beam.IniPos, beam.LastPos, LineType, Weighting)

    def nameList(self) -> list[str]:
        """Returns a list of the beam names"""
        namelist = []
        for beam in self:
            namelist.append(beam.name)
        return namelist.copy()


class classLineTypeList(list[classSegProps]):
    def __init__(self, conceptModel: classConceptModel):
        self.conceptModel = conceptModel
        super().__init__()

    def __FindLineTypeIndex(self, segmentprops: classSegProps) -> int:
        if len(self) == 0: return -1
        found = -1
        for i, lt in enumerate(self):
            if lt == segmentprops:
                found = i
                break
        return found   

    def Add(self, 
            segmentprops: classSegProps, 
            ) -> classSegProps:
        """
        Verifies if the linetype exists, and:
        * if not, add the linetype to the list and returns the new object
        * if exists, return the existing linetype
        """
        i = self.__FindLineTypeIndex(segmentprops)
        if  i < 0:
            self.append(segmentprops)
            return segmentprops
        else:
            return self[i]

    def GenerateAll(self):
        for beam in self.orcbeam._Beams:
            for seg in beam.SegmentList:
                self.Add(seg.properties)


    def __CheckHydroCoefsForHomogeneousPipe(self, HydroCoeffs: classMorisonCoeffs) -> bool:
        ok = True
        if HydroCoeffs.cd.x != HydroCoeffs.cd.y: ok = False
        if HydroCoeffs.ca != None:
            if HydroCoeffs.ca.x != HydroCoeffs.ca.y: ok = False
            if HydroCoeffs.cm != None:
                if HydroCoeffs.cm.x != HydroCoeffs.ca.x+1 or \
                   HydroCoeffs.cm.y != HydroCoeffs.ca.y+1 or \
                   HydroCoeffs.cm.z != HydroCoeffs.ca.z+1:
                    ok = False
        return ok


class classSet(list[str]):
    """
    Class of set (group of entities)
    """
    def __init__(self, name: str) -> None:
        """ 
        Initiates a class of set (group of entities)
        * name: name of the set
        """
        super().__init__()
        self.name = name

    def getNitems(self) -> int:
        return len(self)
    
    nItems = property(getNitems)

    def listItems(self) -> None:
        print('Items: ', end=' ')
        for item in self: print(item, end='; ')
        print('')

    #def copyItemsFrom(self, set: classSet) -> None:
    #    for item in set: self.append(item)


class classSetList(list[classSet]):
    def __init__(self, conceptModel: classConceptModel):
        super().__init__()
        self.conceptModel = conceptModel

    def getNsets(self) -> int:
        return len(self)
    nSets = property(getNsets)    
    """Number of sets"""

    def Add(self, name: str) -> classSet:
        newset = classSet(name)
        self.append(newset)
        return newset

    def PrintAll(self) -> None:
        for set in self:
            print(f'\nSet "{set.name}":')
            set.listItems()

    def listSetsWith(self, member: str) -> list[classSet]:
        setsfound = []
        for set in self:
            if member in set:
                setsfound.append(set)
        return setsfound.copy()



# ==== classConceptModel ==== #
class classConceptModel():
    """
    Includes functions (tools) to insert beams into OrcaFlex model as 'line' object
    """    
    # PRIVATE METHODS (classOrcBeamTools)
    def __init__(self) -> None:    
        self.IncludeTorsion = True
        self.Selections = classOptions()
        self.Environment = classEnvironment()
        self.EquipmentList = classEquipList(self)
        self._Connections = classConnectList()#self)
        self._Beams = classBeamList(self)
        self.Supports = classSupportList(self)
        self._SectionList = classSectionList()#self)
        self._MaterialList = classMatList()
        self._HydroProps = classHPropsList()
        self.SetList = classSetList(self)
        self.__LogFileName = 'log.txt'
        self.LogFile = open(self.__LogFileName, 'w')
        self.OriginInfo = {} # e.g., 'Program', 'Version', 'User'
        self.ConversionInfo = {} # e.g., 'Date'
        self.__nMessages = 0

   
    def _Message(self, text: str, end: str = '\n') -> None:
        #print(text, end=end)
        self.__nMessages += 1
        if end != '\n': ftxt = str(text).rstrip('\n')
        else: ftxt = text+end #+"\n"
        self.LogFile.write(ftxt)
       
    def Status(self) -> str:
        txt = 'There are no error/warning messages reported.'
        if self.__nMessages > 0:
            txt = f'\nThere are {self.__nMessages} error/warning mensages.' + \
                  f' See file {self.__LogFileName} for more details.'
        return(txt)



# ==== PRIVATE METHODS ==== #
def _InterpHydCoeffsByDiameter(D: float, HydroCoeffs: classMorisonCoeffs) -> classMorCoeffPoint:
    _D_list, _cd_list, _cm_list, _cd_nf_list, _cm_nf_list = [], [], [], [], []
    
    for pnt in HydroCoeffs.points:
        _D_list.append(pnt.diameter)
        _cd_list.append(pnt.cd)
        _cm_list.append(pnt.cm)
        _cd_list.append(pnt.cd)
        _cm_list.append(pnt.cm)
    
    cd_D = interpolate.interp1d(_D_list, _cd_list)
    cm_D = interpolate.interp1d(_D_list, _cm_list)
    cd_nf_D = interpolate.interp1d(_D_list, _cm_list)
    cm_nf_D = interpolate.interp1d(_D_list, _cm_list)
    
    return classMorCoeffPoint(D, cd_D(D), cm_D(D), cd_nf_D(D), cm_nf_D(D))



# === AUX FUNCTIONS ==== #
def _CalcDistBetweenBeamAndPoint(beam: classBeam, 
                                 Point: list[float]) \
                                 -> tuple[float, float]:
    """
    see _CalcDistBetweenLineAndPoint
    """
    A, B = beam.EndA, beam.EndB
    Line = [A, B]
    return CalcDistBetweenLineAndPoint(Line, Point)



