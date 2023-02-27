
# LIBS
from structure.conceptmodel import *
from structure.sesam.units import classSesamUnits
from structure.sesam.materials import ImportMaterialsFromSesam
from structure.sesam.sections import ImporSectionstFromSesam
from structure.sesam.hydro import ImportHydroPropsFromSesam
from structure.sesam.beams import ImportStraightBeam
from structure.sesam.supports import ImportSupport
from structure.sesam.sets import ImportSets
import xml.etree.ElementTree as ET

class cSesamModel(classConceptModel):
    def __init__(self, xmlFile: str = None) -> None:
        """
        Import Sesam concept model
        * xmlFile: input .xml file path
        """
        super().__init__()
        if xmlFile:
            self.ImportFromSesamConceptModel(xmlFile)

    def _OpenXmlFile(self, xmlfile: str) -> ET.Element:        
        xml_tree = ET.parse(xmlfile)
        xml_root= xml_tree.getroot()
        return xml_root     

    def ImportFromSesamConceptModel(self, xmlfile: str) -> None:
        """
        Import model from Sesam to OrcaFlex
        * self: class containing pointer to OrcaFlex model in self.orcmodel
        * xmlfile: file path to .xml file of the Sesam model
        """    

        # TODO: Handle units (assuming, for now, S.I.)
        xml_root = self._OpenXmlFile(xmlfile)
        self._ImportAdmInfo(xml_root)

        xml_model = xml_root.find('model')

        self.Units = classSesamUnits(xml_model)
        ImportMaterialsFromSesam(self._MaterialList, xml_model, self.Units)
        ImporSectionstFromSesam(xml_model, self._SectionList, self)
        ImportHydroPropsFromSesam(xml_model, self._HydroProps, self)        

        structure_domain = xml_model.find('structure_domain')
        structures = structure_domain.find('structures')   
        self._ImportStructures(structures, self.Selections)        
        #self._Beams.DetectIntersections()        
        #self._Connections.print()

        ImportSets(structure_domain, self.SetList, self.Selections.ExcludeSets)

    def _ImportAdmInfo(self, xml_root: ET.Element):
        xml_adm = xml_root.find('administrative')
        xml_prog = xml_adm.find('program')
        program = xml_prog.get('program')
        version = xml_prog.get('version')
        xml_session = xml_adm.find('session_info')
        user = xml_session.get('user')
        xml_model = xml_root.find('model')
        modelName = xml_model.get('name')
        date = xml_session.get('date')
        
        self.OriginInfo['Program'] = program
        self.OriginInfo['Version'] = version
        self.OriginInfo['User'] = user
        self.OriginInfo['Model'] = modelName
        self.OriginInfo['Date'] = date

    def _ImportStructures(self, xml_structures: ET.Element, selections: classOptions):
        for child in xml_structures:
            for structure in child:
                if structure.tag == 'straight_beam':                    
                    ImportStraightBeam(self._Beams, 
                        structure, 
                        self._SectionList, 
                        self.Environment, 
                        selections, 
                        self
                        )                    
                elif structure.tag == 'support_point':
                    ImportSupport(self.Supports, structure)
                else:
                    name = structure.get('name')
                    self._Message(f'Warning! The structure "{name}" type is "{structure.tag}", which is not supported '
                          +'by the current version of the converter and will be skipped.')           