import sys
import json
import spinedb_api as api

spinedb = sys.argv[1]
jsondb = sys.argv[2]

with api.DatabaseMapping(spinedb) as db_map:
    data = api.export_data(db_map,parse_value=api.parameter_value.load_db_value)
    with open(jsondb, 'w') as f:
        json.dump(data, f, indent=4)