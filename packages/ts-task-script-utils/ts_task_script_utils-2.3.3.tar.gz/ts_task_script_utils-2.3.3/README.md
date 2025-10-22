# ts-task-script-utils <!-- omit in toc -->

## Version <!-- omit in toc -->

v2.3.3

## Table of Contents <!-- omit in toc -->

- [Summary](#summary)
- [Installation](#installation)
- [Usage](#usage)
  - [Parsing Numbers](#parsing-numbers)
  - [Parsing Datetimes](#parsing-datetimes)
    - [`DatetimeParser` Usage](#datetimeparser-usage)
  - [Generating Random UUIDs for Task Scripts](#generating-random-uuids-for-task-scripts)
  - [Using Python's `logging` module in Task Scripts](#using-pythons-logging-module-in-task-scripts)
  - [WellPosition](#wellposition)
  - [Writing Parquet Files](#writing-parquet-files)
- [Changelog](#changelog)
  - [v2.3.3](#v233)
  - [v2.3.2](#v232)
  - [v2.3.1](#v231)
  - [v2.3.0](#v230)
  - [v2.2.0](#v220)
  - [v2.1.0](#v210)
  - [v2.0.1](#v201)
  - [v2.0.0](#v200)
  - [v1.9.0](#v190)
  - [v1.8.1](#v181)
  - [v1.8.0](#v180)
  - [v1.7.0](#v170)
  - [v1.6.0](#v160)
  - [v1.5.0](#v150)
  - [v1.4.0](#v140)
  - [v1.3.1](#v131)
  - [v1.3.0](#v130)
  - [v1.2.0](#v120)
  - [v1.1.1](#v111)
  - [v1.1.0](#v110)

## Summary

Utility functions for Tetra Task Scripts

## Installation

`pip install ts-task-script-utils`

## Usage

### Parsing Numbers

```python
from task_script_utils.parse import to_int

string_value = '1.0'
int_value = to_int(string_value)

# `int_value` now has the parsed value of the string
assert isinstance(int_value, int)
assert int_value == 1

# it returns `None` if the value is unparseable
string_value = 'not an int'
int_value = to_int(string_value)

assert int_value is None
```

### Parsing Datetimes

> [!WARNING]
> **DEPRECATION** Do not use the old datetime parsing functions:
>
> - `convert_datetime_to_ts_format` from `task_script_utils.convert_datetime_to_ts_format`
> - `parse` from `task_script_utils.datetime_parser`

Use the `DatetimeParser` from `task_script_utils.datetime_parser` to parse datetimes.

`DatetimeParser` takes a list of formats used for parsing datetimes.
`DatetimeParser` does not infer the structure of a datetime string, formats must be provided.

#### `DatetimeParser` Usage

Using `DatetimeParser` with a list of formats

```python
from task_script_utils.datetime_parser import DatetimeParser

datetime_parser = DatetimeParser(formats=["YYYY-MM-DD[T]hh:mm A Z"])

ts_formatted_datetime: str | None = datetime_parser.to_tsformat("2004-12-23T12:30 AM +05:30")
```

Using `DatetimeParser` with a timezone mapping and a list of formats

```python
from task_script_utils.datetime_parser import DatetimeParser

formats = ["YYYY-MM-DD[T]hh:mm A zz"]
tz_dict = {"EST": "-05:00"}
datetime_parser = DatetimeParser(formats=formats, tz_dict=tz_dict)

ts_formatted_datetime: str | None = datetime_parser.to_tsformat("2004-12-23T12:30 AM EST")
```

If you need the `TSDatetime` object, you can use `DatetimeParser.parse() -> TSDatetime`.
`TSDatetime` gives access to  `TSDatetime.datetime` which can be used as a regular python datetime object.

You can read more about the datetime parser [here](task_script_utils/datetime_parser/README.md).

### Generating Random UUIDs for Task Scripts

To generate UUIDs, the `task_script_utils.uuid.uuid` function can be used.
This function generates UUIDs following UUID Version 7, meaning they are time-ordered: they can be sorted in order of creation time.
For more details on UUID Version 7, see <https://www.rfc-editor.org/rfc/rfc9562#name-uuid-version-7>.

**WARNING**: By default the output of `task_script_utils.uuid.uuid` will not be deterministic, and will depend on when the tests are run.
This is the desired behavior for task scripts running in TDP.
To achieve deterministic UUIDs for integration/unit tests, use the `mock_uuid_generator` fixture from [`ts-lib-pytest`](https://github.com/tetrascience/ts-lib-pytest/tree/main?tab=readme-ov-file#fixtures) to mock the UUID generator (this is a private TetraScience GitHub repository. Please contact TetraScience if you want to use it or you can create your own UUID mocker).

### Using Python's `logging` module in Task Scripts

Task Scripts can write workflow logs which are visible to users on TDP, but only if the logs are written via the logger provided by the `context` object. The `context` logger is documented here: [context.get_logger](https://developers.tetrascience.com/docs/context-api#contextget_logger).

This utility is a wrapper for the `context` logger which allows Task Scripts to use Python's `logging` module for creating TDP workflow logs, instead of directly using the `context` logger object. This means the `context` logger object doesn't need to be passed around to each function which needs to do logging, and Task Script code can benefit from other features of the Python `logging` module such as [integration with `pytest`](https://docs.pytest.org/en/7.1.x/how-to/logging.html).

To log warning messages on the platform from a task script do the following:

- Setup the log handler in `main.py`:

```python
from task_script_utils.workflow_logging import (
    setup_ts_log_handler,
)
```

- Then within the function called by the protocol:

```python
setup_ts_log_handler(context.get_logger(), "main")
```

- In a module where you wish to log a warning:

```python
import logging
logger = logging.getLogger("main." + __name__)
```

- Log a warning message with:

```python
logger.warning("This is a warning message")
```

### WellPosition

For plate readers, you can parse the well label using `task_script_utils.plate_reader.WellPosition`.

`WellPosition` encapsulates row and column indexes for a well on a plate.

You can use `WellPosition.from_well_label` to parse the `well_label: str` and get the `WellPosition` object.

For example:

```python
from plate_reader import WellPosition
WellPosition.from_well_label("P45") # returns WellPosition(row=16, column=45)
```

A `well_label` must satisfy following conditions:

  1. It must start with a letter
  2. It can contain at max two letters
      - When it contains two letters, they must both be uppercase
  3. Letter(s) must be followed by at least one and at max two digits

If the label cannot be parsed, `InvalidWellLabelError` is raised.

eg, `A45, a45, A01, A1, z1, z01, AC23` are valid well labels

Following are the example of invalid well labels:

- `A245`: `well_label` with more than 2 digits is not supported
- `A` or `a` or `aa`: `well_label`  doesn't contain any digit. Hence it is not supported.
- `aB02, Ab02, ab02`: Both letters must be uppercase.

Parsing for `well_label` containing a single letter is case sensitive ie. well labels A02 and a02 represent different wells on the plate

Parsing for `well_label` containing two letters is limited to uppercase only ie. AB01 is supported but ab01, Ab01 and aB01 are not supported

The following are the only supported sequence of rows for a plate:

  1. A -> Z and then a -> z
  2. A -> Z and then AA -> AZ

For `well_label` with single letter, even though well labels starting with `w`, `x`, `y`, and `z` are supported by the parser, in real life this is not possible as the largest plate contains `3456 wells` which is `48x72`, so the last well label is going to be `v72`.

Similarly, for `well_label` with two letters, in real life the largest possible `well_label` would be `AV72` for a plate with 3456 wells. However, `well_label` beyond `AV72` are also supported by parser.

### Writing Parquet Files

In order to use parquet files within your task script you must first install either `pandas` or `polars` depending on your use case.

If one of these packages is not installed, the parquet function will not work since it relies on the underlying DataFrame implementations and conversion methods provided by either package.

Specifically, the function checks that the provided object implements the required DataFrameProtocol—which is satisfied by a real pandas or polars DataFrame—and then uses methods like to_parquet() to generate the parquet bytes.

Without one of these libraries, you’ll encounter a runtime error when the function attempts to perform these conversions.

To build and write parquet files there are two functions that can be called:

  1. `pandas_dataframe_to_parquet` : Will convert a given pandas dataframe into parquet bytes and write to the Tetra Data Lake.
  2. `polars_dataframe_to_parquet` : Will convert a given polars dataframe into parquet bytes and write to the Tetra Data Lake.

For example with pandas:

```python
from ts_task_script_utils.parquet import pandas_dataframe_to_parquet
import pandas as pd

df = pd.DataFrame({
    'Integers': (1, 2, 3, 4, 5),
    'Fruits': ("apples", "bananas", "loquat", "kiwi", "mango"),
    'Food': ("pizza", "hot dog", "churro", "fruit smoothie", "chocolate cookie")
})

# Convert the DataFrame to Parquet bytes and write the result to storage.
# 'pyarrow' is preferred as the engine and 'snappy' for compression.
file_id = pandas_dataframe_to_parquet(
    df,
    context=context,
    file_name="report.parquet",
    engine="pyarrow",
    compression="snappy"
)
```

or with polars:

```python
from ts_task_script_utils.parquet import polars_dataframe_to_parquet, write_parquet_file
import polars as pl

df = pl.DataFrame({
    'Integers': (1, 2, 3, 4, 5),
    'Fruits': ("apples", "bananas", "loquat"),
    'Food': ("pizza", "hot dog", "churro", "fruit smoothie", "chocolate cookie")
})

# Convert the DataFrame to Parquet bytes and write the result to storage.
# 'snappy' is preferred for compression.
file_id = polars_dataframe_to_parquet(
    df,
    context=context,
    file_name="report.parquet",
    compression="snappy"
)
```

The compression can be `ztsd`, `snappy`, `gzip`, etc., with `snappy` preferred and automatically will default.

For pandas the engine that is supported is either `fastparquet` or `pyarrow` with `pyarrow` preferred.

## Changelog

### v2.3.3

- Update `task_script_utils.uuid.uuid` in line with the python v3.14 standard library implementation

### v2.3.2

- Update `task_script_utils.parquet.pandas_dataframe_to_parquet` to not write dataframe indices to parquet.

### v2.3.1

- Fix timezone handling when timezone abbreviations are substrings of each other
  - Now timezone abbreviations in `tz_dict` are sorted by length to ensure longer names are replaced first

### v2.3.0

- Add `task_script_utils.parquet.pandas_dataframe_to_parquet` for generating parquet bytes and writing parquet files using pandas.
- Add `task_script_utils.parquet.polars_dataframe_to_parquet` for generating parquet bytes and writing parquet files using polars.

### v2.2.0

- Add `task_script_utils.uuid.uuid` for generating UUIDs following UUID Version 7
- Deprecate `task_script_utils.task_script_uuid_generator.TaskScriptUUIDGenerator` in favor of `task_script_utils.uuid.uuid`
  - **WARNING**: When migrating from the deprecated `TaskScriptUUIDGenerator` to the `uuid` method, please be aware of potential breaking changes.
    The generated UUIDs will now be time-ordered but non-deterministic.
    In order for the UUIDs to be deterministic for integration/unit tests in task scripts, the `mock_uuid_generator` fixture from `ts-lib-pytest` should be used.
    Note: `ts-lib-pytest` is a private TetraScience GitHub repository.
    Please contact TetraScience if you want to use it or you can create your own UUID mocker.

### v2.1.0

- Deprecate datetime parsing function `parse()`, replaced by object `DatetimeParser`
  - **WARNING**: When migrating from the deprecated `parse` method to the `DatetimeParser` method, please be aware of potential breaking changes.
  The `parse` method used speculative parsing strategies when a format string was not provided, which may have masked potential issues.
  The `DatetimeParser` method does not use these fallback strategies, which may lead to unexpected results if the correct format string is not provided.
  Please thoroughly test your code after migrating to ensure it behaves as expected.
- Add `DatetimeParser`
- Update to pendulum 3.0.0 and adapt to breaking changes

### v2.0.1

- Restrict pendulum to `<3.0.0`

### v2.0.0

- Python minimum requirement is now 3.9
- Removed parquet support
- Made dependencies less restrictive

### v1.9.0

- Add `task_script_utils.plate_reader.WellPosition.to_label` for converting a `WellPosition` to a well label
- Add `task_script_utils.plate_reader.create_well_to_pk_map` for creating a map of `WellPosition` to primary keys from a list of samples

### v1.8.1

- Update to python dependency to >=3.7.2,<4

### v1.8.0

- Add `task_script_utils.plate_reader.WellPosition` for parsing well labels
- Update `task_script_utils.random.Singleton` used by `TaskScriptUUIDGenerator` and rename to `task_script_utils.random.CacheLast`
  - `CacheLast` no longer provides singleton behavior, but it still provides the method `get_last_created`
  - Instantiating `TaskScriptUUIDGenerator` always seeds the random generator. A second instance will repeat the same sequence of UUIDs as the first instance (if instantiated with the same arguments).
  - Rename `NoPreviouslyCreatedSingletonError` to `NoPreviouslyCreatedInstanceError`
  - Add type information to `get_last_created`

### v1.7.0

- Add `task_script_utils.workflow_logging` for logging warning messages in task scripts

### v1.6.0

- Add `task_script_utils.datacubes.parquet` for creating Parquet file representations of datacubes

### v1.5.0

- Add `TaskScriptUUIDGenerator` class for generating random UUIDs and random bytes.

### v1.4.0

- Add `extract-to-decorate` functions

### v1.3.1

- Update datetime parser usage in README.md

### v1.3.0

- Added string parsing functions

### v1.2.0

- Add boolean config parameter `require_unambiguous_formats` to `DatetimeConfig`
- Add logic to `parser._parse_with_formats` to be used when `DatetimeConfig.require_unambiguous_formats` is set to `True`
  - `AmbiguousDatetimeFormatsError` is raised if mutually ambiguous formats are detected and differing datetimes are parsed
- Add parameter typing throughout repository
- Refactor `datetime_parser` package
- Add base class `DateTimeInfo`
- Segregate parsing logic into `ShortDateTimeInfo` and `LongDateTimeInfo`

### v1.1.1

- Remove `convert_to_ts_iso8601()` method

### v1.1.0

- Add `datetime_parser` package
