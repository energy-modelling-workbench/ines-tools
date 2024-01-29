import spinedb_api as api
from spinedb_api import DatabaseMapping

url_db_in = "sqlite:///C:/Users/prokjt/Teknologian Tutkimuskeskus VTT/EU ESI Mopo - General/WP5 Cases CONFIDENTIAL/T5-2 certification process for components and models/generic_energy_data_specification.sqlite"
# sys.argv[1]
url_db_out = "sqlite:///C:/data/Toolbox_projects/generic_to_models/flextool_input_data.sqlite"
# sys.argv[2]

entity_copy = ["node", "node", [1]], \
              ["link", "connection", [1]], \
              ["unit", "unit", [1]], \
              ["unit__to_node", "unit__outputNode", [1, 2]], \
              ["node__to_unit", "unit__inputNode", [2, 1]], \
              ["node__link__node", "connection__node__node", [2, 1, 3]], \
              ["unit__to_node", "profile", [1]]


parameter_transforms = {"node": {"demand_profile": {"node": ["inflow", -1]},
                                 "penalty_upward": {"node": ["penalty_up"]},
                                 "penalty_downward": {"node": ["penalty_down"]},
                                 "upper_limit": {"node": ["existing"]},
                                 "commodity_price": {"commodity": ["price"]},
                                 "salvage_value": {"node": ["salvage_value"]},
                                 },
                        "unit": {"availability": {"unit": ["availability"]},
                                 "efficiency": {"unit": ["efficiency"]},
                                 "interest_rate": {"unit": ["interest_rate"]},
                                 "investment_cost": {"unit": ["invest_cost"]},
                                 "startup_cost": {"unit": ["startup_cost"]},
                                 "shutdown_cost": {"unit": ["shutdown_cost"]},
                                 "salvage_value": {"unit": ["salvage_value"]},
                                 },
                        "link": {"availability": {"connection": ["availability"]},
                                 "efficiency": {"connection": ["efficiency"]},
                                 "interest_rate": {"connection": ["interest_rate"]},
                                 "investment_cost": {"connection": ["invest_cost"]},
                                 "capacity": {"connection": ["existing"]},
                                 "lifetime": {"connection": ["lifetime"]},
                                 "salvage_value": {"connection": ["salvage_value"]},
                                 },
                        "unit__to_node": {"conversion_coefficient": {"unit__outputNode": ["coefficient"]},
                                          "other_operational_cost": {"unit__outputNode": ["other_operational_cost"]},
                                          "ramp_cost": {"unit__outputNode": ["ramp_cost"]},
                                          "ramp_limit_up": {"unit__outputNode": ["ramp_limit_up"]},
                                          "ramp_limit_down": {"unit__outputNode": ["ramp_limit_down"]},
                                          "profile_limit_upper": {"profile": ["profile"]}
                                         },
                        "node__to_unit": {"conversion_coefficient": {"unit__inputNode": ["coefficient"]},
                                          "other_operational_cost": {"unit__inputNode": ["other_operational_cost"]},
                                          "ramp_cost": {"unit__inputNode": ["ramp_cost"]},
                                          "ramp_limit_up": {"unit__inputNode": ["ramp_limit_up"]},
                                          "ramp_limit_down": {"unit__inputNode": ["ramp_limit_down"]}
                                         }
                        }


parameter_methods = {"node": {"node_type": {"node": {"balance": {"has_balance": "yes"},
                                                     "storage": {"has_balance": "yes",
                                                                 "has_storage": "yes"}}},
                               "demand_method": {"node": {"no_inflow": {"inflow_method": "no_inflow"},
                                                          "use_profile_directly": {"inflow_method": "use_original"},
                                                          "scale_to_annual": {"inflow_method": "scale_to_annual_flow"}}}},
                     "unit": {"conversion_method": {"unit": {"constant_efficiency": {"conversion_method": "constant_efficiency"},
                                                             "partial_load_efficiency": {"conversion_method": "min_load_efficiency"},
                                                             "coefficients_only": {"conversion_method": "none"}}},
                              "startup_method": {"unit": {"no_startup": {"startup_method": "no_startup"},
                                                          "linear": {"startup_method": "linear"},
                                                          "integer": {"startup_method": "binary"}}},
                             "investment_method": {"unit": {"not_allowed": {"invest_method": "not_allowed"},
                                                            "limit_total_capacity": {"invest_method": "invest_total"},
                                                            "no_limits": {"invest_method": "invest_no_limit"}}}},
                     "link": {"transfer_method": {"connection": {"no_losses_no_cost": {"transfer_method": "no_losses_no_variable_cost"},
                                                                 "regular_linear": {"transfer_method": "regular"},
                                                                 "exact_integer": {"transfer_method": "exact"},
                                                                 "only_cost": {"transfer_method": "variable_cost_only"}}},
                     "unit__to_node": {"ramp_method": {"unit__outputNode": {"no_constraint": {"ramp_method": "none"},
                                                                            "ramp_limit": {"ramp_method": "ramp_limit"},
                                                                            "ramp_cost": {"ramp_method": "ramp_cost"},
                                                                            "ramp_limit_and_cost": {"ramp_method": "both"}}},
                                       "profile_method": {"profile": {"upper_limit": {"profile_method": "upper_limit"}}}},
                     "node__to_unit": {"ramp_method": {"unit__outputNode": {"no_constraint": {"ramp_method": "none"},
                                                                            "ramp_limit": {"ramp_method": "ramp_limit"},
                                                                            "ramp_cost": {"ramp_method": "ramp_cost"},
                                                                            "ramp_limit_and_cost": {"ramp_method": "both"}}}}}}


def main():
    ## Convert method names to Spine DB format (by traversing the method tree)
    for source_entity_class, items1 in parameter_methods.items():
        for source_feature, items2 in items1.items():
            for target_entity_class, items3 in items2.items():
                for source_method, items4 in items3.items():
                    for target_method, items5 in items4.items():
                        data, type_ = api.to_database(items5)
                        parameter_methods[source_entity_class][source_feature][target_entity_class][source_method][target_method] = data

    with DatabaseMapping(url_db_in) as db_generic:
        with DatabaseMapping(url_db_out) as db_flextool:
            ## Empty the database
            db_flextool.purge_items('parameter_value')
            db_flextool.purge_items('entity')
            db_flextool.purge_items('alternative')
            db_flextool.commit_session("Purged stuff")
            db_flextool.refresh_session()
            ## Copy alternatives
            for alternative in db_generic.get_alternative_items():
                db_flextool.add_alternative_item(name=alternative.get('name'))
            db_flextool.commit_session("Added alternatives")
            ## Copy entities
            for i in entity_copy:
                for entity in db_generic.get_entity_items(class_name=i[0]):
                    if len(i[2]) == 1:
                        added, error = db_flextool.add_item("entity", class_name=i[1], name=entity["name"])
                    if len(i[2]) > 1:
                        new_element_name_list = []
                        counter = 0
                        for j in i[2]:
                            new_element_name_list.append(entity["element_name_list"][i[2][counter]-1])
                            counter = counter + 1
                        added, error = db_flextool.add_item("entity", class_name=i[1], element_name_list=(new_element_name_list))
                    if error:
                        print("139: " + error)
                    #for entity_alternative in db_generic.get_entity_alternative_items(entity_class_name=i[0], entity_byname=entity["byname"]):
                        #added, error = db_flextool.add_item("entity_alternative", class_name=i[1], entity_byname=entity["byname"], alternative=alternative["name"])
                        #if error: print(error)
            db_flextool.commit_session("Added entities")
            db_flextool.refresh_session()
            ## Copy numeric parameters
            db_flextool = process_parameters(db_generic, db_flextool, parameter_transforms, "transform")
            ## Copy method parameters
            db_flextool = process_parameters(db_generic, db_flextool, parameter_methods, "method")
            db_flextool = process_capacities(db_generic, db_flextool)
            try:
                db_flextool.commit_session("Added parameter values")
            except:
                print("commit parameters error")

def process_parameters(db_generic, db_flextool, parameter_, mode):
    for source_entity_class in parameter_:
        for source_feature in parameter_[source_entity_class]:
            for source_entity in db_generic.get_entity_items(class_name=source_entity_class):
                for parameter in db_generic.get_parameter_value_items(parameter_definition_name=source_feature,
                                                                      entity_name=source_entity["name"]):
                    specific_parameters = {}
                    type_ = None
                    if mode == "transform":
                        db_flextool, specific_parameters, type_, = process_parameter_transforms(db_flextool, source_entity_class, source_feature, source_entity, parameter)
                    elif mode == "method":
                        specific_parameters, type_, = process_parameter_methods(source_entity_class, source_feature, parameter)
                    for target_entity_class, target_parameter in specific_parameters.items():
                        for target_parameter_name, target_value in target_parameter.items():
                            #print(target_entity_class + ', ' + target_parameter_name)
                            added, error = db_flextool.add_item("parameter_value", check=True,
                                           entity_class_name=target_entity_class,
                                           parameter_definition_name=target_parameter_name,
                                           entity_byname=(source_entity["name"],),
                                           alternative_name=parameter["alternative_name"],
                                           value=target_value,
                                           type=type_)
                            if error:
                                print("161: " + error)
    return db_flextool


def process_parameter_transforms(db_flextool, source_entity_class, source_feature, source_entity, parameter_):
    specific = {}
    for target_entity_class, target_method in parameter_transforms[source_entity_class][source_feature].items():
        ## Very specific case to create connection classes
        if source_entity_class == "node" and target_entity_class == "commodity":
            foo = db_flextool.add_item("entity",
                                   class_name=target_entity_class,
                                   name=source_entity["name"])
            if foo[1] is not None:
                print("172: " + foo[1])
            foo = db_flextool.add_item("entity",
                                   class_name=target_entity_class + '__' + source_entity_class,
                                   name=source_entity["name"] + '__' + source_entity["name"])
            if foo[1] is not None:
                print("177: " + foo[1])
        data = api.from_database(parameter_["value"], parameter_["type"])
        try:
            int(data)
            if len(target_method) > 1:
                data = data * target_method[1]
        except:
            if len(target_method) > 1:
                if data.VALUE_TYPE == 'time series':
                    data.values = data.values * target_method[1]
                else:
                    data.values = [i * target_method[1] for i in data.values]
            if data.VALUE_TYPE == 'time series':
                data = api.Map([str(x) for x in data.indexes], data.values, index_name=data.index_name)
                # data = api.convert_containers_to_maps(data)
        value, type_ = api.to_database(data)
        specific = {target_entity_class: {target_method[0]: value}}
    return db_flextool, specific, type_


def process_parameter_methods(source_entity_class, source_feature, parameter_):
    specific = {}
    data = api.from_database(parameter_["value"], parameter_["type"])
    generic_to_specific = parameter_methods[source_entity_class][source_feature]
    for target_entity_class, source_target_method in generic_to_specific.items():
        for source_feature_name, target_method in source_target_method.items():
            if source_feature_name == str(parameter_["value"].decode('ascii')).strip('\"'):
                specific = {target_entity_class: target_method}
            else:
                print("method " + source_feature + ":" + source_feature_name + " missing")
    return specific, None


def process_capacities(db_generic, db_flextool):
    for unit_source in db_generic.get_entity_items(class_name="unit"):
        for alternative in db_generic.get_alternative_items():
            capacity = 0
            alt_ent_class = (alternative["name"], unit_source["byname"], "unit")
            existing_units = get_parameter_from_DB(db_generic, "existing", alt_ent_class)
            for unit__to_node_source in db_generic.get_entity_items(class_name="unit__to_node"):
                if unit_source["name"] == unit__to_node_source["byname"][0]:
                    #print(unit_source["name"] + ', ' + unit__to_node_source["name"] + ', ' + alternative["name"])
                    alt_ent_class = (alternative["name"], unit__to_node_source["byname"], "unit__to_node")
                    more_capacity = get_parameter_from_DB(db_generic, "capacity", alt_ent_class)
                    if more_capacity:
                        capacity = capacity + more_capacity
            if capacity == 0:
                for node__to_unit_source in db_generic.get_entity_items(class_name="node__to_unit"):
                    if unit_source["name"] == node__to_unit_source["byname"][0]:
                        alt_ent_class = (alternative["name"], node__to_unit_source["byname"], "node__to_unit")
                        more_capacity = get_parameter_from_DB(db_generic, "capacity", alt_ent_class)
                        if more_capacity:
                            capacity = capacity + more_capacity
            alt_ent_class = (alternative["name"], unit_source["byname"], "unit")
            error = None
            if capacity:
                db_flextool, error = add_item_to_DB(db_flextool, "existing", alt_ent_class, capacity)
            if existing_units:
                virtual_unit_size = capacity / existing_units
            else:
                virtual_unit_size = capacity
            if virtual_unit_size:
                db_flextool, error = add_item_to_DB(db_flextool, "virtual_unitsize", alt_ent_class, virtual_unit_size)
            if error:
                print("241" + error)
    return db_flextool


def get_parameter_from_DB(db, param_name, alt_ent_class):
    parameter_ = db.get_parameter_value_item(parameter_definition_name=param_name,
                                                  alternative_name=alt_ent_class[0],
                                                  entity_byname=alt_ent_class[1],
                                                  entity_class_name=alt_ent_class[2])
    if parameter_:
            param = api.from_database(parameter_["value"], parameter_["type"])
        return param
    else:
        return None

def add_item_to_DB(db, param_name, alt_ent_class, value):
    value_x, type_ = api.to_database(value)
    added, error = db.add_item("parameter_value", check=True,
                                        entity_class_name=alt_ent_class[2],
                                        parameter_definition_name=param_name,
                                        entity_byname=alt_ent_class[1],
                                        alternative_name=alt_ent_class[0],
                                        value=value_x,
                                        type=None)
    if error:
        print("266: " + error)
    return db

if __name__ == "__main__":
    main()

#def create_csv_timeseries(timeline, *timeseries):
#    csv_timeseries =
#    return csv_timeseries

