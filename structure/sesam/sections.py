# ========== LIBS =========== #
import xml.etree.ElementTree as ET
from structure.conceptmodel import classPipeSection, classISection, classSectionList, classBoxSection, classConceptModel


# ======== CLASSES ========== #
def ImporSectionstFromSesam(xml_model: ET.Element, seclist: classSectionList, conceptModel: classConceptModel):
    """
    Import sections from a Sesam model to an OrcaFlex model
    * xml_model: Sesam model in xml element object
    * orcmodel: OrcaFlex model (pointer)
    """
    structure_domain = xml_model.find('structure_domain')
    properties = structure_domain.find('properties')
    xml_sections = properties.find('sections')
    __ProcessSections(xml_sections, seclist, conceptModel)


def __ProcessSections(xml_sections: ET.Element, seclist: classSectionList, conceptModel: classConceptModel):
    for section in xml_sections.findall('section'):
        secname = section.get('name')
        SecType = _GetSectionType(section)
        if SecType == 'pipe_section': sectionobj = __ProcPipeSection(section)   
        elif SecType == 'i_section': sectionobj = __ProcISection(section)       
        elif SecType == 'pgd_section': sectionobj = __ProcISection(section)     # double I
        elif SecType == 'bar_section': sectionobj = __ProcBarSection(section)
        elif SecType == 'box_section': sectionobj = __ProcBoxSection(section)
        elif SecType == 'pgb_section': sectionobj = __ProcBoxSection(section)   # double box
        else: conceptModel._Message(f'Warning! The beam section "{secname}" type is "{SecType}", which is not recognized.')   

        props = section[0]
        genpropmethod = props.get('general_properties_method')
        if genpropmethod == 'computed': 
            pass
        elif genpropmethod == 'library' or genpropmethod == 'manual':
            A, Ixx, Iyy, Izz = _GetLibGenSecProps(section)
            #sectionobj.SetGeneralSection(A, Ixx, Iyy, Izz)
            sectionobj.SetGeneralSection(A, Iyy, Izz, Ixx) # sequence changed to be compatible with the OrcaFlex reference
        else:
            conceptModel._Message(f'Warning! general_properties_method = {genpropmethod} not supported') # TODO: include what to in this case

        seclist.Add(sectionobj)

def __ProcPipeSection(section: ET.Element) -> classPipeSection:
    secname = section.get('name')
    props = section[0]
    _od, _th = props.get('od'), props.get('th')
    try:
        od, th = float(_od), float(_th)
    except:
        print('Error converting pipe sections parameters '
            + f'({_od}, {_th})from text to float.')
    else:        
        sectionobj = classPipeSection(secname, od, th)
        return sectionobj
        
def __ProcISection(section: ET.Element):
    secname = section.get('name')
    props = section[0]
    _h, _b, _tw, _tf, ws = props.get('h'), props.get('b'), props.get('tw'), props.get('tf'), props.get('ws')
    _fillet_radius = props.get('fillet_radius', default='0.0')
    try:
        h, b, tw, tf, fillet_radius  = float(_h), float(_b), float(_tw), float(_tf), float(_fillet_radius)
        if ws != None: ws = float(ws)
    except:
        raise Exception(f'Error converting I section "{secname}" parameters from text ' 
                        + f'({_h}, {_b}, {_tw}, {_tf}, {_fillet_radius}, and {ws}) to float.')
    else:        
        sectionobj = classISection(secname, h, b, tw, tf, fillet_radius, ws)

    return sectionobj

def __ProcBarSection(section: ET.Element):
    secname = section.get('name')
    props = section[0]
    _h, _b, _sfy, _sfz = props.get('h'), props.get('b'), props.get('sfy'), props.get('sfz')
    if _sfy != '1' or _sfz != '1': 
        print(f'Warning! Bar section {secname} has sfy <> sfz ({_sfy} and {_sfz}), ' \
               'which is not supported by the current version of the converter.')
    try:
        h, b = float(_h), float(_b)
    except:
        raise Exception('Error converting bar section parameters from text ' 
                        + f'({_h} and {_b}) to float.')
    else:        
        sectionobj = classBoxSection(secname, h, b)

    return sectionobj          

def __ProcBoxSection(section: ET.Element):
    secname = section.get('name')
    p = section[0]
    _h, _b, _tw, tftop, tfbot, _sfy, _sfz, otw = \
        p.get('h'), p.get('b'), p.get('tw'), p.get('tftop'), \
        p.get('tfbot'), p.get('sfy'), p.get('sfz'), p.get('otw')
    if _sfy != '1' or _sfz != '1': 
        print(f'Warning! Bar section {secname} has sfy <> sfz ({_sfy} and {_sfz}), ' \
               'which is not supported by the current version of the converter.')
    try:
        h, b, tw = float(_h), float(_b), float(_tw)
        if tftop != None: tftop, tfbot = float(tftop), float(tfbot)
        if otw != None: otw = float(otw)
    except:
        raise Exception(f'Error converting box section {secname} parameters from text ' 
                        + f'({_h}, {_b}, {_tw}, {tftop}, {tfbot}, {_sfy}, {_sfz}, and {otw}) to float.')
    else:        
        sectionobj = classBoxSection(secname, h, b, tw, tftop, tfbot, otw)

    return sectionobj          

    
# === XML HANDLING AUXILIARY FUNCTIONS ==== #            

def _GetSectionType(section: ET.Element):
    """
    Extract the section type from the XML 'element'
    * section XML 'element' which defines the section
    * returns: string with the section type text
    """
    return section[0].tag

def _GetLibGenSecProps(section: ET.Element):    
    if section[0].get('general_properties_method') == 'manual':
        p = section[0]
    else:
        p = section[0].find('libraryGeneralSection') # 'library'

    _A, _Ixx, _Iyy, _Izz = p.get('area'), p.get('ix'), p.get('iy'), p.get('iz') # TODO: verify if Izz = J ?
    try:
        A, Ixx, Iyy, Izz = float(_A), float(_Ixx), float(_Iyy), float(_Izz)
    except:
        raise Exception('Error converting library properties from text ' 
                        + f'({_A}, {_Ixx}, {_Iyy}, {_Izz}) to float.')
    else:
        return A, Ixx, Iyy, Izz
