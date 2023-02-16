# INPUTS
ifcFilePath = r'C:\Temp\PCE_JACKET_IFC4_ComInfo.ifc'
sesamFilePath = r'C:\Temp\2022.05.19.TRIDENT_PCE1_ULS.xml'


# LIBS
import structure.ifcStructure as structBeam
from structure.sesammodel import cSesamModel
import ifcopenshell as ifc


ifcFile = ifc.open(ifcFilePath)
ifcBeam = ifcFile.by_guid('07KLEqOE5F8fgf$OpiNJ5g')



newbeam = structBeam.bimBeam(ifcFile, ifcBeam, 'Model', 'Axis')
print(newbeam.EndA)
print(newbeam.EndB)