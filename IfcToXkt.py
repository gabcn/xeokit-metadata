"""
Script para conversão de arquivo .ifc para .xkt
Requer:
        * Node.js (https://nodejs.org/en/download/)
        * .NET 7.0 Runtime (https://dotnet.microsoft.com/pt-br/download/dotnet/thank-you/runtime-7.0.2-windows-x64-installer?cid=getdotnetcore)
"""

# INPUTS
ifcFile = r'..\PCE_JACKET.ifc'
ifcConvPath = r'dependencies\compiled\IfcConvert.exe'
colladaPath = r'dependencies\compiled\COLLADA2GLTF-bin.exe'
xeometaPath = r'dependencies\compiled\xeokit-metadata\xeokit-metadata.exe'
tempDir = r'C:\Temp\dependencies'

# LIBS
import os

# CONSTANTS
daeFile = ifcFile.replace('.ifc', '.dae')
gltfFile = ifcFile.replace('.ifc', '.gltf') 
jsonFile = ifcFile.replace('.ifc', '.json')
xktFile = ifcFile.replace('.ifc', '.xkt')

# FUNCTION
def checkfile(file: str) -> bool:
        if not os.path.isfile(file):
                print(f'ERROR! File {file} not created.')
                return False
        else:
                return True

print('\n\nConverting from .ifc to .dae (COLLADA)')
cmdline = f'"{ifcConvPath}" --use-element-guids {ifcFile} {daeFile} --exclude=entities IfcOpeningElement'
os.system(cmdline)
if not checkfile(daeFile): exit()

print('\n\nConverting from .dae (COLLADA) to .gltf (GL transmission format)')
cmdline = rf'"{colladaPath}" --materialsCommon' + \
          f' -i {daeFile} -o {gltfFile}'
os.system(cmdline)
if not checkfile(gltfFile): exit()

print('\n\nConverting from .ifc to .json (metadata)')
cmdline = fr'"{xeometaPath}" {ifcFile} {jsonFile}'
os.system(cmdline)
if not checkfile(jsonFile): exit()

# install the required package
print('\n\nInstalling xeokit-convert package')
cmdline = 'npm i @xeokit/xeokit-convert'
os.system(cmdline)

# convert .gltf and .json to .xkt
print('\n\nConverting from .gltf () and .json (metadata) to .xkt')
cmdline =  fr'node.exe conv-gltf-and-json-to-xkt.js {gltfFile} {jsonFile} {xktFile} -l'
os.system(cmdline)
checkfile(xktFile)

# node.exe conv-gltf-and-json-to-xkt.js -s ..\PCE_JACKET.gltf -m ..\PCE_JACKET.json -o ..\PCE_JACKET.xkt -l

# delete the installed package
print('\n\nUnistalling the package')
cmdline = 'npm uninstall @xeokit/xeokit-convert'
os.system(cmdline)


