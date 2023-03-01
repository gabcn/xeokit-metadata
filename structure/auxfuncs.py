"""
Auxiliary functions
"""

import numpy as np
import math

def CalcBarSecProps(h, b):
    """
    Calcuate the properties of a bar (rectangular) section
    * h, b: bar (rect.) section dimensions
    * return: A, Ixx, Iyy, J
    """
    A = h*b
    Ixx = b*h**3/12
    Iyy = h*b**3/12
    J = b*h*(b**2+h**2)/12
    return A, Ixx, Iyy, J
    
def CalcBoxSecProps(h, b, tw=None, tftop=None, tfbot=None, otw=None) -> tuple[float, float, float, float]:
    """
    Calcuate the properties of a box section
    * h, b: box section dimensions
    * tw, tftop, tfbot: plate thickness (box section), if 'None', bar (rect.) section is considered
    * otw: outer web thickness (in case of double box section)
    * return: A, Ixx, Iyy, J
    """
    if tw == None: # bar section
        A = h*b
        Ixx = b*h**3/12
        Iyy = b**3*h/12
        J = b*h*(b**2+h**2)/12
    elif tftop != None: # box section  # TODO: verify the inertia formulae
        A = h*b - (b-2*tw)*(h-tfbot-tftop)
        Ixx = b*h**3/12 - (b-2*tw)*(h-tfbot-tftop)**3/12
        Iyy = h*b**3/12 - (b-2*tw)**3*(h-tfbot-tftop)/12
        J = b*h*(b**2+h**2)/12 - (b-2*tw)*(h-tfbot-tftop)*((b-2*tw)**2+(h-tfbot-tftop)**2)/12
    if otw != None: # double box section
        A = h*b - (b-2*otw)*(h-2*otw) + tw*(h-2*otw)
        Ixx = b*h**3/12 - (b-2*otw)*(h-2*otw)**3/12 + tw*(h-2*otw)**3/12
        Iyy = h*b**3/12 - (b-2*otw)**3*(h-2*otw)/12 + tw**3*(h-2*otw)/12
        J = b*h*(b**2+h**2)/12 - (b-2*otw)*(h-2*otw)*((b-2*otw)**2+(h-2*otw)**2)/12 + tw*(h-2*otw)*(tw**2+(h-2*otw)**2)/12
    
    return A, Ixx, Iyy, J
    #return CrossSectionProps(A, Ixx, Iyy, J)

def CalcISecProps(h, b, tw, tf, fillet_radius, ws=None
    ) -> tuple[float, float, float, float]:
    """
    Calcuate the properties of an I section
    * h, b, tw, tf, fillet_radius: I section dimensions
    * ws: web spacing (double I sections)
    * return: A, Ixx, Iyy, J
    """
    # TODO: Include torsion inertia
    # TODO: Include fillet_radius
    hi = h-2*tf
    A = 2*b*tf + tw*hi    
    Ixx = tw*hi**3/12 + b/12*(h**3-hi**3)
    Iyy = hi*tw**3/12 + b**3/12*(h-hi)
    if ws != None: # double I section
        A += tw*hi
        Ixx += tw*hi**3/12
        Iyy = hi*(ws+tw)**3/12 - hi*(ws-tw)**3/12 + b**3/12*(h-hi)
    J = (Ixx+Iyy)/2 # TODO: temporary
    return A, Ixx, Iyy, J
    #return CrossSectionProps(A, Ixx, Iyy, J)


def setVecValuesAtoB(vecA: list[float], vecB: list[float]) -> None:
    for i in range(len(vecA)): vecB[i] = vecA[i]

def CalcAngleBetweenVectors(Vector1: list[float], 
                           Vector2: list[float]) -> float:
    """
    Calculates the angle between two vectors
    * Vector1: vector defined by components = [xV1, yV1, zV1]
    * return: angle between the vectors (in radians)
    """
    V1, V2 = np.array(Vector1), np.array(Vector2)
    V1xV2 = np.cross(V1, V2)
    mV1xV2 = np.linalg.norm(V1xV2)
    mV1, mV2 = np.linalg.norm(V1), np.linalg.norm(V2)
    _sin = min(1.,mV1xV2/(mV1*mV2))
    angle = math.asin(_sin)
    return angle



def CalcDistBetweenLineAndPoint(Line, Point) -> tuple[float, float]:
    """
    Calculates the distance between line and point. The line is defined by two points (A and B)
    * Line = [A, B]
    * Point = [xP, yP, zP]
    * returns: tuple:
        - length along Line (A->B) of the projection of the Point
        - distance
    A = [xA, yA, zA] 
    B = [xB, yB, zB]
    eta = (P-A).(B-A)/(B-A).(B-A)
    dist = |A + eta.(B-A)|
    """
    A, B = Line[0], Line[1]
    P = np.array(Point)
    P_A = P - np.array(A)
    B_A = np.array(B) - np.array(A)
    AB = np.linalg.norm(B_A)
    eta = np.dot(P_A,B_A)/AB**2
    X = np.array(A) + eta*B_A
    P_X = P - X
    dist = np.linalg.norm(P_X)
    return eta, dist
    
def CalcDistBetweenLines(Line1, Line2, 
                          angletol: float, disttol:float
                          ) -> tuple[float, float, float]:
    """
    Calculate the distance between two lines. Each line is defined by two points (A and B)
    * Line = [A, B]
    * tolerance = tolerance of the cross product of the vectors which define the lines to consider as paralel lines
    A = [xA, yA, zA] 
    B = [xB, yB, zB]
    dist = |(b1 x b2).(a2-a1)|/|b1 x b2|
    """

    # definition of each line as P = a + ksi1*b, where a is a point and b the vector which defines the line direction
    a1 = np.array(Line1[0])
    b1 = np.array(Line1[1]) - a1
    a2 = np.array(Line2[0])
    b2 = np.array(Line2[1]) - a2

    b1xb2 = np.cross(b1,b2)
    d_num = abs(np.dot(b1xb2,a2-a1))
    d_den = np.linalg.norm(b1xb2)

    mod_b1, mod_b2 = np.linalg.norm(b1), np.linalg.norm(b2)
    sin_theta = d_den/(mod_b1*mod_b2)
    sin_theta = min(sin_theta, 1)
    sin_theta = max(sin_theta, 0)
    angle = math.asin(sin_theta)*180/math.pi

    #if d_den <= tolerance: # if parallel
    if angle <= angletol: # if parallel
        ksiij = [0,1]
        connected = False
        for i in range(2):
            P1 = Line1[i]
            for j in range(2):
                P2 = Line2[j]                
                if _CalcDist(P1, P2) < disttol: 
                    ksi1 = ksiij[i]
                    ksi2 = ksiij[j]
                    connected = True
        if connected:
            return 0, ksi1, ksi2
        else:
            return None, None, None
    else:
        A = np.array([b1, b2])
        A_ = np.array([[b1[0], -b2[0]], [b1[1], -b2[1]], [b1[2], -b2[2]]])
        A = np.dot(A,A_)
        B = np.array([np.dot(a2-a1,b1), np.dot(a2-a1,b2)])
        if np.linalg.det(A) == 0:
            return None, None, None
        else:
            X = np.linalg.solve(A, B)
            ksi1, ksi2 = X[0], X[1]
            ksi1tol, ksi2tol = disttol/mod_b1, disttol/mod_b2
            #if ksi1 >= -0.001 and ksi1 <= 1.001 and ksi2 >= -0.001 and ksi2 <= 1.001:               
            if ksi1 >= -ksi1tol and ksi1 <= 1+ksi1tol \
               and ksi2 >= -ksi2tol and ksi2 <= 1+ksi2tol:

                d = d_num/d_den
                return d, ksi1, ksi2
            else:
                return None, None, None

def CalcDist(Pa: list[float], Pb: list[float]) -> float:
    dist = math.sqrt((Pa[0]-Pb[0])**2+(Pa[1]-Pb[1])**2+(Pa[2]-Pb[2])**2)
    return dist

def CalcSimpDist(Pa: np.ndarray, Pb: np.ndarray) -> float:
    delta = Pa - Pb
    absdelta = abs(delta)
    return max(absdelta)

def CalcDirection(
        Pa: list[float], Pb: list[float]
        ) -> tuple[list[float],float]:
    """Calculates the direction vector (normalized) from Pa to Pb"""
    V = np.array(Pb) - np.array(Pa)
    length = np.linalg.norm(V)
    normV = V*(1./length)
    return normV.tolist().copy(), length


def CalcBetweenCoordinates(
    endA: list[float], 
    endB: list[float], 
    pos: float
    ): # -> np.ndarray[float]:
    """
    Calculates the coordinates (x, y, z) of a position between endA and endB
    endA: [xA, yA, zA]
    endB: [xB, yB, zB]
    position: natural coordinate (0 for initial position)
    """
    A = np.array(endA)
    B = np.array(endB)
    P = A + (B-A)*pos
    return P.copy()