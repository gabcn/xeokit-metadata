# ========== LIBS =========== #
import xml.etree.ElementTree as ET
from structure.conceptmodel import classSegProps, classBeamList, classBeam, classEnvironment, classOptions, classConceptModel
from structure.sesam.sections import classSectionList


# ======== IMPORT PROCEDURES ========== #
def __ImportBeam(xml_structure: ET.Element, BeamList: classBeamList) -> classBeam:
    name = xml_structure.get('name')
    segments = xml_structure.find('segments')
    IniPos, _ = _GetCoordsABfromSeg(segments[0])
    newbeam = BeamList.AddBeam(name, IniPos)
    return newbeam

def __GetStraightSegments(xml_structure: ET.Element, 
                          sections: classSectionList,  
                          beam: classBeam, 
                          env: classEnvironment,
                          conceptModel: classConceptModel
                          ):
    segments = xml_structure.find('segments')
    nseg = 0
    for seg in segments:
        nseg += 1
        if seg.tag != 'straight_segment':
            conceptModel._Message(f'Warning! Segments which are not straight ({seg.tag}) are not supported in this version of the converter.')
            #print(f'Warning! Segments which are not straight ({seg.tag}) are not supported in this version of the converter.')
        else:
            __ProcStraightSeg(seg, sections, beam, env, conceptModel)    


def __ProcStraightSeg(segment: ET.Element, 
                      sections: classSectionList, 
                      beam: classBeam, 
                      env: classEnvironment,
                      conceptModel: classConceptModel,
                      ):
    section = segment.get('section_ref')
    material = segment.get('material_ref')
    hydrocoeffs = segment.get('morison_coefficient_ref')
    airdragcoeffs = segment.get('air_drag_coefficient_ref')
    if section not in sections.SectionNames():
        conceptModel._Message(f'Warning! A segment of the structure {beam.name} is defined ' +\
              f'with the section {section}, which could not be imported.')
        #print(f'Warning! A segment of the structure {beam.name} is defined ' +\
        #      f'with the section {section}, which could not be imported.')
    else:
        EndA, EndB = _GetCoordsABfromSeg(segment)
        if (EndA[0], EndA[1], EndA[2]) != (beam.LastPos[0], beam.LastPos[1], beam.LastPos[2]):
            #print(f'Warning! Discontinuities between segments will be disregarded.')
            conceptModel._Message(
                f'Warning! Discontinuities between segments will be disregarded. ' + \
                '\nEnd position of the previous segment: ' + \
                f'{beam.LastPos[0]}, {beam.LastPos[1]}, {beam.LastPos[2]}' + \
                '\nStart position of the current segment: ' + \
                f'{EndA[0]}, {EndA[1]}, {EndA[2]}'                
            )

        if (EndA[2]+EndB[2]) > env.WaterSurfaceZ + env.MaxWaveHeight:
            selectedhydrocoeffs = airdragcoeffs
        else:
            selectedhydrocoeffs = hydrocoeffs
        sectionPntr = sections.Find(section)
        segprops = classSegProps(section, material, selectedhydrocoeffs, sectionPointer=sectionPntr)
        beam.AddSegmentByEnd(EndB, segprops)

def __GetCurveLocalSys(beam: classBeam,
                       xml_structure: ET.Element):                       
    xml_curve_orientation = xml_structure.find('curve_orientation')
    custom_curve_orient = xml_curve_orientation.find('customizable_curve_orientation')
    orientation = custom_curve_orient.find('orientation')
    lsys = orientation.find('local_system')
    xvec, yvec, zvec = \
        lsys .find('xvector'), lsys .find('yvector'), lsys.find('zvector')   
    # matrix with rotation and translation
    M, row = [], []
    for dir in ['x', 'y', 'z']:
        row.clear()
        for ivec in [xvec, yvec, zvec]: row.append(ivec.get(dir))
        row.append(0) # translation
        M.append(row.copy())
    beam.locToGlobTransfMtx = M.copy()
    

def ImportStraightBeam(BeamList: classBeamList, 
                       xml_structure: ET.Element, 
                       sections: classSectionList, 
                       env: classEnvironment,
                       selections: classOptions,
                       conceptModel: classConceptModel
                       ) -> bool:
    beam = __ImportBeam(xml_structure, BeamList)
    __GetStraightSegments(xml_structure, sections, beam, env, conceptModel)   

    if beam.Nsegs == 0:
        conceptModel._Message(f'Warning! The structure {beam.name} has no segments and will be ignored.')
        BeamList.RemoveBeam(beam)
    else:
        if beam.length < selections.MinLength:
            conceptModel._Message(f'Exclusion: structure {beam.name} length ({beam.length:0.4f}m) smaller '+\
                  'than the minimum value selected.')
            BeamList.RemoveBeam(beam)  

        elif not selections.IsWithinLimits(beam.MeanCoords()):
            conceptModel._Message(f'Exclusion: the structure {beam.name} coordinates ({beam.MeanCoords()}m) is not '+\
                  'within the limiting values selected.')
            BeamList.RemoveBeam(beam)  
        else:
            beam.Description = beam.SegmentList[0].properties.section # sets the beam description as the section name of the fisrt segment
            for seg in beam.SegmentList:
                if len(selections.ExcludeSections) > 0:
                    if seg.properties.section in selections.ExcludeSections:
                        conceptModel._Message(f'Exclusion: beam {beam.name} has a segment whose '+ \
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