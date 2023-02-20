"""
Defines a class with multiple inheritance from ifc and sesam classes
"""

from structure.conceptmodel import classConceptModel
from structure.sesammodel import classBeam, cSesamModel, classBeamList
from structure.ifcmodel import bimBeam, ifcModel, ifcBeamList



class beamIfcSesam(bimBeam, classBeam):    
    pass

class beamListIfcSesam(list[beamIfcSesam]):
    def __init__() -> None:
        return super().__init__()

class beamListIfcSesam(ifcBeamList, classBeamList, beamListIfcSesam):
    def __init__(self, conceptModel: classConceptModel, ifcFilePath: str = None):
        #super().__init__(conceptModel, ifcFilePath)
        self.conceptModel = conceptModel
        if ifcFilePath: self.ImportFromIFC(ifcFilePath)

    def AddBeam(self,name: str, IniPos: list[float]) -> beamIfcSesam:
        #return super().AddBeam(name, IniPos)
        beam = beamIfcSesam(name, IniPos)
        super().append(beam)    
        return beam    

class modelIfcSesam(ifcModel, cSesamModel):
    def __init__(self, xmlSesamFile: str = None, ifcFilePath: str = None) -> None:
        super().__init__()
        self._Beams = beamListIfcSesam(self, ifcFilePath)
        if xmlSesamFile: self.ImportFromSesamConceptModel(xmlSesamFile)

        
        
