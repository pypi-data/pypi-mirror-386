# HESTIA Data Validation

[![Pipeline Status](https://gitlab.com/hestia-earth/hestia-data-validation/badges/master/pipeline.svg)](https://gitlab.com/hestia-earth/hestia-data-validation/commits/master)
[![Coverage Report](https://gitlab.com/hestia-earth/hestia-data-validation/badges/master/coverage.svg)](https://gitlab.com/hestia-earth/hestia-data-validation/commits/master)
[![Documentation Status](https://readthedocs.org/projects/hestia-data-validation/badge/?version=latest)](https://hestia-data-validation.readthedocs.io/en/latest/?badge=latest)

## Install

```bash
pip install hestia_earth_validation
```

## Usage

```python
from hestia_earth.validation.preload_requests import enable_preload
from hestia_earth.validation import validate

# enable request preloading
enable_preload()
# for each node, this will return a list containing all the errors/warnings (empty list if no errors/warnings)
errors = validate(nodes)
```

Note: if you want to validate existing data (with `@type` and `@id` fields), please set the following environment variable:

```
VALIDATE_EXISTING_NODES=true
```
