# Basic Configuration: @configuration

Every application needs simple settings: a debug flag, a timeout, or an API key. `pico-ioc` lets you inject these values directly from the environment or a simple JSON file using the `@configuration` decorator.

This approach is ideal for **flat (key-value) configuration**.

**Note:** For complex, nested configuration (like tree-structured YAML or JSON files), `pico-ioc` provides a more powerful system: **[Configuration Tree Binding](./configuration-binding.md)**. This guide covers only the basic approach.

---

## 1. The Concept: `dataclass` + `ConfigSource`

The system works by combining three elements:

1.  **A `dataclass`**: Defines the settings your application needs.
2.  **The `@configuration` decorator**: Tells `pico-ioc` this `dataclass` should be populated from a configuration source.
3.  **A `ConfigSource`**: An object you pass to `init()` that specifies *where* to find the values (e.g., in environment variables or a file).

---

## 2. Step-by-Step: Injecting from Environment Variables

This is the most common way to configure an application.

### Step 1: Define Your Configuration `dataclass`

Create a `dataclass` with the fields and types you need. Use `@configuration` to mark it. The `prefix` argument is optional but highly recommended, as it lets you namespace all your environment variables (e.g., `APP_DEBUG` instead of just `DEBUG`).

```python
# config.py
from dataclasses import dataclass
from pico_ioc import configuration

@configuration(prefix="APP_")
@dataclass
class AppConfig:
    DEBUG: bool = False  # A default value if not found
    API_KEY: str         # Throws an error if not found and no default is provided
    TIMEOUT: int = 30    # A default value
````

`pico-ioc` will automatically coerce the types. `APP_DEBUG="true"` or `APP_DEBUG="1"` in your environment will become `True` (boolean). `APP_TIMEOUT="60"` will become `60` (integer).

### Step 2: Initialize the Container with `EnvSource`

When you call `init()`, pass an `EnvSource` to the `config` tuple.

```python
# main.py
import os
from pico_ioc import init, EnvSource
from config import AppConfig

# Set environment variables BEFORE calling init()
os.environ["APP_DEBUG"] = "true"
os.environ["APP_API_KEY"] = "my-secret-key-123"

# ...
container = init(
    modules=[__name__],
    config=(
        EnvSource(), # Searches all environment variables
    )
)
```

The simplest pattern is:

  * `@configuration(prefix="APP_")` on your `dataclass`.
  * `EnvSource()` in your `init()`.

This combination will correctly look for `APP_DEBUG`, `APP_API_KEY`, etc.

### Step 3: Inject and Use Your Configuration

Now, any other component can simply request `AppConfig` in its constructor.

```python
# services.py
from pico_ioc import component
from config import AppConfig

@component
class ApiClient:
    def __init__(self, config: AppConfig):
        self.api_key = config.API_KEY
        self.timeout = config.TIMEOUT
        
        if config.DEBUG:
            print("API Client initialized in DEBUG mode")
            
    def call_api(self):
        print(f"Calling API with key: {self.api_key[:4]}...")
        # ... API call logic
        
# main.py
# ... (init() code from above)

client = container.get(ApiClient)
client.call_api()

# Output:
# API Client initialized in DEBUG mode
# Calling API with key: my-s...
```

-----

## 3\. Configuration Sources (`ConfigSource`)

You can pass multiple `ConfigSource` objects to `init()`. `pico-ioc` will check them **in order**, and **the first value found wins**.

### `EnvSource`

As seen above, loads from `os.environ`.

`init(config=(EnvSource(),))`

### `FileSource`

Loads from a simple, flat JSON file.

Assume you have a file `config.json`:

```json
{
  "APP_API_KEY": "key-from-file",
  "APP_TIMEOUT": 90
}
```

You can load it like this:

```python
from pico_ioc import init, FileSource, EnvSource

container = init(
    modules=[__name__],
    config=(
        FileSource("config.json"), # Looks in the file
        EnvSource()                # Looks in the environment
    )
)
```

-----

## 4\. Precedence: The First Wins

The order in the `config` tuple is crucial. `pico-ioc` searches for a key (e.g., `APP_API_KEY`) in each source, one by one, and stops as soon as it finds a value.

**This allows you to override configuration.**

Let's see an example where environment variables override `config.json`:

`config.json`:

```json
{
  "APP_API_KEY": "key-from-file",
  "APP_TIMEOUT": 90
}
```

Environment variables:

```bash
export APP_API_KEY="key-from-env"
```

Initialization code:

```python
container = init(
    modules=[__name__],
    config=(
        EnvSource(),                # 1. Searches environment FIRST
        FileSource("config.json")   # 2. Searches file SECOND
    )
)

config = container.get(AppConfig)

# config.API_KEY will be "key-from-env" (because EnvSource was first)
# config.TIMEOUT will be 90 (it wasn't in EnvSource, but was in FileSource)
```

If you had reversed the order, `FileSource` would have won for any keys present in both.

-----

## Next Steps

This approach is excellent for simple settings. However, when your configuration becomes complex and nested (with sections, lists, and sub-objects), this basic system isn't enough.

For that scenario, `pico-ioc` offers a much more powerful system:

  * **[Configuration Tree Binding (`@configured`)](./configuration-binding.md)**: Learn how to map complex `config.yml` or `config.json` files directly to a graph of `dataclasses`.


