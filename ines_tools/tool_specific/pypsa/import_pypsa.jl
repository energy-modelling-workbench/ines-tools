import JSON
#import SpineInterface

#path = dirname(@__DIR__)
#componenttooltemplate = ARGS[1] # use template to verify valid fields?
#map = ARGS[2] # use map to make a general structure like the exporters?
input = ARGS[1]#joinpath(path, "1_external_data", "elec_s_37.json")#
output = ARGS[2]#joinpath(path, "3_select_unprocessed_data", "fulldetaildata.json")#

pypsadict = JSON.parsefile(input)
iodb = Dict(
    "entities" => [],
    "parameter_values" => [],
    "alternatives" => [["PyPSA", ""]]
)

#Bus => node
for (name,parameters) in pypsadict["Bus"]
    push!(iodb["entities"], ["node", "bus "*name, [], nothing])
end

#Generator => node
for (name,parameters) in pypsadict["Generator"]
    push!(iodb["entities"], ["node", "gen "*name, [], nothing])
    push!(iodb["parameter_values"], ["node", "gen "*name, "commodity_price", parameters["marginal_cost"], "PyPSA"])
    push!(iodb["parameter_values"], ["node", "load "*name, "capacity_per_unit", parameters["p_nom"], "PyPSA"])
end

#Load => node
for (name,parameters) in pypsadict["Load"]
    push!(iodb["entities"], ["node", "load "*name, [], nothing])
    push!(iodb["parameter_values"], ["node", "load "*name, "demand_profile", parameters["p_set"], "PyPSA"])
end

#Link => link or node
for (name,parameters) in pypsadict["Link"]
    if parameters["efficiency"]==1 && parameters["marginal_cost"]==0.0 && parameters["p_min_pu"]==-1
        push!(iodb["entities"],["link", "link "*name, [], nothing])
        push!(iodb["entities"],["node__link__node", parameters["bus0"]*"_"*name*"_"*parameters["bus1"], [parameters["bus0"], name, parameters["bus1"]], nothing])
        push!(iodb["parameter_values"], ["link", "link "*name, "capacity", parameters["p_nom"], "PyPSA"])
        push!(iodb["parameter_values"], ["link", "link "*name, "efficiency", 1.0, "PyPSA"])
    else
        push!(iodb["entities"],["node__to_unit", parameters["bus0"]*"_"*name, ["bus0",name], nothing])
        push!(iodb["entities"],["unit", "link "*name, [], nothing])
        push!(iodb["entities"],["unit__to_node", name*"_"*parameters["bus1"], [name,"bus1"], nothing])
        push!(iodb["parameter_values"], ["unit", "link "*name, "efficiency", parameters["efficiency"], "PyPSA"])
        push!(iodb["parameter_values"], ["unit__to_node", ["link "*name, parameters["bus1"]], "other_operational_cost", parameters["marginal_cost"], "PyPSA"])
        push!(iodb["parameter_values"], ["unit__to_node", ["link "*name, parameters["bus1"]], "capacity_per_unit", parameters["p_nom"], "PyPSA"])
    end
end

#SpineInterface.import_data(output, iodb, "import data from PyPSA")
open(output, "w") do f
    JSON.print(f, iodb, 4)
end