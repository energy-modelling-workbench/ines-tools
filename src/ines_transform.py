import spinedb_api as api
from spinedb_api import DatabaseMapping

def copy_entities(source_db, target_db, copy_entities):
    ## Copy entities
    for source_class, targets in copy_entities.items():
        # Elevate target_classes without additional definitions to lists
        if isinstance(targets, str) or isinstance(targets, dict):
            targets = [targets]
        else:
            targets = targets
        for target in targets:
            if isinstance(target, str):
                target_class = target
                target_def = []
            else:
                for target_class, target_def in target.items():
                    if len(target) > 1:  # Ugly way to check if there was a list instead of just single dict
                        print("Too deep entity copy definition: " + target)
            for entity in source_db.get_entity_items(entity_class_name=source_class):
                error = None
                error_ea = None
                param_flag = True
                # If a fourth parameter is provided, check that the entity has the feature in the fourth parameter defined (otherwise it's not copied)
                if len(target_def) == 2:
                    try:
                        int(target_def[1])
                    except:
                        param_flag = False
                        if isinstance(target_def[1], dict):  # If the last item is a dict, it means that a specific method from the parameter_value_list must be chosen
                            for target_feature, target_method in target_def[1].items():
                                param_values = source_db.get_parameter_value_items(entity_class_name=source_class,
                                                                                   parameter_definition_name=target_feature,
                                                                                   entity_name=entity["name"])
                                for param_value in param_values:
                                    if api.from_database(param_value["value"], param_value["type"]) == target_method:
                                        param_flag = True
                                        break  # Enough if one alternative has the method set
                        else:  # If the last item is not a dict, then that feature must have one of the methods selected.
                            param_values = source_db.get_parameter_value_items(entity_class_name=source_class,
                                                                               parameter_definition_name=target_def[1],
                                                                               entity_name=entity["name"])
                            if param_values:
                                param_flag = True
                if param_flag:
                    new_entity_name_list = []
                    if len(target_def) == 0:  # direct copy
                        new_entity_name_list.append(entity["name"])
                    else:
                        if len(target_def) > 1:  # With multiple target_def list members, we need to find out what it contains
                            try:
                                int(target_def[1])  # check if the target_def list second entry is a positive number (if not, there is a string filter and remove the filter)
                            except:
                                target_positions = target_def[0]
                            else:
                                target_positions = target_def
                        else:
                            target_positions = target_def  # With one list member, it has to be a position number
                        if entity["element_name_list"]:  # source is n dimensional
                            for j in range(len(target_positions)):
                                new_entity_name_list.append(entity["element_name_list"][int(target_positions[j]) - 1])
                        else:  # source is 1 dimensional
                            for j in range(len(target_positions)):
                                new_entity_name_list.append(entity["name"])
                    if len(new_entity_name_list) > 1:
                        added, error = target_db.add_entity_item(entity_class_name=target_class,
                                                                 element_name_list=new_entity_name_list)
                    else:
                        added, error = target_db.add_entity_item(entity_class_name=target_class,
                                                                 name=new_entity_name_list[0])
                    # added2, error2 = target_db.add_entity_alternative_item(alternative_name="Base", entity_class_name=target_class, entity_byname=(new_entity_name, ), active=False)
                    for ea in source_db.get_entity_alternative_items("entity_alternative",
                                                                     entity_class_name=entity["entity_class_name"],
                                                                     entity_name=entity["name"]):
                        added_ea, error_ea = target_db.add_entity_alternative_item(entity_class_name=target_class,
                                                                                   entity_byname=new_entity_name_list,
                                                                                   alternative_name=ea[
                                                                                       "alternative_name"],
                                                                                   active=ea["active"])
                if error:
                    print("Copying entities: " + error)
                if error_ea:
                    print("Copying entity_alternatives: " + error_ea)
    try:
        target_db.commit_session("Added entities")
    except:
        print("failed to commit entities and entity_alternatives")
    return target_db


def transform_parameters(source_db, target_db, parameter_transforms, ts_to_map=False):
    for source_entity_class, sec_def in parameter_transforms.items():
        for target_entity_class, tec_def in sec_def.items():
            for source_param, target_param_def in tec_def.items():
                for source_entity in source_db.get_entity_items(entity_class_name=source_entity_class):
                    for parameter in source_db.get_parameter_value_items(entity_class_name=source_entity_class,
                                                                     parameter_definition_name=source_param,
                                                                     entity_name=source_entity["name"]):
                        target_param_value, type_, entity_byname_list \
                            = process_parameter_transforms(source_entity, parameter, target_param_def, ts_to_map)
                        for target_parameter_name, target_value in target_param_value.items():
                            #print(target_entity_class + ', ' + target_parameter_name)
                            added, error = target_db.add_item("parameter_value", check=True,
                                           entity_class_name=target_entity_class,
                                           parameter_definition_name=target_parameter_name,
                                           entity_byname=tuple(entity_byname_list),
                                           alternative_name=parameter["alternative_name"],
                                           value=target_value,
                                           type=type_)
                            if error:
                                print("transform parameters error: " + error)
    return target_db


def process_parameter_transforms(source_entity, parameter, target_param_def, ts_to_map):
    target_param_value = {}
    target_multiplier = None
    target_positions = []
    if isinstance(target_param_def, list):
        target_param = target_param_def[0]
        if len(target_param_def) > 1:
            target_multiplier = float(target_param_def[1])
            if len(target_param_def) > 2:
                target_positions = target_param_def[2]
    else:
        target_param = target_param_def

    data = api.from_database(parameter["value"], parameter["type"])
    try:
        int(data)
        if target_multiplier:
            data = data * target_multiplier
    except:
        if target_multiplier:
            if data.VALUE_TYPE == 'time series':
                data.values = data.values * target_multiplier
            else:
                data.values = [i * target_multiplier for i in data.values]
        if ts_to_map:
            if data.VALUE_TYPE == 'time series':
                data = api.Map([str(x) for x in data.indexes], data.values, index_name=data.index_name)
                # data = api.convert_containers_to_maps(data)
    value, type_ = api.to_database(data)
    target_param_value = {target_param: value}

    entity_byname_list = []
    if target_positions:
        for dimension in target_positions:
            if source_entity["element_name_list"]:
                entity_byname_list.append(source_entity["element_name_list"][int(dimension) - 1])
            else:
                for element in source_entity["entity_byname"]:
                    entity_byname_list.append(element)
    else:
        for element in source_entity["entity_byname"]:
            entity_byname_list.append(element)

    return target_param_value, type_, entity_byname_list


def process_methods(source_db, target_db, parameter_methods):
    for source_entity_class, sec_values in parameter_methods.items():
        for target_entity_class, tec_values in sec_values.items():
            for source_feature, f_values in tec_values.items():
                for source_entity in source_db.get_entity_items(entity_class_name=source_entity_class):
                    for parameter in source_db.get_parameter_value_items(parameter_definition_name=source_feature,
                                                                         entity_name=source_entity["name"]):
                        specific_parameters, type_, entity_byname_list = process_parameter_methods(source_entity, parameter, f_values)
                        for target_parameter_name, target_value in specific_parameters.items():
                            #print(target_entity_class + ', ' + target_parameter_name)
                            added, error = target_db.add_item("parameter_value", check=True,
                                           entity_class_name=target_entity_class,
                                           parameter_definition_name=target_parameter_name,
                                           entity_byname=tuple(entity_byname_list),
                                           alternative_name=parameter["alternative_name"],
                                           value=target_value,
                                           type=type_)
                            if error:
                                print("process methods error: " + error)
    return target_db

def process_parameter_methods(source_entity, parameter, f_values):
    target = {}
    method_of_source_entity = api.from_database(parameter["value"], parameter["type"])
    for source_method_name, target_feature_method in f_values.items():
        if source_method_name == method_of_source_entity:
            for target_feature, target_method_def in target_feature_method.items():
                if isinstance(target_method_def, list):
                    target_method = target_method_def[0]
                    data, type_ = api.to_database(target_method)
                    target.update({target_feature: data})
                else:
                    data, type_ = api.to_database(target_method_def)
                    target.update({target_feature: data})
        #else:
        #    print("feature '" + source_feature_name + "' of the method '" + source_method_name + "' missing for entity: " + parameter_["entity_name"])

    entity_byname_list = []
    if target:
        if isinstance(target_method_def, list):
            for dimension in target_method_def[1]:
                if source_entity["element_name_list"]:
                    entity_byname_list.append(source_entity["element_name_list"][int(dimension) - 1])
                else:
                    for element in source_entity["entity_byname"]:
                        entity_byname_list.append(element)
        else:
            for element in source_entity["entity_byname"]:
                entity_byname_list.append(element)

    return target, None, entity_byname_list


def copy_entities_to_parameters(source_db, target_db, entity_to_parameters):
    for source_entity_class, target in entity_to_parameters.items():
        for target_entity_class, target_parameter in target.items():
            for target_parameter_name, target_parameter_type in target_parameter.items():
                for entity in source_db.get_items("entity", entity_class_name=source_entity_class):
                    for ea in source_db.get_entity_alternative_items(entity_class_name=source_entity_class, entity_name=entity["name"]):
                        if target_parameter_type == "array":
                            value_in_chosen_type = api.Array([entity["name"]])
                        else:
                            value_in_chosen_type = [entity["name"]]
                        val, type_ = api.to_database(value_in_chosen_type)
                        added, error = target_db.add_parameter_value_item\
                            (entity_class_name=target_entity_class,
                             parameter_definition_name=target_parameter_name,
                             entity_byname=entity["entity_byname"],
                             value=val,
                             type=type_,
                             alternative_name=ea["alternative_name"]
                             )
                        if error:
                            print("copy entity to parameter error: " + error)
    return target_db


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


def add_item_to_DB(db, param_name, alt_ent_class, value, value_type=None):
    if value_type:
        if isinstance(value, api.Map):
            value._value_type = value_type
    value_x, type_ = api.to_database(value)
    added, error = db.add_item("parameter_value", check=True,
                                        entity_class_name=alt_ent_class[2],
                                        parameter_definition_name=param_name,
                                        entity_byname=alt_ent_class[1],
                                        alternative_name=alt_ent_class[0],
                                        value=value_x,
                                        type=type_)
    if error:
        print("error trying to add parameter " + param_name + ": " + error)
    return db
