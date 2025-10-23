The core idea is to represent Polars operations and expressions in a JSON
structure. Each step in your data transformation pipeline is an object in the
`"steps"` array of the configuration JSON.

```json
{
  "steps": [
    {
      "operation": "scan_csv",
      "kwargs": {
        "source": "path/to/your/data.csv"
      }
    },
    {
      "operation": "with_columns",
      "kwargs": {
        "new_column": {
          "expr": "add",
          "on": {
            "expr": "col",
            "kwargs": {
              "name": "column_a"
            }
          },
          "kwargs": {
            "other": 10
          }
        }
      }
    },
    {
      "operation": "collect"
    }
  ]
}
```

In this example:

1.  We first load a CSV file using `scan_csv`.
2.  Then, we add a new column named `"new_column"` by adding `10` to
    `"column_a"`.
3.  Finally, we collect the lazy frame into a DataFrame.

This would be equivalent to:

```python
import polars as pl

df = pl.scan_csv("path/to/your/data.csv")
df = df.with_columns(
    new_column=pl.col("column_a").add(10)
)
df = df.collect()
```

## Steps and Operations

Each step is an operation and its arguments. A step defines the function to call
on the result of the previous step for the same dataframe. To use multiple
dataframes, see [Multiple Dataframes](#multiple-dataframes).

Operations are very similar to how [Expressions](#expressions) are implemented,
but they are top-level.

If an operation operates on a dataframe that was not defined before, it executes its function
on the `polars` module instead of the previous dataframe. This is similar to how you would 
define this in code:
```python
# First on the module
df = pl.scan_csv("file.csv")
# Then on the previous dataframe
df = df.collect()
```

## Passing Arguments and Keyword Arguments

You can pass both positional arguments (`args`) and keyword arguments (`kwargs`)
to Polars operations and expressions.

### Args and Kwargs in Operations

```json
{
  "steps": [
    ... // other operations
    {
      "operation": "scan_csv",
      "args": ["tests/test_data/xy.csv"], // <-- args
      "kwargs": { "has_header": true }    // <-- kwargs
    }
  ]
}
```

is equivalent to:

```python
pl.scan_csv("tests/test_data/xy.csv", has_header=True)
```

## Expressions

Polars expressions can be directly embedded as values for arguments or keyword
arguments. See
[Polars expressions](https://docs.pola.rs/api/python/stable/reference/expressions/index.html)
for more info about expressions.

```json
{
  "steps": [
    {
      "operation": "scan_csv",
      "kwargs": { "source": "tests/test_data/xy.csv" }
    },
    {
      "operation": "with_columns",
      "kwargs": {
        "x_eq_y": {
          "expr": "eq",
          "on": { "expr": "col", "kwargs": { "name": "x" } },
          "kwargs": { "other": { "expr": "col", "kwargs": { "name": "y" } } }
        }
      }
    }
  ]
}
```

### Args and Kwargs in Expressions

Works the same as in operations (top-level function calls).

```json
{
  "operation": "with_columns",
  "kwargs": {
    "x_plus_y": {
      "expr": "add",
      "on": {
        "expr": "col",
        "args": ["x"]
      },
      "args": [
        {
          "expr": "col",
          "args": ["y"]
        }
      ]
    }
  }
}
```

is equivalent to:

```python
df = df.with_columns(x_plus_y=pl.col("x").add(pl.col("y")))
```

### Nested Expressions with "on"

Expressions can be chained or nested by using the `"on"` keyword. The expression
defined in `"on"` becomes the subject upon which the current expression
operates.

```json
{
  "operation": "with_columns",
  "kwargs": {
    "sliced_and_upper": {
      "expr": "str.to_uppercase",
      "on": {
        "expr": "str.slice",
        "on": { "expr": "col", "kwargs": { "name": "first" } },
        "kwargs": { "offset": 1, "length": 2 }
      }
    }
  }
}
```

The rule to get the expression nesting is simple. The most inner expression is
the first one you write in Polars, and any chained expressions move up in the
JSON tree, operating "on" the inner expression.

In this example:

1. We select the column `"first"`.
2. We apply `str.slice` (with `offset: 1`, `length: 2`) _on_ the `"first"`
   column.
3. We then apply `str.to_uppercase` _on_ the result of the `str.slice`
   operation.

It is equivalent to:

```python
df = df.with_columns(
    sliced_and_upper=pl.col(name="first")
        .str.slice(offset=1, length=2)
        .str.to_uppercase()
)
```

This allows for building complex, multi-step transformations for a single
column. A more complex example:

```json
{
  "variables": {
    "multiplier": 3
  },
  "steps": [
    {
      "operation": "scan_csv",
      "kwargs": { "source": "tests/test_data/xy.csv" }
    },
    {
      "operation": "with_columns",
      "kwargs": {
        "complex_calc": {
          "expr": "add",
          "on": {
            "expr": "mul",
            "on": { "expr": "col", "args": ["x"] },
            "args": ["$multiplier"]
          },
          "args": [1]
        }
      }
    }
  ]
}
```

This calculates `(x * multiplier) + 1`, or:

```python
df = pl.scan_csv(source="tests/test_data/xy.csv")
df = df.with_columns(complex_calc=pl.col("x").mul(3).add(1))
```

## Variables and Escaping

Configurations can be parameterized using a `"variables"` section. Variables are
prefixed with `$` when used.

```json
{
  "variables": {
    "input_file": "tests/test_data/xy.csv",
    "add_amount": 5
  },
  "steps": [
    { "operation": "scan_csv", "kwargs": { "source": "$input_file" } },
    {
      "operation": "with_columns",
      "kwargs": {
        "x_plus_var": {
          "expr": "add",
          "on": { "expr": "col", "kwargs": { "name": "x" } },
          "kwargs": { "other": "$add_amount" }
        }
      }
    }
  ]
}
```

### Variable Escaping

If you need to use a literal string that starts with a dollar sign, you can
escape it by using two dollar signs (`$$`).

```json
{
  "variables": {
    "my_var": "should_not_be_used"
  },
  "steps": [
    {
      "operation": "scan_csv",
      "kwargs": { "source": "tests/test_data/string_join.csv" }
    },
    {
      "operation": "with_columns",
      "kwargs": {
        "literal_dollar": {
          "expr": "lit",
          "kwargs": { "value": "$$my_var" }
        }
      }
    }
  ]
}
```

In the example above, the `literal_dollar` column will contain the string
`"$my_var"` rather than the value of the `my_var` variable.

You can mix escaped and unescaped variables:

```json
{
  "variables": {
    "actual_value": 42.0,
    "file_path": "tests/test_data/xy.csv"
  },
  "steps": [
    { "operation": "scan_csv", "kwargs": { "source": "$file_path" } },
    {
      "operation": "with_columns",
      "kwargs": {
        "escaped_text": {
          "expr": "lit",
          "kwargs": { "value": "$$actual_value" }
        },
        "real_value": {
          "expr": "lit",
          "kwargs": { "value": "$actual_value" }
        }
      }
    }
  ]
}
```

This will result in a column `"escaped_text"` with the literal string
`"$actual_value"` and a column `"real_value"` with the number `42.0`.

## Custom Functions

You can extend `polars-as-config` with your own Python functions. These
functions are typically applied using Polars' `map_elements` (or similar methods
like `apply` or `map_groups`).

### Defining and Registering Custom Functions

First, define your Python function:

```python
# In your Python code
def multiply_by_two(value: int) -> int:
    return value * 2

def hash_row(row: dict) -> str:
    import hashlib
    row_str = "".join(str(val) for val in row.values())
    return hashlib.sha256(row_str.encode()).hexdigest()
```

Then, register it with the `Config` object:

```python
from polars_as_config.config import Config

custom_functions_dict = {
    "multiply_by_two": multiply_by_two,
    "hash_row": hash_row
}

config_runner = Config().add_custom_functions(custom_functions_dict)
# Now use config_runner.run_config(your_json_config)
```

### Using Custom Functions in JSON

To use a registered custom function, specify its name within a
`"custom_function"` key:

```json
{
  "steps": [
    {
      "operation": "scan_csv",
      "kwargs": { "source": "tests/test_data/xy.csv" }
    },
    {
      "operation": "with_columns",
      "kwargs": {
        "x_doubled": {
          "expr": "map_elements",
          "on": { "expr": "col", "kwargs": { "name": "x" } },
          "kwargs": {
            "function": { "custom_function": "multiply_by_two" },
            "return_dtype": "Utf8"
          }
        },
        "row_hash": {
          "expr": "map_elements",
          "on": { "expr": "struct", "args": [{ "expr": "all" }] },
          "kwargs": {
            "function": { "custom_function": "hash_row" },
            "return_dtype": "Utf8"
          }
        }
      }
    }
  ]
}
```

In this example:

- `multiply_by_two` is applied element-wise to column `"x"`.
- `hash_row` is applied to a struct containing all columns, effectively hashing
  each row.

**Note:** Variables cannot be used to specify the name of a custom function
(e.g., `{"custom_function": "$my_func_name"}` is not supported). The function
name must be a literal string.

## Multiple Dataframes

So far, we've been working with examples that use only one dataframe at a time.
However, `polars-as-config` supports working with multiple named dataframes
simultaneously within a single configuration. This enables complex
multi-dataframe operations like joins, concatenations, and cross-dataframe
transformations.

### The Default Dataframe (None)

When no `"dataframe"` field is specified in a step, the operation uses the
default dataframe identified by `None`. This maintains backward compatibility
with existing single-dataframe configurations:

```json
{
  "steps": [
    { "operation": "scan_csv", "kwargs": { "source": "data.csv" } },
    {
      "operation": "with_columns",
      "kwargs": {
        "new_col": { "expr": "lit", "kwargs": { "value": "default" } }
      }
    }
  ]
}
```

Both steps above operate on the same default dataframe (identified internally as
`None`).

### Named Dataframes

You can specify the name of the dataframe that each operation should work with
using the `"dataframe"` field. This works for both DataFrames and LazyFrames:

```json
{
  "steps": [
    {
      "operation": "scan_csv",
      "dataframe": "customers",
      "kwargs": { "source": "customers.csv" }
    },
    {
      "operation": "scan_csv",
      "dataframe": "orders",
      "kwargs": { "source": "orders.csv" }
    },
    {
      "operation": "with_columns",
      "dataframe": "customers",
      "kwargs": {
        "customer_type": { "expr": "lit", "kwargs": { "value": "premium" } }
      }
    }
  ]
}
```

In this example:

- The first step creates a dataframe named `"customers"`
- The second step creates a separate dataframe named `"orders"`
- The third step adds a column to the `"customers"` dataframe

### Automatic Dataframe Reference Resolution

The most powerful feature of the multiple dataframes system is automatic
reference resolution. When an operation parameter expects a DataFrame or
LazyFrame (detected through Python type hints), you can reference other
dataframes by name using simple strings:

```json
{
  "steps": [
    {
      "operation": "scan_csv",
      "dataframe": "customers",
      "kwargs": { "source": "customers.csv" }
    },
    {
      "operation": "scan_csv",
      "dataframe": "orders",
      "kwargs": { "source": "orders.csv" }
    },
    {
      "operation": "join",
      "dataframe": "customers",
      "kwargs": {
        "other": "orders",
        "left_on": "customer_id",
        "right_on": "customer_id",
        "how": "inner"
      }
    }
  ]
}
```

In the `join` operation:

- The operation is performed on the `"customers"` dataframe
- The `"other"` parameter references the `"orders"` dataframe by name
- The system automatically detects that `other` expects a DataFrame/LazyFrame
  and substitutes the actual dataframe object
- The result is stored back in the `"customers"` dataframe

### Complex Multi-Dataframe Example

Here's a more comprehensive example showing multiple dataframes with
transformations and joins:

```json
{
  "variables": {
    "customer_file": "customers.csv",
    "orders_file": "orders.csv",
    "products_file": "products.csv"
  },
  "steps": [
    {
      "operation": "scan_csv",
      "dataframe": "customers",
      "kwargs": { "source": "$customer_file" }
    },
    {
      "operation": "scan_csv",
      "dataframe": "orders",
      "kwargs": { "source": "$orders_file" }
    },
    {
      "operation": "scan_csv",
      "dataframe": "products",
      "kwargs": { "source": "$products_file" }
    },
    {
      "operation": "with_columns",
      "dataframe": "customers",
      "kwargs": {
        "customer_tier": {
          "expr": "when",
          "kwargs": {
            "condition": {
              "expr": "gt",
              "on": { "expr": "col", "kwargs": { "name": "total_spent" } },
              "kwargs": { "other": 1000 }
            },
            "statement": { "expr": "lit", "kwargs": { "value": "premium" } }
          }
        }
      }
    },
    {
      "operation": "join",
      "dataframe": "orders",
      "kwargs": {
        "other": "products",
        "left_on": "product_id",
        "right_on": "id",
        "how": "left"
      }
    },
    {
      "operation": "join",
      "dataframe": "customers",
      "kwargs": {
        "other": "orders",
        "left_on": "id",
        "right_on": "customer_id",
        "how": "left"
      }
    }
  ]
}
```

This example:

1. Loads three separate dataframes: customers, orders, and products
2. Adds a `customer_tier` column to customers based on spending
3. Joins orders with products to get product details
4. Joins customers with the enriched orders data

### Return Value with Multiple Dataframes

When using multiple dataframes, the `Config.run_config()` method returns a
dictionary mapping dataframe names to their final states:

```python
from polars_as_config.config import Config

config = {
  "steps": [
    {"operation": "scan_csv", "dataframe": "df1", "kwargs": {"source": "file1.csv"}},
    {"operation": "scan_csv", "dataframe": "df2", "kwargs": {"source": "file2.csv"}}
  ]
}

result = Config().run_config(config)
# result is a dict: {"df1": LazyFrame, "df2": LazyFrame}

df1_final = result["df1"].collect()
df2_final = result["df2"].collect()
```

For backward compatibility, the standalone `run_config()` function still returns
only the default dataframe (identified by `None`):

```python
from polars_as_config.config import run_config

config = {
  "steps": [
    {"operation": "scan_csv", "kwargs": {"source": "file.csv"}},
    {"operation": "filter", "kwargs": {"predicates": ...}}
  ]
}

result = run_config(config)  # Returns the default dataframe directly
```

### Error Handling

The system provides clear error messages when dataframe references cannot be
resolved:

```json
{
  "steps": [
    {
      "operation": "scan_csv",
      "dataframe": "customers",
      "kwargs": { "source": "customers.csv" }
    },
    {
      "operation": "join",
      "dataframe": "customers",
      "kwargs": {
        "other": "nonexistent_orders",
        "left_on": "id",
        "right_on": "customer_id"
      }
    }
  ]
}
```

This would raise:

```
ValueError: Dataframe nonexistent_orders not found in current dataframes.
It is possible that the dataframe was not created in the previous steps.
```

### Type-Hint Based Detection

The automatic dataframe reference resolution works by inspecting the type hints
of Polars methods. When a parameter is annotated as expecting a `DataFrame` or
`LazyFrame`, string values for that parameter are treated as dataframe
references rather than literal strings.

This means the feature works seamlessly with any Polars operation that accepts
dataframes as parameters, including:

- `join()` operations
- `concat()` operations
- `union()` operations
- Any custom operations that accept DataFrame/LazyFrame parameters

The system is robust and handles both direct type annotations (`pl.DataFrame`)
and string-based forward references (`"DataFrame"`, `"LazyFrame"`) commonly used
in Polars' internal type system.

### Conversions

Using the `json_to_polars` and `polars_to_json` helpers, you can easily convert
between both formats.

The following test succeeds:

```python

def test_polars_to_json_to_polars():
    expected = """df = polars.read_csv('data.csv')
df = df.with_columns(polars.add(polars.col('a'), 10).alias('new_column', brrr='a'))
df = df.collect()"""
    code = JsonToPolars().json_to_polars(
        PolarsToJson().polars_to_json(expected), format="dataframe"
    )
    assert code == expected
```

The intermediate format is json (the config of this repository).
