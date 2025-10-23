# Dataruns

A powerful Python library for function pipeline execution and convenient data transformations. Build easy pipelines to execute different ops on your data. It is built on top of Pandas and Numpy.

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

## Features

✨ **Core Capabilities:**
- **Pipeline Execution**: Chain multiple data transformations seamlessly
- **Pandas-Like API**: Familiar interface if you know pandas
- **Multiple Data Sources**: Load from CSV, Excel, SQLite, and URLs
- **Built-in Transforms**: Standard scalers, missing value handlers, column selection
- **NumPy & Pandas Support**: Works with both arrays and DataFrames
- **Stateful Operations**: Transforms remember their state (mean, std) for consistent results

## Installation

```bash
pip install dataruns
```

Or with uv:
```bash
uv add dataruns
```

## Quick Start

### Basic Pipeline

```python
from dataruns import Pipeline, standard_scaler, fill_na
import pandas as pd

# Create sample data
df = pd.DataFrame({
    'age': [20, 30, 40],
    'salary': [30000, 50000, 70000]
})

# Create a pipeline
pipeline = Pipeline(
    fill_na(strategy='mean'),      # Fill missing values
    standard_scaler()               # Standardize the data
)

# Execute the pipeline
result = pipeline(df)
print(result)
```

### Load Data from Files

```python
from dataruns import CSVSource, XLSsource, SQLiteSource

# From CSV
csv_source = CSVSource('data.csv')
df = csv_source.extract_data()

# From Excel
excel_source = XLSsource('data.xlsx', sheet_name='Sheet1')
df = excel_source.extract_data()

# From SQLite
sqlite_source = SQLiteSource('database.db', 'SELECT * FROM my_table')
df = sqlite_source.extract_data()

# From URL
csv_source = CSVSource(url='https://example.com/data.csv')
df = csv_source.extract_data()
```

### Quick Convenience Functions

```python
from dataruns import load_csv

# Load CSV quickly
data = load_csv('data.csv')

```

## Core Concepts

### Pipelines

**Pipeline**: Execute transforms sequentially
```python
from dataruns import Pipeline

pipeline = Pipeline(transform1, transform2, transform3, verbose=True)
result = pipeline(data)
```

**Make_Pipeline**: Builder pattern for dynamic construction
```python
from dataruns import Make_Pipeline

builder = Make_Pipeline()
builder.add(fill_na(strategy='mean'))
builder.add(standard_scaler())
pipeline = builder.build()
```

### Available Transforms

```python
from dataruns.core.transforms import get_transforms

# This lists out all available transforms that have been implemented
print(get_transforms())

```

## Complete Example

```python
from dataruns import Pipeline, load_csv
from dataruns.core.transforms import select_columns, fill_na, standard_scaler
import numpy as np

# Load data
data = load_csv('customers.csv')

# Create comprehensive pipeline
pipeline = Pipeline(
    fill_na(strategy='mean'),           # Handle missing values
    select_columns(['age', 'income']),  # Keep relevant columns
    standard_scaler(),                  # Normalize for ML
    verbose=True                        # Show each step
)

# Process data
result = pipeline(data)

# Use with machine learning models
from sklearn.cluster import KMeans
kmeans = KMeans(n_clusters=3)
kmeans.fit(result)
```

## Data Sources

`Datasources` that are supported include `CSVSource`, `XLSsource`, `SQLiteSource`. *More to come soon*

```python
from dataruns import CSVSource, XLSsource, SQLiteSource

# CSV
source = CSVSource(file_path='data.csv')
# or from URL
source = CSVSource(url='https://example.com/data.csv')

# Excel
source = XLSsource(file_path='data.xlsx', sheet_name='Sheet1')

# SQLite
source = SQLiteSource(
    connection_string='database.db',
    query='SELECT * FROM users WHERE age > 18'
)

# Extract data
df = source.extract_data()
```

## Important Notes

### Stateful Transforms

Transforms remember their state from the first call:

```python
scaler = standard_scaler()

# First call: learns mean/std from data1
result1 = scaler(data1)

# Second call: reuses data1's statistics
result2 = scaler(data2)  # Normalized using data1's mean/std!
```

This matches scikit-learn's fit/transform pattern. Create new transform instances for independent scaling:

```python
scaler1 = standard_scaler()  # For data1
result1 = scaler1(data1)

scaler2 = standard_scaler()  # For data2 (fresh state)
result2 = scaler2(data2)
```

### Working with Different Data Types

- **Dataruns** is built on `pandas Dataframe` and `NumPy ndarray`

```python
import numpy as np
import pandas as pd
from dataruns import Pipeline, standard_scaler

# Works with arrays
array = np.array([[1, 2], [3, 4]])
pipeline(array)

# Works with DataFrames
df = pd.DataFrame({'a': [1, 3], 'b': [2, 4]})
pipeline(df)

# Works with lists (converted to array)
lst = [[1, 2], [3, 4]]
pipeline(lst)
```


## Development

Install development dependencies:

```bash
uv add --dev pytest pytest-cov ruff black
```

Run tests:
```bash
uv run pytest
```

Run with coverage:
```bash
uv run pytest --cov=src/dataruns
```

Lint code:
```bash
uv run ruff check src/
```

Format code:
```bash
uv run black src/
```

## License

MIT License - see [LICENSE](LICENSE) file for details

## Author

Daniel Ali

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Issues

*Do note that not all tests were marked as passed(about 8) but these tests are very niche tests*
Found a bug? Please report it on our [issue tracker](https://github.com/DanielUgoAli/dataruns/issues)

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and updates.
