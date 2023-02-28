# ========== LIBS =========== #
from pyclbr import Function
import xml.etree.ElementTree as ET
from structure.conceptmodel import classSetList


# ======== PROCEDURES ========== #
def ImportSets(xml_structDomain: ET.Element, SetList: classSetList, ExcludedSets: list[str], errorMsgFunc: Function) -> bool:
    xml_sets = xml_structDomain.find('sets')
    if len(xml_sets) > 0:
        for xml_set in xml_sets:
            if len(xml_set) > 0:
                for xml_set_group in xml_set:
                    tag = xml_set_group.tag
                    if tag != 'concepts':
                        errorMsgFunc(f'Warning! Set group "{tag}" not supported.')
                    else:
                        name = xml_set.get('name')                
                        if (not name in ExcludedSets) and (len(xml_set_group) > 0):
                            newset = SetList.Add(name)
                            for xml_item in xml_set_group:
                                newset.append(xml_item.get('concept_ref'))