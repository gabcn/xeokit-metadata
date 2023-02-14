# ========== LIBS =========== #
import xml.etree.ElementTree as ET
from structure.conceptmodel import MaterialProps, classMatList
from structure.sesam.units import classSesamUnits
#from typing import Tuple

# ======== CLASSES ========== #

    
def ImportMaterialsFromSesam(MaterialList: classMatList, xml_model: ET.Element, Units: classSesamUnits):
    """
    Import materials from a Sesam model
    * xml_model: Sesam model in xml element object
    """
    structure_domain = xml_model.find('structure_domain')
    props = structure_domain.find('properties')
    materials = props.find('materials')
    for xml_material in materials:
        material = _ProcessMaterial(xml_material, Units)
        MaterialList.append(material)
    
def _ProcessMaterial(xml_material: ET.Element, Units: classSesamUnits) -> MaterialProps:
    name  = xml_material.get('name')
    properties = xml_material[0]
    mattype = properties.tag
    if mattype != 'isotropic_linear_material':
        raise Exception(f'Material {name} type is {mattype}, which is not supported by the current version of the converter.')
    else:
        _Sy = properties.get('yield_stress') # TODO: handle the unit defined in the source model
        _rho = properties.get('density')
        _E = properties.get('youngs_modulus')
        _nu = properties.get('poissons_ratio')
        _alfa = properties.get('thermal_expansion')
        _damping =properties.get('damping')  
        try:
            rho, E, nu, Sy, alfa, damping = float(_rho), float(_E), float(_nu), float(_Sy), float(_alfa), float(_damping)
        except:
            raise Exception('Error converting material parameters from text.' )
        else:
            return MaterialProps(name, 
                                 rho * Units.FactorToSI('density'), 
                                 E * Units.FactorToSI('pressure'),
                                 nu, 
                                 Sy * Units.FactorToSI('pressure'), 
                                 alfa, 
                                 damping)