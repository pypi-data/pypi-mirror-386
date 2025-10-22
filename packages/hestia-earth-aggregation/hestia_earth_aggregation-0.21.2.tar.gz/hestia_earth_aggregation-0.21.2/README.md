# HESTIA Aggregation Engine

[![Pipeline Status](https://gitlab.com/hestia-earth/hestia-aggregation-engine/badges/master/pipeline.svg)](https://gitlab.com/hestia-earth/hestia-aggregation-engine/commits/master)
[![Coverage Report](https://gitlab.com/hestia-earth/hestia-aggregation-engine/badges/master/coverage.svg)](https://gitlab.com/hestia-earth/hestia-aggregation-engine/commits/master)
[![Documentation Status](https://readthedocs.org/projects/hestia-aggregation-engine/badge/?version=latest)](https://hestia-aggregation-engine.readthedocs.io/en/latest/?badge=latest)

## Documentation

Official documentation can be found on [Read the Docs](https://hestia-aggregation-engine.readthedocs.io/en/latest/index.html).

Additional models documentation can be found in the [source folder](./hestia_earth/aggregation).

## Install

1. Install the module:
```bash
pip install hestia_earth.aggregation
```

### Usage

```python
import os
from hestia_earth.aggregation import aggregate

aggregates = aggregate(country_name='Japan')
```

## Generating Covariance martrix

To generate the covariance matrix, some CSV files are generated and stored in a folder.

By default, these files will be created in the `/tmp` directory and removed at the end of aggregation, which can be changed setting the `TMP_DIR` env variable.

You can also choose a different storage method with the `AGGREGATION_COVARIANCE_STORAGE` env variable:
- `temporary`: default value, will store the files in the `TMP_DIR` and delete them at the end;
- `s3#<folder>`: upload the files on the S3 bucket defined by the variable `AWS_BUCKET_UPLOADS`;
- `local#<folder>`: copy the files to a local folder.
