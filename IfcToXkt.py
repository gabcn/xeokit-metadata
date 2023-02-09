"""
Script para conversão de arquivo .ifc para .xkt
Requer Node.js (https://nodejs.org/en/download/)
"""

# INPUTS
ifcFile = r'..\..\PCE_JACKET.ifc'
ifcConvPath = r'dependencies\compiled\IfcConvert.exe'
colladaPath = r'dependencies\compiled\COLLADA2GLTF-bin.exe'
xeometaPath = r'dependencies\compiled\xeokit-metadata.exe'
tempDir = r'C:\Temp\dependencies'

# LIBS
import os
import shutil

# CONSTANTS
daeFile = ifcFile.replace('.ifc', '.dae')
gltfFile = ifcFile.replace('.ifc', '.gltf') 
jsonFile = ifcFile.replace('.ifc', '.json')
xktFile = ifcFile.replace('.ifc', '.xkt')


print('\n\nConverting from .ifc to .dae (COLLADA)')
cmdline = f'"{ifcConvPath}" --use-element-guids {ifcFile} {daeFile} --exclude=entities IfcOpeningElement'
os.system(cmdline)

print('\n\nConverting from .dae (COLLADA) to .gltf (GL transmission format)')
cmdline = rf'"{colladaPath}" --materialsCommon' + \
          f' -i {daeFile} -o {gltfFile}'
os.system(cmdline)

print('\n\nConverting from .ifc to .json (metadata)')
cmdline = fr'"{xeometaPath}" {ifcFile} {jsonFile}'
os.system(cmdline)

'''
print('\n\nConverting from .gltf () and .json (metadata) to .xkt')
cmdline =  r'"D:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Microsoft\VisualStudio\NodeJs\win-x64\node.exe"' + \
        r' xeokit-convert-main\convert2xkt.js' + \
        f' -s {gltfFile} -m {jsonFile} -o {xktFile} -l'

'''

# install the required package
print('\n\nInstalling xeokit-convert package')
cmdline = 'npm i @xeokit/xeokit-convert'
os.system(cmdline)

# convert .gltf and .json to .xkt
cmdline =  r'node.exe convert2xkt.js -s {gltfFile} -m {jsonFile} -o {xktFile} -l'
os.system(cmdline)

# delete the installed package
shutil.rmtree('node_modules')


