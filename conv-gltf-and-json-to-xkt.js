// Install xeokit-convert:
// npm i @xeokit/xeokit-convert

// usage:
// >> node conv-gltf-and-json-to-xkt.js <input.gltf> <input.json> 

// INPUTS
const gltfFile = process.argv[2]; //"../PCE_JACKET.gltf";
const jsonFile = process.argv[3]; // = "../PCE_JACKET.json";
const outxktFile = gltfFile.replace('.gltf','.xkt'); // "../PCE_JACKET_.xkt";

// LIBS
const convert2xkt = require("@xeokit/xeokit-convert/dist/convert2xkt.cjs.js");

// IMPLEMENTATION
convert2xkt.convert2xkt({
    source: gltfFile,
    metaModelSource: jsonFile,
    output: outxktFile,
    log: (msg) => {
        console.log(msg)
    }
}).then(() => {
    console.log("Converted.");
}, (errMsg) => {
    console.error("Conversion failed: " + errMsg)
}); 