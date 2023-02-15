import ifcopenshell as ifc


ifcFile = ifc.file(schema='IFC4')

beam = ifcFile.createIfcWall()

ifcFile.write('test.ifc')



