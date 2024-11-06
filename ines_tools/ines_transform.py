import spinedb_api as api
from spinedb_api import DatabaseMapping, TimeSeries
from sqlalchemy.exc import DBAPIError
from spinedb_api.exception import NothingToCommit
import typing
from sys import exit


def assert_success(result, warn=False):
    error = result[-1]
    if error and warn:
        print("Warning: " + error)
    elif error:
        raise RuntimeError(error)
    return result[0] if len(result) == 2 else result[:-1]


def copy_entities(
    source_db: DatabaseMapping, target_db: DatabaseMapping, copy_entities: typing.Dict
) -> DatabaseMapping:
    # Copy entities
    alternatives = source_db.get_alternative_items()
    for source_class, targets in copy_entities.items():
        # Elevate target_classes without additional definitions to lists
        if isinstance(targets, (str, dict)):
            targets = [targets]
        for target in targets:
            target_def = []
            filter_parameter = None
            if isinstance(target, str):
                target_class = target
            else:
                if len(target) > 1:  # Ugly way to check if there was a list or multiple dicts instead of just single dict
                    print("Wrong format in the entity copy definition: " + target)
                # target_class, target_def = next(iter(target.items()))  # alternative to next two lines
                for target_class, target_def in target.items():
                    pass  # Based on the previous check, there should be only one dict
                if isinstance(target_def[-1], dict) or isinstance(target_def[-1], str):
                    filter_parameter = target_def.pop(-1)
            entities = source_db.get_entity_items(entity_class_name=source_class)
            ea_items = source_db.get_entity_alternative_items(entity_class_name=source_class)
            error = None
            error_ea = None
            param_flag = True
            if filter_parameter:
                if isinstance(filter_parameter, dict):
                    for target_feature, target_method in filter_parameter.items():
                        param_values = source_db.get_parameter_value_items(
                            entity_class_name=source_class,
                            parameter_definition_name=target_feature,
                        )
                elif isinstance(filter_parameter, str):
                    param_values = source_db.get_parameter_value_items(
                        entity_class_name=source_class,
                        parameter_definition_name=filter_parameter,
                    )
            for entity in entities:
                print(entity["name"])
                if filter_parameter:
                    if isinstance(filter_parameter, dict):
                        param_flag = False
                        for param_value in param_values:
                            for target_feature, target_method in filter_parameter.items():
                                if param_value["parameter_definition_name"] == target_feature:
                                    if param_value["entity_name"] in entity["name"]:
                                        if isinstance(target_method,list):
                                                param_flag = any(
                                                    x["parsed_value"] in target_method for x in param_values
                                                )
                                        if isinstance(target_method,str):
                                            param_flag = any(
                                                x["parsed_value"] == target_method for x in param_values
                                            )
                    elif isinstance(filter_parameter, str):
                        param_flag = False
                        if param_values:
                            if param_values["entity_name"] == entity["name"]:
                                param_flag = True
                if param_flag:
                    entity_byname_list = []
                    if not target_def:  # No definition, so straight copy
                        entity_byname_list.append(entity["name"])
                    else:
                        for target_positions in target_def:
                            entity_bynames = []
                            for target_position in target_positions:
                                entity_bynames.append(
                                    entity["entity_byname"][int(target_position) - 1]
                                )
                            entity_byname_list.append("__".join(entity_bynames))
                    assert_success(target_db.add_entity_item(
                        entity_class_name=target_class,
                        entity_byname=tuple(entity_byname_list),
                    ), warn=True)
                    if "__" not in source_class and "__" not in target_class:
                        for ea_item in ea_items:
                            if ea_item["entity_byname"] == entity["entity_byname"]:
                                assert_success(target_db.add_update_entity_alternative_item(
                                    entity_class_name=target_class,
                                    entity_byname=tuple(entity_byname_list),
                                    alternative_name=ea_item["alternative_name"],
                                    active=ea_item["active"],
                                ))
                    elif "__" in source_class and "__" not in target_class:
                        for alt in alternatives:
                            ea_items_temp = []
                            for k, source_class_element in enumerate(
                                source_class.split("__")
                            ):
                                ea_item = source_db.get_entity_alternative_item(
                                    entity_class_name=source_class_element,
                                    entity_byname=(entity["entity_byname"][k], ),
                                    alternative_name=alt["name"]
                                )
                                if ea_item:
                                    ea_items_temp.append(ea_item)
                            if ea_items_temp:
                                if all(ea_item["active"] is True for ea_item in ea_items_temp):
                                    assert_success(target_db.add_update_entity_alternative_item(
                                        entity_class_name=target_class,
                                        entity_byname=entity_byname_list,
                                        alternative_name=alt["name"],
                                        active=True,
                                    ))
                                elif any(ea_item["active"] is False for ea_item in ea_items):
                                    assert_success(target_db.add_update_entity_alternative_item(
                                        entity_class_name=target_class,
                                        entity_byname=entity_byname_list,
                                        alternative_name=alt["name"],
                                        active=False,
                                    ))
    try:
        target_db.commit_session("Added entities")
    except NothingToCommit:
        pass
    except DBAPIError as e:
        print("failed to commit entities and entity_alternatives")
    return target_db


def transform_parameters(
    source_db: DatabaseMapping,
    target_db: DatabaseMapping,
    parameter_transforms,
    ts_to_map=False,
):
    for source_entity_class, sec_def in parameter_transforms.items():
        for target_entity_class, tec_def in sec_def.items():
            for source_param, target_param_def in tec_def.items():
                parameters = source_db.get_parameter_value_items(
                    entity_class_name=source_entity_class,
                    parameter_definition_name=source_param,
                )
                for parameter in parameters:
                    (
                        target_param_value,
                        type_,
                        entity_byname_tuple,
                    ) = process_parameter_transforms(
                        parameter["entity_byname"],
                        parameter["value"],
                        parameter["type"],
                        target_param_def,
                        ts_to_map,
                    )
                    for (
                        target_parameter_name,
                        target_value,
                    ) in target_param_value.items():
                        #check that entity exists
                        target_ent = target_db.get_entity_item(
                            entity_class_name=target_entity_class,
                            entity_byname=entity_byname_tuple,
                        )
                        if target_ent:
                            # print(target_entity_class + ', ' + target_parameter_name)
                            assert_success(target_db.add_parameter_value_item(
                                check=True,
                                entity_class_name=target_entity_class,
                                parameter_definition_name=target_parameter_name,
                                entity_byname=entity_byname_tuple,
                                alternative_name=parameter["alternative_name"],
                                value=target_value,
                                type=type_,
                            ))
    try:
        target_db.commit_session("Added parameters")
    except NothingToCommit:
        pass
    except DBAPIError as e:
        print("failed to commit parameters")
    return target_db


def transform_parameters_use_default(
    source_db: DatabaseMapping,
    target_db: DatabaseMapping,
    parameter_transforms,
    default_alternative="base",
    ts_to_map=False,
):
    for source_entity_class, sec_def in parameter_transforms.items():
        for target_entity_class, tec_def in sec_def.items():
            for source_param, target_param_def in tec_def.items():
                param_def_item = source_db.get_parameter_definition_item(
                    entity_class_name=source_entity_class, name=source_param
                )
                for source_entity in source_db.get_entity_items(
                    entity_class_name=source_entity_class
                ):
                    flag_base_alt = False
                    for parameter in source_db.get_parameter_value_items(
                        entity_class_name=source_entity_class,
                        parameter_definition_name=source_param,
                        entity_name=source_entity["name"],
                    ):
                        if parameter["alternative_name"] == default_alternative:
                            flag_base_alt = True
                        (
                            target_param_value,
                            type_,
                            entity_byname_tuple,
                        ) = process_parameter_transforms(
                            parameter["entity_byname"],
                            parameter["value"],
                            parameter["type"],
                            target_param_def,
                            ts_to_map,
                        )
                        for (
                            target_parameter_name,
                            target_value,
                        ) in target_param_value.items():
                            assert_success(target_db.add_parameter_value_item(
                                check=True,
                                entity_class_name=target_entity_class,
                                parameter_definition_name=target_parameter_name,
                                entity_byname=entity_byname_tuple,
                                alternative_name=parameter["alternative_name"],
                                value=target_value,
                                type=type_,
                            ))
                    if not flag_base_alt:
                        (
                            target_param_value,
                            type_,
                            entity_byname_tuple,
                        ) = process_parameter_transforms(
                            source_entity["entity_byname"],
                            param_def_item["default_value"],
                            param_def_item["default_type"],
                            target_param_def,
                            ts_to_map,
                        )
                        for (
                            target_parameter_name,
                            target_value,
                        ) in target_param_value.items():
                            if (
                                not type_ == float
                                and api.from_database(target_value, type_) != 0
                            ):  # Ignore if the default value is zero (this could be made optional if needed)
                                assert_success(target_db.add_parameter_value_item(
                                    check=True,
                                    entity_class_name=target_entity_class,
                                    parameter_definition_name=target_parameter_name,
                                    entity_byname=entity_byname_tuple,
                                    alternative_name=default_alternative,
                                    value=target_value,
                                    type=type_,
                                ))

    return target_db

def transform_parameters_entity_from_parameter(        
    source_db: DatabaseMapping,
    target_db: DatabaseMapping,
    parameter_transforms: dict,
    ts_to_map=False,
):
    """
    Transforms parameters from source database entity to target database entity.
    The target entity name is gotten from a parameter of the source entity 
    instead of being the same entity name. 

    Example:
    parameter_transforms = {
        "Store":{ 
            "node":{
                "bus":{
                    'capital_cost': 'storage_investment_cost',
                    'e_max_pu': 'storage_state_upper_limit',
                }
            }
        }  
    }
    Adds parameters from the source "Store" class entities to the target "node" class entities.
    The target entity name is the value of source "Store" class parameter "bus".
    Dict keys are source parameter names and dict values are target parameter names.
    
    Args:
        source_db (DatabaseMapping): Source database mapping
        target_db (DatabaseMapping): Target database mapping
        parameter_transforms (dict(dict(dict(dict(str))))): Transform information
        ts_to_map (bool): Flag to change timeseries to maps

    Returns:
        target_db: (DatabaseMapping)
    """
    for source_entity_class, sec_def in parameter_transforms.items():
        for target_entity_class, parameter_entity in sec_def.items():
            for parameter_entity_name, tec_def in parameter_entity.items():
                source_entities = source_db.get_entity_items(entity_class_name=source_entity_class) 
                entity_parameters = source_db.get_parameter_value_items(
                    entity_class_name=source_entity_class,
                    parameter_definition_name=parameter_entity_name,
                )
                for source_param, target_param_def in tec_def.items():
                    parameters = source_db.get_parameter_value_items(
                                    entity_class_name=source_entity_class,
                                    parameter_definition_name=source_param,
                                )
                    for entity in source_entities:
                        #get the new entity name
                        for entity_parameter in entity_parameters:
                            if entity_parameter["entity_name"] == entity["name"]:
                                target_entity_name = api.from_database(entity_parameter["value"],entity_parameter["type"])
                        #transform parameters
                        for parameter in parameters:
                            if parameter["entity_name"] == entity["name"]:
                                (
                                    target_param_value,
                                    type_,
                                    entity_byname_tuple,
                                ) = process_parameter_transforms(
                                    parameter["entity_byname"],
                                    parameter["value"],
                                    parameter["type"],
                                    target_param_def,
                                    ts_to_map,
                                )
                                for (
                                    target_parameter_name,
                                    target_value,
                                ) in target_param_value.items():
                                    # print(target_entity_class + ', ' + target_parameter_name)
                                    assert_success(target_db.add_parameter_value_item(
                                        check=True,
                                        entity_class_name=target_entity_class,
                                        parameter_definition_name=target_parameter_name,
                                        entity_byname=(target_entity_name,),
                                        alternative_name=parameter["alternative_name"],
                                        value=target_value,
                                        type=type_,
                                    ))
    try:
        target_db.commit_session("Added parameters")
    except NothingToCommit:
        pass
    except DBAPIError as e:
        print("failed to commit parameters")
    return target_db
    

def process_parameter_transforms(
    entity_byname_orig, p_value, p_type, target_param_def, ts_to_map
):
    target_param_value = {}
    target_multiplier = None
    target_positions = []
    if isinstance(target_param_def, list):
        target_param = target_param_def[0]
        if len(target_param_def) > 1:
            target_multiplier = float(target_param_def[1])
            if target_multiplier == 1.0:
                target_multiplier = None
            if len(target_param_def) > 2:
                target_positions = target_param_def[2]
    else:
        target_param = target_param_def

    data = api.from_database(p_value, p_type)
    if data is None:
        exit(
            "Data without value for parameter "
            + target_param_def[0]
            + ". Could be parameter default value set to none."
        )
    if isinstance(data, float) and target_multiplier is not None:
        data = data * target_multiplier
    else:
        if target_multiplier:
            if isinstance(data, TimeSeries):
                data.values = data.values * target_multiplier
            elif len(target_param_def) < 4:
                data.values = [i * target_multiplier for i in data.values]
            else:
                collect_data_values = []
                collect_data_indexes = []
                for first_inside_dim in data.values:
                    collect_data_values.extend(first_inside_dim.values)
                    collect_data_indexes.extend(first_inside_dim.indexes)
                data.values = [i * target_multiplier for i in collect_data_values]
                data.indexes = collect_data_indexes
        if ts_to_map:
            if isinstance(data, TimeSeries):
                data = api.Map(
                    [str(x) for x in data.indexes],
                    data.values,
                    index_name=data.index_name,
                )
                # data = api.convert_containers_to_maps(data)
    value, type_ = api.to_database(data)
    target_param_value = {target_param: value}

    if (
        isinstance(target_param_def, str) or len(target_param_def) < 3
    ):  # direct name copy
        entity_byname_tuple = entity_byname_orig
    else:
        entity_byname_list = []
        for target_positions in target_param_def[2]:
            entity_bynames = []
            for target_position in target_positions:
                entity_bynames.append(
                    entity_byname_orig[int(target_position) - 1]
                )
            entity_byname_list.append("__".join(entity_bynames))
        entity_byname_tuple = tuple(entity_byname_list)

    return target_param_value, type_, entity_byname_tuple


def process_methods(source_db, target_db, parameter_methods):
    for source_entity_class, sec_values in parameter_methods.items():
        for target_entity_class, tec_values in sec_values.items():
            for source_feature, f_values in tec_values.items():
                source_entities = source_db.get_entity_items(entity_class_name=source_entity_class) 
                parameter_values = source_db.get_parameter_value_items(
                                    parameter_definition_name=source_feature,
                                    entity_class_name= source_entity_class)
                for source_entity in source_entities:
                    for parameter in parameter_values:
                        if parameter["entity_name"] == source_entity["name"]:
                            (
                                specific_parameters,
                                entity_byname_list,
                            ) = process_parameter_methods(
                                source_entity, parameter, f_values
                            )
                            for (
                                target_parameter_name,
                                target_value,
                            ) in specific_parameters.items():
                                #print(target_entity_class + ', ' + target_parameter_name)
                                assert_success(target_db.add_item(
                                    "parameter_value",
                                    check=True,
                                    entity_class_name=target_entity_class,
                                    parameter_definition_name=target_parameter_name,
                                    entity_byname=entity_byname_list,
                                    alternative_name=parameter["alternative_name"],
                                    value=target_value,
                                    type="str",
                                ))
    try:
        target_db.commit_session("Process methods")
    except NothingToCommit:
        pass
    except DBAPIError as e:
        print("failed to commit process methods")
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
        # else:
        #    print("feature '" + source_feature_name + "' of the method '" + source_method_name + "' missing for entity: " + parameter_["entity_name"])

    entity_byname_list = []
    if target:
        if isinstance(target_method_def, list):
            for dimension in target_method_def[1]:
                if source_entity["element_name_list"]:
                    entity_byname_list.append(
                        source_entity["element_name_list"][int(dimension) - 1]
                    )
                else:
                    for element in source_entity["entity_byname"]:
                        entity_byname_list.append(element)
        else:
            for element in source_entity["entity_byname"]:
                entity_byname_list.append(element)

    return target, entity_byname_list


def copy_entities_to_parameters(source_db, target_db, entity_to_parameters):
    for source_entity_class, target in entity_to_parameters.items():
        for target_entity_class, target_parameter in target.items():
            for target_parameter_name, target_parameter_def in target_parameter.items():
                for entity in source_db.get_items(
                    "entity", entity_class_name=source_entity_class
                ):
                    for k, source_class_element in enumerate(
                        source_entity_class.split("__")
                    ):
                        for ea in source_db.get_entity_alternative_items(
                            entity_class_name=source_class_element,
                            entity_name=entity["entity_byname"][k],
                        ):
                            entity_byname_list = []
                            for target_positions in target_parameter_def[2]:
                                entity_bynames = []
                                for target_position in target_positions:
                                    if entity["element_name_list"]:
                                        entity_bynames.append(
                                            entity["element_name_list"][
                                                int(target_position) - 1
                                            ]
                                        )
                                    else:
                                        entity_bynames.append(entity["name"])
                                entity_byname_list.append("__".join(entity_bynames))
                            entity_byname_tuple = tuple(entity_byname_list)

                            if target_parameter_def[0] == "entity_name":
                                if target_parameter_def[0] == "array":
                                    value_in_chosen_type = api.Array([entity["name"]])
                                else:
                                    value_in_chosen_type = entity["name"]
                                val, type_ = api.to_database(value_in_chosen_type)
                                assert_success(target_db.add_update_parameter_value_item(
                                    entity_class_name=target_entity_class,
                                    parameter_definition_name=target_parameter_name,
                                    entity_byname=entity_byname_tuple,
                                    value=val,
                                    type=type_,
                                    alternative_name=ea["alternative_name"],
                                ))
                            elif target_parameter_def[0] == "new_value":
                                val, type_ = api.to_database(target_parameter_def[1])
                                assert_success(target_db.add_update_parameter_value_item(
                                    entity_class_name=target_entity_class,
                                    parameter_definition_name=target_parameter_name,
                                    entity_byname=entity_byname_tuple,
                                    value=val,
                                    type=type_,
                                    alternative_name=ea["alternative_name"],
                                ))
                            else:
                                exit(
                                    "Inappropriate choice in entities_to_parameters.yaml definition file: "
                                    + entity["name"]
                                )
    return target_db


def transform_parameters_to_relationship_entities(source_db: DatabaseMapping, target_db: DatabaseMapping, parameter_to_relationship: dict,):
    """
    Creates a relationship from an entity and its parameter_value.
    Additionally moves parameters to this relationship.

    parameter_to_relationship = {
        source_entity_class:{
            target_entity_class:{
                parameter_target_entity_class: { 
                    source_parameter: {                #Parameter that gives the other participants of the relationship
                        'position': 1 or 2 or tuple    #Position of the parameter in the relationship, *required
                        'parameters':{                 #Additional parameters *optional
                            additional_source_parameter_1: additional_target_parameter_1,
                            additional_source_parameter_2: additional_target_parameter_2
                    }  
                }
            }    
        }
    } 
    position = 1 -> relationship: source_parameter_value__source_entity
    position = 2 -> relationship: source_entity__source_parameter_value

    If creating relationship with multiple members from multiple parameters,
    parameter_target_entity_class, source_parameter and 'position' are tuples
    where 'position' points the positions of the parameters in the relationship
    position = (1,3) -> source_parameter_value_1__source_entity__source_parameter_value_2
 
    Example:
    parameter_to_relationship : {
        'Generator':{
            'unit':{
                'to_node':{
                    'bus': {
                        'position': 2,
                        'parameters':{
                            'capital_cost': 'investment_cost',
                            'marginal_cost': 'other_operational_cost',
                        }
                    }
                }
        'Line': {
            'link':{
                ('node','node'):{
                    ('bus0','bus1'):{
                        'position': (1,3)
                    },
                }
            }
        }
    }

    Args:
        source_db (DatabaseMapping): source database mapping
        target_db (DatabaseMapping): target database mapping
        parameter_to_relationship (dict(dict(dict(dict(dict()))))): Transfrom information

    Returns:
        target_db (DatabaseMapping)

    """
    for source_entity_class, target_entity_class in parameter_to_relationship.items():
        entities = source_db.get_entity_items(entity_class_name=source_entity_class)
        for target_entity_class_name, parameter_target_entity_class in target_entity_class.items():
            for parameter_target_entity_class_name, source_parameter in parameter_target_entity_class.items():
                for source_parameter_name, info in source_parameter.items():
                    if 'position' not in info.keys():
                        print("'position' is required for " + source_entity_class+", " + source_parameter_name)
                        exit(-1)
                    if isinstance(info['position'],tuple): # if more than two members in the relationship
                        if not(isinstance(source_parameter_name,tuple) and isinstance(parameter_target_entity_class_name,tuple)):
                            print("Either the parameter_target_entity_class, source_parameter and position are all tuples or none of them are")
                            exit(-1)
                        parameter_values = list()
                        for param_name in source_parameter_name:
                            parameter_values.extend(source_db.get_parameter_value_items(
                                parameter_definition_name=param_name,
                                entity_class_name= source_entity_class,
                                ))
                    else:
                        parameter_values = source_db.get_parameter_value_items(
                                parameter_definition_name=source_parameter_name,
                                entity_class_name= source_entity_class,
                                )
                    if 'parameters' in info.keys():
                        additional_parameter_values = list()
                        for additional_source_parameter_name, target_parameter_name in info['parameters'].items():
                            additional_parameter_values.extend(source_db.get_parameter_value_items(
                            entity_class_name=source_entity_class,
                            parameter_definition_name=additional_source_parameter_name,
                            ))
                    for entity in entities:
                        if isinstance(info['position'],tuple): # if more than two members in the relationship
                                parameter_value_list = []
                                for parameter in parameter_values:
                                    if parameter["entity_name"] == entity["name"]:
                                        parameter_value_list.append(api.from_database(parameter["value"], parameter["type"]))
                                target_class_list = list()
                                target_entity_byname_list=list()
                                for i in range(1,len(info['position'])+2):
                                    if i in info['position']:
                                        target_class_list.append(parameter_target_entity_class_name[info['position'].index(i)])
                                        target_entity_byname_list.append(parameter_value_list[info['position'].index(i)])
                                    else:
                                        target_class_list.append(target_entity_class_name)
                                        target_entity_byname_list.append(entity["name"])
                                target_class = "__".join(target_class_list)
                                target_entity_byname =tuple(target_entity_byname_list)
                        else: # two member relationship
                            for parameter in parameter_values:
                                if parameter["entity_name"] == entity["name"]:
                                    parameter_value = api.from_database(parameter["value"], parameter["type"]) 
                            print(entity['name'] + "_param_target")
                            if info['position'] == 2:
                                target_class = target_entity_class_name + "__" + parameter_target_entity_class_name
                                target_entity_byname = (entity["name"], parameter_value)
                            elif info['position'] == 1:
                                target_class = parameter_target_entity_class_name + "__" +  target_entity_class_name
                                target_entity_byname = (parameter_value, entity["name"])
                            else:
                                print("Inappropriate choice for relationship position: "
                                    + str(info['position']) + " for " + source_entity_class+", " + source_parameter_name
                                    + " choose from 1 or 2 ")
                                exit(-1)
                        assert_success(target_db.add_entity_item(
                            entity_class_name=target_class,
                            entity_byname=target_entity_byname
                        ), warn=True)  
                        print(entity['name'] + "_rel")
                        #add additional parameters to the relationship created
                        if 'parameters' in info.keys():
                            for additional_source_parameter_name, target_parameter_name in info['parameters'].items():
                                for additional_parameter in additional_parameter_values:
                                    if (additional_parameter["parameter_definition_name"] == additional_source_parameter_name and
                                        additional_parameter["entity_name"] == entity["name"]):
                                        (
                                            target_param_value,
                                            type_,
                                            entity_byname_tuple,
                                        ) = process_parameter_transforms(
                                            additional_parameter["entity_byname"],
                                            additional_parameter["value"],
                                            additional_parameter["type"],
                                            target_param_def = target_parameter_name,
                                            ts_to_map = True,
                                        )
                                        for (target_parameter_name,target_value) in target_param_value.items():
                                            assert_success(target_db.add_parameter_value_item(
                                                check=True,
                                                entity_class_name=target_class,
                                                parameter_definition_name=target_parameter_name,
                                                entity_byname=target_entity_byname,
                                                alternative_name=additional_parameter["alternative_name"],
                                                value=target_value,
                                                type=type_,
                                            ))
                                        print(entity['name'] + "_param_val")

    try:
        target_db.commit_session("Added relationships from parameters")
    except NothingToCommit:
        pass
    except DBAPIError as e:
        print("failed to add relationships from parameters")
    return target_db
    
def get_parameter_from_DB(db, param_name, alt_ent_class):
    parameter_ = db.get_parameter_value_item(
        parameter_definition_name=param_name,
        alternative_name=alt_ent_class[0],
        entity_byname=alt_ent_class[1],
        entity_class_name=alt_ent_class[2],
    )
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
    assert_success(db.add_item(
        "parameter_value",
        check=True,
        entity_class_name=alt_ent_class[2],
        parameter_definition_name=param_name,
        entity_byname=alt_ent_class[1],
        alternative_name=alt_ent_class[0],
        value=value_x,
        type=type_,
    ))
    return db
