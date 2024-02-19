import sys
import json
import importlib

#path = dirname(@__DIR__)
#tool = "pypsa"#"spineopt"#

ARGS = sys.argv[1:]
map = importlib.import_module(ARGS[1])
input = ARGS[2]
output = ARGS[3]

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
	if len(entity[3])>1:
		entityrelation = entity[3]
	else:
		entityrelation = entity[2]
	entitynames[entity[2]] = entityrelation
	entitydict[entity[2]] = entity

parameterdict = {}
for parameterdefinition in inputdata["parameter_definitions"]:
	entityclass = parameterdefinition[1]
	parametername = parameterdefinition[2]
	parametervalue = parameterdefinition[3]
	parameterdict = parameterdict.get(parameterdict, entityclass, {}) | {parametername : parametervalue}

entityparameterdict = {}
for parametervalue in inputdata["parameter_values"]:
	entityname = entitynames[parametervalue[2]]
	entityparameterdict = entityparameterdict.get(entityname, {}) | {parametervalue[3] : parametervalue[4]}

#correct for missing values
for (entityname,entity) in entitydict:
	entityclass = entity[1]
	entityparameterdict.get(entityname, {})
	for (parametername,parametervalue) in parameterdict[entityclass]:
		entityparameterdict[entityname].get(parametername, parametervalue)

# map the input data to the output data
print("Map input data to output data")
for (entityname, entityparameters) in entityparameterdict:
	entities = [entityname]
	parameters = [entityparameters]
	for entityname in entitydict[entityname][3]:
		entities.append(entityname)
		parameters.append(entityparameterdict[entityname])
	getattr(map,"map_"*entitydict[entityname][1])(iodb,entities,parameters)

# postprocess
print("Postprocessing")
map.map_postprocess(iodb)

# write data to output
print("Writing data")
with open(output, "a") as f:
	print(iodb, file=f)
	