
# LIBS
from structure.conceptmodel import *
from structure.sesam.units import classSesamUnits
from structure.sesam.materials import ImportMaterialsFromSesam
from structure.sesam.sections import ImporSectionstFromSesam
from structure.sesam.hydro import ImportHydroPropsFromSesam
from structure.sesam.beams import ImportStraightBeam
from structure.sesam.supports import ImportSupport
import xml.etree.ElementTree as ET

class cSesamModel(classConceptModel):
    def __init__(self, xmlFile: str) -> None:
        """
        Import Sesam concept model
        * xmlFile: input .xml file path
        """
        super().__init__()
        self.ImportFromSesamConceptModel(xmlFile)

    def _OpenXmlFile(self, xmlfile: str) -> ET.Element:        
        tree = ET.parse(xmlfile)
        root = tree.getroot()
        xml_model = root.find('model')  
        return xml_model     

    def ImportFromSesamConceptModel(self, xmlfile: str) -> None:
        """
        Import model from Sesam to OrcaFlex
        * self: class containing pointer to OrcaFlex model in self.orcmodel
        * xmlfile: file path to .xml file of the Sesam model
        """    

        # TODO: Handle units (assuming, for now, S.I.)

        xml_model = self._OpenXmlFile(xmlfile)

        self.Units = classSesamUnits(xml_model)
        ImportMaterialsFromSesam(self._MaterialList, xml_model, self.Units)
        ImporSectionstFromSesam(xml_model, self._SectionList)
        ImportHydroPropsFromSesam(xml_model, self._HydroProps)

        structure_domain = xml_model.find('structure_domain')
        structures = structure_domain.find('structures')   
        self._ImportStructures(structures, self.Selections)        
        #self._Beams.DetectIntersections()        
        #self._Connections.print()

    def _ImportStructures(self, xml_structures: ET.Element, selections: classOptions):
        for child in xml_structures:
            for structure in child:
                if structure.tag == 'straight_beam':                    
                    ImportStraightBeam(self._Beams, structure, self._SectionList, self.Environment, selections)                    
                elif structure.tag == 'support_point':
                    ImportSupport(self.Supports, structure)
                else:
                    name = structure.get('name')
                    self._Message(f'Warning! The structure "{name}" type is "{structure.tag}", which is not supported '
                          +'by the current version of the converter and will be skipped.')           