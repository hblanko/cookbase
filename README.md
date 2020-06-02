# Cookbase
A platform to validate, store and manage cooking recipes based on the JSON Cookbase Format.

Cookbase proposes and implements a data model striving for an *as-complete-as-possible* data structure applied to cooking data. A new suite of data formats (the **Cookbase Recipe Standard Format**) and a consistent data model structure with its database architecture and recipe data analysis tools are included in the Cookbase project.

Please check out the [documentation](https://cookbase.readthedocs.io/en/latest/) for detailed information about the project and the available API.

## Install

Cookbase can be installed through the PyPI repository using the following command:

```console
pip3 install cookbase
```

## Usage

At [the API documentation](https://cookbase.readthedocs.io/en/latest/) you will find information on how to use libraries.

On top of the API, the following features can be executed directly from the command line.

### Cookbase Schema Builder

It generates the schemas that describe the [Cookbase Data Model](https://cookbase.readthedocs.io/en/latest/cbdm.html). Run:

```console
python -m cookbase schema-builder [-c CONFIG_PATH]
```

where the optional `CONFIG_PATH` refers to a custom configuration file that you may provide. If given, it will override any configuration included in the [default configuration file](cookbase/schema/build-config.yaml).

## Contributing

We are in pre-release development phase, so feel free to come up with any feature that you think should be added to our project.
