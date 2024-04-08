import sys
import json
import spinedb_api as api
from spinedb_api import purge

ARGS = sys.argv[1:]
ines = ARGS[0]
usersettings = ARGS[1]
dataset = ARGS[2]
casedata = ARGS[3]

# improvement: use the database operations instead of dictionaries
# improvement: merging user and dataset for both entities and parameters

# load generic energy format
print("Load ines spec")
with open(ines) as f:
	iodb = json.load(f)
	#the new version of the ines spec is missing fields that the script relies on:
	iodb["entities"]=[]
	iodb["parameter_values"]=[]
	iodb["alternatives"]=[]

# make convenience parameter dictionary
parameterdefinition = {}
for parameter in iodb["parameter_definitions"]:
	if parameter[0] not in parameterdefinition:
		parameterdefinition[parameter[0]] = []
	parameterdefinition[parameter[0]].append(parameter[1])

# load user specifications
print("Load user database")
with open(usersettings) as f:
	userdata = json.load(f)
userentities = userdata["entities"]

# make convenience parameter dictionary

# load full dataset
print("Load full database")
if dataset.split(".")[-1] == 'json':
	with open(dataset) as f:
		fulldata = json.load(f)
else:
	with api.DatabaseMapping(dataset) as source_db:
		fulldata = api.export_data(source_db,parse_value=api.parameter_value.load_db_value)

# create case data
print("Stack the template with a part of the full database and the user database")
alternatives = []
for userentity in userentities:
	# entities
	iodb["entities"].append(userentity)
	# parameters
	userentityclass = userentity[0]
	userentityname = userentity[1]
	#entity = fulldata[userentityname]
	for parametername in parameterdefinition[userentityclass]:
		entityparametervalue = None
		for parametervalue in fulldata["parameter_values"]:
			if parametername == parametervalue[2] and userentityname == parametervalue[1]:
				entityparametervalue = parametervalue
		for parametervalue in userdata["parameter_values"]:
			if parametername == parametervalue[2] and userentityname == parametervalue[1]:
				entityparametervalue = parametervalue
		if entityparametervalue != None:
			iodb["parameter_values"].append(entityparametervalue)
			if entityparametervalue[4] not in alternatives:
				alternatives.append(entityparametervalue[4])

for alternative in alternatives:
	iodb["alternatives"].append([alternative, ""])

#bring the data to the select data set
print("Create Case data")
#import_data(casedata, iodb, "Generate Case data")
if casedata.split(".")[-1] == 'json':
    with open(casedata, 'w') as f:
        json.dump(iodb, f, indent=4)
else:
	with api.DatabaseMapping(casedata) as target_db:
		purge.purge(target_db, purge_settings=None)
		message = api.import_data(target_db,**iodb)
		target_db.refresh_session()
		target_db.commit_session("Import data")

		# debugging
		#print(message)