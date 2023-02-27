# ========== LIBS =========== #
import xml.etree.ElementTree as ET
from structure.conceptmodel import classSetList


# ======== PROCEDURES ========== #
def ImportSets(xml_structDomain: ET.Element, SetList: classSetList, ExcludedSets: list[str]) -> bool:
    xml_sets = xml_structDomain.find('sets')
    if len(xml_sets) > 0:
        for xml_set in xml_sets:
            if len(xml_set) > 0:
                xml_concepts = xml_set.find('concepts')                
                name = xml_set.get('name')                
                if (not name in ExcludedSets) and (len(xml_concepts) > 0):
                    newset = SetList.Add(name)
                    for xml_item in xml_concepts:
                        newset.append(xml_item.get('concept_ref'))