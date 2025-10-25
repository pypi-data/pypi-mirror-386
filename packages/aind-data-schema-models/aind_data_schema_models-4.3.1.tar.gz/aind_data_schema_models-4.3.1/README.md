# aind-data-schema-models

[![License](https://img.shields.io/badge/license-MIT-brightgreen)](LICENSE)
![Code Style](https://img.shields.io/badge/code%20style-black-black)
[![semantic-release: angular](https://img.shields.io/badge/semantic--release-angular-e10079?logo=semantic-release)](https://github.com/semantic-release/semantic-release)
![Interrogate](https://img.shields.io/badge/interrogate-100.0%25-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen?logo=codecov)
![Python](https://img.shields.io/badge/python->=3.10-blue?logo=python)

## Installation

`aind-data-schema-models` is a dependency of `aind-data-schema`. You should not need to install it directly.

## Contributing

Install the dev dependencies:

```bash
pip install -e .[dev]
```

### How to add a new model class

#### tl;dr

Add new classes to the `_generators/models/*.csv` files or create new files containing `Enum`-derived classes directly in the src folder.

Run `./run_all.sh` in the top-level folder to rebuild models from their CSV files.

#### Details

The model class files, `brain_atlas.py` etc, are auto-generated. **You should never need to modify the class files directly.**

Instead, take a look at the `jinja2` templates in the folder `_generators/templates`. The filename of the template is used to pull the corresponding `.csv` file and populate the `data` DataFrame. In the template you can pull data from the various columns and use them to populate each of the fields in your class.

To re-build all the models, run the `run_all.sh` bash script in the root folder, which loops through the template files and runs them through the `generate_code` function.

There are a few special cases, e.g. if data are missing in columns they will show up as `float: nan`. See the `organizations.txt` template for examples of how to handle this.

#### Documentation

Internal registries need to be enumerated in the `aind-data-schema` file `src/aind_data_schema/utils/docs/registries_generator.py` in the variable `registries`. This list controls what classes will have documentation automatically generated and cross-referenced correctly.

If you add a new **external** registry, you need to write the documentation manually in the `aind-data-schema` file `docs/source/aind_data_schema_models/external.md`.
