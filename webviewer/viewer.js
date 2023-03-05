//const modelFile = "../models/2023.02.28.FRADE_SRU.ifc";
//const modelFile = "../models/2023.02.28.FRADE_SRU.xkt";
const modelFile = "../models/example2.xkt";
const csvFile = '../models/example2.csv';

//------------------------------------------------------------------------------------------------------------------
// LIBS
//------------------------------------------------------------------------------------------------------------------
//import {Viewer, WebIFCLoaderPlugin, XKTLoaderPlugin, TreeViewPlugin} from
//    "https://cdn.jsdelivr.net/npm/@xeokit/xeokit-sdk/dist/xeokit-sdk.es.min.js";
import { Viewer, WebIFCLoaderPlugin, XKTLoaderPlugin, TreeViewPlugin } from
    "./dist/xeokit-sdk.min.es.js";

import { csvDataBase, getFatigueResults } from "./assessrst.js";
import { classColorScale } from "./colorscale.js";
import { 
    valuesExtractGeni, colorsExtractGeni,
    valuesBlueToRed10colors, colorsBlueToRed10colors,
    valuesBlueToRed6colors, colorsBlueToRed6colors
    } from "./configs.js"

const csvDB = new csvDataBase(csvFile);
var model; 
var buttons = new Object();

const viewer = new Viewer({
    canvasId: "cavas3Dview",
    transparent: true
});
viewer.camera.eye = [-3.933, 2.855, 27.018];
viewer.camera.look = [4.400, 3.724, 8.899];
viewer.camera.up = [-0.018, 0.999, 0.039];

const scaleBarUC = new classColorScale(
    "canvasColorScale", valuesExtractGeni, colorsExtractGeni
//    "canvasColorScale", valuesBlueToRed10colors, colorsBlueToRed10colors
//    "canvasColorScale", valuesBlueToRed6colors, colorsBlueToRed6colors
);


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
    sortableStoreysTypes: ["IfcBeam", "IfcElement"]
});


//------------------------------------------------------------------------------------------------------------------
// Funcions to load the model file
//------------------------------------------------------------------------------------------------------------------
function loadIFCfile(file) {
    const webIFCLoader = new WebIFCLoaderPlugin(viewer, {
        wasmPath: "https://cdn.jsdelivr.net/npm/@xeokit/xeokit-sdk/dist/"
    });
    model = webIFCLoader.load({
        src: file, 
        edges: true,
        excludeUnclassifiedObjects: false        
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
        excludeUnclassifiedObjects: false
    });
    return xktLoader   
}

function getFileExt(file) {
    var splited = file.split(".");
    var n = splited.length;
    return splited[n-1];
}



function loadModelFile(file) {

    const fileExt = getFileExt(file);
    if (fileExt == 'ifc') {
        return loadIFCfile(modelFile);
    } else if (fileExt == 'xkt') {
        return loadXKTfile(modelFile);
    }    
}

function plotULSresults() {
    for (const obj of model.entityList) {
        //console.log(obj.colorize)
        const id = obj.id;
        const valueUC = csvDB.getUC(id);
        //obj.colorize = csvDB.getUCColor(id);
        //console.log([valueUC, scaleBarUC.colorForValueNormalized(valueUC)]);
        if (valueUC) { // if UC result is available
            //console.log('Member: ' + id + ' UC = ' + valueUC )
            obj.opacity = 1;
            obj.colorize = scaleBarUC.colorForValueNormalized(valueUC);
        } else {
            obj.opacity = 0.4;
            obj.colorize = [1.,1.,1.];
        }        
    }    

        //const metaObj = (viewer.metaScene.metaObjects)[id];
        //console.log(metaObj);//["3tCw4OaF14lRBNgCr7cdqX"]);
    scaleBarUC.drawUCscaleBar();
    setBtnActiveColor('ULS');
    /*
    for (const [key, value] of Object.entries(viewer.metaScene.metaObjects)) {
        //console.log(key);
        if (value.type != 'IfcBeam') {
            console.log(value)
        }
    }
    */
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

function hideShowTView() {
    const container = document.getElementById("treeViewContainer");
    //cont show = treeView.
    //console.log(container.style.width);
    if (container.style.width == "0px") {
        container.style.width = "350px";        
        btnHideShowTView.style.left = "360px";
    } else {
        container.style.width = "0px";
        btnHideShowTView.style.left = "10px";
    }
}

let loader = loadModelFile(modelFile)

let btnULS = document.getElementById("btnULS")
btnULS.onclick = plotULSresults;
buttons['ULS'] = btnULS

let btnFatigue = document.getElementById("btnFatigue")
btnFatigue.onclick = plotFatigueResults;
buttons['Fatigue'] = btnFatigue;

let btnHideShowTView = document.getElementById("btnHideShowTView");
btnHideShowTView.onclick = hideShowTView;

