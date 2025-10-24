"""
This check validates that a source has specified a description for all of its tables.

A dbt source is built from two components: the _source name_ and the _source table_. For example, the source below has a name `poffertjes_shop` and defines two tables: `order` and `customers`.

```yaml
sources:
  - name: poffertjes
    description: "Data about our poffertjes shop"
    tables:
      - name: orders
      - name: customers
        description: "The customers that bought a poffertjes"
```

You can see in the example above that the source table `orders` is not documented.

This check would flag the `orders` table as missing documentation.
"""

from typing import Any


minimum_debby_version = "v0.2.0"
description = "Ensure all source tables include a description"
minimum_description_length_description = (
    "The minimum length of the source table's description"
)


def check(source: dict, minimum_description_length: int = 5):
    assert source["description"] is not None
    assert len(source["description"]) > minimum_description_length
