import sys
import pypsa
import json

ARGS = sys.argv[1:]
inputpath = ARGS[0] # nc file
outputpath = ARGS[1] # json file

n = pypsa.Network(inputpath)

iodb = {
    "Bus": {},
    "Generator": {},
    "Link": {},
    "Load": {},
}

for key, value in n.buses.to_dict("index").items():
    iodb["Bus"][key] = value
for key, value in n.generators.to_dict("index").items():
    iodb["Generator"][key] = value
for key, value in n.links.to_dict("index").items():
    iodb["Link"][key] = value
for key, value in n.loads.to_dict("index").items():
    iodb["Load"][key] = value

with open(outputpath, 'w') as f:
    json.dump(iodb, f, indent=4)