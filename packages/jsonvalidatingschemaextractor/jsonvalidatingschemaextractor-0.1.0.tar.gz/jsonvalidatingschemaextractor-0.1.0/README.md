# jsonschemaextractor

An extension to JSON schema allowing extracting values from objects declaratively by specifying them in the schema.

## Installation

```shell
pip install jsonvalidatingschemaextractor
```

## Usage

To extract a value from a JSON object into a field, specify an `extract_to` property in the JSON schema which contains the name
with which the value should be extracted into the resulting dictionary.

In the example below, we extract the `name` field in the JSON to a `username` field in the dictionary.

```python
from jsonschema.validators import Draft7Validator
from jsonvalidatingschemaextractor import Extractor

schema = {
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "extract_to": "username"
        }
    }
}

validator = Draft7Validator(schema=schema)
extractor = Extractor(validator=validator)  # noqa
result = extractor.validate_and_extract({"name": "John Doe"})

assert result.extracted_values == {"username": "John Doe"}
```
