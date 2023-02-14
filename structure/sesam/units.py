import xml.etree.ElementTree as ET

class classSesamUnits:
    def __init__(self, xml_model: ET.Element = None) -> None:
        self.UnitsDic = {}
        if xml_model != None:
            self.ImportUnits(xml_model)

    def ImportUnits(self, xml_model: ET.Element):
        units = xml_model.find('units')
        model_units = units.find('model_units')
        for qty in ['length', 'time', 'temp_diff', 'force', 'angle', 'mass']:
            self.UnitsDic[qty] = model_units.get(qty)


        #input_units = units.find('input_units')
        #for input in input_units:
        #    phenomenon = input.get('phenomenon')
        #    unit = input.get('unit')
        #    self.UnitsDic[phenomenon] = unit

    def FactorToSI(self, quantity: str) -> float: # TODO: improve
        """
        Returns the conversion factor from Sesam model input to S.I.
        * quantity: physical quantity (length, time, temp_diff, force, angle, mass, density, pressure)
        """
        if len(self.UnitsDic) == 0: raise Exception('Units not read from model.')

        elif quantity == 'force':            
            unit = self.UnitsDic[quantity]
            if unit != '':
                if unit == 'kN': f = 1000.0 
                elif unit == 'N': f = 1.0
                else: raise Exception('Unit not implemented yet.')        
            else: raise Exception('Unit not implemented yet.')        

        elif quantity == 'length':            
            unit = self.UnitsDic[quantity]
            if unit == 'km': f = 1000.0 
            elif unit == 'm': f = 1.0
            else: raise Exception('Unit not implemented yet.')        

        elif quantity == 'time':
            unit = self.UnitsDic[quantity]
            if unit[0] == 's': f = 1.0
            else: raise Exception('Unit not implemented yet.')        

        elif quantity == 'mass':
            unit = self.UnitsDic[quantity]
            if unit != '': 
                unit = self.UnitsDic[quantity]
                if unit == 'kg': f = 1
                else: raise Exception('Unit not implemented yet.')        
            elif self.UnitsDic['force'] != '': 
                F = self.FactorToSI('force')
                T = self.FactorToSI('time')
                L = self.FactorToSI('length')
                f = F*T**2/L
            else:
                raise Exception('Unit not implemented yet.')

        elif quantity == 'density':
            M = self.FactorToSI('mass')
            L = self.FactorToSI('length')
            f = M/L**3

        elif quantity == 'pressure':
            F = self.FactorToSI('force')
            L = self.FactorToSI('length')
            f = F/L**2

        else: raise Exception('Unit not implemented yet.')        

        return f