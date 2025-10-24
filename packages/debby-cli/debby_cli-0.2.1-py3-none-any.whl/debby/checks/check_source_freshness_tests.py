"""
This check validates that a source has specified a 'freshness' test for all of its tables.

In the example below, the `orders` table has specified a freshness test, while the `customers` table has not.

```yaml
sources:
  - name: poffertjes
    tables:
      - name: orders
        freshness:
          error_after:
            count: 1
            period: day
      - name: customers
```

This check would flag the `customers` table as missing a source freshness test.
"""

from typing import Any


minimum_debby_version = "v0.2.0"
description = "Ensure all source tables include a freshness test"


def check(source: dict):
    warning_defined = source["freshness"]["warn_after"]["period"] is not None
    error_defined = source["freshness"]["error_after"]["period"] is not None
    assert warning_defined or error_defined
