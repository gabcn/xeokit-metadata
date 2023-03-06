"""
Class to convert .ifc file to .xkt (xeo-bim-viewer)
Requires:
        * Node.js (https://nodejs.org/en/download/)
        * .NET 7.0 Runtime (https://dotnet.microsoft.com/pt-br/download/dotnet/thank-you/runtime-7.0.2-windows-x64-installer?cid=getdotnetcore)
"""

# CONSTANTS
ifcConvPath = r'dependencies\compiled\IfcConvert.exe'
colladaPath = r'dependencies\compiled\COLLADA2GLTF-bin.exe'
xeometaPath = r'dependencies\compiled\xeokit-metadata\xeokit-metadata.exe'
tempDir = r'C:\Temp\dependencies'

# LIBS
import os

# FUNCTION
class ConvIfcToXkt:
        """Conversion from .IFC file to .XKT"""
        def __init__(self, ifcFile: str, output: str = None) -> None:
                self.ifcFile = ifcFile
                self.daeFile = ifcFile.replace('.ifc', '.dae')
                self.gltfFile = ifcFile.replace('.ifc', '.gltf') 
                self.jsonFile = ifcFile.replace('.ifc', '.json')
                if output: self.xktFile = output
                else: self.xktFile = ifcFile.replace('.ifc', '.xkt')
                
                if self.__convIfcToXkt():
                        print('Successfull file conversion .')
                else:
                        print('Erro converting file.')

        def __checkfile(self, file: str, errorMsg: bool = True) -> bool:
                if not os.path.isfile(file):
                        if errorMsg: print(f'ERROR! File {file} not created.')
                        return False
                else:
                        return True

        def __convIfcToDae(self) -> bool:
                print('\n\n==== Converting from .ifc to .dae (COLLADA) ====')
                if self.__checkfile(self.daeFile): os.remove(self.daeFile)                        
                cmdline = f'"{ifcConvPath}" --use-element-guids '+\
                          f'{self.ifcFile} {self.daeFile} --exclude=entities IfcOpeningElement'
                os.system(cmdline)
                if self.__checkfile(self.daeFile):
                        return True
                else:
                        raise Exception(f'Error!')
                
        def __convDaeToGltf(self) -> bool:
                print('\n\n==== Converting from .dae (COLLADA) to .gltf (GL transmission format) ====')
                cmdline = rf'"{colladaPath}" --materialsCommon' + \
                        f' -i {self.daeFile} -o {self.gltfFile}'
                os.system(cmdline)
                os.remove(self.daeFile)  # erase file
                if self.__checkfile(self.gltfFile): 
                        return True
                else:
                        raise Exception(f'Error!')

        def __convIfcToJson(self) -> bool:
                print('\n\n==== Converting from .ifc to .json (metadata) ====')
                cmdline = fr'"{xeometaPath}" {self.ifcFile} {self.jsonFile}'
                os.system(cmdline)
                if self.__checkfile(self.jsonFile):
                        return True
                else:
                        raise Exception(f'Error!')

        def __installXeoKit(self):
                """install the required package"""
                print('\n\nInstalling xeokit-convert package')
                cmdline = 'npm i @xeokit/xeokit-convert'
                os.system(cmdline)

        def __convGltfJsonToXkt(self) -> bool:
                # convert .gltf and .json to .xkt
                print('\n\n==== Converting from .gltf () and .json (metadata) to .xkt ====')
                cmdline =  'node.exe conv-gltf-and-json-to-xkt.js '+\
                           f'{self.gltfFile} {self.jsonFile} {self.xktFile} -l'
                os.system(cmdline)
                os.remove(self.gltfFile) # erase file
                #os.remove(self.jsonFile) # erase file
                return self.__checkfile(self.xktFile)

        def __uninstallXeoKit(self):
                # delete the installed package
                print('\n\nUnistalling the package')
                cmdline = 'npm uninstall @xeokit/xeokit-convert'
                os.system(cmdline)

        def __convIfcToXkt(self) -> bool:
                self.__convIfcToDae()
                self.__convDaeToGltf()
                self.__convIfcToJson()
                self.__installXeoKit()
                ok = self.__convGltfJsonToXkt()
                self.__uninstallXeoKit()
                return ok





