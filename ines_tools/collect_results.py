import sys
import json

ARGS = sys.argv[1:]
input = ARGS[0]
output = ARGS[1]

# load existing data
with open(output) as f:
	iodb = json.load(f)

# load new data
with open(input) as f:
	results = json.load(f)

# give the data a name
if "tool" not in results:
	results["tool"] = input
toolname = results.pop("tool")

# overwrite data if it exists, create it if it not exists
iodb[toolname] = results 

# print data
with open(output, "w") as f:
	json.dump(iodb, f, indent=4)