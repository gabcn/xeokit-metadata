"""
Get the ID's and names from the IFC file and 
combine with the UC and Damage (fatigue) 
informations from the csv file into a Excel file
"""

ifcFilePath = '.\\models\\example2.ifc'
csvFile = '.\\models\\example2.csv'
UcFile = '.\\models\\example2_UC.xlsx'

import ifcopenshell
import csv
import pandas as pd


ifcFile = ifcopenshell.open(ifcFilePath)

ifcBeams = ifcFile.by_type('IfcBeam')

f = open(csvFile, 'w',  newline='', encoding='UTF8')
writer = csv.writer(f)

UCs = pd.read_excel(UcFile)

def getUC(member: str) -> float:
    df = UCs[UCs['Member'] == member]
    if len(df) > 0:        
        return df.iloc[0]['UC']
    else:
        return 'N/A'


def genList():
    for ifcBeam in ifcBeams:
        guid = ifcBeam.get_info()['GlobalId']
        #guid = ifcBeam.id()
        name = ifcBeam.Name
        UCvalue = getUC(name)
        if UCvalue != 'N/A': 
            print(f'Found for element with id {guid}, name {name}: UC = {UCvalue}')
            print(UCvalue)
        row = [guid, name, UCvalue]
        writer.writerow(row)


genList()
f.close()