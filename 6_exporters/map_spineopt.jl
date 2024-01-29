import SpineOpt

function map_preprocess(iodb)
	# Load SpineOpt template
	println("Load SpineOpt template")
	merge!(iodb, SpineOpt.template())
	iodb["relationships"] = []
	iodb["object_parameter_values"] = []
	iodb["relationship_parameter_values"] = []
	iodb["alternatives"] = [["Base", "Base alternative"]]

	# The template functionality of SpineOpt should be updated with a model template and a system template,
	# for now that is done manually in the workflow
end

function map_postprocess(iodb)
end

# Function map for entity classes; specific to the generic structure
function map_constraint(iodb,entities,parameters)
end

function map_link(iodb,entities,parameters)
	entityname = entities[1]
	push!(iodb["objects"],["connection", entityname, nothing])
end

function map_node(iodb,entities,parameters)
	entityname = entities[1]
	parameter = parameters[1]
	push!(iodb["objects"],["node",entityname,nothing])
	balancetype = "balance_type_none"
	if parameter["node_type"] == "balance"
		balancetype = "balance_type_node"
	end
	push!(iodb["object_parameter_values"],["node", entityname, "balance_type", balancetype, "Base"])
	if parameter["demand_profile"] != nothing
		push!(iodb["object_parameter_values"],["node",entityname,"demand",parameter["demand_profile"],"Base"])
	end
end

function map_period(iodb,entities,parameters)
end

function map_set(iodb,entities,parameters)
end

function map_solve_pattern(iodb,entities,parameters)
end

function map_system(iodb,entities,parameters)
end

function map_temporality(iodb,entities,parameters)
end

function map_tool(iodb,entities,parameters)
end

function map_unit(iodb,entities,parameters)
	entityname = entities[1]
	push!(iodb["objects"],["unit",entityname,nothing])
end

function map_node__to_unit(iodb,entities,parameters)
	nodename = entities[2]
	unitname = entities[3]
	unitparameters = parameters[2]
	push!(iodb["relationships"],["unit__from_node", [unitname, nodename]])

	try# may be easier when using the parameter functions
		nodenameplus = pop!(iodb,"unit__node__node__"*unitname)
		threewayrelation = [unitname, nodenameplus, nodename]
		push!(iodb["relationships"],["unit__node__node",threewayrelation])
		push!(iodb["relationship_parameter_values"],["unit__node__node",threewayrelation,"fix_ratio_out_in_unit_flow",unitparameters["efficiency"],"Base"])
	catch e
		#println(e)
		iodb["unit__node__node__"*unitname] = nodename
	end
end

function map_set__link(iodb,entities,parameters)
end

function map_set_node(iodb,entities,parameters)
end

function map_set_temporality(iodb,entities,parameters)
end

function map_set__unit(iodb,entities,parameters)
end

function map_tool_set(iodb,entities,parameters)
end

function map_unit__to_node(iodb,entities,parameters)
	unitname = entities[2]
	nodename = entities[3]
	unitnodeparameters = parameters[1]
	unitparameters = parameters[2]
	push!(iodb["relationships"],["unit__to_node", [unitname, nodename]])

	push!(iodb["relationship_parameter_values"],["unit__to_node",entities,"vom_cost",unitnodeparameters["other_operational_cost"],"Base"])
	push!(iodb["relationship_parameter_values"],["unit__to_node",entities,"unit_capacity",unitnodeparameters["capacity_per_unit"],"Base"])

	try# may be easier when using the parameter functions
		nodenameplus = pop!(iodb,"unit__node__node__"*unitname)
		threewayrelation = [unitname, nodename, nodenameplus]
		push!(iodb["relationships"],["unit__node__node",threewayrelation])
		push!(iodb["relationship_parameter_values"],["unit__node__node",threewayrelation,"fix_ratio_out_in_unit_flow",unitparameters["efficiency"],"Base"])
	catch e
		#println(e)
		iodb["unit__node__node__"*unitname] = nodename
	end
end

function map_node__link__node(iodb,entities,parameters)
	nodename = entities[2]
	linkname = entities[3]
	nodenameplus = entities[4]
	linkparameters = parameters[3]

	threewayrelation = [nodename, linkname, nodenameplus]
	push!(iodb["relationships"],["connection__node__node", threewayrelation])
	push!(iodb["relationship_parameter_values"],["connection__node__node",threewayrelation,"connection_capacity",linkparameters["capacity"],"Base"])
	push!(iodb["relationship_parameter_values"],["connection__node__node",threewayrelation,"fix_ratio_out_in_connection_flow",linkparameters["efficiency"],"Base"])
end

function map_set__node__temporality(iodb,entities,parameters)
end

function map_set__node__unit(iodb,entities,parameters)
end