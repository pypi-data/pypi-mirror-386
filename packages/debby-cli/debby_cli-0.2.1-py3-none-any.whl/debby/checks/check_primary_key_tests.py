"""
This check ensures all models have a primary key test defined.

A primary key is a single column or set of of columns that can be used to uniquely identify
a row in the table. Tables without a primary key increase the risk of errors from issues
like fanout, and often indicate an issue with the logical model of the data warehouse.

A model with a well defined primary key must have one of:

- A `not_null` and `unique` test applied on a single column
- A `dbt_utils.unique_combination_of_columns` test applied on the table
- A `not_null` _constraint_ and `unique` test applied on a single column

"""

minimum_debby_version = "v0.2.0"
description = "Ensure all models have a primary key defined"
enabled = True


def check(model: dict, tests: list[dict]):
    column_tests = dict()

    for test in tests:
        column_name = test["column_name"]
        test_name = test["test_metadata"]["name"]
        namespace = test["test_metadata"]["namespace"]

        if (test_name, namespace) == ("unique_combination_of_columns", "dbt_utils"):
            return

        if column_name in column_tests:
            column_tests[column_name].append(test_name)
        else:
            column_tests[column_name] = [test_name]

    for column in model["columns"].values():
        for constraint in column["constraints"]:
            if column["name"] in column_tests:
                column_tests[column["name"]].append(constraint["type"])
            else:
                column_tests[column["name"]] = [constraint["type"]]

    for tests in column_tests.values():
        if "not_null" in tests and "unique" in tests:
            return

    raise AssertionError
