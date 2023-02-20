sesamFilePath = r'C:\Temp\2022.05.19.TRIDENT_PCE1_ULS.xml'
outIfcFilePath = r'C:\Temp\from_sesam.ifc'

#import structure.sesammodel as sesam
import structure.ifcsesam

"""
sesamModel = sesam.cSesamModel(sesamFilePath)
sesamBeam = sesamModel._Beams[10]

print(sesamBeam.name)

ifcFile = ifc.file(schema='IFC4')
ifcBeam = exportBeamToIfc(sesamBeam, ifcFile)
ifcFile.write('test.ifc')
"""

model = structure.ifcsesam.modelIfcSesam(xmlSesamFile=sesamFilePath)


import ifcopenshell as ifc
ifcFile = ifc.file(schema='IFC4')
model._Beams[0].exportBeamToIfc(ifcFile)