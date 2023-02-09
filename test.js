const convert2xkt = require("@xeokit/xeokit-convert/dist/convert2xkt.cjs.js");
const fs = require('fs');

convert2xkt.convert2xkt({
     sourceData: fs.readFileSync("../PCE_JACKET.ifc"),
     sourceFormat: "ifc",
     outputXKT: (xtkArrayBuffer) => {
         fs.writeFileSync("../PCE_JACKET.ifc.xkt", xtkArrayBuffer);
     }
 }).then(()  => {
    console.log("Converted.");
}, (errMsg) => {
    console.error("Conversion failed: " + errMsg)
});