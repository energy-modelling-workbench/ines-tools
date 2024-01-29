# import data from json
# create network from json
# run optimisation
# print results to json

import sys
from pathlib import Path
import json
import pypsa

#path = Path(__file__).resolve().parent
ARGS = sys.argv[1:]
inputpath = ARGS[0]#path.joinpath("input_pypsa.json")#
outputpath = ARGS[1]#path.joinpath("output_pypsa.json")#

with open(inputpath) as f:
    networkdict = json.load(f)

network = pypsa.Network()

#Bus needs to go first to avoid warnings of missing busses
buses = networkdict.pop("Bus")
for objectname, object in buses.items():
    network.add("Bus", objectname, **object)

for objectclass, objects in networkdict.items():
    for objectname, object in objects.items():
        network.add(objectclass, objectname, **object)

network.optimize()

with open(outputpath, "a") as f:
    print(network.links_t.p0, file=f)
    print(network.generators_t.p, file=f)