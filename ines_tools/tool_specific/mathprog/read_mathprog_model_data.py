import spinedb_api as api
from spinedb_api import DatabaseMapping
import sys
import pyarrow

def get_params(class_dimen_positions, entity_pos, param_data, inside_dimen_positions, is_class_dimen):
    pointer_to_data = param_data
    for class_pos in class_dimen_positions:
        pointer_to_data = pointer_to_data[class_pos]
        for in_pos in inside_dimen_positions:
            print(pointer_to_data)
    pointer_to_data = param_data.copy()
    for is_class in is_class_dimen:
        if is_class:
            pointer_to_data = pointer_to_data[entity_pos.pop()]
        else:
            pointer_to_data = pointer_to_data
    return pointer_to_data

if len(sys.argv) < 3:
    exit("Not enough arguments (first: mathprog data file path, second: path to Spine DB with model structure")
file = open(sys.argv[1])
url_db = sys.argv[2]
alternative_name = "base"
if len(sys.argv) > 3:
    alternative_name = sys.argv[3]

dimens_to_param = ["YEAR"]

with DatabaseMapping(url_db) as target_db:

    target_db.purge_items('entity')
    target_db.commit_session("Purged entities")
    target_db.purge_items('alternative')
    target_db.commit_session("Purged alternatives")
    target_db.add_alternative_item(name=alternative_name)
    target_db.commit_session("Added alternative " + alternative_name)
    class__param = {}
    class__param__all_dimens = {}
    class__dimen = {}
    entity_classes = target_db.get_entity_class_items()
    for entity_class in entity_classes:
        params = target_db.get_parameter_definition_items(entity_class_name=entity_class["name"])
        params_name_list = []
        all_params_dimen_dict_list = {}
        for param in params:
            params_name_list.append(param["name"])
            all_params_dimen_dict_list[param["name"]] = param["description"].split()
        class__param[entity_class["name"]] = params_name_list
        class__param__all_dimens[entity_class["name"]] = all_params_dimen_dict_list
        dimens_name_list = []
        for dimen in entity_class["dimension_name_list"]:
            dimens_name_list.append(dimen)
        class__dimen[entity_class["name"]] = dimens_name_list

    while True:
        next_line = file.readline()  # This block of code will read the next line, but also the lines after in case there is no ';' sign to mark the end of the MathProg command
        if not next_line:
            break
        elements = next_line.replace(';', ' ;').replace(',', ' , ').replace('[', ' [ ').replace(']', ' ] ').split()
        if len(elements) > 0:
            if elements[0] == "set" or elements[0] == "param":
                while next_line.find(';') == -1:  # Check if the data is all in one line. find() returns -1 if not found --> adds lines until ;
                    next_line = file.readline()
                    if not next_line:
                        break
                    elements = elements + ['\n'] + next_line.replace(';', ' ;').replace(',', ' , ').replace('[', ' [ ').replace(']', ' ] ').split()
            else:
                continue
        else:
            continue

        make_set = False
        first_word = ""
        second_word = ""
        add_all_entity_combinations_to_class = []

        if len(elements) > 0:
            first_word = elements.pop(0)
            if len(elements) > 0:
                second_word = elements.pop(0)
            if first_word == "set":
                class_name_found = False
                class_name_to_parameters = False
                for class_name in class__param.keys():
                    if second_word == class_name:
                        print("Class " + class_name + " found")
                        class_name_found = True
                        break
                for class_name in dimens_to_param:
                    if second_word == class_name:
                        print("Class " + class_name + " going into parameters")
                        class_name_to_parameters = True
                        break
                if not class_name_found and not class_name_to_parameters:
                    exit("No class found for set " + first_word)
                if class_name_found:
                    read_set_elements = False
                    set_member_names = []
                    for i, element in enumerate(elements):
                        if element == ":=":
                            read_set_elements = True
                            continue
                        if element == ";":
                            break
                        if read_set_elements:
                            set_member_names.append(element)
                            added, error = target_db.add_entity_item(entity_class_name=class_name, name=element)
                    if added:
                        target_db.commit_session("Added entities from class " + class_name)
                    continue

            if first_word == "param":
                param_dimen_start = False
                param_dimen_end = False
                param_attributes_start = False
                first_equal_sign = False
                second_equal_sign = False
                colon_sign = False
                tabbed_def_flag = False
                value_given = False
                tabbed_column_headers = []
                param_name_alias = []
                param_dimens = []
                tab_def = []
                is_default_value = False
                current_entity_class_dimens = []
                entity_class_dimens = []
                inside_dimen_positions = []
                class_dimen_positions = []
                is_class_dimen = []
                current_inside_dimens = []
                tabbed_col_orig_pos = []
                tabbed_row_orig_pos = []
                tabbed_col_temp_pos = []
                tabbed_row_temp_pos = []
                found_param = False
                colon_count = 0
                for entity_class in class__param:  # Try to find the param from the DB structure, check all entity_classes
                    for param in class__param[entity_class]:  # Go through every parameter in the class
                        if second_word == param:              # If the parameter name matches DB parameter name
                            if class__dimen[entity_class]:
                                current_entity_class_dimens = class__dimen[entity_class]  # Take the dimensions the parameter class has
                            else:
                                current_entity_class_dimens = [entity_class]
                            if class__param__all_dimens[entity_class][param]:
                                current_parameter_dimens = class__param__all_dimens[entity_class][param]
                            current_list = []
                            param_data = current_list

                            for i, dimen in enumerate(current_parameter_dimens):
                                if i > 1:
                                    nested = []
                                    current_list.append(nested)
                                    current_list = nested
                                found_dimen = False
                                for class_dimen in current_entity_class_dimens:
                                    if dimen == class_dimen:
                                        found_dimen = True
                                        class_dimen_positions.append(i)
                                        is_class_dimen.append(True)
                                        break
                                if not found_dimen:
                                    inside_dimen_positions.append(i)
                                    is_class_dimen.append(False)
                                    current_inside_dimens.append(dimen)
                            found_param = True
                            break
                    if found_param:  # No need to check further entity classes if the parameter has been found (no duplicate parameter names in MathProg)
                        data_headers = [[] for _ in range(len(current_parameter_dimens))]  # List of lists where each dimension has it's own list of header names.
                        data_counter = [-1 for _ in range(len(current_parameter_dimens))]
                        break

                for i, next_word in enumerate(elements):
                    if next_word == '\n':  # Skip end of lines
                        continue
                    if next_word == ';':
                        print(param_data)
                        class_dim_name = []
                        entity_pos = []
                        header_list = data_headers
                        # for m in range(len(class_dimen_positions)):
                        #     for list_of_headers in header_list[class_dimen_positions[m]]:
                        #         for e, name in enumerate(list_of_headers):
                        #             entity_pos.append(e)
                        #             class_dim_name.append(name)
                        #             inside_data = get_params(class_dimen_positions, entity_pos, param_data, inside_dimen_positions, is_class_dimen)
                        #         print(class_dim_name)
                                # header_list = header_list[class_dimen_positions[m]]

                        # for entity_pos[0], class_dim_name[0] in enumerate(data_headers[class_dimen_positions[0]]):
                        #     if len(class_dimen_positions) > 1:
                        #         for entity_pos[1], class_dim_name[1] in enumerate(data_headers[class_dimen_positions[1]]):
                        #             if len(class_dimen_positions) > 2:
                        #                 for entity_pos[2], class_dim_name[2] in enumerate(data_headers[class_dimen_positions[2]]):
                        #                     if len(class_dimen_positions) > 3:
                        #                         for entity_pos[3], class_dim_name[3] in enumerate(data_headers[class_dimen_positions[3]]):
                        #                             if len(class_dimen_positions) > 4:
                        #                                 for entity_pos[4], class_dim_name[4] in enumerate(data_headers[class_dimen_positions[4]]):
                        #                                     inside_data = get_params(data_headers, param_data, inside_dimen_positions, entity_pos)
                        #                                     write_param_to_db(class_dim_name, )


                        #for inside_dimen_position in inside_dimen_positions:
                        #    if inside_dimen_position == tabbed_dims[0]:
                        #        print("foo")
                        #tab_def[tabbed_dims[0]] = row_header
                        #tab_def[tabbed_dims[1]] = column_header
                        # added = target_db.add_update_entity_item(entity_class_name=entity_class,
                        #                                          entity_byname=tab_def)
                        # added, error = target_db.add_parameter_value_item(entity_class_name=entity_class,
                        #                                                   parameter_definition_name=second_word,
                        #                                                   entity_byname=tab_def,
                        #                                                   value=1,
                        #                                                   type=1,
                        #                                                   alternative_name=alternative_name)
                        # if error:
                        #     print(error)
                        if not value_given and is_default_value:
                            add_all_entity_combinations_to_class.append(entity_class)
                        break
                    if next_word == '[':
                        tabbed_def_flag = True
                        dim_number = 0
                        non_tabbed_dim_number = 0
                        read_tabbed = elements.pop(i + 1)
                        first_star_given = False
                        data_header_branches = False
                        while read_tabbed != ']':
                            if read_tabbed != ',':
                                if read_tabbed == '*':
                                    if not first_star_given:
                                        tabbed_row_orig_pos.append(dim_number)
                                        tabbed_dim_loc = len(current_parameter_dimens) - 2
                                        tabbed_row_temp_pos.append(tabbed_dim_loc)
                                        first_star_given = True
                                    else:
                                        tabbed_col_orig_pos.append(dim_number)
                                        tabbed_dim_loc = len(current_parameter_dimens) - 1
                                        tabbed_col_temp_pos.append(tabbed_dim_loc)
                                    #if not data_headers[tabbed_dim_loc]:
                                    data_headers[tabbed_dim_loc].append([])
                                    # else:
                                    #     if not any([] in sublist for sublist in data_headers[tabbed_dim_loc]):
                                    #         temp = data_headers[tabbed_dim_loc]
                                    #         data_headers[tabbed_dim_loc].append([temp])
                                else:
                                    data_header_found = False
                                    if not data_headers[non_tabbed_dim_number]:
                                        data_headers[non_tabbed_dim_number].append([])
                                    for k, data_header in enumerate(data_headers[non_tabbed_dim_number][0]):
                                        if data_header == read_tabbed:
                                            data_header_found = True
                                            data_counter[non_tabbed_dim_number] = k
                                            break
                                    if not data_header_found:
                                        data_headers[non_tabbed_dim_number][0].append(read_tabbed)
                                        data_counter[non_tabbed_dim_number] = len(data_headers[non_tabbed_dim_number]) - 1
                                        data_header_branches = True
                                    if data_header_branches:
                                        if non_tabbed_dim_number == 0:
                                            param_data.append([])
                                        elif non_tabbed_dim_number == 1:
                                            param_data[data_counter[0]].append([])
                                        elif non_tabbed_dim_number == 2:
                                            param_data[data_counter[0]][data_counter[1]].append([])
                                        elif non_tabbed_dim_number == 3:
                                            param_data[data_counter[0]][data_counter[1]][data_counter[2]].append([])
                                        elif non_tabbed_dim_number == 4:
                                            param_data[data_counter[0]][data_counter[1]][data_counter[2]][data_counter[3]].append([])
                                        elif non_tabbed_dim_number == 5:
                                            param_data[data_counter[0]][data_counter[1]][data_counter[2]][data_counter[3]][data_counter[4]].append([])
                                    non_tabbed_dim_number += 1

                                dim_number += 1
                            read_tabbed = elements.pop(i+1)
                        continue
                    if next_word == ':=':  # Skip := signs (unsignificant in MathProg)
                        continue
                    if next_word == ':':
                        colon_sign = True
                        if not tabbed_col_orig_pos:
                            tabbed_col_orig_pos.append(1)
                            tabbed_row_orig_pos.append(0)
                            tabbed_col_temp_pos.append(1)
                            tabbed_row_temp_pos.append(0)
                            data_headers[0].append([])
                            data_headers[1].append([])
                            non_tabbed_dim_number = 0
                        next_column_header_element = elements.pop(i+1)
                        while next_column_header_element != ':=' and next_column_header_element != '\n':
                            data_headers[tabbed_col_temp_pos[colon_count]][colon_count].append(next_column_header_element)
                            next_column_header_element = elements.pop(i + 1)
                        if next_column_header_element == ':=':
                            elements.pop(i+1)
                        value_row_pos = 0
                        tabbed_row_count = -1
                        colon_count += 1
                        continue
                    if colon_sign and value_row_pos == 0:
                        data_headers[tabbed_row_temp_pos[colon_count - 1]][colon_count - 1].append(next_word)
                        tabbed_row_count += 1
                        value_row_pos = 1
                    if colon_sign and value_row_pos > 0:
                        #tab_def[tabbed_dims[0]] = tabbed_row_name
                        #entity_name_dimens = tab_def
                        param_values_in_row = []
                        param_types_in_row = []
                        for j, tabbed_column_header_name in enumerate(data_headers[non_tabbed_dim_number + 1][colon_count - 1]):
                            param_value, param_type = api.to_database(elements.pop(i+1))
                            param_values_in_row.append(param_value)
                            param_types_in_row.append(param_type)
                            #entity_name_dimens[tabbed_dims[1]] = tabbed_column_headers_name
                        current_list = param_data
                        for n in range(2, len(current_parameter_dimens)):
                            current_list = current_list[data_counter[n - 2]]
                        current_list.append(param_values_in_row)
                        value_row_pos = 0
                        value_given = True
                        continue
                    if next_word == 'default' and i == 0:
                        is_default_value = True
                        default_value = elements[i+1]
                        default_value_db, default_value_type = api.to_database(elements[i+1])
                        added = target_db.add_update_parameter_definition_item(entity_class_name=entity_class,
                                                                       name=second_word,
                                                                       default_value=default_value_db,
                                                                       default_type=default_value_type)
                        if added[0]:
                            try:
                                target_db.commit_session("added default")
                            except:
                                print("Default value add_update commit failed")
                        elements.pop(i)
                        continue

                # HERE COMMIT PARAMETER VALUES THAT HAVE BEEN ACCRUED FROM THE param SENTENCE


                # Keeping code to deal with 'in' in the param dimension defs - needs to be implemented
                    # if not param_dimen_start and not param_attributes_start:
                    #     param_name_alias.append(next_word)
                    # elif not param_dimen_end and not param_attributes_start:
                    #     if len(elements) > i + 2 and elements[i + 1] == "in":
                    #         param_dimen_candidate = elements[i + 2]
                    #         elements.pop(i)
                    #         elements.pop(i)
                    #     elif next_word != ',':
                    #         param_dimen_candidate = next_word
                    #     else:
                    #         continue
                    #     for set_name in set_names:
                    #         if param_dimen_candidate == set_name:
                    #             param_dimens.append(param_dimen_candidate)
                    #             break
#    target_db.commit_session("Commit parameters")


    # for param_dimens in param_dimen_list:
    #     new_param_dimens = True  # Start by assuming that the dimens are not in any set yet
    #     for set_dimens in set_dimen_list:
    #         if len(param_dimens) == len(set_dimens):
    #             param_dimens_in_set = True  # Start by assuming that the dimens are the same
    #             for i, param_dimen in enumerate(param_dimens):
    #                 if param_dimen != set_dimens[i]:
    #                     param_dimens_in_set = False  # The dimens weren't the same, so it could be new
    #                     break
    #             if param_dimens_in_set:       # Went through the dimens and it was the same!
    #                 new_param_dimens = False  # So, it's not a new set
    #                 break                     # No point to check the rest
    #     if new_param_dimens:  # It turned out to be a new set
    #         set_dimen_list.append(param_dimens)  # So, let's add it to the set_dimens_list
    #         set_names.append('__'.join(param_dimens))  # And give the set a name
    #
    # for i, set_name in enumerate(set_names):
    #     if len(set_dimen_list[i]) > 1:
    #         added, error = target_db.add_entity_class_item(name=set_name, dimension_name_list=set_dimen_list[i])
    #     else:
    #         added, error = target_db.add_entity_class_item(name=set_name)
    #
    # for i, param_name in enumerate(param_names):
    #     added, error = target_db.add_parameter_definition_item(name=param_name, entity_class_name='__'.join(param_dimen_list[i]))
    #
    # target_db.commit_session("foo")

file.close()


def add_update_entities(entity_class):
    print("foo")


