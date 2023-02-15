"""
Compare beams from IFC file and Sesam model (.xml) to
include the id's from Sesam into the an IFC file
"""

# INPUTS
ifcFilePath = r'C:\Temp\PCE_JACKET_IFC4_ComInfo.ifc'
sesamFilePath = r'C:\Temp\2022.05.19.TRIDENT_PCE1_ULS.xml'
outputTable = r'C:\Temp\ComparingIFCxSesam.xlsx'


# LIBS
import structure.ifcBeam as ifcBeam
from structure.sesammodel import cSesamModel
import pandas as pd

# MAIN
print(f'Reading file {ifcFilePath} ...', flush=True)
ifcBeamList = ifcBeam.ifcBeamList(ifcFilePath)

print(f'Reading Sesam file {sesamFilePath} ...', flush=True)
sesamModel = cSesamModel(sesamFilePath)
print(f'{len(sesamModel._Beams)} beams imported.')

comparingList = [   ]

columns = ['Coincidence level', 
           'Beam A name', 'Beam A Length', 'Beam A EndA', 'Beam A EndB',
           'Beam B name', 'Beam B Length', 'Beam B EndA', 'Beam B EndB', 'Beam B guid', 'Beam B Pset'
           ]

for bA in ifcBeamList:
    maxC = 0
    for bB in sesamModel._Beams:
        coincidentLevel = bA.CoincidentLevel(bB)        
        if coincidentLevel > maxC:
            maxC = max(maxC, coincidentLevel)
            beamA, beamB = bA, bB
    if maxC>0:
        print(f'Max. coincidence level {maxC:0.3f} calculated between {beamA.name} and {beamB.name}.')
        comparingList.append([maxC, 
                              beamA.name, beamA.length, beamA.EndA, beamA.EndB, beamA.guid, beamA.PropSet,
                              beamB.name, beamB.length, beamB.EndA, beamB.EndB
                              ])

df = pd.DataFrame(comparingList, columns=columns)
df.to_excel(outputTable)

"""

for b in sesamModel._Beams:
    if b.name == 'Bm2416':
        beamB = b
        break

clmax = 0
for b in ifcBeamList:
    cl = b.CoincidentLevel(beamB)
    if clmax < cl:
        beamA = b
        clmax = max(cl,clmax)


#beamA = ifcBeamList.ByGUID("07KLEqOE5F8fgf$OpiNGje")
CoincidenceLevel = beamA.CoincidentLevel(beamB)
print('BeamA name: ', beamA.name)
print('BeamA EndA: ', beamA.EndA)
print('BeamA EndB: ', beamA.EndB)
print('BeamA length: ', beamA.length)
print('BeamB name: ', beamB.name)
print('BeamB EndA: ', beamB.EndA)
print('BeamB EndB: ', beamB.EndB)
print('BeamB length: ', beamB.length)
print('CoincidenceLevel = ', CoincidenceLevel)

"""

"""
import ifcopenshell
ifcFile = ifcopenshell.open(ifcFilePath)
beamIfc = ifcFile.by_id('29lW6Z0ED6nAI1Dg8Iubdb')
beamA = ifcBeam.bimBeam(ifcFile, beamIfc, "Model", "Axis")
print('Name = ', beamA.name)
print('GUID = ', beamA.guid)
print('EndA = ', beamA.EndA)
print('EndB = ', beamA.EndB)
#print('Transf. Matrix: ', beamA.TransfMatrix)


"""