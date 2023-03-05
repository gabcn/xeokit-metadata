

//var resultData;

class dbValues{
    constructor(name, UC, FatigueDamage) {
        this.name = name;
        this.UC = UC;
        this.FatigueDamage = FatigueDamage;
    }
}

class csvDataBase {
    data;
    constructor(csvFile) {
        this.csvFile = csvFile;
        this.data = new Object();
        this.readCSVFile(csvFile);
    }

    #normValue(value) {
        return Math.min(1, Math.max(0, value));
    }

    readCSVFile(file) {
        fetch(file)
         .then(Response => Response.text())
         .then(text => this.parseCsv(text))
     }    

    parseCsv(text) {
        var newValues;
        const rows = text.split('\r\n');
        for (const row of rows) {
            const items = row.split(',');
            const id = items[0];
            const beamName = items[1];
            const valueUC = items[2];
            if (valueUC != 'N/A') {
                newValues = new dbValues(beamName, valueUC, 0.);
                this.data[id] = newValues;
                //console.log(row);
            }
        }
    }

    getUC(id) {
        const Values = this.data[id]
        if (Values) {

            return Values.UC;
        } else {
            return undefined
        }
    }

    /* 
    getUCColor(id) {
        const valueUC = this.getUC(id);
        if (valueUC) {
            const nV = this.#normValue(valueUC);
            const R = nV;
            const B = 1-nV;
            return [R, 0, B];
        } else {
            return [0, 0, 0];
        }

    }
     */
}


function getFatigueResults() {
    console.log("Fatigue");
}

export {csvDataBase, getFatigueResults};

