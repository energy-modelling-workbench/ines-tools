import sys
import json
from importlib.machinery import SourceFileLoader

#path = dirname(@__DIR__)
#tool = "pypsa"#"spineopt"#

ARGS = sys.argv[1:]
mapfile = ARGS[0]
input = ARGS[1]
output = ARGS[2]

map = SourceFileLoader("map", mapfile).load_module()

iodb = {}

# preprocess
print("Preprocessing")
map.map_preprocess(iodb)

# Load input data
# assume that input follows the generic energy format template
print("Load input data")
with open(input) as f:
	inputdata = json.load(f)

entitynames = {}
entitydict = {}
for entity in inputdata["entities"]:
	if len(entity[2])>1:
		entityrelation = entity[2]
	else:
		entityrelation = entity[1]
	entitynames[entity[1]] = entityrelation
	entitydict[entity[1]] = entity

parameterdict = {}
for parameterdefinition in inputdata["parameter_definitions"]:
	entityclass = parameterdefinition[0]
	parametername = parameterdefinition[1]
	parametervalue = parameterdefinition[2]
	if entityclass not in parameterdict:
		parameterdict[entityclass] = {}
	parameterdict[entityclass][parametername] = parametervalue

entityparameterdict = {}
for parametervalue in inputdata["parameter_values"]:
	entityname = entitynames[parametervalue[1]]
	if entityname not in entityparameterdict:
		entityparameterdict[entityname] = {}
	entityparameterdict[entityname][parametervalue[2]] = parametervalue[3]

#correct for missing values
for (entityname,entity) in entitydict.items():
	entityclass = entity[0]
	if entityname not in entityparameterdict:
		entityparameterdict[entityname] = {}
	for (parametername,parametervalue) in parameterdict[entityclass].items():
		if parametername not in entityparameterdict[entityname]:
			entityparameterdict[entityname][parametername] = parametervalue

# map the input data to the output data
print("Map input data to output data")
for (entityname, entityparameters) in entityparameterdict.items():
	entities = [entityname]
	parameters = [entityparameters]
	for entityrelation in entitydict[entityname][2]:
		entities.append(entityrelation)
		parameters.append(entityparameterdict[entityrelation])
	getattr(map,"map_"+entitydict[entityname][0])(iodb,entities,parameters)

# postprocess
print("Postprocessing")
map.map_postprocess(iodb)

# write data to output
print("Writing data")
with open(output, "w") as f:
	json.dump(iodb, f, indent=4)
	