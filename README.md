# ines-tools

The ines-tools (interoperable energy system data tools) package contains functions to transform data between ines-spec conforming databases and data in other formats. It can be used for following use cases: importing and exporting data from ines-spec (e.g. building model instances using datapipelines from the Mopo EU project) as well as converting data between modelling tools (e.g. from OSeMOSYS to IRENA FlexTool or to utilize the open certification process to validate model behaviour). In general, the functions in the package should be called from separate tool specific repositories, but there is also a folder for tool specific functions in this repository for convenience (but this will then lack separate version control and version numbering required to build verified workflows).

The ines-tools can be used through scripting, but they can also be integrated into Spine Toolbox workflows for data management, ease-of-use and for version control between tools.

<!-- To Do: Add a more detailed explanation (with examples) to the documentation. -->
