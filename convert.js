const convert2xkt = require("@xeokit/xeokit-convert/dist/convert2xkt.cjs.js");

convert2xkt.convert2xkt({
    source: "PCE_JACKET.ifc",
    output: "PCE_JACKET.ifc.xkt",
    log: (msg) => {
        console.log(msg)
    }
}).then(() => {
    console.log("Converted.");
}, (errMsg) => {
    console.error("Conversion failed: " + errMsg)
}); 