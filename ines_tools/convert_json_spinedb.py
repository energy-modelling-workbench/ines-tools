import sys
import json
import spinedb_api as api

jsondb = sys.argv[1]
spinedb = sys.argv[2]

with open(jsondb) as f:
    data = json.load(f)
    with api.DatabaseMapping(spinedb) as db_map:
        api.import_data(db_map, **data)
        db_map.refresh_session()
        db_map.commit_session("Import data from json")