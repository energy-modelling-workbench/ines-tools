using SpineInterface

input=ARGS[1]
output=ARGS[2]

using_spinedb(input)

value_capacity=capacity(CHP=CHP("Zeb"))

import_data(
	output,
	"load capacity value";
	relationship_parameters=[["unit__to_node","unit_capacity"]], 
	relationship_parameter_values=[["unit__to_node", ["power_plant_a", "electricity_node"], "unit_capacity", value_capacity]]
)