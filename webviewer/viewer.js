//const modelFile = "../models/2023.02.28.FRADE_SRU.ifc";
//const modelFile = "../models/2023.02.28.FRADE_SRU.xkt";
const modelFile = "../models/example2.xkt";
const csvFile = '../models/example2.csv';

//------------------------------------------------------------------------------------------------------------------
// LIBS
//------------------------------------------------------------------------------------------------------------------
import {Viewer, WebIFCLoaderPlugin, XKTLoaderPlugin, TreeViewPlugin} from
    "https://cdn.jsdelivr.net/npm/@xeokit/xeokit-sdk/dist/xeokit-sdk.es.min.js";

import {csvDataBase, getFatigueResults} 
    from "./assessrst.js";

const csvDB = new csvDataBase(csvFile);
var model; 
var buttons = new Object();

const viewer = new Viewer({
    canvasId: "myCanvas",
    transparent: true
});
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
// Funcions to load the model file
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
        edges: true,
        //globalizeObjectIds: true
    });
   
}

function getFileExt(file) {
    var splited = file.split(".");
    var n = splited.length;
    return splited[n-1];
}


function loadModelFile(file) {

    const fileExt = getFileExt(file);
    if (fileExt == 'ifc') {
        loadIFCfile(modelFile);
    } else if (fileExt == 'xkt') {
        loadXKTfile(modelFile);
    }    
    console.log(viewer.metaScene)
}

function plotULSresults() {
    for (const obj of model.entityList) {
        const id = obj.id;
        const valueUC = csvDB.getUC(id);
        if (valueUC) {
            console.log('Member: ' + id + ' UC = ' + valueUC )
            obj.colorize = csvDB.getUCColor(id);
            obj.opacity = 1;
        } else {
            obj.opacity = 0.2;
        }
    }
    console.log(csvDB.getUC('1j4GtMWkT5re2FwlxmMXH2'));
    setBtnActiveColor('ULS');
}

function plotFatigueResults() {
    //getFatigueResults;

    setBtnActiveColor('Fatigue');
}


function setBtnActiveColor(btnName) {
    for (const [key, btn] of Object.entries(buttons)) {
        if (key == btnName) {
            btn.style['background-color'] = 'orange'
        } else {
            btn.style['background-color'] = 'lightgray'
        }
    }
}


loadModelFile(modelFile)



let btnULS = document.getElementById("btnULS")
btnULS.onclick = plotULSresults;
buttons['ULS'] = btnULS

let btnFatigue = document.getElementById("btnFatigue")
btnFatigue.onclick = plotFatigueResults;
buttons['Fatigue'] = btnFatigue

