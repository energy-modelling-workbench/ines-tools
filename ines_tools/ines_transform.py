import spinedb_api as api
from spinedb_api import DatabaseMapping, TimeSeries
import typing


def assert_success(result):
    error = result[-1]
    if error:
        raise RuntimeError(error)
    return result[0] if len(result) == 2 else result[:-1]


def copy_entities(
    source_db: DatabaseMapping, target_db: DatabaseMapping, copy_entities: typing.Dict
) -> DatabaseMapping:
    # Copy entities
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
            for entity in source_db.get_entity_items(entity_class_name=source_class):
                error = None
                error_ea = None
                param_flag = True
                if filter_parameter:
                    # If a feature/method parameter is provided through a dict, check that the entity has the method defined (otherwise it's not copied)
                    if isinstance(filter_parameter, dict):
                        param_flag = False
                        for target_feature, target_method in filter_parameter.items():
                            param_values = source_db.get_parameter_value_items(
                                entity_class_name=source_class,
                                parameter_definition_name=target_feature,
                                entity_name=entity["name"],
                            )
                            param_flag = any(
                                x["parsed_value"] == target_method for x in param_values
                            )  # Enough if one alternative has the method set
                            # for param_value in param_values:
                            #     if param_value["parsed_value"] == target_method:
                            #         param_flag = True
                            #         break
                            # Another option would be to go through them all and throw an error if different values
                    # If the last item is a string, then that parameter must have a value or a method selected.
                    elif isinstance(filter_parameter, str):
                        param_flag = False
                        param_values = source_db.get_parameter_value_items(
                            entity_class_name=source_class,
                            parameter_definition_name=filter_parameter,
                            entity_name=entity["name"],
                        )
                        if param_values:
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
                    added, error = target_db.add_entity_item(
                        entity_class_name=target_class,
                        entity_byname=tuple(entity_byname_list),
                    )
                    if "__" in target_class:
                        for k, source_class_element in enumerate(
                            source_class.split("__")
                        ):
                            for ea in source_db.get_entity_alternative_items(
                                entity_class_name=source_class_element,
                                entity_name=entity["entity_byname"][k],
                            ):
                                assert_success(target_db.add_update_entity_alternative_item(
                                    entity_class_name=target_class,
                                    entity_byname=entity_byname_list,
                                    alternative_name=ea["alternative_name"],
                                    active=ea["active"],
                                ))
                if error:
                    print("Copying entities: " + error)
    try:
        target_db.commit_session("Added entities")
    except:
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
                for source_entity in source_db.get_entity_items(
                    entity_class_name=source_entity_class
                ):
                    for parameter in source_db.get_parameter_value_items(
                        entity_class_name=source_entity_class,
                        parameter_definition_name=source_param,
                        entity_name=source_entity["name"],
                    ):
                        (
                            target_param_value,
                            type_,
                            entity_byname_tuple,
                        ) = process_parameter_transforms(
                            source_entity,
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
                            added, error = target_db.add_item(
                                "parameter_value",
                                check=True,
                                entity_class_name=target_entity_class,
                                parameter_definition_name=target_parameter_name,
                                entity_byname=entity_byname_tuple,
                                alternative_name=parameter["alternative_name"],
                                value=target_value,
                                type=type_,
                            )
                            if error:
                                print("transform parameters error: " + error)
    try:
        target_db.commit_session("Added parameters")
    except:
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
                            source_entity,
                            parameter["value"],
                            parameter["type"],
                            target_param_def,
                            ts_to_map,
                        )
                        for (
                            target_parameter_name,
                            target_value,
                        ) in target_param_value.items():
                            added, error = target_db.add_item(
                                "parameter_value",
                                check=True,
                                entity_class_name=target_entity_class,
                                parameter_definition_name=target_parameter_name,
                                entity_byname=entity_byname_tuple,
                                alternative_name=parameter["alternative_name"],
                                value=target_value,
                                type=type_,
                            )
                            if error:
                                print("transform parameters error: " + error)
                    if not flag_base_alt:
                        param_def_item = source_db.get_parameter_definition_item(
                            entity_class_name=source_entity_class, name=source_param
                        )
                        (
                            target_param_value,
                            type_,
                            entity_byname_tuple,
                        ) = process_parameter_transforms(
                            source_entity,
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
                                added, error = target_db.add_item(
                                    "parameter_value",
                                    check=True,
                                    entity_class_name=target_entity_class,
                                    parameter_definition_name=target_parameter_name,
                                    entity_byname=entity_byname_tuple,
                                    alternative_name=default_alternative,
                                    value=target_value,
                                    type=type_,
                                )
                                if error:
                                    print(
                                        "transform parameter definition to parameters error: "
                                        + error
                                    )

    return target_db


def process_parameter_transforms(
    source_entity, parameter_value, parameter_type, target_param_def, ts_to_map
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

    data = api.from_database(parameter_value, parameter_type)
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
        entity_byname_tuple = source_entity["entity_byname"]
    else:
        entity_byname_list = []
        for target_positions in target_param_def[2]:
            entity_bynames = []
            for target_position in target_positions:
                entity_bynames.append(
                    source_entity["element_name_list"][int(target_position) - 1]
                )
            entity_byname_list.append("__".join(entity_bynames))
        entity_byname_tuple = tuple(entity_byname_list)
    # if target_positions:
    #     for dimension in target_positions:
    #         if source_entity["element_name_list"]:
    #             entity_byname_list.append(source_entity["element_name_list"][int(dimension) - 1])
    #         else:
    #             for element in source_entity["entity_byname"]:
    #                 entity_byname_list.append(element)
    # else:
    #     for element in source_entity["entity_byname"]:
    #         entity_byname_list.append(element)

    return target_param_value, type_, entity_byname_tuple


def process_methods(source_db, target_db, parameter_methods):
    for source_entity_class, sec_values in parameter_methods.items():
        for target_entity_class, tec_values in sec_values.items():
            for source_feature, f_values in tec_values.items():
                for source_entity in source_db.get_entity_items(
                    entity_class_name=source_entity_class
                ):
                    for parameter in source_db.get_parameter_value_items(
                        parameter_definition_name=source_feature,
                        entity_name=source_entity["name"],
                    ):
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
                            # print(target_entity_class + ', ' + target_parameter_name)
                            added, error = target_db.add_item(
                                "parameter_value",
                                check=True,
                                entity_class_name=target_entity_class,
                                parameter_definition_name=target_parameter_name,
                                entity_byname=entity_byname_list,
                                alternative_name=parameter["alternative_name"],
                                value=target_value,
                                type="str",
                            )
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
                                (
                                    added,
                                    update,
                                    error,
                                ) = target_db.add_update_parameter_value_item(
                                    entity_class_name=target_entity_class,
                                    parameter_definition_name=target_parameter_name,
                                    entity_byname=entity_byname_tuple,
                                    value=val,
                                    type=type_,
                                    alternative_name=ea["alternative_name"],
                                )
                                if error:
                                    print("copy entity to parameter error: " + error)
                            elif target_parameter_def[0] == "new_value":
                                val, type_ = api.to_database(target_parameter_def[1])
                                (
                                    added,
                                    update,
                                    error,
                                ) = target_db.add_update_parameter_value_item(
                                    entity_class_name=target_entity_class,
                                    parameter_definition_name=target_parameter_name,
                                    entity_byname=entity_byname_tuple,
                                    value=val,
                                    type=type_,
                                    alternative_name=ea["alternative_name"],
                                )
                                if error:
                                    print("copy entity to parameter error: " + error)
                            else:
                                exit(
                                    "Inappropriate choice in entities_to_parameters.yaml definition file: "
                                    + entity["name"]
                                )
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
    added, error = db.add_item(
        "parameter_value",
        check=True,
        entity_class_name=alt_ent_class[2],
        parameter_definition_name=param_name,
        entity_byname=alt_ent_class[1],
        alternative_name=alt_ent_class[0],
        value=value_x,
        type=type_,
    )
    if error:
        print("error trying to add parameter " + param_name + ": " + error)
    return db
