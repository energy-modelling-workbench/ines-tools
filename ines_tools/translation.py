import sys
import json
from importlib.machinery import SourceFileLoader
import spinedb_api as api
from spinedb_api import purge

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
if input.split(".")[-1] == 'json':
	with open(input) as f:
		inputdata = json.load(f)
else:
	with api.DatabaseMapping(input) as source_db:
		inputdata = api.export_data(source_db,parse_value=api.parameter_value.load_db_value)

entitydict = {}
for entity in inputdata["entities"]:
	entityrelation = ''.join(entity[1])
	entitydict[entityrelation] = entity

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
	entityname = ''.join(parametervalue[1])
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
	# an entity (or relation between entities) and its parameters
	entities = [entitydict[entityname][1]]
	parameters = [entityparameters]
	if type(entitydict[entityname][1]) != str:
		# list or tuple
  		# in other words, if the entity describes a relation
		# we add the related entities as they may be needed in the translation
		for entityrelation in entitydict[entityname][1]:
			entities.append(entityrelation)
			parameters.append(entityparameterdict[entityrelation])
	getattr(map,"map_"+entitydict[entityname][0])(iodb,entities,parameters)

# postprocess
print("Postprocessing")
map.map_postprocess(iodb)

# write data to output
print("Writing data")
if output.split(".")[-1] == 'json':
	with open(output, 'w') as f:
		json.dump(iodb, f, indent=4)
else:
	with api.DatabaseMapping(output) as target_db:
		purge.purge(target_db, purge_settings=None)
		api.import_data(target_db,**iodb)
		target_db.refresh_session()
		target_db.commit_session("Import data")