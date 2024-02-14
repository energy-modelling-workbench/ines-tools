import spinedb_api as api
from spinedb_api import DatabaseMapping
import sys

if len(sys.argv) < 3:
    exit("Not enough arguments (first: mathprog model_file path, second: Spine DB path, optional third: set name for 0-dimensional parameters")
file = open(sys.argv[1])
url_db = sys.argv[2]
if len(sys.argv) > 3:
    model_name = sys.argv[3]
else:
    model_name = "mathprog_model"

with DatabaseMapping(url_db) as target_db:
    target_db.purge_items('entity_class')

    set_names = []
    set_dimen_list = []
    param_names = []
    param_dimen_list = []

    while True:
        next_line = file.readline()
        if not next_line:
            break
        if not next_line.find(';'):
            next_line = next_line + file.readline()
            if not next_line:
                break

        elements = next_line.replace(';', ' ').replace(',', ' , ').replace('{', ' { ').replace('}', ' } ').split()
        dimen_found = False
        make_set = False
        first_word = ""
        second_word = ""

        if len(elements) > 0:
            first_word = elements.pop(0)
            if len(elements) > 0:
                second_word = elements.pop(0)
            if first_word == "set":
                for i, element in enumerate(elements):
                    if element == "dimen":
                        dimen_found = True
                        if isDigit(elements[i+1]):      # Check that the word after 'dimen' is a positive integer
                            if int(elements[i+1]) > 1:  # If dimen is more than 1, stop (just picking fundamental sets here, n-d sets are based on parameters
                                break
                        else:
                            make_set = True
                if not dimen_found:
                    make_set = True
                if make_set:
                    set_names.append(second_word)
                    set_dimen_list.append([second_word])

            if first_word == "param":
                param_dimen_start = False
                param_dimen_end = False
                param_attributes_start = False
                param_expression = False
                param_name_alias = []
                param_dimens = []
                for i, next_word in enumerate(elements):
                    if next_word == '{':
                        param_dimen_start = True
                        continue
                    if next_word == '}':
                        param_dimen_end = True
                        continue
                    if next_word == ':=':
                        param_expression = True
                        break
                    if next_word == ',':
                        if (param_dimen_start and param_dimen_end) or (not param_dimen_start and not param_dimen_end):
                            param_attributes_start = True
                            break  # Attributes are not handled yet
                        continue
                    if not param_dimen_start and not param_attributes_start:
                        param_name_alias.append(next_word)
                    elif not param_dimen_end and not param_attributes_start:
                        if len(elements) > i + 2 and elements[i + 1] == "in":
                            param_dimen_candidate = elements[i + 2]
                            elements.pop(i)
                            elements.pop(i)
                        elif next_word != ',':
                            param_dimen_candidate = next_word
                        else:
                            continue
                        for set_name in set_names:
                            if param_dimen_candidate == set_name:
                                param_dimens.append(param_dimen_candidate)
                                break
                if not param_expression and param_dimen_start and param_dimen_end:
                    param_names.append(second_word)
                    param_dimen_list.append(param_dimens)
                if not param_expression and not param_dimen_start and not param_dimen_end:
                    param_names.append(second_word)
                    param_dimen_list.append([model_name])

    for param_dimens in param_dimen_list:
        new_param_dimens = True  # Start by assuming that the dimens are not in any set yet
        for set_dimens in set_dimen_list:
            if len(param_dimens) == len(set_dimens):
                param_dimens_in_set = True  # Start by assuming that the dimens are the same
                for i, param_dimen in enumerate(param_dimens):
                    if param_dimen != set_dimens[i]:
                        param_dimens_in_set = False  # The dimens weren't the same, so it could be new
                        break
                if param_dimens_in_set:       # Went through the dimens and it was the same!
                    new_param_dimens = False  # So, it's not a new set
                    break                     # No point to check the rest
        if new_param_dimens:  # It turned out to be a new set
            set_dimen_list.append(param_dimens)  # So, let's add it to the set_dimens_list
            set_names.append('__'.join(param_dimens))  # And give the set a name

    for i, set_name in enumerate(set_names):
        if len(set_dimen_list[i]) > 1:
            added, error = target_db.add_entity_class_item(name=set_name, dimension_name_list=set_dimen_list[i])
        else:
            added, error = target_db.add_entity_class_item(name=set_name)

    for i, param_name in enumerate(param_names):
        added, error = target_db.add_parameter_definition_item(name=param_name, entity_class_name='__'.join(param_dimen_list[i]))

    target_db.commit_session("foo")

file.close()
