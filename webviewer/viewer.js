//const modelFile = "../models/2023.02.28.FRADE_SRU.ifc";
//const modelFile = "../models/2023.02.28.FRADE_SRU.xkt";
const modelFile = "../models/example2.xkt";

import {Viewer, WebIFCLoaderPlugin, XKTLoaderPlugin, TreeViewPlugin} from
    "https://cdn.jsdelivr.net/npm/@xeokit/xeokit-sdk/dist/xeokit-sdk.es.min.js";

const viewer = new Viewer({
    canvasId: "myCanvas",
    transparent: true
});

var model;

viewer.camera.eye = [-3.933, 2.855, 27.018];
viewer.camera.look = [4.400, 3.724, 8.899];
viewer.camera.up = [-0.018, 0.999, 0.039];


//------------------------------------------------------------------------------------------------------------------
// Create an IFC structure tree view
//------------------------------------------------------------------------------------------------------------------

const treeView = new TreeViewPlugin(viewer, {
    containerElement: document.getElementById("treeViewContainer"),
    autoExpandDepth: 1, // Initially expand tree one level deep
    hierarchy: "storeys",
    sortNodes: true,

    // With hierarchy:"storeys" and sortNodes:true we can optionally specify which element types
    // we derive the center of each storey from, which we use to spatially sort the storeys on the
    // vertical axis. By default, this is all types, but sometimes some types of element will
    // span multiple storeys, so we have the ability to refine which types contribute to those center points.
    sortableStoreysTypes: ["IfcBeam"]
});


//------------------------------------------------------------------------------------------------------------------
// Funcions to load the file
//------------------------------------------------------------------------------------------------------------------
function loadIFCfile(file) {
    const webIFCLoader = new WebIFCLoaderPlugin(viewer, {
        wasmPath: "https://cdn.jsdelivr.net/npm/@xeokit/xeokit-sdk/dist/"
    });
    model = webIFCLoader.load({
        src: file, //"../models/2023.02.28.FRADE_SRU.ifc",
        edges: true
    });    
}

function loadXKTfile(file) {
    const xktLoader = new XKTLoaderPlugin(viewer);
    model = xktLoader.load({
        id: "myModel",
        src: file, 
        //excludeTypes: ["IfcSpace"],
        edges: true
    });
   
}

function getFileExt(file) {
    var splited = file.split(".");
    var n = splited.length;
    return splited[n-1];
}

function loadModelFile(file){
    const fileExt = getFileExt(file);
    if (fileExt == 'ifc') {
        loadIFCfile(modelFile);
    } else if (fileExt == 'xkt') {
        loadXKTfile(modelFile);
    }    
}

function getULSresults() {
    console.log("ULS");
    console.log(model.entityList)
    for (const obj of model.entityList) {
        console.log(obj.id);
        console.log(obj.Name);
        obj.colorize = [1, 0, 0];
    }
    //model.objects.forEach( obj =>
    //    console.log(obj.id)
    //) 
    
}

function getFatigueResults() {
    console.log("Fatigue");
}


loadModelFile(modelFile)


let btnULS = document.getElementById("btnULS")
btnULS.onclick = getULSresults;

let btnFatigue = document.getElementById("btnFatigue")
btnFatigue.onclick = getFatigueResults;