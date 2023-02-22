sesamFilePath = r'C:\Temp\2022.05.19.TRIDENT_PCE1_ULS.xml'
outIfcFilePath = r'C:\Temp\from_sesam.ifc'

import structure.ifcsesam

model = structure.ifcsesam.modelIfcSesam(xmlSesamFile=sesamFilePath)
#model.ExportToIFC(outIfcFilePath, slice(1))
model.ExportToIFC(outIfcFilePath)

