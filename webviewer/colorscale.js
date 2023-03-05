import "./libs/chroma.min.js"; // https://gka.github.io/chroma.js/

const digits = 2;
const marginY = 10;
const marginX = 10;
const blwAbvWidth = 20;
//const nSteps = 10;
//const valueIni = 0.;
//const valueEnd = 1.;
const valuesTxtHeight = 20;
const gapValuesColors = 10; // gap between the text of the values and the color rectangles
const yText = marginY + valuesTxtHeight;
const y0 = marginY + valuesTxtHeight + gapValuesColors;

/**
 * @param {string} canvasId id of the canvas where the color bar will be draw
 * @param {array} extremeValues 
 * @param {array} colors
 */   
class classColorScale {
    //#colorPalette; 
    colorList = [];
    colorBelowAndAboveAll = [];
    constructor(
        canvasId,
        limitingValues, 
        colors, 
        ) {
        this.canvas = document.getElementById(canvasId);
        this.context2d = this.canvas.getContext("2d");
        this.limitingValues = limitingValues;
        //this.extremeValues = extremeValues;
        //this.colorList = colors;
        this.#copyColorArray(colors, this.colorList);
        //this.#copyColorArray(colorsOusideExtreme, this.colorBelowAndAboveAll);
        this.nSteps = limitingValues.length-1;
        //this.deltValue = (extremeValues[1]-extremeValues[0])/this.nSteps;
        //this.domainValues = [extremeValues[0] + this.deltValue/2., extremeValues[1] - this.deltValue/2.];
        //this.limitingValues = 
        //this.#colorPalette = chroma.scale(colors).domain(this.domainValues);

        this.Width = this.canvas.width;
        this.Height = this.canvas.height;
        this.rectWidth = (this.Width-2*marginX-2*blwAbvWidth)/this.nSteps;
        this.rectHeight = (this.Height-2*marginY-gapValuesColors-valuesTxtHeight);   
    }
    
    #copyColorArray(from, to) {
        from.forEach(function(item) {
            to.push(chroma(item));
        });
    }


    /**
     * Returns the color in format RGB, with each component varying from 0 to 1
     * @param {*} value 
     */
    colorForValueNormalized(value) {
        const rgba = this.colorForValue(value).rgb();
        //console.log(rgba);
        //const array = rgba["_rgb"]
        const R = rgba[0]/255;
        const G = rgba[1]/255;
        const B = rgba[2]/255;
        return [R, G, B];
    }

    /**
     * Returns the color in format rgba 
     * @param {float} value 
     * @returns 
     */

    colorForValue(value) {
        //var color;
        //console.log(this.colorBelowAndAboveAll[1]);
        /*
        if (value < this.extremeValues[0])
            color = this.colorBelowAndAboveAll[0];
        else if (value <= this.extremeValues[1])
            color = this.#colorPalette(value);
        else
            color = this.colorBelowAndAboveAll[1];
        return color;    
        */
       //var color;
       var i = -1;
       while (++i<this.limitingValues.length) {
        if (value < this.limitingValues[i]) { break; }
       }
       return this.colorList[i];
    }

    #drawRectangle(x, y, width, height, fillColor, lineColor) {        
        this.context2d.strokeStyle = lineColor;
        this.context2d.lineWidth = 2;
        this.context2d.strokeRect(x, y, width, height);    
        this.context2d.fillStyle = fillColor;
        this.context2d.fillRect(x, y, width, height);
    }


    drawUCscaleBar() {
        if (this.canvas.getContext) {    
            this.canvas.style.visibility = "visible";           
    
            let x, y, x0 = marginX;
            let color, valueRefColor, valueBoundary, valueTxt, txtWidth;

            // below and above all colors
            this.#drawRectangle(
                x0, y0, blwAbvWidth, this.rectHeight, this.colorList[0], "black"
                );
            this.#drawRectangle(
                this.Width-marginX-blwAbvWidth, y0, blwAbvWidth, this.rectHeight, this.colorList[this.colorList.length-1], "black"
                );
          
            // colors and text from Ini do End
            x0 += blwAbvWidth;
            
            for (var i=0; i<=this.nSteps; i++) {
                x = x0 + this.rectWidth*i;
                y = y0;
                valueRefColor = this.limitingValues[i]; //this.extremeValues[0] + (i+0.5)*this.deltValue;
                if (i<this.nSteps) {
                        color = this.colorList[i+1] //this.colorForValue(valueRefColor);            
                        //console.log(color);
                        this.#drawRectangle(x, y, this.rectWidth, this.rectHeight, color, "black");
                }
    
                // values
                //valueBoundary = valueRefColor - 0.5*this.deltValue;
                //valueTxt = valueBoundary.toFixed(digits)
                valueTxt = valueRefColor.toFixed(digits);
                this.context2d.font = "normal normal 400 " + valuesTxtHeight.toString() + "px arial";
                this.context2d.fillStyle = "black";
                txtWidth = this.context2d.measureText(valueTxt).width;
                this.context2d.fillText(valueTxt, x-txtWidth/2., yText);    
            }    
        }
    } 
}




export {classColorScale};