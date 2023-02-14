"""

Required packages:
    * ifcopenshell: pip install ifcopenshell
"""

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

axisrep = ifcrep.get_representation(beam, "Model", "Axis") #"Model")
print('Representation: ', axisrep)

repItems = axisrep.Items #IfcMapItem
repItem = repItems[0]
print('Representation items: ', repItem)

mapSource = repItem.MappingSource
print('Mapping Source: ', mapSource)

mapTarget = repItem.MappingTarget
print('Mapping Target: ', mapTarget)

mapOrigin = mapSource.MappingOrigin
print('Mapping Origin', mapOrigin)
mapOriginLocation = mapOrigin.Location
print(mapOriginLocation)
x, y, z = mapOriginLocation.Coordinates
mapOriginCoords = [x, y, z]
print(mapOriginCoords)

mapRep = mapSource.MappedRepresentation
print('Mapping Representation: ', mapRep)

RepId = mapRep.RepresentationIdentifier
RepType = mapRep.RepresentationType
RepItems = mapRep.Items
RepItem = RepItems[0]

if RepId != 'Axis': raise Exception('ERROR!')
if RepType != 'Curve3D': raise Exception('ERROR!')

print('Representation item: ', RepItem)