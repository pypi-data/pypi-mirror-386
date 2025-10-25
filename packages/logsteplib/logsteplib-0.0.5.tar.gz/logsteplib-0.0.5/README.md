# logsteplib

* [Description](#package-description)
* [Usage](#usage)
* [Installation](#installation)
* [License](#license)

## Package Description

Package containing a standard format for the logging module.

## Usage

* [logsteplib](#logsteplib)

from a script:

```python
from logsteplib.log_config import LogConfig
from logsteplib.db_metadata import DQMetadata
from logsteplib.dq_exceptions import SchemaMismatch, EmptyFile
```

```python
# Standard Logger: Setup logger
from logsteplib.log_config import LogConfig

logger = LogConfig(name="my_process").logger
logger.info(msg="Starting data quality process...")
```

```python
# Retrieve the standard log message format string
log_format = log_config.get_std_fmt()
print("Log format:", log_format)
```

```python
# DQ: Create metadata object
from logsteplib.db_metadata import DQMetadata

metadata = DQMetadata(
    target="sales_folder",
    key="2025Q3",
    input_file_name="raw_sales.csv",
    file_name="clean_sales.csv",
    user_name="John Doe",
    user_email="john.doe@example.com",
    modify_date="2025-10-24",
    file_size=2048,
    file_row_count=15000,
    status="accepted",
    rejection_reason=None,
    file_web_url="https://example.com/files/clean_sales.csv"
)

logger.info(msg="Metadata created:")
logger.info(msg=metadata.to_json())
```

```python
# DQ: Raise a custom exception (example)
from logsteplib.dq_exceptions import SchemaMismatch, EmptyFile

try:
    raise SchemaMismatch()
except SchemaMismatch as e:
    logger.error(msg=f"Data quality error: {e}")
```

## Installation

* [logsteplib](#logsteplib)

Install python and pip if you have not already.

Then run:

```bash
pip install pip --upgrade
```

For production:

```bash
pip install logsteplib
```

This will install the package and all of it's python dependencies.

If you want to install the project for development:

```bash
git clone https://github.com/aghuttun/logsteplib.git
cd logsteplib
pip install -e ".[dev]"
```

To test the development package: [Testing](#testing)

## License

* [logsteplib](#logsteplib)

BSD License (see license file)
