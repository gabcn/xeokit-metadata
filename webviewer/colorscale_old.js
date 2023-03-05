import "./libs/chroma.min.js"

const marginY = 10;
const marginX = 10;
const blwAbvWidth = 20;
const nSteps = 10;
const valueIni = 0.;
const valueEnd = 1.;
const valuesTxtHeight = 20;
const gapValuesColors = 10; // gap between the text of the values and the color rectangles
const colorsUC = [
    'blue', 'rgb(0,100,255)', 'rgb(0,160,255)', 'rgb(0,210,255)', 'rgb(0,255,255)', 
    'green', 'yellow', 'rgb(255,200,0)', 'rgb(255,120,0)', 'red'
];
const colorBelowAndAboveAll = ['rgb(255,190,200)', 'purple']
const deltValue = (valueEnd-valueIni)/nSteps;
const domainValues = [valueIni + deltValue/2., valueEnd - deltValue/2.]
const colorPalette = chroma.scale(colorsUC).domain(domainValues);


const yText = marginY + valuesTxtHeight;

function colorForValue(value) {
    var color;
    if (value < valueIni)
        color = colorBelowAndAboveAll[0];
    else if (value <= valueEnd)
        color = colorPalette(value);
    else
        color = colorBelowAndAboveAll[1];
    return color;    
}

function drawRectangle(context, x, y, width, height, fillColor, lineColor) {
    context.strokeStyle = lineColor;
    context.lineWidth = 2;
    context.strokeRect(x, y, width, height);    
    context.fillStyle = fillColor;
    context.fillRect(x, y, width, height);
}

function drawUCscaleBar(canvasId) {
    const canvas = document.getElementById(canvasId);
    if (canvas.getContext) {
        
        const Width = canvas.width;
        const Height = canvas.height;
        const rectWidth =  (Width-2*marginX-2*blwAbvWidth)/nSteps;
        const rectHeight =  (Height-2*marginY-gapValuesColors-valuesTxtHeight);

        canvas.style.visibility = "visible";
        const ctx = canvas.getContext("2d");

        let x, y, x0 = marginX, y0 = marginY + valuesTxtHeight + gapValuesColors;
        let color, valueRefColor, valueBoundary, valueTxt, txtWidth;
        // below and above all colors
        drawRectangle(ctx, x0, y0, blwAbvWidth, rectHeight, colorBelowAndAboveAll[0], "black");
        drawRectangle(ctx, Width-marginX-blwAbvWidth, y0, blwAbvWidth, rectHeight, colorBelowAndAboveAll[1], "black");
      
        // colors and text from Ini do End
        x0 += blwAbvWidth;
        
        for (var i=0; i<=nSteps; i++) {
            x = x0 + rectWidth*i;
            y = y0;
            valueRefColor = valueIni + (i+0.5)*deltValue;
            if (i<nSteps) {
                    color = colorForValue(valueRefColor);            
                    drawRectangle(ctx, x, y, rectWidth, rectHeight, color, "black");
            }

            // values
            valueBoundary = valueRefColor - 0.5*deltValue;
            valueTxt = valueBoundary.toFixed(1)
            ctx.font = "normal normal 400 " + valuesTxtHeight.toString() + "px arial";
            ctx.fillStyle = "black";
            txtWidth = ctx.measureText(valueTxt).width;
            console.log(txtWidth)
            ctx.fillText(valueTxt, x-txtWidth/2., yText);

    }


    }
}


export {drawUCscaleBar};