# lazy-decorators

The **lazy-decorators** package provides a set of decorators for implementing **lazy** and **cached properties** in Python. It allows expensive computations to be deferred until they are actually needed and caches the results for later use.

---

## Installation

```bash
pip install lazy-decorators
```

---

## Concept

In applications where operations like database connections or heavy data processing exist, executing them early can waste resources. With **lazy-decorators**, such properties are evaluated only when accessed, and the results are cached. If dependencies change, the cache can be **invalidated manually or automatically**.

The package provides two main types of decorators:

- `NotThreadSafe`: For single-threaded environments
- `ThreadSafe`: For multi-threaded environments

---

## Example Usage (NotThreadSafe)

```python
from lazy_decorators import NotThreadSafe


class DatabaseClient(NotThreadSafe.CachedPropertyDependencyMixin):
    
    def __init__(self, configuration):
        self.configuration = configuration
    
    # The connection is created lazily and cached until dependencies change
    @NotThreadSafe.dependent_cached_property(depends_on=['configuration'])
    def connection(self):
        # Create a connection object based on current configuration
        return f'Connection established with: {self.configuration}'


# Create a client with initial configuration
client = DatabaseClient(configuration={'user': 'user_1', 'password': 'pass_1'})

# First access triggers connection creation and caches the result
connection_first = client.connection

# Subsequent access returns the cached connection
connection_cached = client.connection

# Changing configuration does not automatically recreate connection
client.configuration = {'user': 'user_2', 'password': 'pass_2'}
connection_stale = client.connection

# Manually invalidate the cache
client.invalidate_cache('connection')

# Next access recreates the connection and caches it
connection_new = client.connection
```

---

## Example Usage (ThreadSafe)

```python
from lazy_decorators import ThreadSafe
import time
import threading


class DataLoader(ThreadSafe.CachedPropertyDependencyMixin):
    
    def __init__(self, file_path):
        self.file_path = file_path
    
    # Data is loaded lazily and shared safely across multiple threads
    @ThreadSafe.dependent_cached_property(depends_on=['file_path'])
    def data(self):
        # Simulate loading heavy data from file
        time.sleep(2)
        return f'Data loaded successfully from {self.file_path}'


loader = DataLoader(file_path='dataset.csv')


# Function to access data concurrently
def load_data_task():
    # Only first thread triggers data loading, others use cached value
    data = loader.data


# Launch multiple threads accessing the property
threads = [threading.Thread(target=load_data_task) for _ in range(3)]
for thread in threads:
    thread.start()
for thread in threads:
    thread.join()

# Change dependency and invalidate cache
loader.file_path = 'dataset_v2.csv'
loader.invalidate_cache('data')

# Next access reloads the data and caches it again
data_new = loader.data
```

---

## Suggested Study Path

1. **Caches**  
   - [`static_cache.py`](https://github.com/ehsankarbasian/DesignPatterns/blob/main/Python/Others/lazy_instantiation/static_cache.py)
   - [`semi_dynamic_cache.py`](https://github.com/ehsankarbasian/DesignPatterns/blob/main/Python/Others/lazy_instantiation/semi_dynamic_cache.py)
   - [`dynamic_cache.py`](https://github.com/ehsankarbasian/DesignPatterns/blob/main/Python/Others/lazy_instantiation/dynamic_cache.py)
3. **Usage examples:** [`how_to_use.py`](https://github.com/ehsankarbasian/DesignPatterns/blob/main/Python/Others/lazy_instantiation/how_to_use.py)
4. **Lazy object instantiation:** [`lazy_instantiation.py`](https://github.com/ehsankarbasian/DesignPatterns/blob/main/Python/Others/lazy_instantiation/lazy_instantiation.py)
5. **Thread-Safe versions:**  
   - [`simple_thread_safe.py`](https://github.com/ehsankarbasian/DesignPatterns/blob/main/Python/Others/lazy_instantiation/simple_thread_safe.py)  
   - [`dynamic_cache_thread_safe.py`](https://github.com/ehsankarbasian/DesignPatterns/blob/main/Python/Others/lazy_instantiation/dynamic_cache_thread_safe.py)  
   - [`how_to_use_thread_safe.py`](https://github.com/ehsankarbasian/DesignPatterns/blob/main/Python/Others/lazy_instantiation/how_to_use_thread_safe.py)


## Use Cases

- Managing heavy resources such as databases or large files
- Expensive computations that are called repeatedly
- Dynamic dependencies between properties
- Multi-threaded projects requiring safe caching
