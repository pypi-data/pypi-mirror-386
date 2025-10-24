from typing import Any


def is_staging_model(model: dict[str, Any]):
    if model["name"].startswith("stg"):
        return True
    elif model["original_file_path"].startswith("staging") and not model[
        "name"
    ].startswith("base"):
        return True
    else:
        return False


def is_base_model(model: dict[str, Any]):
    return model["name"].startswith("base") and model["original_file_path"].startswith(
        "staging"
    )


def is_intermediate_model(model: dict[str, Any]):
    return model["original_file_path"].startswith("intermediate")


def is_mart_model(model: dict[str, Any]):
    return model["original_file_path"].startswith("marts")
