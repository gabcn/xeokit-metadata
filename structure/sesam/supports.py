from pyclbr import Function
from structure.conceptmodel import classSupportList, FixType
import xml.etree.ElementTree as ET

__fixtype = {'dx': FixType.x, 'dy': FixType.y, 'dz': FixType.z, 
             'rx': FixType.Rx, 'ry': FixType.Ry, 'rz': FixType.Rz}

def ImportSupport(SupportList: classSupportList, xml_structure: ET.Element, funcErrorMsg: Function) -> bool:
    name = xml_structure.get('name')
    geometry = xml_structure.find('geometry')
    position = geometry.find('position')
    _x, _y, _z = position.get('x'), position.get('y'), position.get('z')
    try:
        x, y, z = float(_x), float(_y), float(_z)
    except:
        raise Exception(f'Error trying to obtain the coordinates from the support point "{name}".')
    else:
        bcs = xml_structure.find('boundary_conditions')
        fixings = []
        for bc in bcs:
            if bc.tag == 'boundary_condition':
                constraint = bc.get('constraint')
                if constraint != 'fixed':
                    funcErrorMsg(f'Warning! The support point "{name}" has a constraint ("{constraint}")' + \
                           ' not allowed in the current version. It will be considered as fixed.')
                    #print(f'Warning! The support point "{name}" has a constraint ("{constraint}")' + \
                    #       ' not allowed in the current version. It will be considered as fixed.')
                fix = bc.get('dof')
                fixings.append(__fixtype[fix])
            else:
                funcErrorMsg(f'The boundary condition "{bc.tag}" (support point "{name}") is not supported.')
                #print(f'The boundary condition "{bc.tag}" (support point "{name}") is not supported.')
        newsupport = SupportList.Add(name)
        newsupport.position = [x,y,z]
        newsupport.fixings = fixings.copy()
        return True