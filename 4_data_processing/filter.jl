#using SpineInterface
using JSON

#path = dirname(@__DIR__)
genericenergyformat = ARGS[1]#joinpath(path, "0_component_tool_template", "generic_data_format.json")#only generic format
usersettings = ARGS[2]#joinpath(path, "4_data_processing", "usersettings.json")#only entities
dataset = ARGS[3]#joinpath(path, "3_select_unprocessed_data", "fulldetaildata.json")#only parameters
casedata = ARGS[4]#joinpath(path, "5_built_data_and_scenarios", "casedata.json")#

# improvement: use the database operations instead of dictionaries
# improvement: merging user and dataset for both entities and parameters

# load generic energy format
println("Load generic energy format")
iodb = open(genericenergyformat, "r") do f
	dicttxt = read(f,String) # file information to string
	return JSON.parse(dicttxt) # parse and transform data
end

# make convenience parameter dictionary
parameterdefinition = Dict()
for parameter in iodb["parameter_definitions"]
	push!(get!(parameterdefinition, parameter[1], []), parameter[2])
end

# load user specifications
println("Load user database")
userdata =  open(usersettings, "r") do f
	dicttxt = read(f,String) # file information to string
	return JSON.parse(dicttxt) # parse and transform data
end
userentities = userdata["entities"]

# make convenience parameter dictionary

# load full dataset
println("Load full database")
#using_spinedb(dataset)
fulldata = open(dataset, "r") do f
	dicttxt = read(f,String)
	return JSON.parse(dicttxt)
end

# create case data
println("Stack the template with a part of the full database and the user database")
alternatives = []
for userentity in userentities
	# entities
	push!(iodb["entities"], userentity)
	# parameters
	userentityname = userentity[2]
	if size(userentity[3],1)>1
		userentityrelation = userentity[3]
	else
		userentityrelation = userentityname
	end
	try#should fail because SpineInterface is disabled
		entity = getfield(Main,Symbol(userentityname))()
		for parametername in parameterdefinition[entity.class_name]
			kwarg = Dict(Symbol(entity.class_name)=>entity)
			parametervalue = getfield(Main,Symbol(parametername))(;kwarg...)
			push!(iodb["parameter_values"],[entity.class_name,userentityrelation,parameter,parametervalue,"Base"])
		end
	catch
		#do nothing
	end
	#use dicts as long as SpineInterface is disabled
	#entity = fulldata[userentityname]
	for parametername in parameterdefinition[userentity[1]]
		entityparametervalue = nothing
		for parametervalue in fulldata["parameter_values"]
			if parametername == parametervalue[3] && userentityrelation == parametervalue[2]
				entityparametervalue = parametervalue
			end
		end
		for parametervalue in userdata["parameter_values"]
			if parametername == parametervalue[3] && userentityrelation == parametervalue[2]
				entityparametervalue = parametervalue
			end
		end
		if isnothing(entityparametervalue) == false
			push!(iodb["parameter_values"],entityparametervalue)
		end
	end
end
for alternative in alternatives
	push!(iodb["alternatives"], [alternative, ""])
end

#bring the data to the select data set
println("Create Case data")
#import_data(casedata, iodb, "Generate Case data")
open(casedata, "w") do f
    JSON.print(f, iodb, 4)
end