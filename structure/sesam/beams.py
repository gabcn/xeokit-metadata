# ========== LIBS =========== #
import xml.etree.ElementTree as ET
from structure.conceptmodel import classSegProps, classBeamList, classBeam, classEnvironment, classOptions
from structure.sesam.sections import classSectionList


# ======== IMPORT PROCEDURES ========== #
def __ImportBeam(xml_structure: ET.Element, BeamList: classBeamList) -> classBeam:
    name = xml_structure.get('name')
    segments = xml_structure.find('segments')
    IniPos, _ = _GetCoordsABfromSeg(segments[0])
    newbeam = BeamList.AddBeam(name, IniPos)
    return newbeam

def __GetStraightSegments(xml_structure: ET.Element, sections: classSectionList,  beam: classBeam, env: classEnvironment):          
    segments = xml_structure.find('segments')
    nseg = 0
    for seg in segments:
        nseg += 1
        if seg.tag != 'straight_segment':
            print(f'Warning! Segments which are not straight ({seg.tag}) are not supported in this version of the converter.')
        else:
            __ProcStraightSeg(seg, sections, beam, env)    


def __ProcStraightSeg(segment: ET.Element, sections: classSectionList, beam: classBeam, env: classEnvironment):
    section = segment.get('section_ref')
    material = segment.get('material_ref')
    hydrocoeffs = segment.get('morison_coefficient_ref')
    airdragcoeffs = segment.get('air_drag_coefficient_ref')
    if section not in sections.SectionNames():
        print(f'Warning! A segment of the structure {beam.name} is defined with the section {section}, which could not be imported.')
    else:
        EndA, EndB = _GetCoordsABfromSeg(segment)
        if (EndA[0], EndA[1], EndA[2]) != (beam.LastPos[0], beam.LastPos[1], beam.LastPos[2]):
            print(f'Warning! Discontinuities between segments will be disregarded.')

        if (EndA[2]+EndB[2]) > env.WaterSurfaceZ + env.MaxWaveHeight:
            selectedhydrocoeffs = airdragcoeffs
        else:
            selectedhydrocoeffs = hydrocoeffs
        segprops = classSegProps(section, material, selectedhydrocoeffs)
        beam.AddSegmentByEnd(EndB, segprops)


def ImportStraightBeam(BeamList: classBeamList, 
                       xml_structure: ET.Element, 
                       sections: classSectionList, 
                       env: classEnvironment,
                       selections: classOptions,
                       ) -> bool:
    beam = __ImportBeam(xml_structure, BeamList)
    __GetStraightSegments(xml_structure, sections, beam, env)   

    if beam.Nsegs == 0:
        print(f'Warning! The structure {beam.name} has no segments and will be ignored.')
        BeamList.RemoveBeam(beam)
    else:
        if beam.length < selections.MinLength:
            print(f'Exclusion: structure {beam.name} length ({beam.length:0.4f}m) smaller '+\
                  'than the minimum value selected.')
            BeamList.RemoveBeam(beam)  

        elif not selections.IsWithinLimits(beam.MeanCoords()):
            print(f'Exclusion: the structure {beam.name} coordinates ({beam.MeanCoords()}m) is not '+\
                  'within the limiting values selected.')
            BeamList.RemoveBeam(beam)  
        else:
            for seg in beam.SegmentList:
                if len(selections.ExcludeSections) > 0:
                    if seg.properties.section in selections.ExcludeSections:
                        print(f'Exclusion: beam {beam.name} has a segment whose '+ \
                            f'section was defined as excluded {seg.properties.section}.')
                        BeamList.RemoveBeam(beam)
                        break
            




# === XML HANDLING AUXILIARY FUNCTIONS ==== #            
def __GetXYZfromXmlElement(XMLelement: ET.Element):
    Point, xis = [], ['x', 'y', 'z']
    for xi in xis: Point.append(float(XMLelement.get(xi))) 
    return Point.copy()    

def __GetCoordsABfromGuide(guide: ET.Element):
    EndA = __GetXYZfromXmlElement(guide[0])
    EndB = __GetXYZfromXmlElement(guide[1])
    return EndA, EndB

def _GetCoordsABfromSeg(segment: ET.Element):
    geo = segment.find('geometry')
    wire = geo.find('wire')
    guide = wire.find('guide')
    return __GetCoordsABfromGuide(guide)