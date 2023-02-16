sesamFilePath = r'C:\Temp\2022.05.19.TRIDENT_PCE1_ULS.xml'
outIfcFilePath = r'C:\Temp\from_sesam.ifc'

import structure.sesammodel as sesam
import ifcopenshell as ifc


def createIfcObjPlace(beam: sesam.classBeam,
                      ifcFile: ifc.file
                      ) -> ifc.entity_instance:
    """
    Creates the IfcObjectPlacement based on the beam information
    * return: entity_instance of the objecte created
    """

    ifcLocPlace = ifcFile.create_entity(type = 'IfcLocalPlacement')
    return ifcLocPlace

    

def exportBeamToIfc(beam: sesam.classBeam,
                    ifcFile: ifc.file
                    ) -> ifc.entity_instance:
    """
    Export beam to Ifc
    * return: entity_instance of the objecte created
    """
    ifcObjPlace = createIfcObjPlace(beam, ifcFile)
    ifcBeam = ifcFile.create_entity(type='IfcBeam',
        GlobalId = ifc.guid.new(),
        Name = beam.name,
        Description = beam.Description
        )

    return ifcBeam



sesamModel = sesam.cSesamModel(sesamFilePath)
sesamBeam = sesamModel._Beams[10]

print(sesamBeam.name)

ifcFile = ifc.file(schema='IFC4')
ifcBeam = exportBeamToIfc(sesamBeam, ifcFile)
ifcFile.write('test.ifc')
