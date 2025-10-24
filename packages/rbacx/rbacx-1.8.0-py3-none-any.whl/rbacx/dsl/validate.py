import json
from importlib import resources
from typing import Any


def validate_policy(policy: dict[str, Any]) -> None:
    try:
        import jsonschema  # type: ignore
    except Exception as e:
        raise RuntimeError("jsonschema is required for validation. Install rbacx[validate].") from e

    schema_text = (
        resources.files("rbacx.dsl").joinpath("policy.schema.json").read_text(encoding="utf-8")
    )
    schema = json.loads(schema_text)
    jsonschema.validate(policy, schema)
