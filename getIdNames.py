file = '.\\models\\example2.ifc'
csvFile = '.\\models\\example2.csv'
UcFile = '.\\models\\example2_UC.xlsx'

import ifcopenshell
import csv
import pandas as pd


ifcFile = ifcopenshell.open(file)

ifcBeams = ifcFile.by_type('IfcBeam')

f = open(csvFile, 'w',  newline='', encoding='UTF8')
writer = csv.writer(f)


UCs = pd.read_excel(UcFile)

def getUC(member: str) -> float:
    df = UCs[UCs['Member'] == member]
    if len(df) > 0:        
        return df['UC']
    else:
        return None

for ifcBeam in ifcBeams:
    guid = ifcBeam.get_info()['GlobalId']
    name = ifcBeam.Name
    UCvalue = getUC(name)
    if UCvalue != None: 
        print(name)
        print(UCvalue)
    #row = f'{ifcBeam.id},{ifcBeam.Name}'
    #row = [ifcBeam.id,ifcBeam.Name]
    row = [guid, name, UCvalue]
    writer.writerow(row)


