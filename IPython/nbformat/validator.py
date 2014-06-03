from __future__ import print_function
import json
import os

from jsonschema import Draft4Validator, Draft3Validator, SchemaError
import jsonpointer as jsonpointer
from IPython.utils.py3compat import iteritems


from .current import nbformat, nbformat_schema

schema_path = os.path.join(
    os.path.dirname(__file__), "v%d" % nbformat, nbformat_schema)
_schema_json = None

def isvalid(nbjson):
    """Checks whether the given notebook JSON conforms to the current
    notebook format schema. Returns True if the JSON is valid, and
    False otherwise.

    To see the individual errors that were encountered, please use the
    `validate` function instead.

    """

    errors = validate(nbjson)
    return errors == []


def validate(nbjson):
    """Checks whether the given notebook JSON conforms to the current
    notebook format schema, and returns the list of errors.

    """
    
    global _schema_json
    if _schema_json is None:
        # load the schema file
        with open(schema_path, 'r') as fh:
            _schema_json = json.load(fh)

    # resolve internal references
    schema_url = _schema_json['$schema']
    if schema_url == "http://json-schema.org/draft-04/schema":
        Validator = Draft4Validator
    elif schema_url == "http://json-schema.org/draft-03/schema":
        Validator = Draft3Validator
    else:
        raise ValueError("Unsupported schema version: %s" % schema_url)

    schema = resolve_ref(_schema_json)
    schema = jsonpointer.resolve_pointer(schema, '/notebook')
    # if schema_json

    # count how many errors there are
    v = Validator(schema)
    errors = list(v.iter_errors(nbjson))
    return errors


def resolve_ref(json, schema=None):
    """Resolve internal references within the given JSON. This essentially
    means that dictionaries of this form:

    {"$ref": "/somepointer"}

    will be replaced with the resolved reference to `/somepointer`.
    This only supports local reference to the same JSON file.

    """

    if not schema:
        schema = json

    # if it's a list, resolve references for each item in the list
    if type(json) is list:
        resolved = []
        for item in json:
            resolved.append(resolve_ref(item, schema=schema))

    # if it's a dictionary, resolve references for each item in the
    # dictionary
    elif type(json) is dict:
        resolved = {}
        for key, ref in iteritems(json):

            # if the key is equal to $ref, then replace the entire
            # dictionary with the resolved value
            if key == '$ref':
                if len(json) != 1:
                    raise SchemaError(
                        "objects containing a $ref should only have one item")
                pointer = jsonpointer.resolve_pointer(schema, ref)
                resolved = resolve_ref(pointer, schema=schema)

            else:
                resolved[key] = resolve_ref(ref, schema=schema)

    # otherwise it's a normal object, so just return it
    else:
        resolved = json

    return resolved
