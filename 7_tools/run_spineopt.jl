import SpineOpt
import SpineInterface
import JSON

path = @__DIR__
input = ARGS[1]#joinpath(path, "input_spineopt.json")#
output = ARGS[2]#joinpath(path, "output_spineopt.json")#

inputdata = open(input, "r") do f
	dicttxt = read(f,String) # file information to string
	return JSON.parse(dicttxt) # parse and transform data
end
#input data needs to be converted to Symbols instead of strings in a lot of places

db_url = "sqlite://"
SpineInterface.close_connection(db_url)
SpineInterface.open_connection(db_url)
SpineInterface.import_data(db_url, inputdata, "")

m = SpineOpt.run_spineopt(db_url)

#=
m = run_spineopt(
    ARGS...;
    upgrade=true,
    mip_solver=nothing,
    lp_solver=nothing,
    add_user_variables=m -> nothing,
    add_constraints=m -> nothing,
    update_constraints=m -> nothing,
    log_level=3,
    optimize=true,
    update_names=false,
    alternative="",
    write_as_roll=0,
    use_direct_model=false,
    filters=Dict("tool" => "object_activity_control"),
    log_file_path=nothing,
    resume_file_path=nothing
)
=#

open(output, "w") do f
    JSON.print(f, m, 4)
end