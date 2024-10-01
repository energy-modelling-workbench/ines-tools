# INES-TOOLS

The `ines-tools` package provides a suite of functions to facilitate the transformation and processing of data between INES-SPEC conforming databases and other formats. This toolbox is designed to support flexible data and modeling workflows for energy systems, leveraging the INES Specification.

## Overview

The `ines-tools` package is part of the Interoperable Energy System (INES) project, which aims to enhance interoperability between various energy modeling tools. This package includes functions for data transformation, validation, and integration, making it easier to work with energy system models. It can be used for following use cases: importing and exporting data from ines-spec (e.g. building model instances using datapipelines from the Mopo EU project) as well as converting data between modelling tools (e.g. from OSeMOSYS to IRENA FlexTool or to utilize the open certification process to validate model behaviour). In general, the functions in the package should be called from separate tool specific repositories, but there is also a folder for tool specific functions in this repository for convenience (but this will then lack separate version control and version numbering required to build verified workflows).

The ines-tools can be used through scripting, but they can also be integrated into Spine Toolbox workflows for data management, ease-of-use and for version control between tools.


## Features

- **Data Transformation**: Convert data between INES-SPEC databases and other formats such as CSV, JSON, and XML.
- **Data Validation**: Ensure data integrity and compliance with the INES Specification.
- **Integration**: Seamlessly integrate with other energy modeling tools and platforms.
- **Flexibility**: Support for complex parameter structures and scenario building.

## Installation

To install the `ines-tools` package, use the following command:

```
pip install ines-tools
```

## Usage

### Data Transformation

Transform data from an INES-SPEC database to a CSV file:

```
from ines_tools import transform
```

# Transform INES-SPEC database to CSV
```
transform.ines_to_csv('ines_spec.sqlite', 'output.csv')
```

Transform data from a CSV file to an INES-SPEC database:
```
from ines_tools import transform
```
# Transform CSV to INES-SPEC database
```
transform.csv_to_ines('input.csv', 'ines_spec.sqlite')
```

### Data Validation

Validate an INES-SPEC database:

```
from ines_tools import validate
```
# Validate INES-SPEC database
```
validate.ines_database('ines_spec.sqlite')
```

### Integration

Integrate data from different energy modeling tools:

```
from ines_tools import integrate
```
# Integrate data from different tools
```
integrate.from_tool('tool_data.json', 'ines_spec.sqlite')
```

## Contributing

We welcome contributions to the `ines-tools` package. Please follow these steps to contribute:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Make your changes.
4. Commit your changes (`git commit -m 'Add new feature'`).
5. Push to the branch (`git push origin feature-branch`).
6. Create a new Pull Request.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Acknowledgements

This work was funded by the MOPO European Energy System Modelling project, which aims to advance the development and integration of energy system models across Europe.

## Contact

For questions or support, please open an issue in the repository or contact the maintainers.




<!-- To Do: Add a more detailed explanation (with examples) to the documentation. -->
