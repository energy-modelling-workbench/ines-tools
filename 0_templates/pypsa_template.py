from pathlib import Path
import pypsa
import pandas as pd
import json

path = Path(__file__).resolve().parent
outputpath = path.joinpath("template_pypsa.json")

n = pypsa.Network()

iodb={}

for component,attributes in n.components.items():
    iodb[component]={}
    for key,value in attributes.items():
        if isinstance(value, pd.DataFrame):
            datadict = value.to_dict(orient='index')
            for datakey,datavalue in datadict.items():
                if 'typ' in datavalue:
                    datadict[datakey]['typ'] = datadict[datakey]['typ'].__name__
                if 'dtype' in datavalue:
                    datadict[datakey]['dtype'] = datadict[datakey]['dtype'].name
            iodb[component][key] = datavalue
        else: 
            iodb[component][key] = value

with open(outputpath, 'w') as f:
    json.dump(iodb, f, indent=4)