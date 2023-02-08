# REQUIREMENTS:

* IfcOpenShell:
    - Git
    - CMake (3.1.3 or newer)
    - IfcOpenShell depends on:
        - Boost (http://www.boost.org/)
        - OpenCascade - for building IfcGeom For converting IFC representation items into BRep solids and tessellated meshes
            (https://dev.opencascade.org/)
        - (Optional) OpenCOLLADA - for IfcConvert to be able to write tessellated Collada (.dae) files 
            (https://github.com/khronosGroup/OpenCOLLADA/)
        - (Optional) SWIG and Python - for building the IfcOpenShell Python interface and use in the BlenderBIM Add-on
            (http://www.swig.org/)
        - (Optional) HDF5 - for caching geometry using the HDF5 format
            (https://www.hdfgroup.org/solutions/hdf5)