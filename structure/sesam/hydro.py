# ========== LIBS =========== #
import xml.etree.ElementTree as ET
from structure.conceptmodel import classMorisonCoeffs, classDirections, classHPropsList, classMorCoeffPoint

# ======= CONSTANTS ========= #


# ======== METHODS ========== #   
def __ImportConstDrag(coeffs: ET.Element) -> classMorisonCoeffs:
    name = coeffs.get('name')
    cd = classDirections()
    try:
        # TODO: include local reference system
        cd.z, cd.x, cd.y = float(coeffs[0].get('c_dx')), float(coeffs[0].get('c_dy')), float(coeffs[0].get('c_dz'))   
    except:
        print('Error trying to obtain drag coefficients from the xml file!')
    else:
        return classMorisonCoeffs(name, cd)

def __ImpMorisonCoefs(coeffs: ET.Element, hpropitem: classMorisonCoeffs) -> None:
    cm, ca = classDirections(), classDirections()
    try:
        cm.z, cm.x, cm.y = float(coeffs[0].get('c_mx')), float(coeffs[0].get('c_my')), float(coeffs[0].get('c_mz'))   
    except:
        print('Error trying to obtain Morison coefficients from the xml file!')
    else:
        ca.x, ca.y, ca.z = max(0,cm.x-1), max(0,cm.y-1), max(0,cm.z-1) # TODO: revise ca (added mass coeff.) calculation according to Sesam (marine growth)
        # TODO: revise ca (added mass coeff.) calculation according to Sesam (marine growth)
        hpropitem.cm, hpropitem.ca = cm, ca

def __ImpMorisonCoefsByD(coeffs: ET.Element) -> classMorisonCoeffs:
    name = coeffs.get('name')
    if coeffs[0][0].tag != 'morison_coefficients_curve':
        raise Exception(f'Hydrod. coeff. by diameter data type {coeffs[0][0].tag} not supported.')
    else:
        newitem = classMorisonCoeffs(name)
        for pnt in coeffs[0][0]:
            _D, _cd, _cm, _cd_nf, _cm_nf = pnt.get('diameter'), pnt.get('c_d'), \
                pnt.get('c_m'), pnt.get('c_d_nf'), pnt.get('c_m_nf')
            try:
                D, cd, cm, cd_nf, cm_nf = float(_D), float(_cd), float(_cm), float(_cd_nf), float(_cm_nf)
            except:
                print('Error trying to obtain hydrodynamic coefficients from the xml file!')
            pnt = classMorCoeffPoint(D, cd, cm, cd_nf, cm_nf)
            newitem.points.append(pnt)    
    return newitem

def __ImpHydroProps(coeffs: ET.Element, hproplist: classHPropsList):
    name = coeffs.get('name')
    type = coeffs[0].tag
    if type == 'constant_air_drag_coefficient':
        newitem = __ImportConstDrag(coeffs)
    elif type == 'constant_morison_coefficients':
        newitem = __ImportConstDrag(coeffs)
        __ImpMorisonCoefs(coeffs, newitem)
    elif type == 'morison_coefficients_by_diameter': 
        newitem = __ImpMorisonCoefsByD(coeffs)
    else: 
        raise Exception(f'Hydrodynamic coefficient type {type} not recognized by the current converter version.')

    hproplist.append(newitem)

def __ImportAllHydroCoeffs(morisoncoeffs: ET.Element, hproplist: classHPropsList):
    for coeffs in morisoncoeffs:
        __ImpHydroProps(coeffs, hproplist)


def ImportHydroPropsFromSesam(xml_model: ET.Element, hproplist: classHPropsList):
    """
    Import Hydrodynamic properties from a Sesam model
    * xml_model: Sesam model in xml element object
    """
    structure_domain = xml_model.find('structure_domain')
    props = structure_domain.find('properties')
    hydroprops = props.find('hydro_properties')
    for hprop in hydroprops:
        if hprop.tag == 'morison_coefficients' or \
           hprop.tag == 'air_drag_coefficients':
            __ImportAllHydroCoeffs(hprop, hproplist)
        else:
            print(f'Warning! The hydrodynamic property type {hprop.tag} '
                    +'is not supported by the current version and will be skipped.')