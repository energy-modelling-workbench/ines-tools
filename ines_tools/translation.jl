#import SpineInterface
import JSON

#path = dirname(@__DIR__)
#tool = "pypsa"#"spineopt"#

#componenttooltemplate = ARGS[1]#joinpath(path,"0_component_tool_template","generic_data_format.json")#
map = ARGS[1]#joinpath(path, "6_exporters", "map_"*tool*".jl")#
input = ARGS[2]#joinpath(path, "5_built_data_and_scenarios", "casedata.json")#
output = ARGS[3]#joinpath(path, "7_tools", "input_"*tool*".json")#

include(map)

iodb = Dict{String,Any}()

# preprocess
println("Preprocessing")
map_preprocess(iodb)

# Load input data
# assume that input follows the generic energy format template
println("Load input data")
#SpineInterface.using_spinedb(input, Main)
inputdata = open(input, "r") do f
	dicttxt = read(f,String)
	return JSON.parse(dicttxt)
end
entitynames = Dict()
entitydict = Dict()
for entity in inputdata["entities"]
	if length(entity[3])>1
		entityrelation = entity[3]
	else
		entityrelation = entity[2]
	end
	entitynames[entity[2]] = entityrelation
	entitydict[entity[2]] = entity
end
parameterdict = Dict()
for parameterdefinition in inputdata["parameter_definitions"]
	entityclass = parameterdefinition[1]
	parametername = parameterdefinition[2]
	parametervalue = parameterdefinition[3]
	merge!(
		get!(parameterdict, entityclass, Dict()),
		Dict(
			parametername => parametervalue
		)
	)
end
#print(JSON.json(parameterdict,4))
entityparameterdict = Dict()
for parametervalue in inputdata["parameter_values"]
	entityname = entitynames[parametervalue[2]]
	merge!(
		get!(entityparameterdict, entityname, Dict()),
		Dict(
			parametervalue[3] => parametervalue[4]
		)
	)
end
#correct for missing values
for (entityname,entity) in entitydict
	entityclass = entity[1]
	get!(entityparameterdict, entityname, Dict())
	for (parametername,parametervalue) in parameterdict[entityclass]
		get!(entityparameterdict[entityname], parametername, parametervalue)
	end
end

# map the input data to the output data
println("Map input data to output data")
for (entityname, entityparameters) in entityparameterdict
	entities = [entityname]
	parameters = [entityparameters]
	for entityname in entitydict[entityname][3]
		push!(entities, entityname)
		push!(parameters, entityparameterdict[entityname])
	end
	getfield(Main,Symbol("map_"*entitydict[entityname][1]))(iodb,entities,parameters)
end

# postprocess
println("Postprocessing")
map_postprocess(iodb)

# write data to output
println("Writing data")
open(output, "w") do f
	JSON.print(f, iodb, 4)
end
	