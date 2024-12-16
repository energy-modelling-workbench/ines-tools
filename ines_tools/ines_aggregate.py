import spinedb_api as api
from spinedb_api import DatabaseMapping
import typing
from sqlalchemy.exc import DBAPIError
from spinedb_api.exception import NothingToCommit
from sys import exit
# from ines_tools import assert_success
from ines_tools.helpers import parse_map_of_weights

weights = parse_map_of_weights("examples/aggregation_weights.csv")
print(weights)
