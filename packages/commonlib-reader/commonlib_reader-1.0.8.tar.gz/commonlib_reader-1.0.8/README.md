# commonlib-reader [![SNYK dependency check](https://github.com/equinor/commonlib-reader/actions/workflows/snyk.yml/badge.svg)](https://github.com/equinor/commonlib-reader/actions/workflows/snyk.yml)
Connector package for Equinor [Commonlib](https://commonlib.equinor.com/) [api](https://commonlibapi.equinor.com/swagger/index.html). 

Current features:
- Reading code tables
- Getting facility data using the [Facility](commonlib_reader/facility.py) class
- [IMS source ](commonlib_reader/ims.py) lookup tables for facilities
- Getting Tag category, Tag type, Tag format, and Tag format element data. See [tag.py](commonlib_reader/tag.py)
- Getting [units of measure](commonlib_reader/ims.py) definitions.


## Use
Try it out by running the [demo](examples/demo.py).

## Installing

Install package from pypi using `pip install commonlib_reader`


## Developing / testing

Poetry is preferred for developers. Clone and install with required packages for testing and coverage:  
`poetry install`

For testing with coverage run:  
`poetry run pytest --cov --cov-report=html`
