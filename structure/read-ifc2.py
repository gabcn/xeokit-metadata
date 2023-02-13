file = r'C:\Temp\PCE_JACKET_IFC4.ifc'
#file = r'C:\Temp\PCE_JACKET_IFC2x3.ifc'
#file = r'C:\Temp\GitHub\example.ifc'

import ifcopenshell

import ifcopenshell.api
import ifcopenshell.util.element as ifcelem
import ifcopenshell.util.placement
import ifcopenshell.util.representation as ifcrep
import ifcopenshell.geom as ifcgeom
import ifcopenshell.util.attribute as ifcattr





print(f'Reading file {file} ...', flush=True)
model = ifcopenshell.open(file)

#beams = model.by_type('IfcBeam')

#print(f'Listing beams ...')

beam = model.by_guid('29lW6Z0ED6nAI1Dg8Iubdd')
print('Beam: ', beam)



psets = ifcopenshell.util.element.get_psets(beam)
#print(psets)

objplacement = beam.ObjectPlacement

matrix = ifcopenshell.util.placement.get_local_placement(objplacement)
print('Matrix: ', matrix)


context = ifcrep.get_context(model, "Model", "Axis")
settings = ifcgeom.settings()
settings.set(settings.DISABLE_TRIANGULATION, True)
settings.set(settings.USE_BREP_DATA, True)
settings.set_context_ids([context.id()])
#settings.set(settings.USE_PYTHON_OPENCASCADE, True)
shape = ifcgeom.create_shape(settings, beam)
print(shape)
#print(shape.geometry.verts)

print(shape.geometry.brep_data)
print(type(shape.geometry.brep_data))
#geometry = shape.geometry # see #1124
## These are methods of the TopoDS_Shape class from pythonOCC
#shape_gpXYZ = geometry.Location().Transformation().TranslationPart()
## These are methods of the gpXYZ class from pythonOCC
#print(shape_gpXYZ.X(), shape_gpXYZ.Y(), shape_gpXYZ.Z())

#ifcgeom.create_shape()