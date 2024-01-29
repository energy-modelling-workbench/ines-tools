function map_preprocess(iodb)
	# instead choose an intermediate format that is closer to spine?
	# e.g. [] instead of Dict()?
	merge!(
		iodb,
		Dict(
			"Bus" => Dict(),
			"Generator" => Dict(),
			"Link" => Dict(),
			"Load" => Dict()
		)
	)
end

function map_postprocess(iodb)
	#filter out nothing values
	for (entitytype,enitities) in iodb
		for (entityname,entitityattributes) in enitities
			for (attribute,value) in entitityattributes
				if isnothing(value)
					delete!(iodb[entitytype][entityname],attribute)
				end
			end
		end
	end
end

# Function map for entity classes; specific to the generic structure
function map_constraint(iodb,entities,parameters)
end

function map_link(iodb,entities,parameters)
	entityname = entities[1]
	parameter = parameters[1]
	merge!(
		get!(iodb["Link"], entityname, Dict()),
		Dict(
			"efficiency" => 1,
			"marginal_cost" => 0.0,
			"p_min_pu" => -1,
			"p_nom" => parameter["capacity"]
		)
	)
end

function map_node(iodb,entities,parameters)
	# can be a node, load or source
	entityname = entities[1]
	parameter = parameters[1]
	get!(iodb["Bus"], entityname, Dict())
	merge!(
		get!(iodb["Load"], "load "*entityname, Dict()),
		Dict(
			"bus" => entityname,
			"p_set" => parameter["demand_profile"]
		)
	)
	merge!(
		get!(iodb["Generator"], "generator "*entityname, Dict()),
		Dict(
			"bus" => entityname,
			"marginal_cost" => parameter["commodity_price"],
			"p_nom" => parameter["upper_limit"]
		)
	)
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
	parameter = parameters[1]
	merge!(
		get!(iodb["Link"], entityname, Dict()),
		Dict(
			"efficiency" => parameter["efficiency"]
		)
	)
end

function map_node__to_unit(iodb,entities,parameters)
	entityname = entities[2]
	parameter = parameters[1]
	merge!(
		get!(iodb["Link"], entityname, Dict()),
		Dict(
			"efficiency" => parameter["conversion_coefficient"],
			"marginal_cost" => parameter["other_operational_cost"],
			"p_nom" => parameter["capacity_per_unit"]
		)
	)
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
	entityname = entities[2]
	busname = entities[3]
	parameter = parameters[1]
	merge!(
		get!(iodb["Link"], entityname, Dict()),
		Dict(
			"bus1" => busname,
			"marginal_cost" => parameter["other_operational_cost"],
			"p_nom" => parameter["capacity_per_unit"]
		)
	)
end

function map_node__link__node(iodb,entities,parameters)
	entityname = entities[1]
	busname0 = entities[2]
	busname1 = entities[4]
	merge!(
		get!(iodb["Link"], entityname, Dict()),
		Dict(
			"bus0" => busname0,
			"bus1" => busname1
		)
	)
end

function map_set__node__temporality(iodb,entities,parameters)
end

function map_set__node__unit(iodb,entities,parameters)
	entityname = entities[3]
	busname = entities[2]
	merge!(
		get!(iodb["Link"], entityname, Dict()),
		Dict(
			"bus1" => busname
		)
	)
end