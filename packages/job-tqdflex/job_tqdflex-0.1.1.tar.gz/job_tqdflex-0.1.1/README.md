# job-tqdflex

[![License: CC BY-SA 4.0](https://img.shields.io/badge/License-CC%20BY--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-sa/4.0/)
[![GitHub Actions](https://img.shields.io/endpoint.svg?url=https%3A%2F%2Factions-badge.atrox.dev%2FDavid-Araripe%2Fjob_tqdflex%2Fbadge%3Fref%3Dmaster&style=flat-square)](https://actions-badge.atrox.dev/David-Araripe/job_tqdflex/goto?ref=master)

A Python library supporting parallel processing with progress bars using joblib (*job*) and tqdm (*tqd*), with flexibility (*flex*) for chunked processing for memory efficiency.

## Features

- **Memory efficient** - supports generators and iterators
- **Context manager support** - automatic cleanup of resources
- **Easy parallel processing** with automatic chunking for optimal performance
- **Error handling** - support for error handling with detailed logging
- **Custom logging support** - compatible with loguru and standard python logging

## Installation

```bash
pip install job-tqdflex
```

## Quick Start

```python
from job_tqdflex import ParallelApplier
import time

def slow_square(x): 
    time.sleep(0.1) # (slow) function to apply
    return x ** 2

data = range(20)

# Create and run parallel applier
applier = ParallelApplier(slow_square, data, n_jobs=4)
results = applier()

print(results)  # [0, 1, 4, 9, 16, 25, ...]
```

## Usage Examples

### Basic Usage

```python
from job_tqdflex import ParallelApplier

def process_item(item):
    # Your processing logic here
    return item * 2

data = [1, 2, 3, 4, 5]
applier = ParallelApplier(process_item, data)
results = applier()
```

### With Additional Arguments

```python
def power_function(base, exponent=2):
    return base ** exponent

data = [1, 2, 3, 4, 5]
applier = ParallelApplier(power_function, data)
results = applier(exponent=3)  # [1, 8, 27, 64, 125]
```

### Using functools.partial for Complex Arguments

```python
from functools import partial

def complex_function(item, multiplier, offset=0):
    return item * multiplier + offset

# Pre-configure the function
configured_func = partial(complex_function, multiplier=3, offset=10)

data = [1, 2, 3, 4, 5]
applier = ParallelApplier(configured_func, data)
results = applier()  # [13, 16, 19, 22, 25]
```

### Working with Generators

```python
def data_generator():
    for i in range(1000):
        yield i

def expensive_computation(x):
    return sum(range(x))

# Works seamlessly with generators
applier = ParallelApplier(expensive_computation, data_generator(), n_jobs=8)
results = applier()
```

### Context Manager Usage

```python
def process_data(item):
    return item ** 2

data = range(100)

# Automatic resource cleanup
with ParallelApplier(process_data, data, n_jobs=4) as applier:
    results = applier()
```

### Different Backends

```python
# For CPU-bound tasks (default)
applier = ParallelApplier(cpu_intensive_func, data, backend="loky")

# For I/O-bound tasks
applier = ParallelApplier(io_bound_func, data, backend="threading")

# For other use cases
applier = ParallelApplier(some_func, data, backend="multiprocessing")
```

### Custom Progress Bar Settings

```python
# Disable progress bar
applier = ParallelApplier(func, data, show_progress=False)

# Custom chunk size for memory management
applier = ParallelApplier(func, large_dataset, chunk_size=100)

# Custom progress bar description (default: "Applying {func_name} to chunks")
applier = ParallelApplier(func, data, custom_desc="Processing...")
```

### Using the Low-Level `tqdm_joblib` Context Manager

```python
from job_tqdflex import tqdm_joblib
from joblib import Parallel, delayed
from tqdm import tqdm

def slow_function(x):
    time.sleep(0.1)
    return x ** 2

# Direct integration with joblib
with tqdm_joblib(tqdm(total=10, desc="Processing")) as progress_bar:
    results = Parallel(n_jobs=4)(delayed(slow_function)(i) for i in range(10))
```

## Configuration Options

### ParallelApplier Parameters

- **`func`**: The function to apply to each item
- **`iterable`**: Input data (list, generator, or any iterable)
- **`show_progress`**: Whether to show progress bars (default: `True`)
- **`n_jobs`**: Number of parallel jobs (default: `8`, use `-1` for all cores)
- **`backend`**: Parallelization backend (`"loky"`, `"threading"`, or `"multiprocessing"`)
- **`chunk_size`**: Size of chunks to process (default: auto-calculated)
- **`custom_desc`**: Custom description for the progress bar (default: `None`, uses `"Applying {func_name} to chunks"`)
- **`logger`**: Optional custom logger instance (supports standard logging and loguru)

### Performance Tips

1. **Choose the right backend**:
   - `"loky"` (default): Best for CPU-bound tasks
   - `"threading"`: Good for I/O-bound tasks
   - `"multiprocessing"`: For CPU-bound tasks with shared memory concerns

2. **Optimize chunk size**:
   - Larger chunks reduce overhead but increase memory usage
   - Smaller chunks provide better load balancing
   - Auto-calculation usually works well

3. **Use generators for large datasets**:
   ```python
   def large_data_generator():
       for i in range(1_000_000):
           yield expensive_data_loader(i)
   
   applier = ParallelApplier(process_func, large_data_generator())
   ```

## Error Handling

The library provides comprehensive error handling:

```python
def potentially_failing_function(x):
    if x == 42:
        raise ValueError("The answer to everything!")
    return x * 2

try:
    applier = ParallelApplier(potentially_failing_function, range(100))
    results = applier()
except RuntimeError as e:
    print(f"Parallel processing failed: {e}")
```

## Logging

### Standard Python Logging

Enable debug logging to monitor performance:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("joblib_tqdm")

# Your parallel processing code here
```

### Custom Logger Support (including Loguru)

The library supports custom logger instances, including loguru:

```python
# With loguru (if installed)
from loguru import logger as loguru_logger

def process_item(x):
    return x ** 2

data = range(100)

# Use loguru for all internal logging
applier = ParallelApplier(process_item, data, logger=loguru_logger)
results = applier()

# Or with tqdm_joblib context manager
from tqdm import tqdm
with tqdm_joblib(tqdm(total=100, desc="Processing"), logger=loguru_logger) as pbar:
    results = Parallel(n_jobs=4)(delayed(process_item)(i) for i in data)
```

```python
# With standard logging custom logger
import logging

custom_logger = logging.getLogger("my_custom_logger")
custom_logger.setLevel(logging.INFO)

applier = ParallelApplier(process_item, data, logger=custom_logger)
results = applier()
```

**Note**: Loguru is not a required dependency. It's included in the `[dev]` optional dependencies for testing purposes. You can use any logger object that has `debug()` and `error()` methods.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the CC BY-SA 4.0 License - see the [LICENSE](LICENSE) file for details.

## Attribution

This project includes code based on the [tqdm_joblib](https://github.com/louisabraham/tqdm_joblib) implementation by Louis Abraham, which is distributed under CC BY-SA 4.0. The original implementation was inspired by a Stack Overflow solution for integrating tqdm with joblib's parallel processing.

## Acknowledgments

- Built on top of the excellent [joblib](https://joblib.readthedocs.io/) library
- Progress bars provided by [tqdm](https://tqdm.github.io/)
- Based on the original [tqdm_joblib](https://github.com/louisabraham/tqdm_joblib) by Louis Abraham
- Inspired by the need for simple parallel processing with progress tracking and custom logging support

## Changelog

### 0.1.0 (2025)
- Initial release
- Basic parallel processing with progress bars
- Support for multiple backends (loky, threading, multiprocessing)
- Generator and iterator support
- Context manager support
- Custom logger support (compatible with loguru and standard logging)
- Comprehensive test suite including loguru integration tests
- Memory efficient chunking with auto-calculated chunk sizes
