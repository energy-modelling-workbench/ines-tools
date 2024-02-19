import sys
import json

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
	iodb["parametervalues"]=[]

# make convenience parameter dictionary
parameterdefinition = {}
for parameter in iodb["parameter_definitions"]:
	parameterdefinition.get(parameter[1],[]).append(parameter[2])

# load user specifications
print("Load user database")
with open(usersettings) as f:
	userdata = json.load(f)
userentities = userdata["entities"]

# make convenience parameter dictionary

# load full dataset
print("Load full database")
with open(dataset) as f:
	fulldata = json.load(f)

# create case data
print("Stack the template with a part of the full database and the user database")
alternatives = []
for userentity in userentities:
	# entities
	iodb["entities"].append(userentity)
	# parameters
	userentityname = userentity[2]
	if userentity[3]:
		userentityrelation = userentity[3]
	else:
		userentityrelation = userentityname
	#entity = fulldata[userentityname]
	for parametername in parameterdefinition[userentity[1]]:
		entityparametervalue = None
		for parametervalue in fulldata["parameter_values"]:
			if parametername == parametervalue[3] and userentityrelation == parametervalue[2]:
				entityparametervalue = parametervalue
		for parametervalue in userdata["parameter_values"]:
			if parametername == parametervalue[3] and userentityrelation == parametervalue[2]:
				entityparametervalue = parametervalue
		if entityparametervalue == None:
			iodb["parameter_values"].append(entityparametervalue)

for alternative in alternatives:
	iodb["alternatives"].append([alternative, ""])

#bring the data to the select data set
print("Create Case data")
#import_data(casedata, iodb, "Generate Case data")
with open(casedata, "a") as f:
	print(iodb, file=f)