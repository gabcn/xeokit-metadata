sesamFilePath = r'C:\Temp\2022.05.19.TRIDENT_PCE1_ULS.xml'
outIfcFilePath = r'C:\Temp\from_sesam.ifc'

import structure.ifcsesam
#model = structure.ifcsesam.modelIfcSesam(xmlSesamFile=sesamFilePath)
model = structure.ifcsesam.modelIfcSesam()
model.Selections.ExcludeSets.extend(
    ['_ALL','Bucking_KY_1_0','Buckling_BeC','Buckling_KY_0_7','Buckling_KY_0_8',
     'Buckling_Lenght','BuoyancyArea','JACKET_analysis'])
model.Selections.ExcludedEquipsLoadCases.append('LC_EQUIP_GENERATION_MOD_wet')
model.ImportFromSesamConceptModel(sesamFilePath)
#model.ExportToIFC(outIfcFilePath)

"""
sesamFile = r'C:\Temp\2023.02.28.FRADE_SRU.xml'
ifcFile = sesamFile.replace('.xml', '.ifc')
model = structure.ifcsesam.modelIfcSesam(xmlSesamFile=sesamFile)
model.ExportToIFC(ifcFile)
"""