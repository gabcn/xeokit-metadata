sesamFilePath = r'D:\Temp\2022.05.19.TRIDENT_PCE1_ULS.xml'
outIfcFilePath = r'D:\Temp\from_sesam.ifc'

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
#ifcFile = ifc.file(schema='IFC4')

"""
for i, beam in enumerate(model._Beams):
    found = None
    name = 'Bm581'
    if beam.name == name:
        found = beam
        break
    if not found: raise Exception(f'Beam {name} not found')
"""
model.ExportToIFC(outIfcFilePath, slice(1))

#model._Beams[0].exportBeamToIfc(ifcFile)
#ifcFile.write(outIfcFilePath)