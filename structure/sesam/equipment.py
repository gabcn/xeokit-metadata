# ========== LIBS =========== #
from pyclbr import Function
import xml.etree.ElementTree as ET
from structure.conceptmodel import classConceptModel, classEquipList, classEquipment
from dataclasses import dataclass

@dataclass
class cSesamEquip:
    name: str
    mass: float
    dimensions: list[float]
    cog: list[float]
    footprint: list[float]

class cSesamEqpList(list[cSesamEquip]):
    def Find(self, name: str) -> cSesamEquip:
        found = None
        for eqp in self:
            if eqp.name == name:
                found = eqp
                break
        return found
    

def ImportEquipmentsFromSesamm(conceptModel: classConceptModel, xml_model: ET.Element) -> bool:
    sesamEqpList = __ImportEquips(xml_model, conceptModel._Message)
    if len(sesamEqpList) > 0:
        xml_analysis = xml_model.find('analysis_domain').find('analyses')
        xml_loads = xml_analysis.find('global').find('loads')
        xml_eqpsLoads = xml_loads.find('equipment_loads')
        if xml_eqpsLoads != None:
            if len(xml_eqpsLoads) > 0:
                for xml_item in xml_eqpsLoads:
                    if xml_item.tag != 'placed_shape':
                        conceptModel._Message(f'Warning! Equip. load type {xml_item.tag} no supported.')
                    else:
                        newEqp = __ImportEqpLoad(conceptModel, sesamEqpList, xml_item)
                        conceptModel.EquipmentList.append(newEqp)
                            
    
def __ImportEqpLoad(conceptModel: classConceptModel, sesamEqpList: cSesamEqpList, xml_eqpLoad: ET.Element) -> classEquipment:
    loadCase = xml_eqpLoad.get('loadcase_ref')
    equipName = xml_eqpLoad.get('equipment_ref')
    if loadCase in conceptModel.Selections.ExcludedEquipsLoadCases:
        conceptModel._Message(f'Warning! The equip. {equipName} found in load {loadCase} will not be imported '+\
                               '(excluded list).')
        return None
    else:
        origin = __getXmlItemXYZ(xml_eqpLoad, 'origo')
        xml_localSys = xml_eqpLoad.find('local_system')
        for xml_vec in xml_localSys:
            dirI = xml_vec.get('dir')
            if  dirI == 'x': dirX = __getXmlXYZ(xml_vec)
            elif dirI == 'y': dirY = __getXmlXYZ(xml_vec)
            elif dirI == 'z': dirZ = __getXmlXYZ(xml_vec)
            else: 
                conceptModel._Message(f'Warning! Direction {dirI} not supported.')
                return None
        sesamEqp = sesamEqpList.Find(equipName)
        if not sesamEqp:
            raise Exception(f'Error! The load case {loadCase} specifies the equip. {equipName}, '+\
                'which was not found in the equip. list of the .xml file.')
        else:
            newEqp = classEquipment(equipName)
            newEqp.CoG = sesamEqp.cog
            newEqp.dimensions = sesamEqp.dimensions
            newEqp.footprint = sesamEqp.footprint
            newEqp.LoadCase = loadCase
            newEqp.mass = sesamEqp.mass
            newEqp.origin = origin
            newEqp.OrientationMatrix = [
                [dirX[0],dirY[0],dirZ[0]],
                [dirX[1],dirY[1],dirZ[1]],
                [dirX[2],dirY[2],dirZ[2]]
            ]
            return newEqp





def __ImportEquips(xml_model: ET.Element, funcErrorMsg: Function) -> cSesamEqpList:
    resultList = cSesamEqpList()
    xml_eqpDomain = xml_model.find('equipment_domain')
    if xml_eqpDomain == None:
        return None
    else:
        for xml_eqpList in xml_eqpDomain:
            if xml_eqpList.tag != 'equipment_concepts':
                funcErrorMsg(f'Warning! Equipment list type {xml_eqpList.tag} not supported.')
            else:
                xml_eqps = xml_eqpList[0]
                if xml_eqps.tag != 'equipments':
                    funcErrorMsg(f'Warning! Equipment list type {xml_eqps.tag} not supported.')
                    return None
                else:
                    for xml_item in xml_eqps:
                        if xml_item.tag != 'prism_shape':
                            funcErrorMsg(f'Warning! Equipment concept type {xml_item.tag} not supported.')
                        else:
                            newEqp = __ImportEqp(xml_item, funcErrorMsg)
                            resultList.append(newEqp)

    return resultList

def __ImportEqp(xml_eqp: ET.Element, funcErrorMsg: Function) -> cSesamEquip:
    xml_footprint = xml_eqp.find('footprint')
    if xml_footprint[0].tag != 'polygon':
        funcErrorMsg(f'Warning! Footprint type {xml_footprint[0].tag} not supported')
        return None
    else:
        dim = __getXmlItemXYZ(xml_eqp, 'dimensions')
        cog = __getXmlItemXYZ(xml_eqp, 'cog')
        polygon = __getXmlItemXYZ(xml_footprint, 'polygon', ['x1', 'y1', 'x2', 'y2'])
        name = xml_eqp.get('name')
        mass = __strToFloat(xml_eqp.get('mass'))

        return cSesamEquip(name, mass, dim, cog, polygon)

def __getXmlItemXYZ(xml: ET.Element, tag: str, attrs: list[str] = ['x', 'y', 'z']) -> list[float]:
    xml_item = xml.find(tag)
    return __getXmlXYZ(xml_item, attrs)

def __getXmlXYZ(xml: ET.Element, attrs: list[str] = ['x', 'y', 'z']) -> list[float]:
    list_str = []
    for attr in attrs: list_str.append(xml.get(attr))
    return __StrListToFloat(list_str)

def __StrListToFloat(strList: list[str]) -> list[float]:
    result = []
    for str in strList: result.append(__strToFloat(str))
    return result.copy()

def __strToFloat(str: str) -> float:
    try:
        result = float(str)
    except:
        raise Exception('Error converting string to float!')
    else:
        return result
    